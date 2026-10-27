"""Independent NumPy implementation of ordinary isotropic stout smearing.

Convention checked against PyQUDA/pyquda/dirac/gauge.py::stoutSmear and
QUDA include/kernels/gauge_stout.cuh::STOUT and gauge_utils.cuh
(upstream QUDA Developers, MIT license; see quda/LICENSE).
No upstream implementation is copied. The mathematical prescription is
Morningstar & Peardon, Phys. Rev. D 69, 054501 (2004), hep-lat/0311018.
"""

import operator

import numpy as np
from mpi4py import MPI


def _dagger(a):
    return a.conj().swapaxes(-1, -2)


def stout_smear(gauge, steps=0, rho=0.125, dir_ignore=4, comm=MPI.COMM_WORLD):
    """Return a new contiguous complex128 gauge, never modifying ``gauge``.

    Input layout is rank-local lexicographic [t,z,y,x,mu,3,3], mu=x,y,z,t.
    Ranks must form consecutive equal t slabs; spatial dimensions are local.
    Calls are collective on ``comm`` and must run on the MPI main thread.
    Gauge links are periodic and *untwisted*, including across temporal seams.

    As in PyQUDA/QUDA, dir_ignore=4 updates all four directions using all
    transverse staples. dir_ignore=3 updates spatial links using spatial
    staples only, leaving temporal links unchanged. Values 0..2 analogously
    exclude the indicated direction both from updates and from staples.
    rho multiplies the staple SUM; it is not divided by the staple count.
    Each step uses only links from the previous step. No reunitarization is
    applied: the traceless Hermitian generator is exponentiated using eigh.
    """
    if not MPI.Is_thread_main():
        raise RuntimeError("stout_smear must run on the MPI main thread")
    error = None
    try:
        steps, dir_ignore = operator.index(steps), operator.index(dir_ignore)
        rho = float(rho)
        if steps < 0 or not 0 <= dir_ignore <= 4 or not np.isfinite(rho):
            raise ValueError("steps must be nonnegative, rho finite, dir_ignore in 0..4")
        if not isinstance(gauge, np.ndarray) or gauge.dtype != np.complex128:
            raise ValueError("gauge must be a complex128 NumPy array")
        if gauge.ndim != 7 or gauge.shape[-3:] != (4, 3, 3) or min(gauge.shape[:4]) < 1:
            raise ValueError("gauge must have shape [t,z,y,x,4,3,3] with positive extents")
        if not np.isfinite(gauge).all():
            raise ValueError("gauge contains nonfinite links")
    except (TypeError, ValueError, OverflowError) as exc:
        error = str(exc)
    errors = comm.allgather(error)
    if any(e is not None for e in errors):
        raise ValueError("invalid stout input: " + next(e for e in errors if e is not None))
    descriptions = comm.allgather((gauge.shape, steps, rho, dir_ignore))
    if any(d != descriptions[0] for d in descriptions):
        raise ValueError("stout shapes and parameters must agree on all ranks (equal t slabs)")
    old = np.array(gauge, dtype=np.complex128, order="C", copy=True)
    if steps == 0 or rho == 0:
        return old
    directions = [mu for mu in range(4) if mu != dir_ignore]
    nt = old.shape[0]
    rank, size = comm.Get_rank(), comm.Get_size()
    eye = np.eye(3, dtype=np.complex128)
    for _ in range(steps):
        # One temporal face suffices even for the backward bent staple:
        # its displacement is -nu+mu, at most one temporal lattice unit.
        extended = np.empty((nt + 2,) + old.shape[1:], dtype=np.complex128)
        extended[1:-1] = old
        if size == 1:
            extended[0], extended[-1] = old[-1], old[0]
        else:
            comm.Sendrecv(old[-1], dest=(rank + 1) % size, sendtag=710,
                          recvbuf=extended[0], source=(rank - 1) % size, recvtag=710)
            comm.Sendrecv(old[0], dest=(rank - 1) % size, sendtag=711,
                          recvbuf=extended[-1], source=(rank + 1) % size, recvtag=711)
        new = old.copy()
        # Work a time plane at a time to bound eigensolver/intermediate memory.
        for t in range(nt):
            def link(mu, shifts=()):
                dt = sum(sign for direction, sign in shifts if direction == 3)
                value = extended[t + 1 + dt, ..., mu, :, :]
                for direction, sign in shifts:
                    if direction != 3:
                        value = np.roll(value, -sign, axis=2 - direction)
                return value

            for mu in directions:
                u = link(mu)
                staple = np.zeros_like(u)
                for nu in directions:
                    if nu == mu:
                        continue
                    staple += link(nu) @ link(mu, ((nu, 1),)) @ _dagger(link(nu, ((mu, 1),)))
                    staple += (_dagger(link(nu, ((nu, -1),))) @ link(mu, ((nu, -1),))
                               @ link(nu, ((nu, -1), (mu, 1))))
                omega = rho * staple @ _dagger(u)
                q = (omega - _dagger(omega)) / (2j)
                q -= (np.trace(q, axis1=-2, axis2=-1) / 3)[..., None, None] * eye
                eigenvalues, vectors = np.linalg.eigh(q)
                exponential = (vectors * np.exp(1j * eigenvalues)[..., None, :]) @ _dagger(vectors)
                new[t, ..., mu, :, :] = exponential @ u
        old = new
    return old
