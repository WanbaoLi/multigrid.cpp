"""Health check for one LIME gauge: one RHS and a complete 12-column solve.

The gauge read, optional stout pass and hierarchy setup happen once. Timed
samples start only after ``setup`` and every solve uses a zero initial guess.
The script is deliberately independent of the campaign ledger: it is a small
geometry-aware smoke/acceptance driver for real CPU nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import socket
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "bindings"))
SOLVE_TUNING_KEYS = {
    "LQCD_MG_SAP_STEPS", "LQCD_MG_SAP_CYCLES", "LQCD_MG_COARSE_IT",
    "LQCD_MG_COARSE_TOL", "LQCD_CORRECTION_BASE_TOL", "LQCD_FLOAT_CORRECTION_VERIFY",
    "LQCD_FINE_TEAM_FUSED", "LQCD_COARSE_CGS2", "LQCD_RESTRICT_FLOAT",
    "LQCD_GCR_FUSED", "LQCD_COARSE_THREADS", "LQCD_COARSE_BATCH_REDUCE",
    "LQCD_OUTER_FLOAT", "LQCD_RELIABLE_FUSED", "LQCD_SAP_SCHEDULE",
}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def apply_context_environment(context):
    """Clear inherited solve-only knobs before the library is loaded."""
    for key in SOLVE_TUNING_KEYS:
        os.environ.pop(key, None)
    os.environ.update({str(key): str(value) for key, value in context.items()})


def load_plan(path):
    if path is None:
        return {}, {}, None, None
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = plan.get("cases", [])
    if len(cases) != 1:
        raise ValueError("health plan must contain exactly one case")
    case = cases[0]
    return (plan, plan.get("context_environment", {}),
            int(plan.get("setup_threads", case["threads"])),
            case)


def local_geometry(lattice, ranks, rank):
    if ranks < 1 or lattice[3] % ranks:
        raise ValueError("MPI ranks must divide the time extent")
    local = tuple(n // p for n, p in zip(lattice, (1, 1, 1, ranks)))
    return (1, 1, 1, ranks), (0, 0, 0, rank), local


def point_source(lattice, grid, coords, point, source_scale):
    """Return a rank-local lexical source [t,z,y,x,spin,color]."""
    import numpy as np
    local = tuple(n // p for n, p in zip(lattice, grid))
    source = np.zeros((local[3], local[2], local[1], local[0], 4, 3), dtype=np.complex128)
    local_point = tuple(p - c * n for p, c, n in zip(point, coords, local))
    if all(0 <= p < n for p, n in zip(local_point, local)):
        px, py, pz, pt = local_point
        source[pt, pz, py, px, 0, 0] = source_scale
    return source


def phase_summary(samples):
    times = [float(row["wall_seconds"]) for row in samples]
    return dict(first_seconds=times[0], second_seconds=times[1],
                steady_median_seconds=statistics.median(times[1:]),
                samples=len(times))


def native_timing(stats):
    """Count a shared native batch timer once, retaining per-column metadata."""
    solver_seconds = api_seconds = 0.0
    index = 0
    while index < len(stats):
        row = stats[index]
        solver_seconds += float(row["solver_seconds"])
        api_seconds += float(row["api_seconds"])
        index += int(row.get("batch_size", 1)) if row.get("timing_scope") == "shared_batch" else 1
    return dict(native_solver_seconds=solver_seconds, native_api_seconds=api_seconds,
                correction_solves_occurred=any(int(row.get("refinement_steps", 0)) > 0 for row in stats),
                refinement_steps=[int(row.get("refinement_steps", 0)) for row in stats])


def collective(comm, function, root_only=False):
    value = error = None
    try:
        if not root_only or comm.rank == 0:
            value = function()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    errors = comm.allgather(error)
    if any(errors):
        raise RuntimeError(f"collective health operation failed: {errors}")
    return comm.bcast(value, root=0) if root_only else value


def source_provenance():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(PROJECT), *args], text=True).strip()
    return dict(source_commit=git("rev-parse", "HEAD"),
                source_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
                source_tracked_status=git("status", "--porcelain", "--untracked-files=no"),
                driver_sha256=digest(__file__))


def finite_stats(stats, tol):
    return all(bool(row.get("converged")) and math.isfinite(float(row["true_residual"]))
               and float(row["true_residual"]) <= tol for row in stats)


def _measure(comm, function):
    from mpi4py import MPI
    comm.Barrier()
    begin = time.perf_counter()
    value = function()
    elapsed = comm.allreduce(time.perf_counter() - begin, op=MPI.MAX)
    return value, elapsed


def run(args):
    import numpy as np
    from mpi4py import MPI
    from lqcd_cpu import Solver
    from lqcd_cpu.io import read_lime_gauge, read_lime_metadata
    from lqcd_cpu.propagator_io import write_propagator
    from lqcd_cpu.smearing import stout_smear

    comm = MPI.COMM_WORLD
    rank = comm.rank
    ranks = comm.size
    metadata = collective(comm, lambda: read_lime_metadata(args.gauge))
    lattice = tuple(metadata["lattice_xyzt"])
    grid, coords, local = local_geometry(lattice, ranks, rank)
    plan, context, setup_threads, case = load_plan(args.plan)
    case = {} if case is None else case
    setup_threads = setup_threads or args.threads or int(
        os.environ.get("LQCD_CPU_THREADS", os.environ.get("OMP_NUM_THREADS", len(os.sched_getaffinity(0)))))
    solve_threads = int(args.threads or case.get("threads", setup_threads))
    batch = int(case.get("batch", args.batch))
    solve_environment = dict(case.get("environment", {}))
    if not 1 <= batch <= 12:
        raise ValueError("RHS batch must be between 1 and 12")
    resolved_mass = metadata.get("mass") if args.mass is None else args.mass
    resolved_csw = metadata.get("csw") if args.csw is None else args.csw
    if resolved_mass is None or resolved_csw is None:
        raise ValueError("--mass and --csw are required when LIME metadata omits them")
    mass, csw = float(resolved_mass), float(resolved_csw)
    if not math.isfinite(mass) or not math.isfinite(csw):
        raise ValueError("mass and csw must be finite")
    output = Path(args.output).resolve()
    collective(comm, lambda: output.mkdir(parents=True, exist_ok=False), root_only=True)
    report = dict(
        complete=False, measurements_complete=False, phase="created",
        backend=args.backend, host=socket.gethostname(), lattice_xyzt=list(lattice),
        grid_xyzt=list(grid), coords_xyzt=list(coords), ranks=ranks,
        block_xyzt=list(args.block), mass=mass, csw=csw, tol=args.tol,
        source_xyzt=list(args.source), source_scale=args.source_scale,
        normalization="mass", zero_initial_guess=True,
        gauge_sha256=collective(comm, lambda: digest(args.gauge), root_only=True),
        gauge_path=str(Path(args.gauge).resolve()),
        context_environment=context, solve_environment=solve_environment,
        setup_threads=setup_threads, solve_threads=solve_threads, batch=batch,
        resources=[], single_samples=[], twelve_samples=[],
        stout=dict(steps=args.stout_steps, rho=args.stout_rho, dir_ignore=args.stout_dir_ignore),
        gamma_basis="DeGrand-Rossi", fermion_t_boundary=-1, gauge_t_boundary=1,
        gauge_reunitarized=False, seed=args.seed,
    )
    report.update(collective(comm, source_provenance, root_only=True))
    placement = comm.allgather(dict(rank=rank, cpus=sorted(os.sched_getaffinity(0)),
        omp_places=os.environ.get("OMP_PLACES"), omp_proc_bind=os.environ.get("OMP_PROC_BIND")))
    report["placement"] = placement
    if rank == 0:
        atomic(output / "checkpoint.json", report)

    apply_context_environment(context)
    os.environ["LQCD_RHS_BATCH"] = "1"
    gauge, io_seconds = _measure(comm, lambda: read_lime_gauge(
        args.gauge, grid, coords, comm=comm))
    gauge, smear_seconds = _measure(comm, lambda: stout_smear(
        gauge, steps=args.stout_steps, rho=args.stout_rho,
        dir_ignore=args.stout_dir_ignore, comm=comm))
    if rank == 0:
        report.update(lime_metadata=metadata, lime_read_seconds=io_seconds,
                      stout_seconds=smear_seconds, phase="preprocessed")
        atomic(output / "checkpoint.json", report)
    collective(comm, lambda: np.save(output / f"gauge_rank{rank:05d}.npy", gauge, allow_pickle=False))
    source = point_source(lattice, grid, coords, tuple(args.source), args.source_scale)
    single_final = None
    twelve_final = None
    with Solver(lattice, grid, mass=mass, csw=csw, block=args.block,
                threads=setup_threads, seed=args.seed, normalization="mass",
                library=args.library, backend=args.backend, comm=comm) as solver:
        report["capabilities"] = solver.capabilities
        report["library"] = str(Path(solver.lib._name).resolve())
        report["library_sha256"] = collective(comm, lambda: digest(report["library"]), root_only=True)
        _, report["gauge_load_clover_seconds"] = _measure(comm, lambda: solver.load_gauge(gauge, layout="lex"))
        setup_seconds = comm.allreduce(float(solver.setup()), op=MPI.MAX)
        solver.set_threads(solve_threads)
        report["setup_seconds"] = setup_seconds
        report["resources"] = comm.allgather(dict(rank=rank, threads=solve_threads,
            cpus=sorted(os.sched_getaffinity(0)), omp_places=os.environ.get("OMP_PLACES"),
            omp_proc_bind=os.environ.get("OMP_PROC_BIND")))
        if rank == 0:
            report["phase"] = "setup_complete"
            atomic(output / "checkpoint.json", report)

        os.environ.update({str(k): str(v) for k, v in solve_environment.items()})
        single_samples = []
        for index in range(args.repeats):
            solution, elapsed = _measure(comm, lambda: solver.solve(source, args.tol, layout="lex"))
            stats = [dict(solver.last_result)]
            if not finite_stats(stats, args.tol):
                raise RuntimeError("single-column true residual gate failed")
            single_samples.append(dict(run=index + 1, wall_seconds=elapsed,
                                       stats=stats, timing_scope="single_column_api", **native_timing(stats)))
            single_final = solution
        report["single_samples"] = single_samples
        report["single_summary"] = phase_summary(single_samples)
        collective(comm, lambda: np.save(output / f"single_rank{rank:05d}.npy", single_final, allow_pickle=False))
        if rank == 0:
            report["phase"] = "single_complete"
            atomic(output / "checkpoint.json", report)

        os.environ["LQCD_RHS_BATCH"] = str(batch)
        twelve_samples = []
        for index in range(args.repeats):
            (propagator, stats), elapsed = _measure(comm, lambda: solver.solve_propagator(
                tuple(args.source), args.tol, source_scale=args.source_scale, layout="lex"))
            if len(stats) != 12 or not finite_stats(stats, args.tol):
                raise RuntimeError("full12 true residual gate failed")
            twelve_samples.append(dict(run=index + 1, wall_seconds=elapsed,
                                       stats=[dict(item) for item in stats],
                                       timing_scope="full12_api", batch=batch, **native_timing(stats)))
            twelve_final = propagator
        report["twelve_samples"] = twelve_samples
        report["twelve_summary"] = phase_summary(twelve_samples)
        if rank == 0:
            report["phase"] = "twelve_complete"
            atomic(output / "checkpoint.json", report)

        if args.profile_diagnostic:
            os.environ["LQCD_VERBOSE"] = "1"
            (_, stats), elapsed = _measure(comm, lambda: solver.solve_propagator(
                tuple(args.source), args.tol, source_scale=args.source_scale, layout="lex"))
            if len(stats) != 12 or not finite_stats(stats, args.tol):
                raise RuntimeError("diagnostic full12 true residual gate failed")
            report["diagnostic"] = dict(wall_seconds=elapsed, stats=stats,
                timing_scope="diagnostic_full12_api", accepted_timing=False, **native_timing(stats))

    # Compare the same source column solved through the scalar and 12-RHS API.
    first = twelve_final[..., :, 0, :, 0]
    delta = single_final - first
    numerator = comm.allreduce(float(np.vdot(delta, delta).real))
    denominator = comm.allreduce(float(np.vdot(first, first).real))
    consistency = math.sqrt(numerator / denominator) if denominator else float("inf")
    if consistency > 1e-6:
        raise RuntimeError(f"single/full12 first-column mismatch: {consistency}")
    write_propagator(output / "propagator.npy", twelve_final, lattice, grid, coords, comm)
    report.update(measurements_complete=True, phase="measurements_complete",
                  consistency_first_column=consistency,
                  single_max_true_residual=max(s["true_residual"] for row in report["single_samples"] for s in row["stats"]),
                  twelve_max_true_residual=max(s["true_residual"] for row in report["twelve_samples"] for s in row["stats"]),
                  propagator_sha256=collective(comm, lambda: digest(output / "propagator.npy"), root_only=True))
    if collective(comm, lambda: digest(report["library"]), root_only=True) != report["library_sha256"]:
        raise RuntimeError("loaded library changed during health measurements")
    gauge_hash = collective(comm, lambda: digest(output / f"gauge_rank{rank:05d}.npy"))
    single_hash = collective(comm, lambda: digest(output / f"single_rank{rank:05d}.npy"))
    report["output_gauge_files"] = comm.allgather((rank, gauge_hash))
    report["output_single_files"] = comm.allgather((rank, single_hash))
    if rank == 0:
        report["checkpoint_sha256"] = digest(output / "checkpoint.json")
        atomic(output / "result.json", report)
    comm.Barrier()
    return report


def main(argv=None):
    from mpi4py import MPI
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gauge", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("x86", "arm"), required=True)
    parser.add_argument("--mass", type=float)
    parser.add_argument("--csw", type=float)
    parser.add_argument("--block", nargs=4, type=int, required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--source", nargs=4, type=int, default=(0, 0, 0, 0))
    parser.add_argument("--source-scale", type=float, default=1.0)
    parser.add_argument("--stout-steps", type=int, default=1)
    parser.add_argument("--stout-rho", type=float, default=0.125)
    parser.add_argument("--stout-dir-ignore", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--tol", type=float, default=1e-8)
    parser.add_argument("--seed", type=int, default=1024)
    parser.add_argument("--profile-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    if args.repeats < 2 or not 0 < args.tol < 1:
        parser.error("--repeats must be >=2 and --tol must be in (0,1)")
    try:
        run(args)
    except Exception as error:
        output = Path(args.output)
        if MPI.COMM_WORLD.rank == 0 and output.is_dir():
            atomic(output / "failure.json", {"complete": False, "error": repr(error)})
        raise


if __name__ == "__main__":
    main()
