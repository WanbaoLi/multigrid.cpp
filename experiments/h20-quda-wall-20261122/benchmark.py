"""Benchmark synchronized Wilson–Clover wall-source solves on one GPU."""

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import time

import cupy as cp
from mpi4py import MPI
import pyquda
from pyquda.enum_quda import (
    QudaInverterType,
    QudaPrecision,
    QudaPreserveSource,
    QudaReconstructType,
    QudaUseInitGuess,
    QudaVerbosity,
)
from pyquda.field import LatticeInfo, MultiLatticeFermion
from pyquda_utils import core, io, source


LATTICE = [24, 24, 24, 64]
MASS = -0.279
CSW = 1.160678675188
TOL = 1e-8
BLOCK = [6, 6, 6, 4]


def synchronize():
    cp.cuda.runtime.deviceSynchronize()


def timed_invert(invert, rhs, dirac, width, compute_seconds):
    if compute_seconds is not None:
        synchronize()
        before = compute_seconds(width > 1)
        solution = invert(rhs)
        synchronize()
        elapsed = compute_seconds(width > 1) - before
        if not math.isfinite(elapsed) or elapsed <= 0:
            raise RuntimeError("QUDA recorded no solver compute time")
        return solution, {
            "solver_seconds": elapsed,
            "quda_iterations": int(dirac.invert_param.iter),
        }
    synchronize()
    start = time.perf_counter()
    solution = invert(rhs)
    synchronize()
    elapsed = time.perf_counter() - start
    return solution, {
        "api_seconds": elapsed,
        "quda_seconds": float(dirac.invert_param.secs),
        "quda_iterations": int(dirac.invert_param.iter),
    }


def relative_norm(delta, reference):
    return math.sqrt(float(cp.vdot(delta.ravel(), delta.ravel()).real)
                     / float(cp.vdot(reference.ravel(), reference.ravel()).real))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gauge", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--solve-tol", type=float, default=TOL)
    parser.add_argument("--compute-only", action="store_true")
    parser.add_argument("--mg-profile", choices=("original", "ensemble"), default="original")
    args = parser.parse_args()
    if args.repeats < 2 or MPI.COMM_WORLD.size != 1 or not 0 < args.solve_tol <= TOL:
        parser.error("requires one MPI rank, at least two repetitions and solve tolerance <= 1e-8")

    compute_seconds = None
    if args.compute_only:
        library = ctypes.CDLL("libquda.so")
        compute_seconds = library.qudaBenchmarkInvertComputeSeconds
        compute_seconds.argtypes = [ctypes.c_int]
        compute_seconds.restype = ctypes.c_double

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cache = args.output.parent / "quda-cache"
    cache.mkdir(exist_ok=True)
    pyquda.init([1, 1, 1, 1], LATTICE, backend="cupy", resource_path=str(cache),
                enable_nvshmem=False, max_multi_rhs=16)
    with args.gauge.open("rb") as fixture:
        gauge_hash = hashlib.file_digest(fixture, "sha256").hexdigest()
    start = time.perf_counter()
    gauge = io.readChromaQIOGauge(str(args.gauge), checksum=True)
    read_seconds = time.perf_counter() - start
    if list(gauge.latt_info.global_size) != LATTICE:
        raise ValueError("unexpected gauge lattice geometry")
    synchronize()
    start = time.perf_counter()
    gauge.stoutSmear(1, 0.125, 4)
    synchronize()
    stout_seconds = time.perf_counter() - start

    lattice = LatticeInfo(LATTICE, -1, 1.0)
    blocks = [BLOCK] if args.mg_profile == "original" else [[3, 3, 3, 2], [2, 2, 2, 2]]
    dirac = core.getClover(lattice, MASS, args.solve_tol, 1000, 1.0, CSW, CSW, blocks)
    double = QudaPrecision.QUDA_DOUBLE_PRECISION
    single = QudaPrecision.QUDA_SINGLE_PRECISION
    no_reconstruct = QudaReconstructType.QUDA_RECONSTRUCT_NO
    dirac.setPrecision(cuda=double, sloppy=single, refinement_sloppy=single, precondition=single)
    dirac.setReconstruct(
        cuda=no_reconstruct, sloppy=no_reconstruct, refinement_sloppy=no_reconstruct,
        precondition=no_reconstruct, eigensolver=no_reconstruct,
    )
    dirac.multigrid.setParam(setup_tol=0.1, setup_maxiter=40, coarse_tol=0.25,
                             coarse_maxiter=16, smoother_tol=0.25,
                             smoother_nu_pre=2, smoother_nu_post=2)
    if args.mg_profile == "ensemble":
        mg_param = dirac.multigrid.param
        mg_param.n_vec = [24, 32, 32]
        mg_param.smoother = [QudaInverterType.QUDA_MR_INVERTER] * 3
        dirac.multigrid.setParam(
            setup_tol=5e-6, setup_maxiter=500, coarse_tol=0.1, coarse_maxiter=12,
            smoother_tol=0.1, smoother_nu_pre=0, smoother_nu_post=8,
        )
    dirac.setVerbosity(QudaVerbosity.QUDA_SILENT)
    invert = dirac.invert_param
    invert.gcrNkrylov = 24 if args.mg_profile == "original" else 20
    if args.mg_profile == "ensemble":
        invert.pipeline = 4
    invert.use_init_guess = QudaUseInitGuess.QUDA_USE_INIT_GUESS_NO
    invert.preserve_source = QudaPreserveSource.QUDA_PRESERVE_SOURCE_YES
    invert.chrono_use_resident = 0
    invert.chrono_make_resident = 0
    invert.compute_true_res = 1

    synchronize()
    start = time.perf_counter()
    dirac.loadGauge(gauge)
    synchronize()
    setup_seconds = time.perf_counter() - start
    samples = {"1": [], "12": []}
    second_solutions = {}
    residual_seconds = 0.0
    try:
        mg = dirac.multigrid
        if (mg.instance is None or mg.param.n_level < 2
                or invert.inv_type_precondition != QudaInverterType.QUDA_MG_INVERTER
                or invert.inv_type != QudaInverterType.QUDA_GCR_INVERTER
                or repr(mg.instance) == "Pointer at 0x0000000000000000"
                or repr(invert.preconditioner) != repr(mg.instance)):
            raise RuntimeError("Expected GCR with the active QUDA multigrid preconditioner")
        mg_levels = int(mg.param.n_level)
        print(f"Verified QUDA multigrid preconditioner with {mg_levels} levels", flush=True)
        rhs = MultiLatticeFermion(lattice, 12)
        for spin in range(4):
            for color in range(3):
                rhs[3 * spin + color] = source.wall(lattice, 0, spin, color)
        for width, field, solve in ((1, rhs[0], dirac.invert), (12, rhs, dirac.invertMultiSrc)):
            for run in range(1, args.repeats + 1):
                solution, sample = timed_invert(solve, field, dirac, width, compute_seconds)
                if run == 2:
                    second_solutions[width] = solution
                start = time.perf_counter()
                pairs = [(solution, field)] if width == 1 else [
                    (solution[i], field[i]) for i in range(width)
                ]
                residuals = [
                    relative_norm(dirac.mat(x).data - b.data, b.data) for x, b in pairs
                ]
                residual_seconds += time.perf_counter() - start
                sample.update(run=run, warmup=run == 1, full_relative_residuals=residuals)
                samples[str(width)].append(sample)
                print("SAMPLE", width, json.dumps(sample), flush=True)

        one = second_solutions[1].data
        multi_zero = second_solutions[12][0].data
        time_key = "solver_seconds" if args.compute_only else "api_seconds"
        second_one = samples["1"][1][time_key]
        second_multi = samples["12"][1][time_key]
        result = {
            "host": socket.gethostname(),
            "gpu": cp.cuda.runtime.getDeviceProperties(0)["name"].decode(),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "mpi_ranks": MPI.COMM_WORLD.size,
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "gauge": args.gauge.name,
            "gauge_sha256": gauge_hash,
            "gauge_read_seconds": read_seconds,
            "stout": {"steps": 1, "rho": 0.125, "directions": "xyzt", "seconds": stout_seconds},
            "gauge_fixing": None,
            "lattice": LATTICE,
            "mass": MASS,
            "clover_csw": CSW,
            "temporal_boundary": -1,
            "source": {"type": "wall", "time_slice": 0, "spins": 4, "colors": 3},
            "multigrid_active": True,
            "multigrid_levels": mg_levels,
            "multigrid_profile": args.mg_profile,
            "multigrid_blocks": blocks,
            "multigrid_null_vectors": list(mg.param.n_vec)[:len(blocks)],
            "gauge_clover_hierarchy_seconds": setup_seconds,
            "full_residual_validation_seconds": residual_seconds,
            "zero_initial_guess": True,
            "correction_solves": 0,
            "requested_solve_tolerance": args.solve_tol,
            "full_residual_threshold": TOL,
            "samples": samples,
            f"second_{time_key}_1": second_one,
            f"second_{time_key}_12": second_multi,
            "second_solution_column_zero_relative_difference": relative_norm(multi_zero - one, one),
        }
        if args.compute_only:
            result["timing_scope"] = "QUDA_PROFILE_COMPUTE"
            del result["gauge_read_seconds"]
            del result["stout"]["seconds"]
            del result["gauge_clover_hierarchy_seconds"]
            del result["full_residual_validation_seconds"]
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        if any(r > TOL for series in samples.values() for sample in series
               for r in sample["full_relative_residuals"]):
            raise RuntimeError("a full relative residual exceeded the acceptance threshold")
    finally:
        dirac.freeGauge()


if __name__ == "__main__":
    main()
