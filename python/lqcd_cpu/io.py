"""Independent single-file LIME/SciDAC/ILDG gauge reader (NumPy + mpi4py).

No projection/reunitarization is performed, including for single precision.
Coordinates and process-grid dimensions are XYZT, independent of MPI rank order.
"""
import math
import operator
import os
import struct
import xml.etree.ElementTree as ET
import zlib

import numpy as np
from mpi4py import MPI


def read_lime_metadata(path):
    """Read record headers/XML only; precision is 32 or 64 (bits per real).

    Returns lattice_xyzt, precision, binary_offset/bytes, and optional checksum
    (two integers), mass/csw. Ambiguous action parameters are omitted.
    Only a single, full-volume gauge field per file is supported.
    """
    path = os.path.expandvars(os.path.expanduser(os.fspath(path)))
    roots, binary = {}, []
    size = os.path.getsize(path)
    with open(path, 'rb') as stream:
        while stream.tell() < size:
            header = stream.read(144)
            if len(header) != 144:
                raise ValueError('truncated LIME header')
            magic, version, flags, length, name = struct.unpack('>IHHQ128s', header)
            if magic != 0x456789AB or version != 1:
                raise ValueError('invalid LIME magic/version')
            name = name.split(b'\0', 1)[0].decode('ascii')
            offset = stream.tell()
            if offset + length > size:
                raise ValueError('truncated LIME record')
            if name in ('ildg-binary-data', 'scidac-binary-data'):
                binary.append((offset, length))
            if name.endswith('-xml') or name in ('ildg-format', 'scidac-checksum'):
                if name in roots:
                    raise ValueError('multiple LIME fields/duplicate XML records unsupported')
                if length > 16 * 1024 * 1024:
                    raise ValueError('LIME XML exceeds 16 MiB limit')
                roots[name] = ET.fromstring(stream.read(length).rstrip(b'\0 \r\n\t'))
            stream.seek(offset + length + (-length) % 8)
    if len(binary) != 1:
        raise ValueError('expected exactly one gauge binary record')

    def fields(root):
        return {e.tag.rsplit('}', 1)[-1]: (e.text or '').strip() for e in root.iter()}

    dims, precisions = [], []
    if 'scidac-private-file-xml' in roots:
        f = fields(roots['scidac-private-file-xml'])
        if int(f.get('spacetime', 4)) != 4 or int(f.get('volfmt', 0)) != 0:
            raise ValueError('only four-dimensional single-file SciDAC supported')
        dims.append(tuple(map(int, f['dims'].split())))
    if 'scidac-private-record-xml' in roots:
        f = fields(roots['scidac-private-record-xml'])
        bits = {'F': 32, 'D': 64}.get(f['precision'])
        if bits is None or int(f.get('colors', 3)) != 3 or int(f.get('datacount', 4)) != 4:
            raise ValueError('expected F/D SU(3) gauge record with four directions')
        if int(f.get('typesize', 18 * bits // 8)) != 18 * bits // 8 or int(f.get('recordtype', 0)) != 0:
            raise ValueError('unsupported SciDAC record shape/type')
        precisions.append(bits)
    if 'ildg-format' in roots:
        f = fields(roots['ildg-format'])
        if f.get('field') != 'su3gauge':
            raise ValueError('expected ILDG su3gauge field')
        dims.append(tuple(int(f['l' + d]) for d in 'xyzt'))
        precisions.append(int(f['precision']))
    if not dims or any(d != dims[0] for d in dims) or len(dims[0]) != 4 or min(dims[0]) < 1:
        raise ValueError('missing/inconsistent lattice dimensions')
    if not precisions or any(p != precisions[0] for p in precisions) or precisions[0] not in (32, 64):
        raise ValueError('missing/inconsistent gauge precision')
    offset, length = binary[0]
    if length != math.prod(dims[0]) * 72 * (precisions[0] // 8):
        raise ValueError('gauge binary size does not match metadata')
    result = dict(lattice_xyzt=dims[0], precision=precisions[0], binary_offset=offset, binary_bytes=length)
    if 'scidac-checksum' in roots:
        f = fields(roots['scidac-checksum'])
        sums = tuple(int(f[k], 16) for k in ('suma', 'sumb'))
        if any(s < 0 or s > 0xffffffff for s in sums):
            raise ValueError('invalid SciDAC checksum')
        result['checksum'] = sums
    for key, tags in [('mass', {'mass'}), ('csw', {'csw', 'clovcoeff', 'clovcoeffr', 'clovcoefft'})]:
        values = set()
        for root in roots.values():
            for elem in root.iter():
                if elem.tag.rsplit('}', 1)[-1].lower() in tags:
                    try:
                        values.add(float(elem.text))
                    except (TypeError, ValueError):
                        pass
        if len(values) == 1:
            result[key] = values.pop()
    return result


def _collective_error(comm, error):
    errors = comm.allgather(error)
    for rank, message in enumerate(errors):
        if message is not None:
            raise ValueError(f'LIME reader rank {rank}: {message}')


def read_lime_gauge(path, grid=(1, 1, 1, 1), coords=(0, 0, 0, 0),
                    comm=MPI.COMM_WORLD, checksum=True):
    """Collectively return owned contiguous complex128 [t,z,y,x,4,3,3].

    Each coordinate must occur exactly once in comm; rank order is arbitrary.
    Memory mapping touches only the local rectangle (contiguous for t slabs).
    checksum=True requires a SciDAC checksum and verifies original on-disk
    big-endian bytes, before conversion. All ranks must call this function.
    """
    error = None
    metadata = None
    try:
        grid = tuple(operator.index(v) for v in grid)
        coords = tuple(operator.index(v) for v in coords)
        if len(grid) != 4 or len(coords) != 4 or min(grid) < 1:
            raise ValueError('grid/coords must have four integer entries and positive grid')
        if math.prod(grid) != comm.size or any(c < 0 or c >= g for c, g in zip(coords, grid)):
            raise ValueError('grid/coords do not match communicator')
        metadata = read_lime_metadata(path)
        dims = metadata['lattice_xyzt']
        if any(n % g for n, g in zip(dims, grid)):
            raise ValueError('lattice must divide evenly over process grid')
        if checksum and 'checksum' not in metadata:
            raise ValueError('SciDAC checksum missing; explicitly use checksum=False to skip')
    except Exception as exc:
        error = str(exc)
    _collective_error(comm, error)
    descriptions = comm.allgather((grid, coords, metadata, bool(checksum)))
    if any((g, m, check) != (grid, metadata, bool(checksum)) for g, c, m, check in descriptions):
        raise ValueError('LIME metadata/grid/checksum setting differs across ranks')
    if len({c for g, c, m, check in descriptions}) != comm.size:
        raise ValueError('duplicate process coordinates')
    error = None
    try:
        shape = tuple(n // g for n, g in zip(dims, grid))
        starts = tuple(c * n for c, n in zip(coords, shape))
        slices = tuple(slice(s, s + n) for s, n in zip(starts[::-1], shape[::-1]))
        filename = os.path.expandvars(os.path.expanduser(os.fspath(path)))
        mapped = np.memmap(filename, mode='r', dtype=f'>c{metadata["precision"] // 4}',
                           offset=metadata['binary_offset'], shape=(*dims[::-1], 4, 3, 3))
        raw = np.ascontiguousarray(mapped[slices])
        sums = [0, 0]
        if checksum:
            rows = raw.reshape(-1, 36).view(np.uint8).reshape(-1, 72 * (metadata['precision'] // 8))
            lx, ly, lz, lt = shape
            sx, sy, sz, st = starts
            nx, ny, nz, nt = dims
            for i, row in enumerate(rows):
                x = i % lx + sx
                y = i // lx % ly + sy
                z = i // (lx * ly) % lz + sz
                t = i // (lx * ly * lz) + st
                site = ((t * nz + z) * ny + y) * nx + x
                crc = zlib.crc32(row)
                for j, modulus in enumerate((29, 31)):
                    shift = site % modulus
                    sums[j] ^= ((crc << shift) | (crc >> (32 - shift))) & 0xffffffff
        gauge = np.array(raw, dtype=np.complex128, order='C', copy=True)
        del raw, mapped
    except Exception as exc:
        error = str(exc)
    _collective_error(comm, error)
    if checksum:
        observed = tuple(comm.allreduce(s, op=MPI.BXOR) for s in sums)
        if observed != metadata['checksum']:
            raise ValueError(f'SciDAC checksum mismatch: computed {observed}, expected {metadata["checksum"]}')
    return gauge
