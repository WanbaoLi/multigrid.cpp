"""Distribute 512 physical CPUs across 16 or 32 local MPI ranks."""
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_numa import discover_nodes, rank_environment

local = int(os.environ['OMPI_COMM_WORLD_LOCAL_RANK'])
size = int(os.environ['OMPI_COMM_WORLD_LOCAL_SIZE'])
if size not in (16, 32):
    raise RuntimeError(f'Unsupported number of ranks on this host: {size}')
ranks_per_numa = size // 16
threads = 32 // ranks_per_numa
nodes = discover_nodes()
if len(nodes) == 16 and all(len(c)>=32 for c in nodes.values()):
    node = sorted(nodes)[local // ranks_per_numa]
    start = (local % ranks_per_numa) * threads
elif len(nodes) == 1 and len(next(iter(nodes.values()))) >= threads:
    # Donau may expose a prepartitioned task mask or one NUMA domain.
    node = next(iter(nodes))
    start = (local % ranks_per_numa) * threads if len(nodes[node]) >= 32 else 0
else:
    raise RuntimeError(f'Cannot place {threads} threads in one granted NUMA domain: {nodes}')
cpus = nodes[node][start:start + threads]
os.sched_setaffinity(0,cpus)
os.environ.update(rank_environment(dict(cpus=cpus,node=node)))
if os.environ.get("LS_AFFINITY_LOG") == "1":
    print(f"LS_AFFINITY {socket.gethostname()} rank={local} numa={node} cpus={','.join(map(str, cpus))}",
          flush=True)
os.execvp(sys.argv[1],sys.argv[1:])
