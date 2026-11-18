"""Check adaptive setup batching against exact free Wilson eigenmodes."""
import json
import os
from pathlib import Path
import sys

from mpi4py import MPI
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings"))
from lqcd_cpu import Solver


def main():
    comm = MPI.COMM_WORLD
    assert comm.size == 2
    lattice = (8, 8, 8, 8)
    grid = (1, 1, 1, comm.size)
    mass = .25
    options = dict(mass=mass, block=(2, 2, 2, 2), threads=1, comm=comm)
    os.environ.update(LQCD_MG_SETUP_PASSES="1", LQCD_MG_SETUP_ITERATIONS="1",
                      LQCD_MG_SETUP_SMOOTH="4", LQCD_COARSE_BATCH_REDUCE="1",
                      LQCD_SETUP_UPDATE="inverse", LQCD_RHS_BATCH="2")
    for invalid in ("0", "13", "1.5", str(comm.rank + 1)):
        os.environ["LQCD_MG_SETUP_BATCH"] = invalid
        try:
            with Solver(lattice, grid, **options):
                raise AssertionError("Invalid or inconsistent setup width was accepted")
        except RuntimeError as exc:
            assert "LQCD_MG_SETUP_BATCH" in str(exc), exc

    local_t = lattice[3] // comm.size
    ts = np.arange(local_t) + comm.rank * local_t
    shape = (local_t, 8, 8, 8, 4, 3)
    gauge = np.broadcast_to(np.eye(3, dtype=np.complex128), (*shape[:4], 4, 3, 3)).copy()
    solutions, sources = [], []
    for momentum, spin, color in ((np.pi / 8, 0, 0), (3 * np.pi / 8, 1, 2)):
        solution = np.zeros(shape, dtype=np.complex128)
        solution[..., spin, color] = np.exp(1j * momentum * ts)[:, None, None, None]
        gamma_t_solution = np.concatenate((solution[..., 2:, :], solution[..., :2, :]), axis=-2)
        source = (1 + mass - np.cos(momentum)) * solution + 1j * np.sin(momentum) * gamma_t_solution
        solutions.append(solution)
        sources.append(source)

    evidence = []
    for width in (1, 5):
        os.environ["LQCD_MG_SETUP_BATCH"] = str(width)
        with Solver(lattice, grid, **options) as solver:
            solver.load_gauge(gauge, "lex")
            setup_seconds = comm.allreduce(solver.setup(), op=MPI.MAX)
            actual, statistics = solver.solve_many(np.stack(sources), tol=1e-10, layout="lex")
        errors = [comm.allreduce(float(np.linalg.norm(got - expected) ** 2)) ** .5
                  / comm.allreduce(float(np.linalg.norm(expected) ** 2)) ** .5
                  for got, expected in zip(actual, solutions)]
        assert len(statistics) == len(errors) == 2 and max(errors) < 2e-9, errors
        assert all(row["converged"] and 0 <= row["true_residual"] <= 1e-10 for row in statistics)
        evidence.append(dict(width=width, setup_seconds=setup_seconds, relative_errors=errors,
                             residuals=[row["true_residual"] for row in statistics]))
    if comm.rank == 0:
        print(json.dumps(dict(passed=True, ranks=comm.size, rejected_invalid_widths=True, cases=evidence)))


if __name__ == "__main__":
    main()
