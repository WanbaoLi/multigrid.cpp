"""Small t-slab halo correctness test for the native backend.

Run with the runtime's MPI Python environment, for example:
  mpiexec -n 2 python tests/runtime/test_native_halo.py
It deliberately uses different OpenMP counts (1 and 2) to catch accidental
rank-wide thread assumptions while comparing every rank's operator to a global
analytic Wilson stencil.
"""

import os, sys
from pathlib import Path
import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from lqcd_cpu import Solver
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo

comm = MPI.COMM_WORLD
if comm.size != 2:
    raise SystemExit("test_native_halo requires exactly two MPI ranks")
grid = (1, 1, 1, 2)
initGrid(grid_size=grid)
lat = (8, 8, 8, 16)
li = LatticeInfo(list(lat), -1, 1.0)
# pyquda_comm coordinates are represented in x,y,z,t order by this API.
coords = tuple(int(x) for x in li.grid_coord)
local = tuple(n // p for n, p in zip(lat, grid))
sl = tuple(slice(c * n, (c + 1) * n) for c, n in zip(coords[::-1], local[::-1]))
rng = np.random.default_rng(9173)
full = (
    rng.standard_normal((16, 8, 8, 8, 4, 3))
    + 1j * rng.standard_normal((16, 8, 8, 8, 4, 3))
).astype(np.complex128)
gamma = np.array(
    [
        [[0, 0, 0, 1j], [0, 0, 1j, 0], [0, -1j, 0, 0], [-1j, 0, 0, 0]],
        [[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]],
        [[0, 0, 1j, 0], [0, 0, 0, -1j], [-1j, 0, 0, 0], [0, 1j, 0, 0]],
        [[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]],
    ],
    dtype=np.complex128,
)
mass = 0.05
kappa = 1 / (2 * (4 + mass))


def wilson_mass(field):
    result = field.copy()
    for mu in range(4):
        axis = 3 - mu
        plus = np.roll(field, -1, axis=axis)
        minus = np.roll(field, 1, axis=axis)
        if mu == 3:
            plus[-1] *= -1
            minus[0] *= -1
        result -= kappa * (
            np.einsum("ij,...jc->...ic", np.eye(4) - gamma[mu], plus)
            + np.einsum("ij,...jc->...ic", np.eye(4) + gamma[mu], minus)
        )
    return result / (2 * kappa)


expected = wilson_mass(full)
# Public EO-x source and gauge are rank-local.
source_lex = full[sl].copy()
rhs = li.evenodd(source_lex, False)
gauge_lex = np.broadcast_to(
    np.eye(3, dtype=np.complex128), (4, *local[::-1], 3, 3)
).copy()
gauge = li.evenodd(gauge_lex, True)
expected_local = li.evenodd(expected[sl].copy(), False)


def rel(a, b):
    num = comm.allreduce(float(np.vdot((a - b).ravel(), (a - b).ravel()).real))
    den = comm.allreduce(float(np.vdot(b.ravel(), b.ravel()).real))
    return np.sqrt(num / den)


threads = 1 + comm.rank
os.environ["OMP_NUM_THREADS"] = str(threads)
results = []
for overlap, adaptive in (("0", "1"), ("1", "1"), ("1", "0")):
    os.environ["LQCD_HALO_OVERLAP"] = overlap
    os.environ["LQCD_ADAPTIVE_CORRECTION"] = adaptive
    with Solver(
        lat, grid, mass=mass, block=[2] * 4, levels=2, threads=threads
    ) as solver:
        solver.load_gauge(gauge)
        solver.setup()
        assert rel(solver.apply(rhs), expected_local) < 2e-12
        # Each rank has four coarse time planes, including two interior planes.
        # Full solves exercise nonblocking halo traffic throughout MG iteration.
        original = rhs.copy()
        x = solver.solve(rhs, tol=1e-8)
        assert np.array_equal(rhs, original)
        assert solver.last_result["true_residual"] <= 1e-8
        x2 = solver.solve(rhs, tol=1e-8)
        assert rel(x, x2) < 2e-10
        full_solution = np.concatenate(comm.allgather(li.lexico(x2, False)), axis=0)
        independent = np.linalg.norm(
            (wilson_mass(full_solution) - full).ravel()
        ) / np.linalg.norm(full.ravel())
        assert independent <= 1e-8, independent
        results.append(x2.copy())
        if comm.rank == 0:
            print(
                f"halo_overlap={overlap}, adaptive={adaptive}: independent_residual={independent:.3e}",
                flush=True,
            )
        if overlap == "1" and adaptive == "1":
            for scale, tolerance in ((1e-4, 1e-2), (1e4, 1e-10)):
                scaled = solver.solve(rhs * scale, tol=tolerance)
                whole = np.concatenate(comm.allgather(li.lexico(scaled, False)), axis=0)
                residual = np.linalg.norm(
                    (wilson_mass(whole) - full * scale).ravel()
                ) / np.linalg.norm((full * scale).ravel())
                assert residual <= tolerance, (scale, tolerance, residual)
assert rel(results[0], results[1]) < 2e-10
assert rel(results[1], results[2]) < 1e-6
if comm.rank == 0:
    print(
        "PASS: blocking/overlapped two-rank halo, independent operator/residual, repeated solves, unequal threads",
        flush=True,
    )
