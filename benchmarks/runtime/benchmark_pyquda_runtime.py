"""Matching PyQUDA reference for the native CPU host API benchmark.

Reads the accepted post-stout fixture; never changes its gauge or reference.
Select the GPU using CUDA_VISIBLE_DEVICES. Run in the pyquda conda environment.
"""

import argparse
import json
import os
from pathlib import Path
import statistics
import time

import h5py
import numpy as np
from mpi4py import MPI

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
LAT = (24, 24, 24, 64)
MASS = -0.277
KAPPA = 1 / (2 * (4 + MASS))


def read_cpu_solution(directory):
    """Assemble native rank-local EO-x fields; supports arbitrary even origins."""
    from pyquda.field import lexico

    files = sorted(directory.glob("solution_rank*.h5"))
    if not files:
        raise ValueError(f"no native solution_rank*.h5 in {directory}")
    whole = np.empty((64, 24, 24, 24, 4, 3), dtype=np.complex128)
    coverage = np.zeros((64, 24, 24, 24), dtype=np.uint8)
    for path in files:
        with h5py.File(path, "r") as f:
            eo = np.asarray(f["solution_eo_x"])
            coord = tuple(int(c) for c in f.attrs["grid_coord_xyzt"])
            assert tuple(f.attrs["global_lattice_xyzt"]) == LAT
        local = lexico(eo, [0, 1, 2, 3, 4])
        shape = local.shape[:4]
        origin = tuple(c * n for c, n in zip(coord[::-1], shape))
        if sum(origin) % 2:
            raise ValueError(
                "odd local origin requires explicit global-parity conversion"
            )
        sl = tuple(slice(o, o + n) for o, n in zip(origin, shape))
        whole[sl] = local
        coverage[sl] += 1
    if not np.all(coverage == 1):
        raise ValueError("native rank files do not cover the lattice exactly once")
    return whole


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture",
        type=Path,
        default=WORKSPACE / "PyQCU/data/lime_mg_20261013/input.h5",
    )
    p.add_argument(
        "--reference",
        type=Path,
        default=WORKSPACE / "PyQCU/data/lime_mg_20261013/quda_solution.h5",
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repeats", type=int, default=4)
    p.add_argument("--grid", nargs=4, type=int, default=[1, 1, 1, 1])
    p.add_argument("--tol", type=float, default=1e-8)
    p.add_argument("--cpu-solution-dir", type=Path)
    args = p.parse_args()
    comm = MPI.COMM_WORLD
    if args.grid[:3] != [1, 1, 1] or args.grid[3] != comm.size or 64 % comm.size:
        raise ValueError("requires --grid 1 1 1 N, N ranks, and N dividing 64")
    local_t = 64 // comm.size
    if local_t % 4:
        raise ValueError("local time extent must contain complete size-4 MG blocks")
    ts = slice(comm.rank * local_t, (comm.rank + 1) * local_t)

    def global_relative(actual, expected):
        delta = (actual - expected).ravel()
        ref = expected.ravel()
        numerator = comm.allreduce(float(np.vdot(delta, delta).real))
        denominator = comm.allreduce(float(np.vdot(ref, ref).real))
        return float(np.sqrt(numerator / denominator))

    if args.repeats < 2 or not 0 < args.tol <= 1e-8:
        raise ValueError("at least two repeats and 0 < tol <= 1e-8 are required")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "quda_cache").mkdir(exist_ok=True)
    with h5py.File(args.fixture, "r") as f:
        assert float(f.attrs["mass"]) == MASS
        assert int(f.attrs["temporal_boundary"]) == -1
        assert float(f.attrs["clover_csw"]) == 1.0
        gauge_lex = (
            np.asarray(f["gauge"][:, :, :, :, :, :, ts])
            .transpose(2, 6, 5, 4, 3, 0, 1)
            .copy()
        )
        source_lex = np.asarray(f["b"][:, :, :, :, :, ts]).transpose(
            5, 4, 3, 2, 0, 1
        ).copy() / (2 * KAPPA)
        probe_lex = (
            np.asarray(f["probe"][:, :, :, :, :, ts]).transpose(5, 4, 3, 2, 0, 1).copy()
        )
        expected_lex = np.asarray(f["D_probe"][:, :, :, :, :, ts]).transpose(
            5, 4, 3, 2, 0, 1
        ).copy() / (2 * KAPPA)
    import cupy as cp
    from pyquda_utils import core
    from pyquda.field import LatticeFermion, LatticeGauge, lexico
    from pyquda.enum_quda import (
        QudaPrecision,
        QudaReconstructType,
        QudaVerbosity,
        QudaUseInitGuess,
        QudaPreserveSource,
    )

    core.init(
        args.grid,
        list(LAT),
        backend="cupy",
        resource_path=str(args.output / "quda_cache"),
        enable_mps=False,
    )
    li = core.LatticeInfo(list(LAT), -1, 1.0)
    source_host = li.evenodd(source_lex, False)
    original_source = source_host.copy()
    # QUDA gauge_param.location defaults to CPU; fermion fields remain CUDA.
    gauge = LatticeGauge(li, li.evenodd(gauge_lex, True))
    source = LatticeFermion(li)
    probe = LatticeFermion(li, cp.asarray(li.evenodd(probe_lex, False)))
    expected = li.evenodd(expected_lex, False)
    d = core.getClover(li, MASS, args.tol, 1000, 1.0, 1.0, 1.0, [[6, 6, 6, 4]])
    double = QudaPrecision.QUDA_DOUBLE_PRECISION
    single = QudaPrecision.QUDA_SINGLE_PRECISION
    d.setPrecision(
        cuda=double, sloppy=single, refinement_sloppy=single, precondition=single
    )
    no = QudaReconstructType.QUDA_RECONSTRUCT_NO
    d.setReconstruct(cuda=no, sloppy=no, precondition=no)
    d.multigrid.param.n_vec = [24] * len(d.multigrid.param.n_vec)
    d.multigrid.setParam(
        setup_tol=0.1,
        setup_maxiter=40,
        coarse_tol=0.25,
        coarse_maxiter=16,
        smoother_tol=0.25,
        smoother_nu_pre=2,
        smoother_nu_post=2,
    )
    d.invert_param.gcrNkrylov = 24
    d.invert_param.verbosity = QudaVerbosity.QUDA_SUMMARIZE
    d.invert_param.use_init_guess = QudaUseInitGuess.QUDA_USE_INIT_GUESS_NO
    d.invert_param.preserve_source = QudaPreserveSource.QUDA_PRESERVE_SOURCE_YES
    d.invert_param.chrono_use_resident = 0
    d.invert_param.chrono_make_resident = 0
    d.invert_param.compute_true_res = 1
    cp.cuda.runtime.deviceSynchronize()
    comm.Barrier()
    start = time.perf_counter()
    d.loadGauge(gauge)
    cp.cuda.runtime.deviceSynchronize()
    setup_seconds = comm.allreduce(time.perf_counter() - start, op=MPI.MAX)
    try:
        operator_error = global_relative(d.mat(probe).data.get(), expected)
        assert operator_error < 1e-11, operator_error
        samples = []
        for run in range(args.repeats):
            cp.cuda.runtime.deviceSynchronize()
            comm.Barrier()
            start = time.perf_counter()
            source.data.set(source_host)
            cp.cuda.runtime.deviceSynchronize()
            invert_start = time.perf_counter()
            x = d.invert(source)
            cp.cuda.runtime.deviceSynchronize()
            device_seconds = time.perf_counter() - invert_start

            def scalar(value):
                # QUDA exposes residual arrays indexed by RHS; this solves RHS 0.
                if isinstance(value, (list, tuple, np.ndarray)):
                    return value[0]
                return value

            solve_stats = dict(
                iterations=int(scalar(d.invert_param.iter)),
                quda_solver_seconds=float(scalar(d.invert_param.secs)),
                quda_reported_residual=float(scalar(d.invert_param.true_res)),
            )
            x_host = x.data.get()
            transfer_api_seconds = time.perf_counter() - start
            # Full double-precision D residual mirrors the native public API gate.
            # The device-resident source is preserved explicitly above.
            delta = d.mat(x).data - source.data
            numerator = comm.allreduce(
                float(cp.vdot(delta.ravel(), delta.ravel()).real)
            )
            denominator = comm.allreduce(
                float(cp.vdot(source.data.ravel(), source.data.ravel()).real)
            )
            residual = float(np.sqrt(numerator / denominator))
            cp.cuda.runtime.deviceSynchronize()
            api_seconds = time.perf_counter() - start
            device_seconds = comm.allreduce(device_seconds, op=MPI.MAX)
            transfer_api_seconds = comm.allreduce(transfer_api_seconds, op=MPI.MAX)
            api_seconds = comm.allreduce(api_seconds, op=MPI.MAX)
            sample = dict(
                run=run,
                device_invert_seconds=device_seconds,
                host_transfer_api_seconds=transfer_api_seconds,
                python_wall_seconds=api_seconds,
                true_residual=residual,
                **solve_stats,
            )
            samples.append(sample)
            assert np.array_equal(source_host, original_source)
            assert np.array_equal(source.data.get(), original_source)
            assert np.isfinite(residual) and residual <= args.tol, sample
            if comm.rank == 0:
                print("SAMPLE", run, json.dumps(sample), flush=True)
        canonical = np.ascontiguousarray(lexico(x_host, [0, 1, 2, 3, 4]))
        slabs = comm.gather(canonical, root=0)
        if comm.rank == 0:
            with (args.output / "canonical_solution.bin").open("wb") as file:
                for slab in slabs:
                    slab.tofile(file)
        with h5py.File(args.output / f"solution_rank{comm.rank}.h5", "w") as f:
            f["solution_eo_x"] = x_host
            f.attrs["global_lattice_xyzt"] = LAT
            f.attrs["grid_xyzt"] = args.grid
            f.attrs["grid_coord_xyzt"] = (0, 0, 0, comm.rank)
            f.attrs["normalization"] = "mass"
            f.attrs["gamma_basis"] = "DeGrand-Rossi"
        with h5py.File(args.reference, "r") as f:
            reference = np.asarray(f["x"][:, :, :, :, :, ts]).transpose(
                5, 4, 3, 2, 0, 1
            )
        reference_error = global_relative(canonical, reference)
        assert reference_error < 1e-6, reference_error
        result = dict(
            implementation="PyQUDA",
            gpu_count=comm.size,
            grid=args.grid,
            cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
            fixture=str(args.fixture.resolve()),
            lattice=LAT,
            mass=MASS,
            clover_csw=1.0,
            temporal_boundary=-1,
            normalization="mass",
            tolerance=args.tol,
            zero_initial_guess=True,
            setup_seconds=setup_seconds,
            operator_error=operator_error,
            solution_error_vs_reference=reference_error,
            samples=samples,
            second_api_seconds=samples[1]["python_wall_seconds"],
            second_device_seconds=samples[1]["device_invert_seconds"],
            steady_api_median=statistics.median(
                s["python_wall_seconds"] for s in samples[1:]
            ),
            steady_device_median=statistics.median(
                s["device_invert_seconds"] for s in samples[1:]
            ),
            timing_composition={
                "device_invert_seconds": "synchronized invert; input/output on GPU",
                "host_transfer_api_seconds": "host upload + synchronized invert + host download",
                "python_wall_seconds": "host upload + synchronized invert + host download + explicit double full residual; max rank time",
                "excluded": "gauge load/setup, fixture conversion, independent reference comparison, output files",
            },
        )
        if args.cpu_solution_dir:
            cpu_slabs = None
            if comm.rank == 0:
                whole = read_cpu_solution(args.cpu_solution_dir)
                cpu_slabs = [
                    np.ascontiguousarray(whole[r * local_t : (r + 1) * local_t])
                    for r in range(comm.size)
                ]
            cpu = comm.scatter(cpu_slabs, root=0)
            cpu_error = global_relative(cpu, canonical)
            cpu_field = LatticeFermion(li, cp.asarray(li.evenodd(cpu, False)))
            cpu_residual = global_relative(d.mat(cpu_field).data.get(), source_host)
            result.update(
                cpu_solution_error_vs_quda=cpu_error,
                cpu_solution_residual_with_quda_operator=cpu_residual,
            )
            assert cpu_error < 1e-6, cpu_error
            assert np.isfinite(cpu_residual) and cpu_residual <= args.tol, cpu_residual
        if comm.rank == 0:
            (args.output / "result.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print("RESULT", json.dumps(result), flush=True)
    finally:
        d.freeGauge()


if __name__ == "__main__":
    main()
