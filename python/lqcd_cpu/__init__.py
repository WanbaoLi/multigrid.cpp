"""CPU solver API; NumPy complex128 arrays use PyQUDA EO-x packing.

MPI is initialized/owned by mpi4py, never by the native solver. All calls are
collective. Hardware backends x86/arm use the project-owned MG implementation.
One live context per process, no concurrent operations.
"""

import ctypes as C
import json
import os
import operator
import platform
from pathlib import Path
import numpy as np
from mpi4py import MPI


def columns_to_propagator(columns):
    """[12,p,t,z,y,x/2,s,c] -> PyQUDA [p,t,z,y,x/2,s,S,c,C]."""
    if (
        not isinstance(columns, np.ndarray)
        or columns.ndim != 8
        or columns.shape[0] != 12
        or columns.shape[1] != 2
        or columns.shape[-2:] != (4, 3)
    ):
        raise ValueError(
            "expected twelve EO-x fermion columns in source_spin*3+source_color order"
        )
    return (
        columns.reshape(4, 3, *columns.shape[1:])
        .transpose(2, 3, 4, 5, 6, 7, 0, 8, 1)
        .copy()
    )


def propagator_to_columns(propagator):
    """Inverse of columns_to_propagator, preserving PyQUDA source indexing."""
    if (
        not isinstance(propagator, np.ndarray)
        or propagator.ndim != 9
        or propagator.shape[0] != 2
        or propagator.shape[-4:] != (4, 4, 3, 3)
    ):
        raise ValueError("expected PyQUDA EO-x propagator")
    p = propagator.transpose(6, 8, 0, 1, 2, 3, 4, 5, 7)
    return p.reshape(12, *propagator.shape[:5], 4, 3).copy()


class Config(C.Structure):
    _fields_ = [
        ("abi_version", C.c_uint32),
        ("struct_size", C.c_uint32),
        ("lattice", C.c_int32 * 4),
        ("process_grid", C.c_int32 * 4),
        ("block", C.c_int32 * 4),
        ("threads", C.c_int32),
        ("levels", C.c_int32),
        ("t_boundary", C.c_int32),
        ("normalization", C.c_int32),
        ("mass", C.c_double),
        ("csw", C.c_double),
        ("seed", C.c_uint32),
        ("mpi_comm_f", C.c_int64),
    ]


class View(C.Structure):
    _fields_ = [
        ("data", C.c_void_p),
        ("complex_elements", C.c_uint64),
        ("layout", C.c_int32),
        ("precision", C.c_int32),
    ]


class Result(C.Structure):
    _fields_ = [
        ("struct_size", C.c_uint32),
        ("converged", C.c_int32),
        ("iterations", C.c_int32),
        ("refinement_steps", C.c_int32),
        ("solver_seconds", C.c_double),
        ("api_seconds", C.c_double),
        ("true_residual", C.c_double),
    ]


def _library(path):
    if path is None:
        path = os.environ.get(
            "LQCD_CPU_LIBRARY",
            str(Path(__file__).resolve().parents[2] / "build/runtime/liblqcd_cpu.so"),
        )
    lib = C.CDLL(str(path))
    lib.lqcd_last_error.restype = C.c_char_p
    lib.lqcd_backend_capabilities.argtypes = [C.c_char_p]
    lib.lqcd_backend_capabilities.restype = C.c_char_p
    lib.lqcd_create.argtypes = [C.c_char_p, C.POINTER(Config), C.POINTER(C.c_void_p)]
    lib.lqcd_load_gauge.argtypes = [C.c_void_p, C.POINTER(View)]
    lib.lqcd_setup.argtypes = [C.c_void_p, C.POINTER(C.c_double)]
    lib.lqcd_apply.argtypes = [C.c_void_p, C.POINTER(View), C.POINTER(View)]
    lib.lqcd_solve.argtypes = [
        C.c_void_p,
        C.POINTER(View),
        C.POINTER(View),
        C.c_double,
        C.POINTER(Result),
    ]
    if hasattr(lib, "lqcd_solve_batch"):
        lib.lqcd_solve_batch.argtypes = [C.c_void_p, C.POINTER(View), C.POINTER(View),
                                       C.c_int, C.c_double, C.POINTER(Result)]
        lib.lqcd_solve_batch.restype = C.c_int
    lib.lqcd_destroy.argtypes = [C.c_void_p]
    # Preserve loading historical libraries for benchmark/reference comparison.
    # Only calling the new resource setter requires this additive ABI symbol.
    if hasattr(lib, "lqcd_set_threads"):
        lib.lqcd_set_threads.argtypes = [C.c_void_p, C.c_int32]
        lib.lqcd_set_threads.restype = C.c_int
    return lib


def _resolve_threads(threads):
    """Resolve rank-local resources before dlopen can bind the calling thread."""
    if threads is None:
        requested = os.environ.get("OMP_NUM_THREADS")
        if requested:
            try:
                values = [int(value.strip()) for value in requested.split(",")]
            except ValueError as exc:
                raise ValueError(
                    "OMP_NUM_THREADS must contain positive integer thread counts"
                ) from exc
            if any(value < 1 or value > 2147483647 for value in values):
                raise ValueError("OMP_NUM_THREADS counts must fit a positive int32")
            threads = values[0]
        else:
            threads = (
                len(os.sched_getaffinity(0))
                if hasattr(os, "sched_getaffinity")
                else os.cpu_count() or 1
            )
    if isinstance(threads, (bool, np.bool_)):
        raise ValueError("threads must be a positive integer, not a boolean")
    try:
        threads = operator.index(threads)
    except TypeError as exc:
        raise ValueError("threads must be a positive integer") from exc
    if not 1 <= threads <= 2147483647:
        raise ValueError("threads must fit a positive int32")
    return threads


def _resolve_backend(backend=None):
    """Select the executing CPU architecture, never a library/NPU brand alias."""
    if backend is not None:
        if not isinstance(backend, str) or not backend:
            raise ValueError("backend must be a nonempty string")
        return backend  # C ABI reports unavailable explicit backends collectively
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64", "i386", "i486", "i586", "i686"):
        return "x86"
    if machine in ("aarch64", "arm64"):
        return "arm"
    raise ValueError(f"no native hardware backend for machine {machine!r}")


class Solver:
    def __init__(
        self,
        lattice,
        process_grid,
        *,
        mass,
        csw=1.0,
        t_boundary=-1,
        block=(6, 6, 6, 4),
        levels=2,
        threads=None,
        normalization="mass",
        seed=1024,
        comm=MPI.COMM_WORLD,
        library=None,
        backend=None,
    ):
        self.comm = comm
        self._handle = C.c_void_p()
        self.last_result = None
        # libgomp initialization may pin the main thread and shrink the affinity
        # visible to sched_getaffinity; capture the request before loading it.
        try:
            backend = _resolve_backend(backend)
            threads = _resolve_threads(threads)
            error = None
        except Exception as exc:
            error = str(exc)
        self._check_collective(error is None, error or "invalid backend/thread configuration")
        self._backend_name = backend
        try:
            self.lib = _library(library)
            error = None
        except Exception as exc:
            error = str(exc)
        self._check_collective(error is None, error or "library load failed")
        self._check_collective(
            len(lattice) == 4 and len(process_grid) == 4 and len(block) == 4,
            "four-dimensional geometry required",
        )
        self._check_collective(
            normalization in ("mass", "kappa"), "normalization must be mass or kappa"
        )
        try:
            cfg = Config(
                1,
                C.sizeof(Config),
                (C.c_int32 * 4)(*lattice),
                (C.c_int32 * 4)(*process_grid),
                (C.c_int32 * 4)(*block),
                threads,
                levels,
                t_boundary,
                int(normalization == "kappa"),
                mass,
                csw,
                seed,
                comm.py2f(),
            )
            error = None
        except Exception as exc:
            error = str(exc)
        self._check_collective(error is None, error or "invalid configuration type")
        self._call(
            self.lib.lqcd_create(backend.encode(), C.byref(cfg), C.byref(self._handle))
        )
        self.global_size = tuple(lattice)
        self.grid = tuple(process_grid)
        self.local = tuple(n // p for n, p in zip(lattice, process_grid))
        self.coords = tuple(int(x) for x in np.unravel_index(comm.rank, self.grid))
        self.config = cfg

    def _check_collective(self, condition, message):
        if not MPI.Is_thread_main():
            raise RuntimeError("collective API requires the MPI main thread")
        failures = self.comm.allgather(None if condition else message)
        if any(failures):
            raise ValueError(str(failures))

    def _call(self, status):
        if status:
            raise RuntimeError(
                f"lqcd status {status}: {self.lib.lqcd_last_error().decode()}"
            )

    def _view(self, array, layout, gauge=False):
        x, y, z, t = self.local
        shapes = {
            "pyquda": (
                (4, 2, t, z, y, x // 2, 3, 3) if gauge else (2, t, z, y, x // 2, 4, 3)
            ),
            "lex": ((t, z, y, x, 4, 3, 3) if gauge else (t, z, y, x, 4, 3)),
        }
        valid = (
            layout in shapes
            and isinstance(array, np.ndarray)
            and array.dtype == np.complex128
            and array.flags.c_contiguous
            and array.shape == shapes.get(layout)
        )
        self._check_collective(
            valid,
            "expected contiguous host complex128 array with declared local layout",
        )
        return View(array.ctypes.data, array.size, int(layout == "pyquda"), 0)

    def load_gauge(self, gauge, layout="pyquda"):
        self._live()
        v = self._view(gauge, layout, True)
        self._call(self.lib.lqcd_load_gauge(self._handle, C.byref(v)))

    def setup(self):
        self._live()
        seconds = C.c_double()
        self._call(self.lib.lqcd_setup(self._handle, C.byref(seconds)))
        return seconds.value

    def set_threads(self, threads):
        """Collectively change rank-local OpenMP resources on a ready hierarchy."""
        self._live()
        supported = hasattr(self.lib, "lqcd_set_threads")
        self._check_collective(supported, "loaded library does not support set_threads")
        try:
            threads = _resolve_threads(threads)
            error = None
        except Exception as exc:
            error = str(exc)
        self._check_collective(error is None, error or "invalid thread configuration")
        self._call(self.lib.lqcd_set_threads(self._handle, threads))
        self.config.threads = threads

    def apply(self, source, layout="pyquda"):
        self._live()
        src = self._view(source, layout)
        out = np.empty_like(source)
        dst = self._view(out, layout)
        self._call(self.lib.lqcd_apply(self._handle, C.byref(src), C.byref(dst)))
        return out

    def solve(self, source, tol=1e-8, layout="pyquda"):
        self._live()
        src = self._view(source, layout)
        out = np.empty_like(source)
        return self._solve_into(src, out, tol, layout)

    def _solve_into(self, source_view, out, tol, layout):
        """Internal: source_view is already collectively validated by the caller.

        The output is fresh writable storage owned by solve/solve_many, with
        no overlap with the source. Native lqcd_solve uses a zero initial guess.
        """
        dst = self._view(out, layout)
        r = Result()
        r.struct_size = C.sizeof(r)
        status = self.lib.lqcd_solve(
            self._handle, C.byref(source_view), C.byref(dst), tol, C.byref(r)
        )
        self.last_result = {
            name: getattr(r, name) for name, _ in r._fields_ if name != "struct_size"
        }
        self._call(status)
        return out

    def solve_pyquda(self, source, tol=1e-8):
        """Return a PyQUDA LatticeFermion; caller supplies a CPU/NumPy field.

        Use normalization='mass' for raw Mx=b. Compatibility is explicit,
        not dependent on any high-level helper's hidden RHS rescaling.
        """
        li = self._field_info(source)
        from pyquda.field import LatticeFermion

        return LatticeFermion(li, self.solve(source.data, tol))

    def _field_info(self, field):
        li = getattr(field, "latt_info", None)
        self._check_collective(
            li is not None
            and tuple(li.global_size) == self.global_size
            and tuple(li.grid_size) == self.grid
            and tuple(li.grid_coord) == self.coords
            and li.anisotropy == 1
            and li.t_boundary == self.config.t_boundary,
            "PyQUDA geometry/rank map/boundary mismatch",
        )
        return li

    def load_pyquda_gauge(self, gauge):
        self._field_info(gauge)
        self.load_gauge(gauge.data)

    def solve_many(self, sources, tol=1e-8, layout="pyquda"):
        """Independent zero-start RHS solves; optional groups of up to twelve share batch wall timing."""
        self._check_collective(
            isinstance(sources, np.ndarray) and sources.ndim >= 2,
            "sources must be an array of RHS fields",
        )
        counts = self.comm.allgather(len(sources))
        self._check_collective(
            len(set(counts)) == 1 and counts[0] > 0, "RHS count must agree across ranks"
        )
        requested = os.environ.get("LQCD_RHS_BATCH", "1")
        self._check_collective(requested in tuple(str(i) for i in range(1, 13)), "LQCD_RHS_BATCH must be an integer from 1 through 12")
        modes = self.comm.allgather(requested)
        self._check_collective(all(mode == requested for mode in modes),
                               "LQCD_RHS_BATCH must agree across ranks")
        batch = int(requested)
        if batch > 1:
            self._check_collective(hasattr(self.lib, "lqcd_solve_batch"),
                                   "loaded library does not support RHS batching")
        solutions = None
        results = []
        for index in range(0, len(sources), batch):
            count = min(batch, len(sources) - index)
            try:
                self._live()
                src = [self._view(sources[index + j], layout) for j in range(count)]
                if solutions is None:
                    # The batch axis may be strided, but each source field must
                    # meet the existing C-contiguous external layout contract.
                    solutions = np.empty(sources.shape, dtype=np.complex128, order="C")
                if count == 1:
                    self._solve_into(src[0], solutions[index], tol, layout)
                    results.append(dict(self.last_result))
                else:
                    dst = [self._view(solutions[index + j], layout) for j in range(count)]
                    stats = (Result * count)()
                    for result in stats:
                        result.struct_size = C.sizeof(Result)
                    status = self.lib.lqcd_solve_batch(
                        self._handle, (View * count)(*src), (View * count)(*dst),
                        count, tol, stats)
                    batch_results = [dict(
                        **{name: getattr(r, name) for name, _ in r._fields_ if name != "struct_size"},
                        batch_size=count, timing_scope="shared_batch") for r in stats]
                    self.last_result = batch_results[-1]
                    self._call(status)
                    results.extend(batch_results)
            except RuntimeError as exc:
                label = f"RHS {index}" if count == 1 else f"RHS batch starting at {index}"
                raise RuntimeError(f"{label} failed: {self.last_result}") from exc
        return solutions, results

    def solve_propagator(self, point=(0, 0, 0, 0), tol=1e-8, *, source_scale=1.0,
                         layout="pyquda"):
        """Solve all twelve spin/color point sources sharing one MG setup.

        ``point`` is a global XYZT coordinate. With mass normalization and
        source_scale=1, the result is M^-1(x, point). The return value is
        (local propagator, twelve result dictionaries). Output has PyQUDA's
        [p,t,z,y,x/2,s,S,c,C] order, or [t,z,y,x,s,S,c,C] for layout='lex'.
        Capital S/C index the source; columns run in S*3+C order. Every column
        starts from zero; this is independent RHS solving, not block Krylov.
        """
        self._live()
        error = None
        try:
            point = tuple(operator.index(x) for x in point)
            source_scale = float(source_scale)
            if len(point) != 4 or any(not 0 <= x < n for x, n in zip(point, self.global_size)):
                raise ValueError("point must be a global XYZT coordinate inside the lattice")
            if layout not in ("lex", "pyquda") or not np.isfinite(source_scale) or source_scale == 0:
                raise ValueError("invalid layout or nonfinite/zero source_scale")
        except (TypeError, ValueError, OverflowError) as exc:
            error = str(exc)
        self._check_collective(error is None, error or "invalid point source")
        descriptions = self.comm.allgather((point, source_scale, layout))
        self._check_collective(all(x == descriptions[0] for x in descriptions),
                               "point/source_scale/layout must agree across ranks")
        x, y, z, t = self.local
        shape = ((t, z, y, x, 4, 3) if layout == "lex"
                 else (2, t, z, y, x // 2, 4, 3))
        rhs = np.zeros((12, *shape), dtype=np.complex128)
        local_point = tuple(p - c * n for p, c, n in zip(point, self.coords, self.local))
        if all(0 <= p < n for p, n in zip(local_point, self.local)):
            px, py, pz, pt = local_point
            site = ((pt, pz, py, px) if layout == "lex"
                    else (sum(point) % 2, pt, pz, py, px // 2))
            for spin in range(4):
                for color in range(3):
                    rhs[(spin * 3 + color, *site, spin, color)] = source_scale
        columns, stats = self.solve_many(rhs, tol, layout)
        if layout == "pyquda":
            return columns_to_propagator(columns), stats
        # [S,C,t,z,y,x,s,c] -> [t,z,y,x,s,S,c,C].
        propagator = columns.reshape(4, 3, t, z, y, x, 4, 3).transpose(2, 3, 4, 5, 6, 0, 7, 1)
        return np.ascontiguousarray(propagator), stats

    @property
    def capabilities(self):
        return json.loads(
            self.lib.lqcd_backend_capabilities(self._backend_name.encode())
        )

    def _live(self):
        self._check_collective(bool(self._handle.value), "solver is closed")

    def close(self):
        if self._handle.value:
            self._call(self.lib.lqcd_destroy(self._handle))
            self._handle = C.c_void_p()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # No __del__: collective MPI finalization must never occur unpredictably in GC.
