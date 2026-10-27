"""Real-data acceptance via actual CPU PyQUDA field objects, with API timing."""

import argparse, json, time, sys, statistics, os, socket
from pathlib import Path
import numpy as np
import h5py
from mpi4py import MPI

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
sys.path.insert(0, str(PROJECT / "python"))
from lqcd_cpu import Solver
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo, LatticeFermion, LatticeGauge

p = argparse.ArgumentParser()
p.add_argument("--grid", nargs=4, type=int)
p.add_argument("--threads", type=int)
p.add_argument("--levels", type=int, default=2)
p.add_argument("--repeats", type=int, default=6)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--twelve-rhs", action="store_true")
p.add_argument(
    "--twelve-repeats", type=int,
    help="repeat the complete 12-column solve at least twice; omitted keeps one legacy round",
)
p.add_argument(
    "--thread-sweep",
    nargs="+",
    type=int,
    help="additional rank-local thread counts, reusing the generated hierarchy",
)
p.add_argument("--backend", default="x86")
p.add_argument(
    "--profile-control",
    type=Path,
    help="after normal samples, publish rank PIDs and wait for a go file for external perf",
)
p.add_argument("--profile-repeats", type=int, default=8)
args = p.parse_args()
comm = MPI.COMM_WORLD
if args.twelve_repeats is not None:
    if not args.twelve_rhs or args.twelve_repeats < 2:
        p.error("--twelve-repeats requires --twelve-rhs and a count >=2")
if args.repeats < 2:
    p.error("--repeats must be at least 2 for second-solve acceptance")
if args.profile_control and args.profile_repeats < 1:
    p.error("--profile-repeats must be positive")
if args.thread_sweep:
    if (
        len(set(args.thread_sweep)) != len(args.thread_sweep)
        or min(args.thread_sweep) < 1
    ):
        p.error("--thread-sweep requires distinct positive counts")
    limit = os.environ.get("LQCD_CPU_THREADS")
    invalid = limit is not None and max(args.thread_sweep) > int(limit)
    if comm.allreduce(invalid, op=MPI.LOR):
        p.error("thread sweep exceeds a NUMA rank CPU allocation")
if args.grid is None:
    args.grid = [1, 1, 1, comm.size]
initGrid(grid_size=args.grid)
lat = (24, 24, 24, 64)
li = LatticeInfo(list(lat), -1, 1.0)
local = tuple(li.size)
coords = tuple(li.grid_coord)
sl = tuple(slice(c * n, (c + 1) * n) for c, n in zip(coords, local))
kappa = 1 / (2 * (4 - 0.277))
with h5py.File(WORKSPACE / "PyQCU/data/lime_mg_20261013/input.h5", "r") as f:
    g = (
        np.asarray(f["gauge"][(slice(None),) * 3 + sl])
        .transpose(2, 6, 5, 4, 3, 0, 1)
        .copy()
    )
    b = np.asarray(f["b"][(slice(None),) * 2 + sl]).transpose(
        5, 4, 3, 2, 0, 1
    ).copy() / (2 * kappa)
    probe = (
        np.asarray(f["probe"][(slice(None),) * 2 + sl])
        .transpose(5, 4, 3, 2, 0, 1)
        .copy()
    )
    expected = np.asarray(f["D_probe"][(slice(None),) * 2 + sl]).transpose(
        5, 4, 3, 2, 0, 1
    ).copy() / (2 * kappa)
gauge = LatticeGauge(li, li.evenodd(g, True))
source = LatticeFermion(li, li.evenodd(b, False))
probe = li.evenodd(probe, False)
expected = li.evenodd(expected, False)


def relative(a, b):
    d = (a - b).ravel()
    bb = b.ravel()
    return np.sqrt(
        comm.allreduce(float(np.vdot(d, d).real))
        / comm.allreduce(float(np.vdot(bb, bb).real))
    )


begin = time.perf_counter()
with Solver(
    lat,
    args.grid,
    mass=-0.277,
    threads=args.threads,
    levels=args.levels,
    normalization="mass",
    backend=args.backend,
) as s:
    resources = comm.allgather(
        dict(
            rank=comm.rank,
            host=socket.gethostname(),
            threads=s.config.threads,
            cpus=sorted(os.sched_getaffinity(0)),
            cpus_scope="calling_thread_after_OpenMP_binding; team places below",
            omp_places=os.environ.get("OMP_PLACES"),
            omp_proc_bind=os.environ.get("OMP_PROC_BIND"),
            adaptive_correction=os.environ.get("LQCD_ADAPTIVE_CORRECTION", "1"),
            setup_update=os.environ.get("LQCD_SETUP_UPDATE", "inverse"),
            sap_eo=os.environ.get("LQCD_SAP_EO", "1"),
            coarse_eo=os.environ.get("LQCD_COARSE_EO", "1"),
            halo_profile=os.environ.get("LQCD_HALO_PROFILE", "0"),
            halo_overlap=os.environ.get("LQCD_HALO_OVERLAP", "1"),
        )
    )
    s.load_pyquda_gauge(gauge)
    setup = s.setup()
    setup_wall = comm.allreduce(time.perf_counter() - begin, op=MPI.MAX)
    operator_error = relative(s.apply(probe), expected)
    assert operator_error < 1e-11, operator_error
    samples = []
    original = source.data.copy()
    for run in range(args.repeats):
        comm.Barrier()
        start = time.perf_counter()
        x = s.solve_pyquda(source)
        wall = comm.allreduce(time.perf_counter() - start, op=MPI.MAX)
        sample = dict(s.last_result, python_wall_seconds=wall)
        samples.append(sample)
        assert np.array_equal(original, source.data)
        if comm.rank == 0:
            print("SAMPLE", run, json.dumps(sample), flush=True)
    with h5py.File(
        WORKSPACE / "PyQCU/data/lime_mg_20261013/quda_solution.h5", "r"
    ) as f:
        reference = (
            np.asarray(f["x"][(slice(None),) * 2 + sl])
            .transpose(5, 4, 3, 2, 0, 1)
            .copy()
        )
    solution_error = relative(x.data, li.evenodd(reference, False))
    assert solution_error < 1e-6, solution_error
    args.output.mkdir(parents=True, exist_ok=True)
    with h5py.File(args.output / f"solution_rank{comm.rank}.h5", "w") as f:
        f["solution_eo_x"] = x.data
        f.attrs["global_lattice_xyzt"] = lat
        f.attrs["grid_xyzt"] = args.grid
        f.attrs["grid_coord_xyzt"] = coords
        f.attrs["normalization"] = "mass"
        f.attrs["gamma_basis"] = "DeGrand-Rossi"
    result = dict(
        lattice=lat,
        grid=args.grid,
        threads=s.config.threads,
        resources=resources,
        levels=args.levels,
        setup_threads_per_rank=[q["threads"] for q in resources],
        setup_seconds=setup,
        create_load_setup_wall_seconds=setup_wall,
        operator_error=operator_error,
        solution_error_vs_quda=solution_error,
        normalization="mass",
        capabilities=s.capabilities,
        samples=samples,
        second_api_seconds=samples[1]["python_wall_seconds"],
        steady_api_median=statistics.median(
            q["python_wall_seconds"] for q in samples[1:]
        ),
        steady_solver_median=statistics.median(
            q["solver_seconds"] for q in samples[1:]
        ),
        performance_gate_passed=samples[1]["python_wall_seconds"] < 5.0,
    )
    if args.thread_sweep:
        result["thread_sweep"] = []
        for count in args.thread_sweep:
            s.set_threads(count)
            phase = []
            for run in range(args.repeats):
                comm.Barrier()
                start = time.perf_counter()
                trial = s.solve_pyquda(source)
                wall = comm.allreduce(time.perf_counter() - start, op=MPI.MAX)
                phase.append(dict(s.last_result, python_wall_seconds=wall))
                assert np.array_equal(original, source.data)
                if comm.rank == 0:
                    print(
                        "THREAD_SAMPLE", count, run, json.dumps(phase[-1]), flush=True
                    )
            error = relative(trial.data, li.evenodd(reference, False))
            assert error < 1e-6, error
            case = dict(result)
            case.pop("thread_sweep", None)
            case.update(
                threads=count,
                resources=[dict(q, threads=count) for q in resources],
                samples=phase,
                solution_error_vs_quda=error,
                second_api_seconds=phase[1]["python_wall_seconds"],
                steady_api_median=statistics.median(
                    q["python_wall_seconds"] for q in phase[1:]
                ),
                steady_solver_median=statistics.median(
                    q["solver_seconds"] for q in phase[1:]
                ),
                performance_gate_passed=phase[1]["python_wall_seconds"] < 5.0,
                hierarchy_reused_from=str(args.output),
            )
            directory = args.output / f"threads_{count}"
            directory.mkdir(parents=True, exist_ok=True)
            with h5py.File(directory / f"solution_rank{comm.rank}.h5", "w") as f:
                f["solution_eo_x"] = trial.data
                f.attrs["global_lattice_xyzt"] = lat
                f.attrs["grid_xyzt"] = args.grid
                f.attrs["grid_coord_xyzt"] = coords
                f.attrs["normalization"] = "mass"
                f.attrs["gamma_basis"] = "DeGrand-Rossi"
            result["thread_sweep"].append(
                dict(
                    threads=count,
                    second_api_seconds=case["second_api_seconds"],
                    steady_api_median=case["steady_api_median"],
                    output=str(directory),
                )
            )
            if comm.rank == 0:
                (directory / "result.json").write_text(
                    json.dumps(case, indent=2) + "\n"
                )
        # Complete propagators, when requested, use the measured best resource
        # count; retain the original single-column timing as a separate record.
        choices = [(result["steady_api_median"], result["threads"])] + [
            (q["steady_api_median"], q["threads"]) for q in result["thread_sweep"]
        ]
        s.set_threads(min(choices)[1])
    if args.twelve_rhs:
        result["twelve_rhs_threads"] = s.config.threads
        rhs = np.zeros((12, *source.data.shape), dtype=np.complex128)
        if all(c == 0 for c in coords):
            for spin in range(4):
                for color in range(3):
                    rhs[spin * 3 + color, 0, 0, 0, 0, 0, spin, color] = 1 / (2 * kappa)
        original_rhs = rhs.copy()
        twelve_samples = []
        for twelve_run in range(args.twelve_repeats or 1):
            if twelve_run:
                del xs  # release the preceding output outside the timed region
            comm.Barrier()
            start = time.perf_counter()
            # solve_many calls independent zero-initial-guess solves. Only the
            # hierarchy/workspace is reused, never a preceding round's solution.
            xs, stats = s.solve_many(rhs)
            wall = comm.allreduce(time.perf_counter() - start, op=MPI.MAX)
            assert np.array_equal(original_rhs, rhs)
            assert len(stats) == 12
            assert all(q["converged"] and q["true_residual"] <= 1e-8 for q in stats)
            twelve_samples.append(dict(wall_seconds=wall, stats=stats))
            if comm.rank == 0:
                print("TWELVE_SAMPLE", twelve_run, json.dumps(twelve_samples[-1]), flush=True)
        # Legacy fields describe the final exported round. New fields separate
        # second/steady complete propagators from individual source timings.
        result["twelve_rhs_wall_seconds"] = twelve_samples[-1]["wall_seconds"]
        result["twelve_rhs_stats"] = twelve_samples[-1]["stats"]
        result["twelve_rhs_samples"] = twelve_samples
        result["twelve_rhs_initial_guess"] = "zero_for_every_column_every_round"
        if len(twelve_samples) >= 2:
            result["twelve_rhs_second_wall_seconds"] = twelve_samples[1]["wall_seconds"]
            result["twelve_rhs_steady_median_seconds"] = statistics.median(
                sample["wall_seconds"] for sample in twelve_samples[1:]
            )
        with h5py.File(
            args.output / f"propagator_columns_rank{comm.rank}.h5", "w"
        ) as f:
            f["columns_eo_x"] = xs
            f.attrs["column_order"] = "source_spin*3+source_color"
            f.attrs["grid_coord_xyzt"] = coords
    if args.profile_control:
        # Profiling gets a separate phase so setup, file exports and ordinary
        # acceptance samples do not contaminate the perf recording.
        s.set_threads(result["threads"])
        args.profile_control.mkdir(parents=True, exist_ok=True)
        ready = args.profile_control / f"rank{comm.rank}.ready.json"
        ready.write_text(
            json.dumps(
                dict(
                    rank=comm.rank,
                    pid=os.getpid(),
                    threads=s.config.threads,
                    host=socket.gethostname(),
                )
            )
        )
        deadline = time.monotonic() + 300
        while not (args.profile_control / "go").exists():
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    "external profiler did not create the go file within 300s"
                )
            time.sleep(0.05)
        profile_samples = []
        # Optional PMPI tools can delimit exactly this phase. This is a no-op
        # with the ordinary MPI library, and never wraps acceptance samples.
        MPI.Pcontrol(1)
        for run in range(args.profile_repeats):
            comm.Barrier()
            start = time.perf_counter()
            profiled = s.solve_pyquda(source)
            wall = comm.allreduce(time.perf_counter() - start, op=MPI.MAX)
            profile_samples.append(dict(s.last_result, python_wall_seconds=wall))
            assert np.array_equal(original, source.data)
        MPI.Pcontrol(0)
        assert relative(profiled.data, li.evenodd(reference, False)) < 1e-6
        result["profile_samples"] = profile_samples
        (args.profile_control / f"rank{comm.rank}.done").touch()
    if comm.rank == 0:
        (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            "RESULT",
            json.dumps(
                {
                    k: v
                    for k, v in result.items()
                    if k not in ("samples", "twelve_rhs_stats", "twelve_rhs_samples")
                }
            ),
            flush=True,
        )
