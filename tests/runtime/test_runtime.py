"""Collective MPI contract/numerical tests; no GPU or real gauge required."""

import os, sys
from pathlib import Path
import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from lqcd_cpu import Solver, columns_to_propagator, propagator_to_columns
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo, LatticeFermion, LatticePropagator

comm = MPI.COMM_WORLD
grid = {1: (1, 1, 1, 1), 2: (1, 1, 1, 2), 4: (1, 1, 1, 4)}[comm.size]
initGrid(grid_size=grid)
li = LatticeInfo([8] * 4, -1, 1.0)
coords = np.unravel_index(comm.rank, grid)
local = tuple(8 // p for p in grid)
sl = tuple(slice(c * n, (c + 1) * n) for c, n in zip(coords[::-1], local[::-1]))
rng = np.random.default_rng(314159)
full = (
    rng.standard_normal((8, 8, 8, 8, 4, 3))
    + 1j * rng.standard_normal((8, 8, 8, 8, 4, 3))
).astype(np.complex128)
i = 1j
gammas = np.array(
    [
        [[0, 0, 0, i], [0, 0, i, 0], [0, -i, 0, 0], [-i, 0, 0, 0]],
        [[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]],
        [[0, 0, i, 0], [0, 0, 0, -i], [-i, 0, 0, 0], [0, i, 0, 0]],
        [[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]],
    ]
)
mass = 0.05
kappa = 1 / (2 * (4 + mass))
expected = full.copy()
for mu in range(4):
    axis = 3 - mu
    plus = np.roll(full, -1, axis)
    minus = np.roll(full, 1, axis)
    if mu == 3:
        plus[-1] *= -1
        minus[0] *= -1
    expected -= kappa * (
        np.einsum("ij,...jc->...ic", np.eye(4) - gammas[mu], plus)
        + np.einsum("ij,...jc->...ic", np.eye(4) + gammas[mu], minus)
    )
rhs_lex = full[sl].copy()
rhs = li.evenodd(rhs_lex, False)
columns = np.stack([rhs * (j + 1) for j in range(12)])
prop = LatticePropagator(li, columns_to_propagator(columns))
assert np.array_equal(propagator_to_columns(prop.data), columns)
for spin in range(4):
    for color in range(3):
        assert np.array_equal(
            prop.getFermion(spin, color).data, columns[spin * 3 + color]
        )
g = np.broadcast_to(np.eye(3, dtype=np.complex128), (4, *local[::-1], 3, 3)).copy()
g = li.evenodd(g, True)


def relative(a, b):
    return np.sqrt(
        comm.allreduce(float(np.vdot((a - b).ravel(), (a - b).ravel()).real))
        / comm.allreduce(float(np.vdot(b.ravel(), b.ravel()).real))
    )


def must_fail(fn):
    caught = False
    try:
        fn()
    except (ValueError, RuntimeError):
        caught = True
    assert comm.allreduce(int(caught)) == comm.size


must_fail(
    lambda: Solver(
        [8] * 4, grid, mass=mass, block=[2] * 4, threads=2, backend="missing"
    )
)
if comm.size > 1:
    must_fail(
        lambda: Solver(
            [8] * 4, grid, mass=mass + comm.rank * 0.01, block=[2] * 4, threads=2
        )
    )
saved_setup = os.environ.get("LQCD_SETUP_UPDATE")
for invalid in ("invalid", "mismatched") if comm.size > 1 else ("invalid",):
    os.environ["LQCD_SETUP_UPDATE"] = (
        ("paper" if comm.rank == 0 else "inverse")
        if invalid == "mismatched"
        else invalid
    )
    with Solver([8] * 4, grid, mass=mass, block=[2] * 4, threads=2) as bad_setup:
        bad_setup.load_gauge(g)
        must_fail(bad_setup.setup)
if saved_setup is None:
    os.environ.pop("LQCD_SETUP_UPDATE", None)
else:
    os.environ["LQCD_SETUP_UPDATE"] = saved_setup
for normalization in ("mass", "kappa"):
    # Uneven NUMA/cpuset resources must not change the collective equation.
    # Exercise both explicit per-rank counts and the environment-derived default.
    local_threads = 1 + comm.rank % 2
    os.environ["OMP_NUM_THREADS"] = str(local_threads)
    with Solver(
        [8] * 4,
        grid,
        mass=mass,
        block=[2] * 4,
        levels=2,
        threads=local_threads if normalization == "mass" else None,
        normalization=normalization,
    ) as s:
        assert s.config.threads == local_threads
        must_fail(lambda: s.solve(rhs))
        must_fail(lambda: s.set_threads(2))  # not ready until setup completes
        s.load_gauge(g)
        s.setup()
        s.set_threads(2 + comm.rank % 2)
        assert s.config.threads == 2 + comm.rank % 2
        previous = s.config.threads
        must_fail(lambda: s.set_threads(0 if comm.rank == 0 else 2))
        must_fail(lambda: s.set_threads(2**32 + 1 if comm.rank == 0 else 2))
        assert s.config.threads == previous
        # Exercise native C validation separately from the Python guard.
        must_fail(
            lambda: s._call(
                s.lib.lqcd_set_threads(s._handle, 0 if comm.rank == 0 else 2)
            )
        )
        assert s.config.threads == previous
        expected_local = li.evenodd(expected[sl].copy(), False)
        if normalization == "mass":
            expected_local /= 2 * kappa
        assert relative(s.apply(rhs), expected_local) < 1e-12
        rhs_copy = rhs.copy()
        x = s.solve(rhs)
        assert np.array_equal(rhs, rhs_copy)
        assert relative(s.apply(x), rhs) < 1e-8
        s.set_threads(local_threads)
        assert s.config.threads == local_threads
        x2 = s.solve(rhs)
        assert relative(s.apply(x2), rhs) < 1e-8
        assert relative(x2, x) < 1e-8
        x = x2  # subsequent repeat checks use the restored thread configuration
        assert np.count_nonzero(s.solve(np.zeros_like(rhs))) == 0
        assert s.last_result["iterations"] == 0
        bad = rhs.astype(np.complex64) if comm.rank == 0 else rhs
        must_fail(lambda: s.solve(bad))
        must_fail(lambda: s.solve(rhs[..., ::-1]))
        if comm.size > 1:
            must_fail(lambda: s.apply(rhs) if comm.rank == 0 else s.solve(rhs))
        must_fail(lambda: s.load_gauge(g))
        must_fail(lambda: Solver([8] * 4, grid, mass=mass, block=[2] * 4, threads=2))
        field = LatticeFermion(li, rhs)
        out = s.solve_pyquda(field)
        assert out.data.shape == field.data.shape
        assert relative(out.data, x) < 1e-11
        lex = s.solve(rhs_lex, layout="lex")
        assert relative(li.evenodd(lex, False), x) < 1e-11
        many, stats = s.solve_many(np.stack([rhs, np.zeros_like(rhs)]))
        assert relative(many[0], x) < 1e-11 and np.count_nonzero(many[1]) == 0
        assert stats[1]["iterations"] == 0
    must_fail(lambda: s.solve(rhs))
    s.close()
if comm.rank == 0:
    print(
        "PASS: normalization, PyQUDA packing, MPI topology, repeated solve, zero RHS, lifecycle, collective errors",
        flush=True,
    )
