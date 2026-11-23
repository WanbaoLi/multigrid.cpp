"""Compare face packing and exchange for two 32-rank C24 decompositions."""

import json
import math
import os
import socket

import numpy as np
from mpi4py import MPI


LATTICE = (24, 24, 24, 64)
BLOCK = (6, 6, 6, 2)
LAYOUTS = ((1, 1, 1, 32), (2, 1, 1, 16))
SAMPLES = 3
REPETITIONS = 60


def compare_faces(cart, extents, reals_per_site):
    """Exchange each required face, with separate tags for each direction."""
    field = np.empty((*extents[::-1], reals_per_site), dtype=np.float32)
    faces = []
    for direction, count in enumerate(cart.Get_topo()[0][::-1]):
        if count == 1:
            continue
        before, after = cart.Shift(3 - direction, 1)
        array_axis = 3 - direction
        for side, peer in enumerate((before, after)):
            selection = [slice(None)] * field.ndim
            selection[array_axis] = 0 if side == 0 else -1
            view = field[tuple(selection)]
            faces.append((peer, 2 * direction + side, view,
                          np.empty(view.shape, view.dtype), np.empty(view.shape, view.dtype)))

    def exchange(check=False):
        requests = [cart.Irecv(receive, source=peer, tag=tag ^ 1)
                    for peer, tag, _, _, receive in faces]
        for peer, tag, view, send, _ in faces:
            np.copyto(send, view)
            if check:
                send.fill(8 * cart.rank + tag)
            requests.append(cart.Isend(send, dest=peer, tag=tag))
        MPI.Request.Waitall(requests)

    field.fill(cart.rank)
    exchange(check=True)
    correct = all(np.all(receive == 8 * peer + (tag ^ 1))
                  for peer, tag, _, _, receive in faces)
    if not cart.allreduce(correct, op=MPI.LAND):
        raise RuntimeError("Halo data verification failed")
    seconds = []
    for _ in range(SAMPLES):
        cart.Barrier()
        start = MPI.Wtime()
        for _ in range(REPETITIONS):
            exchange()
        seconds.append(cart.allreduce((MPI.Wtime() - start) / REPETITIONS, op=MPI.MAX))
    return {"bytes_sent_per_rank": sum(send.nbytes for _, _, _, send, _ in faces),
            "pack_and_exchange_seconds": seconds}


def main():
    comm = MPI.COMM_WORLD
    placement = comm.allgather((socket.gethostname(), sorted(os.sched_getaffinity(0))))
    if (comm.size != 32 or len({host for host, _ in placement}) != 1
            or any(len(cpus) != 16 for _, cpus in placement)
            or len({cpu for _, cpus in placement for cpu in cpus}) != 512):
        raise RuntimeError("Expected 32 ranks on one host with 512 disjoint CPUs")
    for layout in LAYOUTS:
        local = tuple(n // p for n, p in zip(LATTICE, layout))
        coarse = tuple(n // b for n, b in zip(local, BLOCK))
        cart = comm.Create_cart(layout[::-1], periods=(True,) * 4, reorder=False)
        # Cartesian dimensions are reversed so the rank order has x fastest.
        try:
            rows = {}
            for name, extents, components in (("fine", local, 24), ("coarse", coarse, 96)):
                rows[name] = {rhs: compare_faces(cart, extents, components * rhs)
                              for rhs in (1, 2)}
            interior = math.prod(n if p == 1 else max(n - 2, 0)
                                 for n, p in zip(local, layout))
            if comm.rank == 0:
                print("HALO_LAYOUT " + json.dumps(dict(
                    host=placement[0][0], mpi_xyzt=layout, local_xyzt=local,
                    coarse_local_xyzt=coarse, fine_interior_fraction=interior / math.prod(local),
                    repetitions_per_sample=REPETITIONS, verified=True, faces=rows)), flush=True)
        finally:
            cart.Free()


if __name__ == "__main__":
    main()
