"""Collective shared-filesystem NumPy propagator IO, compatible with PyQUDA.

Only complete t slabs are supported. Files contain global lexical complex128
[T,Z,Y,X,sink_spin,source_spin,sink_color,source_color]; physics metadata belongs
in the application's manifest. All MPI ranks must call on their main thread.
"""
from pathlib import Path
import os
import numpy as np
from mpi4py import MPI


def _errors(comm, error):
    errors = comm.allgather(error)
    if any(errors):
        raise ValueError(f'propagator IO: {errors}')


def _geometry(path, lattice, grid, coords, comm):
    if not MPI.Is_thread_main():
        raise RuntimeError('propagator IO requires the MPI main thread')
    try:
        path = str(Path(path).expanduser().absolute())
        lattice, grid, coords = tuple(lattice), tuple(grid), tuple(coords)
        if any(len(v) != 4 for v in (lattice, grid, coords)):
            raise ValueError('geometry must have four dimensions')
        if any(isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer))
               for v in (lattice, grid, coords) for n in v):
            raise ValueError('geometry entries must be integers')
        if any(n <= 0 or n % 2 for n in lattice):
            raise ValueError('global lattice extents must be positive and even')
        if grid[:3] != (1, 1, 1) or grid[3] != comm.size:
            raise ValueError('one complete t slab per MPI rank required')
        if any(p <= 0 or n % p for n, p in zip(lattice, grid)):
            raise ValueError('process grid must divide lattice')
        local = tuple(n // p for n, p in zip(lattice, grid))
        if any(n % 2 for n in local):
            raise ValueError('local extents must be even for PyQUDA')
        if any(c < 0 or c >= p for c, p in zip(coords, grid)):
            raise ValueError('coordinates outside process grid')
        record = (path, lattice, grid, coords)
        error = None
    except Exception as exc:
        error = str(exc); record = None
    _errors(comm, error)
    records = comm.allgather(record)
    if any(r[:3] != record[:3] for r in records):
        raise ValueError('path/lattice/grid must agree on every MPI rank')
    if len({r[3] for r in records}) != comm.size:
        raise ValueError('rank coordinates do not cover all t slabs exactly once')
    shape = (*lattice[::-1], 4, 4, 3, 3)
    local_shape = (*local[::-1], 4, 4, 3, 3)
    start = coords[3] * local[3]
    return path, shape, local_shape, slice(start, start + local[3])


def _check_file(path, shape):
    array = np.load(path, mmap_mode='r', allow_pickle=False)
    if not isinstance(array, np.memmap) or array.shape != shape or array.dtype != np.dtype('<c16'):
        raise ValueError('expected global lexical little-endian complex128 propagator')
    if not array.flags.c_contiguous:
        raise ValueError('propagator file must use C order')
    return array


def write_propagator(path, propagator, lattice, grid, coords, comm):
    """Write new global .npy using disjoint mmap slab writes, never overwrite."""
    path, shape, local_shape, slab = _geometry(path, lattice, grid, coords, comm)
    valid = (isinstance(propagator, np.ndarray) and propagator.shape == local_shape
             and propagator.dtype == np.dtype('<c16') and propagator.flags.c_contiguous)
    _errors(comm, None if valid else 'input must be local lexical C-contiguous complex128')
    error = None
    if comm.rank == 0:
        try:
            # O_EXCL reserves the path without a TOCTOU overwrite window.
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            os.close(descriptor)
            array = np.lib.format.open_memmap(path, mode='w+', dtype='<c16', shape=shape)
            array.flush(); del array
        except Exception as exc:
            error = str(exc)
    _errors(comm, error)
    comm.Barrier()  # complete header/size visible before other processes mmap
    try:
        array = _check_file(path, shape)
        del array
        array = np.lib.format.open_memmap(path, mode='r+')
        array[slab] = propagator
        array.flush(); del array
        error = None
    except Exception as exc:
        error = str(exc)
    _errors(comm, error)
    comm.Barrier()  # callers may now read the complete file on this shared FS


def read_propagator(path, lattice, grid, coords, comm):
    """Return an independent C-contiguous copy of this rank's lexical slab."""
    path, shape, _, slab = _geometry(path, lattice, grid, coords, comm)
    try:
        array = _check_file(path, shape)
        result = np.array(array[slab], dtype=np.complex128, order='C', copy=True)
        del array
        error = None
    except Exception as exc:
        error = str(exc); result = None
    _errors(comm, error)
    return result
