#!/usr/bin/env python3
"""Measure actual spin-color point-source propagator columns with KUPL.

Run from a sourced PyQCU checkout. Gauge/Clover/coarse assets and the LatticeSet
are reused; every column has a unit point RHS and a zero initial solution.
KUPL internally constructs a LegacyCloverMultigrid object on each ABI call;
that native workspace cost is deliberately included in solve time.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import statistics
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from mpi4py import MPI

from pyqcu.testing.simple import kupl_multigrid as mg
from pyqcu.testing.simple.kupl_bistabcg import (
    NumpyTensor, PARITY, PLAN_CLOVER, PLAN_SOLVER, SET_PLAN,
    cpu_memory_snapshot, kupl_backend, load_gauge, make_params,
    prebind_kupl_inputs,
)
from pyqcu.testing.simple.kupl_residual import distributed_relative_residual
from pyqcu.testing.simple._common import qcu_gauge_to_kupl, resolve_csw
from pyqcu.tools._legacy_mg_cache import (
    file_sha256, legacy_mg_cache_identity, logical_array_sha256,
    save_legacy_mg_cache, validate_legacy_mg_cache,
)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def timed(comm, operation):
    comm.Barrier()
    started = time.perf_counter()
    value = operation()
    elapsed = time.perf_counter() - started
    return value, float(comm.allreduce(elapsed, op=MPI.MAX))


def point_rhs(array: np.ndarray, point, starts, local, column: int) -> None:
    """Fill native [parity,12,x,y,z,t/2], component=3*spin+color."""
    array.fill(0)
    if all(starts[d] <= point[d] < starts[d] + local[d] for d in range(4)):
        x, y, z, t = (point[d] - starts[d] for d in range(4))
        parity = sum(point) % 2
        array[parity, column, x, y, z, t // 2] = 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gauge", type=Path, required=True)
    parser.add_argument("--lat", nargs=4, type=int, default=(24, 24, 24, 64))
    parser.add_argument("--grid", nargs=4, type=int)
    parser.add_argument("--mass", type=float)
    parser.add_argument("--csw", type=float)
    parser.add_argument("--dtype", choices=("c64", "c128"), default="c64")
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--max-iter", type=int, default=2000)
    parser.add_argument("--max-residual-restarts", type=int, default=2,
        help="maximum fine BiCGStab warm restarts of the same RHS after an independent residual failure (0 disables)")
    parser.add_argument("--levels", type=int, choices=(1, 2), default=2)
    parser.add_argument("--restart", type=int, default=5)
    parser.add_argument("--dof", nargs=2, type=int, default=(12, 2))
    parser.add_argument("--mg-grid", nargs=4, type=int, default=(2, 2, 2, 2))
    parser.add_argument("--coarse-max-iter", type=int, default=200)
    parser.add_argument("--coarse-tol-factor", type=float, default=1e4)
    parser.add_argument("--nv-iters", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--build-cache-only", action="store_true")
    parser.add_argument("--no-deflate", action="store_true")
    parser.add_argument("--source-point", "--point", nargs=4, type=int, default=(0, 0, 0, 0))
    parser.add_argument("--boundary", nargs=4, type=int, choices=(-1, 1), default=(1, 1, 1, 1),
        help="physical boundary signs already encoded in input links; this driver does not apply them again")
    parser.add_argument("--columns", nargs="+", type=int, default=list(range(12)))
    parser.add_argument("--verbose-native", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank, size = comm.rank, comm.size
    grid = tuple(args.grid or (1, size, 1, 1))
    lattice, point = tuple(args.lat), tuple(args.source_point)
    if np.prod(grid) != size:
        parser.error("--grid product must equal the MPI size")
    if len(set(args.columns)) != len(args.columns) or any(c not in range(12) for c in args.columns):
        parser.error("--columns must contain distinct indices from 0 through 11")
    if any(not 0 <= point[d] < lattice[d] for d in range(4)):
        parser.error("--source-point lies outside the lattice")
    if args.atol <= 0 or args.max_iter <= 0:
        parser.error("--atol and --max-iter must be positive")
    if args.max_residual_restarts < 0:
        parser.error("--max-residual-restarts must be nonnegative")
    coarse_active = args.levels > 1 and args.restart > 0
    if args.build_cache_only and (not coarse_active or size != 1 or args.cache is None):
        parser.error("--build-cache-only requires one rank, levels=2, restart>0, and --cache")
    if coarse_active and size > 1 and (args.cache is None or not args.cache.is_file()):
        parser.error("multi-rank Legacy MG requires a prebuilt global --cache")
    coordinate, local, starts = mg._rank_geometry(lattice, grid, rank)
    dtype = np.dtype(np.complex64 if args.dtype == "c64" else np.complex128)
    qcu = kupl_backend()
    if isinstance(qcu, Exception):
        raise RuntimeError(f"KUPL backend unavailable: {qcu}")
    report: dict[str, Any] = {
        "status": "RUNNING", "backend": "kupl", "lattice": list(lattice),
        "grid": list(grid), "mpi_size": size, "dtype": str(dtype),
        "source_kind": "unit point source, spin-major/color-minor",
        "source_point": list(point), "columns_requested": args.columns,
        "complete_12_columns": sorted(args.columns) == list(range(12)),
        "levels": args.levels, "restart": args.restart, "dof": args.dof,
        "mg_grid": args.mg_grid, "nv_iters": args.nv_iters,
        "coarse_max_iter": args.coarse_max_iter,
        "coarse_tol_factor": args.coarse_tol_factor,
        "deflate": not args.no_deflate, "atol_requested": args.atol,
        "acceptance": "independent full relative residual <= atol_requested",
        "max_iter": args.max_iter,
        "initial_guess": "zero for every column's first pass; only that column's retained solution for residual restarts",
        "max_residual_restarts": args.max_residual_restarts,
        "residual_restart_path": "applyCloverBistabCgQcu, same original unit-point RHS, params[57]=1; no cross-column warm start",
        "solver_path": ("Legacy MG with adaptive fine-BiCGStab fallback"
                        if coarse_active else "parity-Schur BiCGStab"),
        "adaptive_fallback_observed": None,
        "adaptive_fallback_note": "ABI exposes no per-MG-call fallback/iteration counter; inspect verbose native logs if enabled",
        "reuse": "gauge, Clover/inverse, coarse assets, same LatticeSet; native Legacy MG workspace rebuilt each ABI call",
        "timings": {}, "columns": [],
        "hostname_by_rank": comm.allgather(socket.gethostname()),
        "threads_per_rank": os.environ.get("KUPL_OMP_THREADS", os.environ.get("OMP_NUM_THREADS")),
        "affinity_cpus_by_rank": comm.allgather(sorted(os.sched_getaffinity(0))),
        "omp_proc_bind": os.environ.get("OMP_PROC_BIND"),
        "kupl_numa_bind": os.environ.get("KUPL_NUMA_BIND"),
        "library": os.environ.get("PYQCU_KUPL_LIB"),
    }
    timings = report["timings"]
    program_started = time.perf_counter()
    if os.environ.get("KUPL_NUMA_BIND", "0") not in ("0", "", "false", "False"):
        _, timings["input_prebind_seconds"] = timed(comm, lambda: prebind_kupl_inputs(
            qcu, local, float(args.mass or 0.0), args.atol,
            float(args.csw if args.csw is not None else 1.0), dtype, args.max_iter,
            grid, rank, size))
        report["affinity_cpus_after_prebind_by_rank"] = comm.allgather(sorted(os.sched_getaffinity(0)))

    # Read once on rank zero, distribute canonical native local slabs.  The
    # global view is retained only for cache identity/build, then released.
    def read_and_distribute():
        if rank == 0:
            full, metadata = load_gauge(str(args.gauge), lattice, dtype)
            blocks = []
            for target in range(size):
                _, target_local, target_starts = mg._rank_geometry(lattice, grid, target)
                blocks.append(qcu_gauge_to_kupl(mg._slice_last4(full, target_starts, target_local)))
        else:
            full, metadata, blocks = None, None, None
        metadata = comm.bcast(metadata, root=0)
        gauge = comm.scatter(blocks, root=0)
        return full, metadata, np.ascontiguousarray(gauge)

    (gauge_full, metadata, gauge), timings["input_read_convert_distribute_seconds"] = timed(comm, read_and_distribute)
    mass_value = args.mass if args.mass is not None else metadata.get("reference_mass", metadata.get("mass"))
    if mass_value is None:
        parser.error("LIME has no explicit reference_mass/mass; supply --mass (light/strange is not inferred)")
    mass, csw = float(mass_value), float(resolve_csw(args.csw, metadata))
    kappa = 1.0 / (2.0 * mass + 8.0)
    report.update({"gauge": str(args.gauge.resolve()), "gauge_metadata": metadata,
                   "mass": mass, "mass_source": "cli" if args.mass is not None else "LIME metadata",
                   "csw": csw, "kappa": kappa,
                   "boundary_conditions": list(args.boundary),
                   "boundary_encoding": "already encoded in input links; native and independent operator use periodic indexing"})

    assets = ((), (), (), ())
    if coarse_active:
        def cache_identity():
            identity = None
            if rank == 0:
                identity = legacy_mg_cache_identity(
                    gauge_canonical_sha256=logical_array_sha256(gauge_full),
                    gauge_file_sha256=file_sha256(args.gauge), lattice=lattice,
                    dtype=dtype, mass=mass, csw=csw, dof=args.dof,
                    mg_grid=args.mg_grid, nv_iters=args.nv_iters, seed=args.seed)
            return comm.bcast(identity, root=0)
        identity, timings["input_cache_identity_hash_seconds"] = timed(comm, cache_identity)
        report["cache_identity"] = identity
        building = args.cache is None or not args.cache.is_file() or args.build_cache_only
        if building:
            if size != 1:
                raise RuntimeError("global cache build requires exactly one MPI rank")
            setup_stats: dict[str, Any] = {}
            assets, timings["coarse_build_seconds"] = timed(comm, lambda: mg.build_coarse_assets(
                gauge_full, lattice, mass, kappa, csw, dtype, args.levels,
                args.dof, args.mg_grid, args.nv_iters, args.seed,
                verbose=args.verbose_native, device_name="cpu", setup_stats=setup_stats))
            report["coarse_build_stats"] = setup_stats
            if args.cache is not None:
                def save_cache():
                    nulls, hnn, hdg, sit = assets
                    return save_legacy_mg_cache(args.cache,
                        {"lonv": nulls[0], "hnn": hnn[0], "hdg": hdg[0], "sit": sit[0]},
                        identity=identity, setup_method="cxx-null-vector+local-33-stencil",
                        setup_backend="kupl-qcu-cxx", source_metadata=metadata,
                        setup_seconds=timings["coarse_build_seconds"])
                manifest, timings["coarse_cache_write_seconds"] = timed(comm, save_cache)
                report["cache_manifest_setup_seconds"] = manifest.get("setup_seconds")
            report["coarse_source"] = "built in this run"
        else:
            def validate_cache():
                manifest = None
                if rank == 0:
                    manifest = validate_legacy_mg_cache(args.cache, identity,
                        verify_file_sha256=True, verify_dataset_sha256=True)
                return comm.bcast(manifest, root=0)
            manifest, timings["coarse_cache_validate_seconds"] = timed(comm, validate_cache)
            report["cache_manifest_setup_seconds"] = manifest.get("setup_seconds")
            def load_cache():
                _, coarse_local, coarse_starts = mg.inspect_cache_layout(
                    args.cache, lattice, args.mg_grid, list(grid), starts, "auto")
                return mg.load_coarse_assets(args.cache, dtype,
                    starts=coarse_starts if size > 1 else None,
                    local_shape=coarse_local if size > 1 else None)
            assets, timings["coarse_cache_load_slab_seconds"] = timed(comm, load_cache)
            report["coarse_source"] = str(args.cache.resolve())
    gauge_full = None
    if args.build_cache_only:
        timings["total_program_seconds"] = float(comm.allreduce(time.perf_counter() - program_started, op=MPI.MAX))
        report["status"] = "PASS"
        report["measurement_kind"] = "global MG cache build only; no propagator solve"
        if rank == 0:
            atomic_json(args.report, report)
            print(json.dumps(report), flush=True)
        return 0

    source = np.zeros((2, 12, *local[:3], local[3] // 2), dtype=dtype)
    solution = np.zeros_like(source)
    clover_shape = (4, 3, 4, 3, *local[:3], local[3] // 2)
    even, odd, even_inv, odd_inv = (np.empty(clover_shape, dtype=dtype) for _ in range(4))
    params, argv, set_ptrs = make_params(local, mass, args.atol, csw, dtype,
        args.max_iter, grid=grid, rank=rank, size=size)
    params[mg.MG_NUM_LEVEL] = args.levels
    params[51], params[57] = int(args.verbose_native), 0
    if coarse_active:
        mg.configure_mg(params, argv, set_ptrs, args.levels, args.atol,
            args.restart, args.coarse_max_iter, args.coarse_tol_factor,
            not args.no_deflate, *[list(a) for a in assets])
    set_ptrs[mg.SET_PTRS_LEGACY_LAYOUT] = mg.resolve_legacy_layout(
        "auto", coarse_active, tuple(assets[0]), local)
    wrapped = {name: NumpyTensor(array) for name, array in {
        "source": source, "solution": solution, "gauge": gauge,
        "even": even, "odd": odd, "even_inv": even_inv, "odd_inv": odd_inv,
        "params": params, "argv": argv, "set_ptrs": set_ptrs}.items()}
    for name, array in (("source", source), ("solution", solution)):
        assert np.shares_memory(wrapped[name].array, array), name
    def abi_call(name: str):
        return getattr(qcu, name)(wrapped["solution"], wrapped["source"], wrapped["gauge"],
            wrapped["even"], wrapped["odd"], wrapped["even_inv"], wrapped["odd_inv"],
            wrapped["set_ptrs"], wrapped["params"])

    _, timings["runtime_init_seconds"] = timed(comm, lambda: qcu.applyInitQcu(
        wrapped["set_ptrs"], wrapped["params"], wrapped["argv"]))
    try:
        def clover_setup():
            params[SET_PLAN] = PLAN_CLOVER
            params[PARITY] = 0
            qcu.applyCloversQcu(wrapped["even"], wrapped["even_inv"], wrapped["gauge"], wrapped["set_ptrs"], wrapped["params"])
            params[PARITY] = 1
            qcu.applyCloversQcu(wrapped["odd"], wrapped["odd_inv"], wrapped["gauge"], wrapped["set_ptrs"], wrapped["params"])
            params[SET_PLAN] = PLAN_SOLVER
        _, timings["clover_and_inverse_seconds"] = timed(comm, clover_setup)
        point_rhs(source, point, starts, local, args.columns[0])
        if coarse_active:
            verify, timings["mg_verifier_seconds"] = timed(comm, lambda: abi_call("verifyCloverMultigridQcu"))
            report["verify_status"] = int(comm.allreduce(verify, op=MPI.MAX))
            if report["verify_status"] != 0:
                raise RuntimeError(f"MG verifier rejected hierarchy: {report['verify_status']}")

        report["samples"] = []
        for repetition in range(1 if __import__("os").environ.get("FAIR_PILOT")=="1" else 1):
            # Store the 12 outputs so verification runs after the timed solve pass.
            # This avoids NumPy residual reconstruction evicting the solver working
            # set between columns. Output copies and RHS preparation are timed too.
            report["columns"] = []
            saved = []
            comm.Barrier()
            pass_started = time.perf_counter()
            for column in args.columns:
                def prepare_column():
                    point_rhs(source, point, starts, local, column)
                    solution.fill(0)
                    params[57] = 0
                _, prep_seconds = timed(comm, prepare_column)
                rhs_norm2 = float(comm.allreduce(float(np.vdot(source.ravel(), source.ravel()).real)))
                if rhs_norm2 != 1.0:
                    raise RuntimeError(f"point RHS has global squared norm {rhs_norm2}")
                if rank == 0:
                    print(f"PROPAGATOR_COLUMN_BEGIN column={column} spin={column//3} color={column%3}", flush=True)
                native_epoch_start = time.time()
                _, solve_seconds = timed(comm, lambda: abi_call("applyCloverMultigridQcu"))
                native_epoch_end = time.time()
                retained, copy_seconds = timed(comm, lambda: solution.copy())
                saved.append(retained)
                iterations = None
                if not coarse_active:
                    iterations = int(qcu.getCloverBistabCgIterationsQcu(wrapped["set_ptrs"], wrapped["params"]))
                record = {"column": column, "spin": column // 3, "color": column % 3,
                    "native_epoch_start": native_epoch_start, "native_epoch_end": native_epoch_end,
                    "rhs_prepare_seconds": prep_seconds,
                    "first_pass_native_solve_seconds": solve_seconds,
                    "native_solve_seconds": solve_seconds,
                    "solution_copy_seconds": copy_seconds,
                    "first_pass_iterations": iterations, "iterations": iterations,
                    "residual_restarts": []}
                report["columns"].append(record)
                if rank == 0:
                    print("PROPAGATOR_COLUMN_SOLVED " + json.dumps(record), flush=True)
                    atomic_json(args.report, report)
            timings["propagator_pass_wall_seconds"] = float(comm.allreduce(time.perf_counter() - pass_started, op=MPI.MAX))
            timings["first_pass_native_solve_sum_seconds"] = sum(r["first_pass_native_solve_seconds"] for r in report["columns"])
            timings["rhs_prepare_sum_seconds"] = sum(r["rhs_prepare_seconds"] for r in report["columns"])
            timings["solution_copy_sum_seconds"] = sum(r["solution_copy_seconds"] for r in report["columns"])
            timings["first_column_first_pass_native_seconds"] = report["columns"][0]["first_pass_native_solve_seconds"]
            comm.Barrier()
            verification_pass_started = time.perf_counter()
            for record, retained in zip(report["columns"], saved):
                # The retained vector and the RHS belong to this exact spin/color
                # column. No value from another column is used as an initial guess.
                point_rhs(source, point, starts, local, record["column"])
                residual, seconds = timed(comm, lambda: distributed_relative_residual(
                    retained, source, gauge, even, odd, kappa, comm, coordinate, grid))
                record.update({"first_pass_independent_true_relative_residual": residual,
                    "independent_true_relative_residual": residual,
                    "residual_check_seconds": seconds,
                    "status": "PASS" if np.isfinite(residual) and residual <= args.atol else "FAIL"})
                if rank == 0:
                    print("PROPAGATOR_COLUMN_FIRST_CHECK " + json.dumps(record), flush=True)
                    atomic_json(args.report, report)
                while (np.isfinite(residual) and residual > args.atol and
                       len(record["residual_restarts"]) < args.max_residual_restarts):
                    attempt = {"attempt": len(record["residual_restarts"]) + 1,
                        "column": record["column"],
                        "before_independent_true_relative_residual": residual,
                        "solver": "applyCloverBistabCgQcu", "initial_guess": "same-column retained solution",
                        "initial_guess_params_57": 1, "status": "RUNNING"}
                    record["residual_restarts"].append(attempt)
                    if rank == 0:
                        print("PROPAGATOR_RESIDUAL_RESTART_BEGIN " + json.dumps(attempt), flush=True)
                        atomic_json(args.report, report)
                    # A fresh full independent residual was just reconstructed.
                    # The fine solver also rebuilds its Schur residual from the
                    # original RHS and this same-column solution on entry.
                    _, attempt["initial_solution_copy_seconds"] = timed(
                        comm, lambda: np.copyto(solution, retained))
                    params[57] = 1
                    try:
                        _, attempt["native_solve_seconds"] = timed(
                            comm, lambda: abi_call("applyCloverBistabCgQcu"))
                        attempt["iterations"] = int(qcu.getCloverBistabCgIterationsQcu(
                            wrapped["set_ptrs"], wrapped["params"]))
                    finally:
                        params[57] = 0
                    _, attempt["retained_solution_copy_seconds"] = timed(
                        comm, lambda: np.copyto(retained, solution))
                    record["native_solve_seconds"] += attempt["native_solve_seconds"]
                    residual, check_seconds = timed(comm, lambda: distributed_relative_residual(
                        retained, source, gauge, even, odd, kappa, comm, coordinate, grid))
                    attempt.update({"after_independent_true_relative_residual": residual,
                        "residual_check_seconds": check_seconds,
                        "status": "PASS" if np.isfinite(residual) and residual <= args.atol else "FAIL"})
                    record["residual_check_seconds"] += check_seconds
                    record["independent_true_relative_residual"] = residual
                    record["status"] = attempt["status"]
                    if rank == 0:
                        print("PROPAGATOR_RESIDUAL_RESTART_END " + json.dumps(attempt), flush=True)
                        atomic_json(args.report, report)
                record["residual_restart_count"] = len(record["residual_restarts"])
                record["residual_restart_native_solve_seconds"] = sum(
                    attempt["native_solve_seconds"] for attempt in record["residual_restarts"])
                record["residual_restart_iterations_sum"] = sum(
                    attempt["iterations"] for attempt in record["residual_restarts"])
                record["total_known_iterations"] = (
                    None if record["first_pass_iterations"] is None else
                    record["first_pass_iterations"] + record["residual_restart_iterations_sum"])
                if rank == 0:
                    print("PROPAGATOR_COLUMN_VERIFIED " + json.dumps(record), flush=True)
                    atomic_json(args.report, report)
            timings["verification_and_residual_restart_wall_seconds"] = float(comm.allreduce(
                time.perf_counter() - verification_pass_started, op=MPI.MAX))
            timings["residual_restart_native_sum_seconds"] = sum(
                r["residual_restart_native_solve_seconds"] for r in report["columns"])
            timings["native_solve_sum_seconds"] = sum(r["native_solve_seconds"] for r in report["columns"])
            timings["per_column_native_mean_seconds"] = statistics.mean(r["native_solve_seconds"] for r in report["columns"])
            timings["per_column_native_median_seconds"] = statistics.median(r["native_solve_seconds"] for r in report["columns"])
            timings["first_column_native_seconds"] = report["columns"][0]["native_solve_seconds"]
            report["residual_restart_count_total"] = sum(r["residual_restart_count"] for r in report["columns"])
            report["rhs_per_second_native"] = len(args.columns) / timings["native_solve_sum_seconds"]
            if report["complete_12_columns"]:
                report["propagators_per_hour_native"] = 3600 / timings["native_solve_sum_seconds"]
            report["native_timing_note"] = "native_solve_sum_seconds and rates include every residual-restart native solve; first-pass wall excludes subsequent independent checks and residual restarts"
            timings["independent_residual_sum_seconds"] = sum(r["residual_check_seconds"] for r in report["columns"])
            report["max_independent_true_relative_residual"] = max(r["independent_true_relative_residual"] for r in report["columns"])
            report["status"] = "PASS" if all(r["status"] == "PASS" for r in report["columns"]) else "FAIL"
            report["samples"].append({"repeat":repetition,"warmup":False,"native_seconds":timings["native_solve_sum_seconds"],"max_residual":report["max_independent_true_relative_residual"],"restarts":report["residual_restart_count_total"],"columns":[dict(c) for c in report["columns"]]})
            if report["status"] != "PASS": raise RuntimeError("Full12 precision gate failed")
            if rank==0: atomic_json(args.report,report)
        from pyqcu.testing.simple._common import kupl_fermion_to_qcu
        column0=kupl_fermion_to_qcu(saved[0]).transpose(5,4,3,2,0,1)/3.723
        np.save(args.report.parent/("column0-rank%05d.npy"%rank),np.ascontiguousarray(column0))
        report["memory_by_rank"] = comm.allgather(cpu_memory_snapshot())
    finally:
        _, timings["runtime_end_seconds"] = timed(comm, lambda: qcu.applyEndQcu(wrapped["set_ptrs"], wrapped["params"]))
    timings["total_program_seconds"] = float(comm.allreduce(time.perf_counter() - program_started, op=MPI.MAX))
    if rank == 0:
        atomic_json(args.report, report)
        print("PROPAGATOR_BENCHMARK_FINAL " + json.dumps(report), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        result = main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        MPI.COMM_WORLD.Abort(1)
        raise
    if not MPI.Is_finalized():
        MPI.Finalize()
    raise SystemExit(result)
