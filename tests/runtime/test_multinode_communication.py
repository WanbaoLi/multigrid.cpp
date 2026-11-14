"""Preflight actual 16-rank/host placement, metadata collectives and large halos."""
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
    assert comm.size >= 32 and comm.size % 16 == 0
    phase('shared_split')
    local = comm.Split_type(MPI.COMM_TYPE_SHARED)
    assert local.size == 16
    phase('object_allgather')
    rows = comm.allgather(dict(rank=rank, host=socket.gethostname(),
                              cpus=sorted(os.sched_getaffinity(0))))
    assert len({row['host'] for row in rows}) == comm.size // 16
    for host in {row['host'] for row in rows}:
        masks = [set(row['cpus']) for row in rows if row['host'] == host]
        assert len(masks) == 16 and all(len(cpus) == 32 for cpus in masks)
        assert len(set.union(*masks)) == 16 * 32
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
