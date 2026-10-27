"""Optional local Schur SAP correctness gate; two MPI ranks, no GPU/real gauge.

Compares all fine/coarse even-odd combinations through the same external
Wilson operator, using an independent NumPy stencil for the final full residual.
"""

import os
from pathlib import Path
import sys
import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from lqcd_cpu import Solver
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo

comm = MPI.COMM_WORLD
if comm.size != 2:
    raise SystemExit("test_sap_eo requires exactly two MPI ranks")
grid = (1, 1, 1, 2)
initGrid(grid_size=grid)
lat = (8, 8, 8, 8)
li = LatticeInfo(list(lat), -1, 1.0)
local = tuple(n // p for n, p in zip(lat, grid))
coords = tuple(int(x) for x in li.grid_coord)
sl = tuple(slice(c * n, (c + 1) * n) for c, n in zip(coords[::-1], local[::-1]))
rng = np.random.default_rng(61593)
full = (
    rng.standard_normal((*lat[::-1], 4, 3))
    + 1j * rng.standard_normal((*lat[::-1], 4, 3))
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


def wilson(field):
    # Unit gauge has identity links and zero clover field strength.
    result = (4 + mass) * field.copy()
    for mu in range(4):
        plus = np.roll(field, -1, axis=3 - mu)
        minus = np.roll(field, 1, axis=3 - mu)
        if mu == 3:
            plus[-1] *= -1
            minus[0] *= -1
        result -= 0.5 * (
            np.einsum("ij,...jc->...ic", np.eye(4) - gamma[mu], plus)
            + np.einsum("ij,...jc->...ic", np.eye(4) + gamma[mu], minus)
        )
    return result


def rel(a, b):
    num = comm.allreduce(float(np.vdot((a - b).ravel(), (a - b).ravel()).real))
    den = comm.allreduce(float(np.vdot(b.ravel(), b.ravel()).real))
    return np.sqrt(num / den)


def unit_gauge(info):
    data = np.broadcast_to(
        np.eye(3, dtype=np.complex128), (4, *info.size[::-1], 3, 3)
    ).copy()
    return info.evenodd(data, True)


def must_fail(fn, message):
    caught = False
    try:
        fn()
    except (ValueError, RuntimeError) as error:
        caught = message in str(error)
    assert comm.allreduce(int(caught)) == comm.size, "expected rejection on every rank"


rhs_lex = full[sl].copy()
rhs = li.evenodd(rhs_lex, False)
expected = li.evenodd(wilson(full)[sl].copy(), False)
solutions = []
for fine_mode, coarse_mode in (("0", "0"), ("1", "0"), ("0", "1"), ("1", "1")):
    os.environ["LQCD_SAP_EO"] = fine_mode
    os.environ["LQCD_COARSE_EO"] = coarse_mode
    with Solver(
        lat, grid, mass=mass, block=[2] * 4, levels=2, threads=1 + comm.rank
    ) as solver:
        solver.load_gauge(unit_gauge(li))
        solver.setup()
        assert rel(solver.apply(rhs), expected) < 2e-12
        original = rhs.copy()
        x = solver.solve(rhs, tol=1e-8)
        assert np.array_equal(rhs, original)
        assert solver.last_result["true_residual"] <= 1e-8
        # Swapping external layouts exercises independent packing of the same RHS.
        x_lex = solver.solve(rhs_lex, tol=1e-8, layout="lex")
        assert rel(li.evenodd(x_lex, False), x) < 1e-6
        full_x = np.concatenate(comm.allgather(x_lex), axis=0)
        independent = np.linalg.norm((wilson(full_x) - full).ravel()) / np.linalg.norm(
            full.ravel()
        )
        assert independent <= 1e-8, independent
        zero = solver.solve(np.zeros_like(rhs))
        assert np.count_nonzero(zero) == 0
        assert solver.last_result["iterations"] == 0
        solutions.append(x.copy())
        if comm.rank == 0:
            print(
                f"sap_eo={fine_mode}, coarse_eo={coarse_mode}: independent_full_residual={independent:.3e}",
                flush=True,
            )
for solution in solutions[1:]:
    assert rel(solution, solutions[0]) < 1e-6

# Non-x odd block extent alternates global origin parity between aggregates.
# B=24 gives 12 sites per parity, exercising a SIMD tail not divisible by8.
os.environ["LQCD_SAP_EO"] = "1"
os.environ["LQCD_COARSE_EO"] = "1"
tail_lat = (8, 12, 8, 8)
tail_li = LatticeInfo(list(tail_lat), -1, 1.0)
tail_local = tuple(n // p for n, p in zip(tail_lat, grid))
tail_coords = tuple(int(x) for x in tail_li.grid_coord)
tail_sl = tuple(
    slice(c * n, (c + 1) * n) for c, n in zip(tail_coords[::-1], tail_local[::-1])
)
tail_full = (
    rng.standard_normal((*tail_lat[::-1], 4, 3))
    + 1j * rng.standard_normal((*tail_lat[::-1], 4, 3))
).astype(np.complex128)
tail_rhs = tail_li.evenodd(tail_full[tail_sl].copy(), False)
tail_expected = tail_li.evenodd(wilson(tail_full)[tail_sl].copy(), False)
with Solver(
    tail_lat, grid, mass=mass, block=[2, 3, 2, 2], levels=2, threads=1 + comm.rank
) as solver:
    solver.load_gauge(unit_gauge(tail_li))
    solver.setup()
    assert rel(solver.apply(tail_rhs), tail_expected) < 2e-12
    tail_original = tail_rhs.copy()
    tail_x = solver.solve(tail_rhs, tol=1e-8)
    assert np.array_equal(tail_rhs, tail_original)
    assert solver.last_result["true_residual"] <= 1e-8
    tail_full_x = np.concatenate(comm.allgather(tail_li.lexico(tail_x, False)), axis=0)
    independent = np.linalg.norm(
        (wilson(tail_full_x) - tail_full).ravel()
    ) / np.linalg.norm(tail_full.ravel())
    assert independent <= 1e-8, independent
    if comm.rank == 0:
        print(
            f"fine/coarse EO odd-by SIMD tail: independent_full_residual={independent:.3e}",
            flush=True,
        )

# The public geometry accepts bx=3 with global Lx=12, coarse extent4. The
# optional Schur SAP implementation must reject its unsupported local packing.
os.environ["LQCD_SAP_EO"] = "1"
os.environ["LQCD_COARSE_EO"] = "0"
odd_lat = (12, 8, 8, 8)
odd_li = LatticeInfo(list(odd_lat), -1, 1.0)


def odd_block_setup():
    with Solver(
        odd_lat, grid, mass=mass, block=[3, 2, 2, 2], levels=2, threads=1 + comm.rank
    ) as solver:
        solver.load_gauge(unit_gauge(odd_li))
        solver.setup()


must_fail(odd_block_setup, "LQCD_SAP_EO=1 requires an even x block size")

# All ranks must agree on a numerical smoother mode before setup computation.
os.environ["LQCD_SAP_EO"] = str(comm.rank)


def mismatched_mode_setup():
    with Solver(
        lat, grid, mass=mass, block=[2] * 4, levels=2, threads=1 + comm.rank
    ) as solver:
        solver.load_gauge(unit_gauge(li))
        solver.setup()


must_fail(
    mismatched_mode_setup, "LQCD_SAP_EO must be 0 or 1 and agree on every MPI rank"
)
# Invalid values must not silently enable/disable a smoother.
os.environ["LQCD_SAP_EO"] = "invalid"
must_fail(
    mismatched_mode_setup, "LQCD_SAP_EO must be 0 or 1 and agree on every MPI rank"
)
os.environ["LQCD_SAP_EO"] = "0"
os.environ["LQCD_COARSE_EO"] = str(comm.rank)
must_fail(
    mismatched_mode_setup, "LQCD_COARSE_EO must be 0 or 1 and agree on every MPI rank"
)
os.environ["LQCD_COARSE_EO"] = "invalid"
must_fail(
    mismatched_mode_setup, "LQCD_COARSE_EO must be 0 or 1 and agree on every MPI rank"
)
if comm.rank == 0:
    print(
        "PASS: four fine/coarse EO combinations, independent residual, layouts, zero RHS, collective mode/geometry rejection",
        flush=True,
    )
