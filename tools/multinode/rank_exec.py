"""Bind one of sixteen local MPI ranks to its own NUMA domain (32 CPUs)."""
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_numa import discover_nodes, rank_environment

local = int(os.environ['OMPI_COMM_WORLD_LOCAL_RANK'])
assert int(os.environ['OMPI_COMM_WORLD_LOCAL_SIZE']) == 16
nodes = discover_nodes()
if len(nodes) == 16 and all(len(c)>=32 for c in nodes.values()):
    node = sorted(nodes)[local]
elif len(nodes) == 1 and len(next(iter(nodes.values()))) >= 32:
    # Donau may assign one NUMA domain per requested MPI task instead of
    # exposing the whole host cpuset to every process.
    node = next(iter(nodes))
else:
    raise RuntimeError(f'Cannot place 32 threads in one granted NUMA domain: {nodes}')
cpus = nodes[node][:32]
os.sched_setaffinity(0,cpus)
os.environ.update(rank_environment(dict(cpus=cpus,node=node)))
os.execvp(sys.argv[1],sys.argv[1:])
