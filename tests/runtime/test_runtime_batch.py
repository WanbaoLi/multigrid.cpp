"""MPI2 two-RHS regression with an independent NumPy Wilson stencil."""
import os
import ctypes as C
from pathlib import Path
import sys

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from lqcd_cpu import Solver, View, Result
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo

comm = MPI.COMM_WORLD
assert comm.size == 2
initGrid(grid_size=[1, 1, 1, 2])
li = LatticeInfo([8] * 4, -1, 1.)
sl = slice(4 * comm.rank, 4 * (comm.rank + 1))
rng = np.random.default_rng(1928)
whole = rng.normal(size=(2, 8, 8, 8, 8, 4, 3)) + 1j * rng.normal(size=(2, 8, 8, 8, 8, 4, 3))
rhs = np.stack([li.evenodd(np.ascontiguousarray(v[sl]), False) for v in whole])
gauge = li.evenodd(np.broadcast_to(np.eye(3, dtype=np.complex128), (4, 4, 8, 8, 8, 3, 3)).copy(), True)
gamma = np.array([
    [[0,0,0,1j],[0,0,1j,0],[0,-1j,0,0],[-1j,0,0,0]],
    [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
    [[0,0,1j,0],[0,0,0,-1j],[-1j,0,0,0],[0,1j,0,0]],
    [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]],
], dtype=np.complex128)


def wilson(field):
    result = 4.05 * field.copy()
    for mu in range(4):
        plus, minus = np.roll(field, -1, axis=3-mu), np.roll(field, 1, axis=3-mu)
        if mu == 3:
            plus[-1] *= -1
            minus[0] *= -1
        result -= .5 * (np.einsum("ij,...jc->...ic", np.eye(4)-gamma[mu], plus)
                        + np.einsum("ij,...jc->...ic", np.eye(4)+gamma[mu], minus))
    return result


def relative(actual, expected):
    delta = actual - expected
    return np.sqrt(comm.allreduce(float(np.vdot(delta, delta).real)) /
                   comm.allreduce(float(np.vdot(expected, expected).real)))


def check(solver, sources, expected=None, layout="pyquda", normalization="mass"):
    before = sources.copy()
    solution, stats = solver.solve_many(sources, tol=1e-10, layout=layout)
    assert np.array_equal(sources, before)
    assert len(stats) == len(sources)
    for i, (x, b) in enumerate(zip(solution, sources)):
        assert stats[i]["converged"] and stats[i]["true_residual"] <= 1e-10
        if not comm.allreduce(float(np.vdot(b, b).real)):
            assert np.count_nonzero(x) == 0 and stats[i]["iterations"] == 0
            continue
        assert relative(solver.apply(x, layout=layout), b) <= 1e-10
        full_x = np.concatenate(comm.allgather(li.lexico(x, False) if layout == "pyquda" else x), axis=0)
        full_b = np.concatenate(comm.allgather(li.lexico(b, False) if layout == "pyquda" else b), axis=0)
        image = wilson(full_x) / (4.05 if normalization == "kappa" else 1.)
        assert np.linalg.norm(image-full_b) / np.linalg.norm(full_b) <= 1e-10
        if expected is not None:
            assert relative(x, expected[i]) < 1e-8
    return solution, stats


with Solver([8]*4, [1,1,1,2], mass=.05, block=[2]*4, threads=1+comm.rank) as solver:
    solver.load_gauge(gauge)
    solver.setup()
    os.environ["LQCD_RHS_BATCH"] = "1"
    reference, _ = check(solver, rhs)
    os.environ["LQCD_RHS_BATCH"] = "2"
    first, stats = check(solver, rhs, reference)
    repeated, repeated_stats = check(solver, rhs, reference)
    assert [s["iterations"] for s in stats] == [s["iterations"] for s in repeated_stats]
    assert relative(repeated, first) < 1e-12
    # Three strided fields exercise a pair plus scalar tail without copying
    # away the public batch-axis stride; each individual field is contiguous.
    storage = np.zeros((6,) + rhs.shape[1:], dtype=np.complex128)
    storage[0], storage[2], storage[4] = rhs[0], rhs[1], rhs[0]
    assert not storage[::2].flags.c_contiguous and storage[0].flags.c_contiguous
    check(solver, storage[::2], np.stack([reference[0],reference[1],reference[0]]))
    check(solver, np.stack([rhs[0], rhs[0]]), np.stack([reference[0], reference[0]]))
    check(solver, np.stack([np.zeros_like(rhs[0]), rhs[1]]))
    check(solver, np.zeros_like(rhs))
    for key, value in (("LQCD_FLOAT_CORRECTION_VERIFY", "1"), ("LQCD_GCR_FUSED", "0")):
        previous = os.environ.get(key)
        os.environ[key] = value
        check(solver, rhs, reference)
        if previous is None:
            del os.environ[key]
        else:
            os.environ[key] = previous
    # Faults must be collective and leave the live context usable. Call the C
    # entry directly for counts the public Python pair loop cannot generate.
    def rejected_then_recover(call):
        caught = False
        try:
            call()
        except (ValueError, RuntimeError):
            caught = True
        assert comm.allreduce(int(caught)) == comm.size
        os.environ["LQCD_RHS_BATCH"] = "2"
        check(solver, rhs, reference)

    for value in ("invalid", str(1 + comm.rank)):
        os.environ["LQCD_RHS_BATCH"] = value
        rejected_then_recover(lambda: solver.solve_many(rhs))

    def c_batch(count=2, tolerance=1e-10, source=rhs):
        output = np.empty_like(source)
        ins = (View * 2)(*[solver._view(source[j], "pyquda") for j in range(2)])
        outs = (View * 2)(*[solver._view(output[j], "pyquda") for j in range(2)])
        stats = (Result * 2)()
        for r in stats:
            r.struct_size = C.sizeof(Result)
        solver._call(solver.lib.lqcd_solve_batch(solver._handle, ins, outs, count, tolerance, stats))

    for count in (0, 3, 1 + comm.rank):
        rejected_then_recover(lambda count=count: c_batch(count=count))
    rejected_then_recover(lambda: c_batch(tolerance=1e-10 * (1 + comm.rank)))
    invalid_source = rhs.copy()
    if comm.rank == 0:
        invalid_source[1].flat[0] = np.nan
    rejected_then_recover(lambda: c_batch(source=invalid_source))
    # Layout conversion must commute with the batch path.
    lex_sources = np.stack([li.lexico(b, False) for b in rhs])
    lex_reference = np.stack([li.lexico(x, False) for x in reference])
    check(solver, lex_sources, lex_reference, layout="lex")

with Solver([8]*4, [1,1,1,2], mass=.05, block=[2]*4, threads=1+comm.rank,
            normalization="kappa") as solver:
    solver.load_gauge(gauge)
    solver.setup()
    os.environ["LQCD_RHS_BATCH"] = "2"
    # D_kappa = D_mass / (4+mass), hence x_kappa = (4+mass)*x_mass.
    check(solver, rhs, 4.05 * reference, normalization="kappa")
    check(solver, lex_sources, 4.05 * lex_reference, layout="lex", normalization="kappa")
if comm.rank == 0:
    print("PASS batch independent RHS, zero/repeated/odd tail/strides, zero starts, scalar and independent stencil gates")
