#!/usr/bin/env python3
"""Generate time-slab matrix-free 2+1 Wilson–Clover RHMC validation fields."""
import argparse
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--library", type=Path, default=os.environ.get("LQCD_HMC_SCHUR_LIBRARY"))
    parser.add_argument("--lattice", nargs=4, type=int, default=(4, 4, 4, 4))
    parser.add_argument("--beta", type=float, default=5.6)
    parser.add_argument("--mass-light", type=float, default=.5)
    parser.add_argument("--mass-strange", type=float, default=.8)
    parser.add_argument("--csw", type=float, default=1.)
    parser.add_argument("--trajectories", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--length", type=float, default=.08)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--save-every", type=int, default=1)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    if args.library is None:
        parser.error("Provide the native Schur library")
    if (args.threads < 1 or args.steps < 1 or not math.isfinite(args.length) or args.length <= 0
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
                            args.csw, comm, args.library)
    commit = on_root(comm, lambda: subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip())
    lib_digest = on_root(comm, lambda: lime_sha256(args.library))
    on_root(comm, lambda: args.output.mkdir(parents=True))
    rng = torch.Generator().manual_seed(args.seed + comm.rank)
    gauge = model.cold()
    report = dict(complete=False, algorithm="time-slab matrix-free 2+1 RHMC",
                  lattice_xyzt=args.lattice, beta=args.beta, mass_light=args.mass_light,
                  mass_strange=args.mass_strange, csw=args.csw, nf="2+1", rhmc=True,
                  mpi_ranks=comm.size, threads=args.threads, seed=args.seed,
                  timing_aggregation="maximum rank elapsed time for each phase independently",
                  rank_seed_rule="seed + MPI rank", source_commit=commit, native_schur_sha256=lib_digest,
                  strange_md_interval=model.interval, strange_rational_grid_error=model.grid_errors,
                  trajectory_length=args.length, integration_steps=args.steps, integrator="omelyan",
                  thermalization_established=False, independent_samples_established=False,
                  trajectories=args.trajectories, warmup=args.warmup, samples=[], saved_configurations=[])
    for trajectory in range(1, args.trajectories + 1):
        start = perf_counter()
        gauge, sample = model.trajectory(gauge, rng, args.length, args.steps)
        total = perf_counter() - start
        phases = sample["phase_seconds"]
        force_phases = sample["force_seconds"]
        elapsed = np.array([total, *phases.values(), *force_phases.values()], dtype=np.float64)
        comm.Allreduce(MPI.IN_PLACE, elapsed, op=MPI.MAX)
        seconds, *phase_seconds = elapsed.tolist()
        phases.update(zip(phases, phase_seconds[:len(phases)]))
        force_phases.update(zip(force_phases, phase_seconds[len(phases):]))
        sample.update(model.observables(gauge), trajectory=trajectory,
                      warmup=trajectory <= args.warmup, seconds=seconds)
        report["samples"].append(sample)
        if trajectory > args.warmup and (trajectory - args.warmup) % args.save_every == 0:
            local = gauge.contiguous().numpy()
            global_links = np.empty((comm.size, *local.shape), dtype=local.dtype) if comm.rank == 0 else None
            comm.Gather(local, global_links, root=0)

            def save():
                path = args.output / f"hmc_{trajectory:06d}.lime"
                write_lime(path, global_links, args.lattice,
                           {key: report[key] for key in ("nf", "beta", "mass_light", "mass_strange",
                                                         "csw", "source_commit", "mpi_ranks", "seed")})
                return dict(file=path.name, trajectory=trajectory, sha256=lime_sha256(path),
                            plaquette=sample["plaquette"], bytes=path.stat().st_size)

            report["saved_configurations"].append(on_root(comm, save))
        on_root(comm, lambda: atomic_json(args.output / "result.json", report))
        if comm.rank == 0:
            print(json.dumps(sample), flush=True)
    accepted = sum(item["accepted"] for item in report["samples"])
    if not report["saved_configurations"] or not accepted:
        raise RuntimeError("The run must save an updated gauge field")
    report.update(complete=True, accepted=accepted, acceptance_rate=accepted / args.trajectories)
    on_root(comm, lambda: atomic_json(args.output / "result.json", report))
    return report


if __name__ == "__main__":
    main()
