"""CPU-only single/batch solves with automatic and unequal rank-local teams."""
import os
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bindings"))
from lqcd_cpu import Solver, _resolve_threads

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from run_numa import discover_nodes, rank_environment

comm = MPI.COMM_WORLD
assert comm.size in (1, 2, 4)
os.environ["LQCD_MG_SETUP_SMOOTH"] = "0"
os.environ["LQCD_MG_SETUP_PASSES"] = "0"
os.environ["LQCD_COARSE_THREADS"] = "1"
# MPI4 gives one aggregate time plane/rank, with coincident lower/upper
# boundary ownership. MPI2 also exercises independent interior time planes.
bt = int(os.environ.get("LQCD_TEST_BLOCK_T", "4" if comm.size == 4 else "2"))
lat = (8, 8, 8, 4 * bt)
local_t = lat[3] // comm.size
rng = np.random.default_rng(913 + comm.rank)
rhs = (rng.normal(size=(2, local_t, 8, 8, 8, 4, 3))
       + 1j * rng.normal(size=(2, local_t, 8, 8, 8, 4, 3)))
gauge = np.broadcast_to(np.eye(3, dtype=np.complex128),
                        (local_t, 8, 8, 8, 4, 3, 3)).copy()
# Use the available physical cores, partitioned per rank within a NUMA domain.
# Read before dlopen/OpenMP can bind the calling thread to a single CPU.
nodes = discover_nodes()
node_ids = sorted(nodes)
node = node_ids[comm.rank % len(node_ids)]
node_ranks = list(range(comm.rank % len(node_ids), comm.size, len(node_ids)))
cpus = nodes[node]
index = node_ranks.index(comm.rank)
first = len(cpus) * index // len(node_ranks)
last = len(cpus) * (index + 1) // len(node_ranks)
cpus = cpus[first:last]
assert cpus, "each test rank needs at least one allowed physical core"
auto_environment = rank_environment(dict(node=node, cpus=cpus))
os.environ.update(auto_environment)
automatic_threads = _resolve_threads(None)
assert automatic_threads == len(cpus)
team_counts = comm.allgather(automatic_threads)
max_residual = 0.0
for overlap in ("0", "1"):
    os.environ["LQCD_HALO_OVERLAP"] = overlap
    with Solver(lat, (1, 1, 1, comm.size), mass=2., block=(2, 2, 2, bt),
                threads=None, seed=1024) as solver:
        solver.load_gauge(gauge, "lex")
        assert solver.config.threads == automatic_threads
        solver.setup()
        reference = solver.solve(rhs[0], tol=1e-8, layout="lex")
        # A different team on each rank must not alter the collective sequence
        # or rebuild the hierarchy; then restore the NUMA-derived automatic team.
        solver.set_threads(1 + comm.rank)
        solver.solve(rhs[0], tol=1e-8, layout="lex")
        os.environ.update(auto_environment)
        solver.set_threads(None)
        assert solver.config.threads == automatic_threads
        actual = solver.solve(rhs[0], tol=1e-8, layout="lex")
        assert np.linalg.norm(actual - reference) / np.linalg.norm(reference) < 1e-7
        os.environ["LQCD_RHS_BATCH"] = "2"
        batch, stats = solver.solve_many(rhs, tol=1e-8, layout="lex")
        assert all(r["true_residual"] <= 1e-8 for r in stats)
        # Recheck the single-precision MG solutions with the full double operator.
        for r, x in enumerate(batch):
            image = solver.apply(x, layout="lex")
            num = comm.allreduce(float(np.linalg.norm(image - rhs[r]) ** 2))
            den = comm.allreduce(float(np.linalg.norm(rhs[r]) ** 2))
            residual = np.sqrt(num / den)
            max_residual = max(max_residual, residual)
            assert residual <= 1e-8
        assert np.linalg.norm(batch[0] - actual) / np.linalg.norm(actual) < 1e-7
if comm.rank == 0:
    print(f"PASS fine-site single/batch, NUMA-derived teams {team_counts}, unequal teams and automatic restore, blocking/overlap; max_residual={max_residual:.3e}")
