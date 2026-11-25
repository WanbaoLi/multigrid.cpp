"""Distribute 512 physical CPUs across the local MPI ranks."""
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_numa import discover_nodes, rank_environment

local = int(os.environ['OMPI_COMM_WORLD_LOCAL_RANK'])
size = int(os.environ['OMPI_COMM_WORLD_LOCAL_SIZE'])
if size not in (4, 8, 16, 32):
    raise RuntimeError(f'Unsupported number of ranks on this host: {size}')
threads = 512 // size
ranks_per_numa = max(1, size // 16)
domains_per_rank = max(1, 16 // size)
nodes = discover_nodes()
if len(nodes) == 16 and all(len(c)>=32 for c in nodes.values()):
    first = local // ranks_per_numa * domains_per_rank
    domains = sorted(nodes)[first:first + domains_per_rank]
    width = threads // domains_per_rank
    start = (local % ranks_per_numa) * width
    cpus = [cpu for node in domains for cpu in nodes[node][start:start + width]]
elif size < 16 and len(nodes) == domains_per_rank and all(len(c) >= 32 for c in nodes.values()):
    domains = sorted(nodes)
    cpus = [cpu for node in domains for cpu in nodes[node][:32]]
elif size >= 16 and len(nodes) == 1 and len(next(iter(nodes.values()))) >= threads:
    # Donau may expose a prepartitioned task mask or one NUMA domain.
    node = next(iter(nodes))
    domains = [node]
    start = (local % ranks_per_numa) * threads if len(nodes[node]) >= 32 else 0
    cpus = nodes[node][start:start + threads]
else:
    raise RuntimeError(f'Cannot place {threads} threads in {domains_per_rank} granted NUMA domains: {nodes}')
os.sched_setaffinity(0,cpus)
env = rank_environment(dict(cpus=cpus, node=domains[0]))
if len(domains) > 1:
    del env['LQCD_NUMA_NODE']
    os.environ.pop('LQCD_NUMA_NODE', None)
env['LQCD_NUMA_NODES'] = ','.join(map(str, domains))
os.environ.update(env)
if os.environ.get("LS_AFFINITY_LOG") == "1":
    print(f"LS_AFFINITY {socket.gethostname()} rank={local} numa={env['LQCD_NUMA_NODES']} cpus={','.join(map(str, cpus))}",
          flush=True)
os.execvp(sys.argv[1],sys.argv[1:])
