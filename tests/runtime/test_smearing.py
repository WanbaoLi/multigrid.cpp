"""CPU-only stout gate: run directly or with mpiexec -n 2/4."""
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from lqcd_cpu.smearing import stout_smear


def oracle(field, steps, rho, ignore):
    """Independent scalar periodic stencil and Taylor matrix exponential."""
    shape = field.shape[:4]
    directions = [d for d in range(4) if d != ignore]
    result = field.copy()
    def moved(x, mu, sign):
        y = list(x)
        axis = 3 - mu
        y[axis] = (y[axis] + sign) % shape[axis]
        return tuple(y)
    for _ in range(steps):
        old = result
        result = old.copy()
        for x in np.ndindex(shape):
            for mu in directions:
                c = np.zeros((3, 3), dtype=np.complex128)
                for nu in directions:
                    if mu == nu:
                        continue
                    minus = moved(x, nu, -1)
                    c += old[x][nu] @ old[moved(x, nu, 1)][mu] @ old[moved(x, mu, 1)][nu].conj().T
                    c += old[minus][nu].conj().T @ old[minus][mu] @ old[moved(minus, mu, 1)][nu]
                omega = rho * c @ old[x][mu].conj().T
                a = (omega - omega.conj().T) / 2
                a -= np.eye(3) * np.trace(a) / 3
                exponential = np.eye(3, dtype=np.complex128)
                term = exponential.copy()
                for k in range(1, 65):
                    term = term @ a / k
                    exponential += term
                result[x][mu] = exponential @ old[x][mu]
    return result


comm = MPI.COMM_WORLD
rank, size = comm.rank, comm.size
rng = np.random.default_rng(913)
# Local t=1 deliberately stresses both halo faces, including size=2 same-peer.
shape = (size, 2, 2, 3, 4, 3, 3)
a = rng.normal(size=shape) + 1j * rng.normal(size=shape)
q, _ = np.linalg.qr(a)
q[..., :, 0] *= np.linalg.det(q).conj()[..., None]
full = np.ascontiguousarray(q)
local = full[rank:rank + 1].copy()
saved = local.copy()
identity = np.broadcast_to(np.eye(3, dtype=np.complex128), local.shape).copy()
assert np.max(np.abs(stout_smear(identity, 2, comm=comm) - identity)) < 1e-14
for steps, rho in [(0, .125), (3, 0.)]:
    output = stout_smear(local, steps, rho, comm=comm)
    assert np.array_equal(output, local) and not np.shares_memory(output, local)
for ignore in (4, 3, 0):
    output = stout_smear(local, 2, .125, ignore, comm)
    expected = oracle(full, 2, .125, ignore)[rank:rank + 1]
    error = comm.allreduce(float(np.max(np.abs(output - expected))), op=MPI.MAX)
    assert error < 2e-13, error
    assert output.flags.c_contiguous and output.dtype == np.complex128
    unitary = output @ output.conj().swapaxes(-1, -2)
    assert np.max(np.abs(unitary - np.eye(3))) < 2e-13
    assert np.max(np.abs(np.linalg.det(output) - 1)) < 2e-13
    if ignore < 4:
        assert np.array_equal(output[..., ignore, :, :], local[..., ignore, :, :])
assert np.array_equal(local, saved)
# Every rank rejects a bad source or mismatched parameters before halo traffic.
try:
    stout_smear(local.astype(np.complex64) if rank == 0 else local, 1, comm=comm)
except ValueError:
    pass
else:
    raise AssertionError("invalid dtype accepted")
if size > 1:
    try:
        stout_smear(local, rank, comm=comm)
    except ValueError:
        pass
    else:
        raise AssertionError("rank-dependent step count accepted")
if rank == 0:
    print(f"stout NumPy oracle/unitarity/input/collective gates passed ({size} ranks)")
