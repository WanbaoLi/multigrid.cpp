#!/usr/bin/env python3
"""Generate time-slab matrix-free 2+1 Wilson–Clover RHMC validation fields."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from mpi4py import MPI
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from hmc.distributed_rhmc import DistributedRHMC
from hmc.reference import lime_sha256, write_lime
from generate import atomic_json

CHECKPOINT_COMPATIBILITY = (
    "lattice_xyzt", "beta", "mass_light", "mass_strange", "csw", "mpi_ranks",
    "threads", "seed", "torch_version", "native_schur_sha256", "integrator",
    "trajectory_length", "integration_steps", "gauge_substeps_per_drift",
    "strange_md_interval", "strange_rational_poles", "md_relative_true_residual_tolerance",
    "direct_clover_adjoint", "packed_temporal_faces", "compact_spin_force",
    "half_power_rational_method", "rational_coefficients_sha256",
)


def on_root(comm, function):
    """Share root I/O failures before any rank proceeds to the next collective."""
    value, error = None, None
    if comm.rank == 0:
        try:
            value = function()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    value, error = comm.bcast((value, error), root=0)
    if error:
        raise RuntimeError(error)
    return value


def resume_from(path, report, rng, comm):
    sys.path.insert(0, str(ROOT / "bindings"))
    from lqcd_cpu.io import read_lime_gauge

    def read_checkpoint():
        previous = json.loads(path.read_text())
        previous.setdefault("direct_clover_adjoint", False)
        previous.setdefault("packed_temporal_faces", False)
        previous.setdefault("compact_spin_force", False)
        previous.setdefault("half_power_rational_method", "quadrature")
        previous.setdefault("rational_coefficients_sha256", report["rational_coefficients_sha256"])
        mismatches = [key for key in CHECKPOINT_COMPATIBILITY if previous.get(key) != report[key]]
        if mismatches:
            raise ValueError(f"Checkpoint parameters differ: {', '.join(mismatches)}")
        saved = previous.get("saved_configurations", [])
        if not saved or "rng_state" not in saved[-1]:
            raise ValueError("No saved configuration with a restart state")
        checkpoint = saved[-1]
        if type(checkpoint.get("trajectory")) is not int or checkpoint["trajectory"] < 1:
            raise ValueError("Invalid checkpoint trajectory index")
        gauge_file, rng_file = checkpoint["file"], checkpoint["rng_state"]["file"]
        if Path(gauge_file).name != gauge_file or Path(rng_file).name != rng_file:
            raise ValueError("Checkpoint filenames must be relative to the report directory")
        gauge_path, rng_path = path.parent / gauge_file, path.parent / rng_file
        if lime_sha256(gauge_path) != checkpoint["sha256"]:
            raise ValueError("Checkpoint LIME digest mismatch")
        if lime_sha256(rng_path) != checkpoint["rng_state"]["sha256"]:
            raise ValueError("Checkpoint RNG digest mismatch")
        states = np.load(rng_path, allow_pickle=False)
        if states.shape != (comm.size, rng.get_state().numel()) or states.dtype != np.uint8:
            raise ValueError("Invalid rank-local RNG state table")
        return checkpoint["trajectory"], gauge_path, checkpoint["sha256"], states

    last, gauge_path, digest, states = on_root(comm, read_checkpoint)
    error = None
    try:
        rng.set_state(torch.from_numpy(states[comm.rank]))
    except RuntimeError as exc:
        error = f"Rank {comm.rank} could not restore its RNG state: {exc}"
    errors = comm.allgather(error)
    if any(errors):
        raise ValueError(next(error for error in errors if error is not None))
    gauge = read_lime_gauge(gauge_path, grid=(1, 1, 1, comm.size),
                            coords=(0, 0, 0, comm.rank), comm=comm)
    return torch.from_numpy(gauge.reshape(-1, 4, 3, 3)), dict(
        trajectory=last, configuration_sha256=digest, report=str(path.resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resume-from", type=Path,
                        help="resume the newest saved LIME and RNG state from a previous result.json")
    parser.add_argument("--library", type=Path, default=os.environ.get("LQCD_HMC_SCHUR_LIBRARY"))
    parser.add_argument("--lattice", nargs=4, type=int, default=(4, 4, 4, 4))
    parser.add_argument("--beta", type=float, default=5.6)
    parser.add_argument("--mass-light", type=float, default=.5)
    parser.add_argument("--mass-strange", type=float, default=.8)
    parser.add_argument("--csw", type=float, default=1.)
    parser.add_argument("--strange-interval", type=float, nargs=2, default=(.004, 4.),
                        metavar=("LOW", "HIGH"), help="fixed interval for the strange Schur normal spectrum")
    parser.add_argument("--trajectories", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--length", type=float, default=.08)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--gauge-steps", type=int, default=0,
                        help="inner Omelyan gauge steps per fermion drift, or zero for one time scale")
    parser.add_argument("--md-order", type=int, default=32,
                        help="strange-force quadrature order per tail (twice as many poles)")
    parser.add_argument("--md-tolerance", type=float, default=1e-12,
                        help="relative true residual for the light and strange MD solves")
    parser.add_argument("--direct-clover", action="store_true",
                        help="evaluate Clover leaf derivatives with the local analytic adjoint")
    parser.add_argument("--packed-faces", action="store_true",
                        help="apply the native Schur operator directly to packed temporal faces")
    parser.add_argument("--compact-spin", action="store_true",
                        help="differentiate a two-component Wilson hopping projection")
    parser.add_argument("--zolotarev", action="store_true",
                        help="use elliptic inverse-square-root coefficients for the strange MD and endpoint")
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    if args.library is None:
        parser.error("Provide the native Schur library")
    lower, upper = args.strange_interval
    if not 0 < lower < upper < math.inf:
        parser.error("The strange spectral interval must contain ascending positive finite endpoints")
    if (args.threads < 1 or args.steps < 1 or args.gauge_steps < 0 or args.md_order < 1
            or not math.isfinite(args.length) or args.length <= 0
            or not 0 < args.md_tolerance < 1
            or not 0 <= args.warmup < args.trajectories
            or not 1 <= args.save_every <= args.trajectories - args.warmup):
        parser.error("Invalid trajectory or thread parameters")
    torch.set_num_threads(args.threads)
    comm = MPI.COMM_WORLD.Dup()
    try:
        report = run(args, comm)
        if comm.rank == 0:
            print(json.dumps(dict(complete=True, accepted=report["accepted"],
                                  configurations=len(report["saved_configurations"]))))
    finally:
        comm.Free()


def run(args, comm):
    model = DistributedRHMC(args.lattice, args.beta, args.mass_light, args.mass_strange,
                            args.csw, comm, args.library, interval=args.strange_interval,
                            md_order=args.md_order, md_tolerance=args.md_tolerance,
                            direct_clover=args.direct_clover, packed_faces=args.packed_faces,
                            compact_spin=args.compact_spin, zolotarev=args.zolotarev)
    commit = on_root(comm, lambda: subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip())
    lib_digest = on_root(comm, lambda: lime_sha256(args.library))
    terms = (model.md_terms, model.endpoint_terms, model.refresh_terms)
    rational_digest = hashlib.sha256(json.dumps(terms, allow_nan=False).encode()).hexdigest()
    rng = torch.Generator().manual_seed(args.seed + comm.rank)
    report = dict(complete=False, algorithm="time-slab matrix-free 2+1 RHMC",
                  lattice_xyzt=list(args.lattice), beta=args.beta, mass_light=args.mass_light,
                  mass_strange=args.mass_strange, csw=args.csw, nf="2+1", rhmc=True,
                  mpi_ranks=comm.size, threads=args.threads, seed=args.seed,
                  timing_aggregation="maximum rank elapsed time for each phase independently",
                  hamiltonian_difference_method="reduce per-rank differences of corresponding action terms",
                  rank_seed_rule="seed + MPI rank", source_commit=commit, native_schur_sha256=lib_digest,
                  torch_version=str(torch.__version__),
                  strange_md_interval=list(model.interval), strange_rational_grid_error=model.grid_errors,
                  strange_cold_free_gap=model.strange_cold_gap,
                  strange_rational_poles=dict(md=len(model.md_terms), endpoint=len(model.endpoint_terms),
                                              refresh=len(model.refresh_terms)),
                  md_relative_true_residual_tolerance=model.md_tolerance,
                  direct_clover_adjoint=model.direct_clover,
                  packed_temporal_faces=model.packed_faces,
                  compact_spin_force=model.compact_spin,
                  half_power_rational_method="zolotarev" if model.zolotarev else "quadrature",
                  rational_coefficients_sha256=rational_digest,
                  trajectory_length=args.length, integration_steps=args.steps, integrator="omelyan",
                  gauge_substeps_per_drift=args.gauge_steps,
                  thermalization_established=False, independent_samples_established=False,
                  trajectories=args.trajectories, warmup=args.warmup, samples=[], saved_configurations=[])
    if args.resume_from is None:
        gauge, first_trajectory = model.cold(), 0
    else:
        gauge, checkpoint = resume_from(args.resume_from, report, rng, comm)
        report["resumed_from"] = checkpoint
        first_trajectory = checkpoint["trajectory"]
    on_root(comm, lambda: args.output.mkdir(parents=True))
    for segment_index in range(1, args.trajectories + 1):
        trajectory = first_trajectory + segment_index
        start = perf_counter()
        gauge, sample = model.trajectory(gauge, rng, args.length, args.steps, gauge_steps=args.gauge_steps)
        total = perf_counter() - start
        phases = sample["phase_seconds"]
        force_phases = sample["force_seconds"]
        elapsed = np.array([total, *phases.values(), *force_phases.values()], dtype=np.float64)
        comm.Allreduce(MPI.IN_PLACE, elapsed, op=MPI.MAX)
        seconds, *phase_seconds = elapsed.tolist()
        phases.update(zip(phases, phase_seconds[:len(phases)]))
        force_phases.update(zip(force_phases, phase_seconds[len(phases):]))
        sample.update(model.observables(gauge), trajectory=trajectory,
                      warmup=segment_index <= args.warmup, seconds=seconds)
        report["samples"].append(sample)
        if segment_index > args.warmup and (segment_index - args.warmup) % args.save_every == 0:
            local = gauge.contiguous().numpy()
            global_links = np.empty((comm.size, *local.shape), dtype=local.dtype) if comm.rank == 0 else None
            comm.Gather(local, global_links, root=0)
            rng_states = comm.gather(rng.get_state().numpy(), root=0)

            def save():
                path = args.output / f"hmc_{trajectory:06d}.lime"
                write_lime(path, global_links, args.lattice,
                           {key: report[key] for key in ("nf", "beta", "mass_light", "mass_strange",
                                                         "csw", "source_commit", "mpi_ranks", "seed")})
                rng_path = path.with_suffix(".rng.npy")
                temporary = rng_path.with_suffix(".tmp")
                with temporary.open("wb") as stream:
                    np.save(stream, np.stack(rng_states), allow_pickle=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(rng_path)
                return dict(file=path.name, trajectory=trajectory, sha256=lime_sha256(path),
                            plaquette=sample["plaquette"], bytes=path.stat().st_size,
                            rng_state=dict(file=rng_path.name, sha256=lime_sha256(rng_path)))

            report["saved_configurations"].append(on_root(comm, save))
        on_root(comm, lambda: atomic_json(args.output / "result.json", report))
        if comm.rank == 0:
            print(json.dumps(sample), flush=True)
    accepted = sum(item["accepted"] for item in report["samples"])
    if not report["saved_configurations"] or (not accepted and args.resume_from is None):
        raise RuntimeError("The run must save an updated gauge field")
    report.update(complete=True, accepted=accepted, acceptance_rate=accepted / args.trajectories)
    on_root(comm, lambda: atomic_json(args.output / "result.json", report))
    return report


if __name__ == "__main__":
    main()
