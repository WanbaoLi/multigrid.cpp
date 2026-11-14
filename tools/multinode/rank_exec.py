"""Bind one of sixteen local MPI ranks to its own NUMA domain (32 CPUs)."""
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_numa import discover_nodes, rank_environment

local = int(os.environ['OMPI_COMM_WORLD_LOCAL_RANK'])
assert int(os.environ['OMPI_COMM_WORLD_LOCAL_SIZE']) == 16
nodes = discover_nodes()
assert len(nodes) == 16 and all(len(c)>=32 for c in nodes.values()), nodes
node = sorted(nodes)[local]
cpus = nodes[node][:32]
os.sched_setaffinity(0,cpus)
os.environ.update(rank_environment(dict(cpus=cpus,node=node)))
os.execvp(sys.argv[1],sys.argv[1:])
