"""Preflight rank placement, metadata collectives and large halos."""
import argparse
import faulthandler
import json
import os
import socket
import traceback

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.rank
faulthandler.dump_traceback_later(30, repeat=True)

def phase(name):
    if rank == 0:
        print('COMM_GATE', name, flush=True)

try:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ranks-per-node', type=int, choices=(4, 8, 16, 32), default=16)
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    ranks_per_node = args.ranks_per_node
    threads = 512 // ranks_per_node
    assert comm.size >= 2 * ranks_per_node and comm.size % ranks_per_node == 0
    if rank == 0:
        print('COMM_CONFIGURATION', json.dumps(dict(
            library=MPI.Get_library_version(),
            environment={k:v for k,v in os.environ.items() if k.startswith('OMPI_MCA_')}
        )), flush=True)
    phase('shared_split')
    local = comm.Split_type(MPI.COMM_TYPE_SHARED)
    assert local.size == ranks_per_node
    phase('object_allgather')
    rows = comm.allgather(dict(rank=rank, host=socket.gethostname(),
                              cpus=sorted(os.sched_getaffinity(0))))
    assert len({row['host'] for row in rows}) == comm.size // ranks_per_node
    for host in {row['host'] for row in rows}:
        masks = [set(row['cpus']) for row in rows if row['host'] == host]
        assert len(masks) == ranks_per_node and all(len(cpus) == threads for cpus in masks)
        assert len(set.union(*masks)) == ranks_per_node * threads
    phase('object_bcast_reduce')
    assert comm.bcast({'payload': list(range(257))} if rank == 0 else None)['payload'][-1] == 256
    assert comm.allreduce(rank, op=MPI.SUM) == comm.size * (comm.size - 1) // 2
    phase('typed_reduce')
    values = np.array([rank, 1], dtype=np.float64)
    comm.Allreduce(MPI.IN_PLACE, values, op=MPI.SUM)
    assert np.array_equal(values, [comm.size * (comm.size - 1) // 2, comm.size])
    phase('8MiB_ring')
    send = np.full(8 * 1024 * 1024, rank, dtype=np.uint8)
    recv = np.empty_like(send)
    comm.Sendrecv(send, dest=(rank + 1) % comm.size, sendtag=981,
                  recvbuf=recv, source=(rank - 1) % comm.size, recvtag=981)
    assert np.all(recv == (rank - 1) % comm.size)
    if args.benchmark:
        def mean_max_seconds(operation, count):
            for _ in range(5):
                operation()
            comm.Barrier()
            start = MPI.Wtime()
            for _ in range(count):
                operation()
            return comm.allreduce((MPI.Wtime() - start) / count, op=MPI.MAX)

        def ring(size):
            return mean_max_seconds(
                lambda: comm.Sendrecv(
                    send[:size], dest=(rank + 1) % comm.size, sendtag=981,
                    recvbuf=recv[:size], source=(rank - 1) % comm.size, recvtag=981), 40)

        reduction = np.ones(8, dtype=np.float64)
        reduced = np.empty_like(reduction)
        metrics = {'ring_seconds': {size: ring(size) for size in
                                   (16 * 1024, 24**3 * 24 * 4, 2 * 24**3 * 24 * 4)},
                   'sum_64_bytes_seconds': mean_max_seconds(
                       lambda: comm.Allreduce(reduction, reduced, MPI.SUM), 100)}
        if rank == 0:
            print('COMM_TIMING', json.dumps(metrics), flush=True)
    local.Free()
    comm.Barrier()
    if rank == 0:
        print('COMM_GATE_PASSED', json.dumps(dict(
            ranks=comm.size, placement=rows,
            mpi_library=MPI.Get_library_version(),
            mpi_environment={k:v for k,v in os.environ.items() if k.startswith('OMPI_MCA_')}
        )), flush=True)
    faulthandler.cancel_dump_traceback_later()
except Exception:
    traceback.print_exc()
    comm.Abort(1)
