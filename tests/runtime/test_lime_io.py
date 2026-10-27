"""Run directly, optionally under mpirun -n 2/4; no native library needed."""
import argparse
from pathlib import Path
import shutil
import struct
import tempfile
import zlib

import numpy as np
from mpi4py import MPI
from lqcd_cpu.io import read_lime_gauge, read_lime_metadata


def write_fixture(path, bits, scidac, nt):
    shape = (nt, 2, 3, 4, 4, 3, 3)
    q = np.arange(np.prod(shape)).reshape(shape)
    field = ((q % 97 - 45) / 31 + 1j * (q % 53 - 23) / 17).astype(f'>c{bits // 4}')
    blob = field.tobytes()
    nsite = nt * 2 * 3 * 4
    width = len(blob) // nsite
    a = b = 0
    for site in range(nsite):
        crc = zlib.crc32(blob[site * width:(site + 1) * width])
        # Independent scalar rotation, deliberately separate from reader.
        def rotate(v, k):
            return v if k == 0 else ((v << k) & 0xffffffff) + (v >> (32 - k))
        a ^= rotate(crc, site % 29)
        b ^= rotate(crc, site % 31)
    with open(path, 'wb') as f:
        def record(kind, data):
            data = data.encode() if isinstance(data, str) else data
            f.write(struct.pack('>IHHQ128s', 0x456789AB, 1, 0xc000, len(data), kind.encode()))
            f.write(data)
            f.write(b'\0' * (-len(data) % 8))
        if scidac:
            record('scidac-private-file-xml', f'<q:file xmlns:q="urn:test"><q:spacetime>4</q:spacetime><q:dims>4 3 2 {nt}</q:dims><q:volfmt>0</q:volfmt></q:file>\0')
            record('scidac-private-record-xml', f'<record><precision>{"F" if bits == 32 else "D"}</precision><colors>3</colors><typesize>{18 * bits // 8}</typesize><datacount>4</datacount></record>')
        else:
            record('ildg-format', f'<ildgFormat xmlns="urn:ildg"><field>su3gauge</field><precision>{bits}</precision><lx>4</lx><ly>3</ly><lz>2</lz><lt>{nt}</lt></ildgFormat>')
        record('scidac-record-xml', '<action><Mass>-0.277</Mass><clovCoeff>1.2</clovCoeff></action>')
        record('scidac-binary-data' if scidac else 'ildg-binary-data', blob)
        record('scidac-checksum', f'<checksum xmlns="urn:test"><suma>{a:08x}</suma><sumb>{b:08x}</sumb></checksum>')
    return field.astype(np.complex128)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', type=Path)
    args = parser.parse_args()
    comm = MPI.COMM_WORLD
    directory = comm.bcast(tempfile.mkdtemp(prefix='lqcd-lime-') if comm.rank == 0 else None)
    directory = Path(directory)
    # Reverse ranks to detect accidental rank-based/global-site checksum indices.
    coords = (0, 0, 0, comm.size - 1 - comm.rank)
    grid = (1, 1, 1, comm.size)
    try:
        for bits in (32, 64):
            for scidac in (False, True):
                path = directory / f'{bits}-{scidac}.lime'
                expected = write_fixture(path, bits, scidac, 2 * comm.size) if comm.rank == 0 else None
                expected = comm.bcast(expected)
                metadata = read_lime_metadata(path)
                assert metadata['precision'] == bits
                assert metadata['mass'] == -0.277 and metadata['csw'] == 1.2
                actual = read_lime_gauge(path, grid, coords, comm)
                t = 2 * coords[3]
                assert actual.flags.c_contiguous and actual.dtype == np.complex128
                np.testing.assert_array_equal(actual, expected[t:t + 2])
                if 4 % comm.size == 0:
                    xc = comm.size - 1 - comm.rank
                    spatial = read_lime_gauge(path, (comm.size, 1, 1, 1), (xc, 0, 0, 0), comm)
                    width = 4 // comm.size
                    np.testing.assert_array_equal(spatial, expected[:, :, :, xc * width:(xc + 1) * width])

        def fails(call, text):
            try:
                call()
            except ValueError as exc:
                assert text in str(exc), str(exc)
            else:
                raise AssertionError('expected collective ValueError')

        fails(lambda: read_lime_gauge(directory / 'missing' if comm.rank == 0 else path,
                                     grid, coords, comm), 'rank 0')
        fails(lambda: read_lime_gauge(path, grid, (0, 0, 0, comm.size) if comm.rank == 0 else coords,
                                     comm), 'grid/coords')
        if comm.size > 1:
            fails(lambda: read_lime_gauge(path, grid, (0, 0, 0, 0), comm), 'duplicate')
            fails(lambda: read_lime_gauge(path, grid, coords, comm, checksum=comm.rank != 0), 'differs')
        if comm.rank == 0:
            with path.open('r+b') as f:
                f.seek(metadata['binary_offset'] + 3)
                value = f.read(1)
                f.seek(-1, 1)
                f.write(bytes([value[0] ^ 1]))
        comm.Barrier()
        fails(lambda: read_lime_gauge(path, grid, coords, comm), 'checksum mismatch')
        read_lime_gauge(path, grid, coords, comm, checksum=False)
        if args.real:
            metadata = read_lime_metadata(args.real)
            assert metadata['lattice_xyzt'] == (24, 24, 24, 64)
            assert metadata['checksum'] == (0x94615d60, 0x68418899)
            gauge = read_lime_gauge(args.real, grid, coords, comm)
            assert gauge.shape == (64 // comm.size, 24, 24, 24, 4, 3, 3)
            assert np.isfinite(gauge).all()
        if comm.rank == 0:
            print(f'LIME reader PASS ({comm.size} ranks, F/D, SciDAC/ILDG, raw-byte checksum, collective failures)')
    finally:
        comm.Barrier()
        if comm.rank == 0:
            shutil.rmtree(directory)


if __name__ == '__main__':
    main()
