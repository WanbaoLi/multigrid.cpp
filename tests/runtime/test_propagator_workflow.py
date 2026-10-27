"""LIME -> CPU stout -> 12 RHS -> PyQUDA-loadable output, independent residual."""
from pathlib import Path
import json
import shutil
import struct
import sys
import tempfile
import zlib

import numpy as np
from mpi4py import MPI
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from lqcd_cpu import Solver, propagator_to_columns
from lqcd_cpu.propagator import solve_lime_propagator
from lqcd_cpu.propagator_io import read_propagator
from pyquda_comm import initGrid
from pyquda.field import LatticeInfo, LatticePropagator

comm = MPI.COMM_WORLD
lat = (8, 8, 8, 8)
grid = (1, 1, 1, comm.size)
initGrid(grid_size=list(grid))
li = LatticeInfo(list(lat), -1, 1.)
coords = tuple(li.grid_coord)
point = (3, 1, 2, 5)
base = Path(comm.bcast(tempfile.mkdtemp(prefix='lqcd-propagator-') if comm.rank == 0 else None))
try:
    path = base / 'unit.lime'
    if comm.rank == 0:
        gauge = np.broadcast_to(np.eye(3), (*lat[::-1], 4, 3, 3)).astype('>c16').copy()
        blob = gauge.tobytes()
        checks = [0, 0]
        for s in range(np.prod(lat)):
            crc = zlib.crc32(blob[s * 576:(s + 1) * 576])
            for j, modulus in enumerate((29, 31)):
                n = s % modulus
                checks[j] ^= ((crc << n) | (crc >> ((32 - n) % 32))) & 0xffffffff
        with path.open('wb') as f:
            def record(name, data):
                data = data.encode() if isinstance(data, str) else data
                f.write(struct.pack('>IHHQ128s', 0x456789AB, 1, 0xc000, len(data), name.encode()))
                f.write(data); f.write(b'\0' * (-len(data) % 8))
            record('ildg-format', '<ildgFormat><field>su3gauge</field><precision>64</precision>'
                   '<lx>8</lx><ly>8</ly><lz>8</lz><lt>8</lt></ildgFormat>')
            record('scidac-record-xml', '<action><Mass>0.05</Mass><clovCoeff>1.160920226</clovCoeff></action>')
            record('ildg-binary-data', blob)
            record('scidac-checksum', f'<c><suma>{checks[0]:08x}</suma><sumb>{checks[1]:08x}</sumb></c>')
    comm.Barrier()
    output = base / 'output'
    tuning = {'LQCD_MG_SAP_STEPS': 6, 'LQCD_MG_COARSE_TOL': .2,
              'LQCD_CORRECTION_BASE_TOL': .003, 'LQCD_COARSE_CGS2': 1}
    import os
    before = {key: os.environ.get(key) for key in tuning}
    report = solve_lime_propagator(path, output, block=(2, 2, 2, 2), point=point,
                                   stout_steps=2, repeats=2, threads=2, comm=comm,
                                   solve_tuning=tuning)
    assert before == {key: os.environ.get(key) for key in tuning}
    assert report['input']['solve_tuning'] == tuning
    assert report['mass'] == .05 and report['csw'] == 1.160920226
    assert report['mass_source'] == report['csw_source'] == 'lime'
    assert report['source_scale'] == 1 and report['normalization'] == 'mass'
    assert report['max_true_residual'] <= 1e-8
    assert len(report['samples']) == 2 and all(len(r['stats']) == 12 for r in report['samples'])
    prop = read_propagator(output / 'propagator.npy', lat, grid, coords, comm)
    loaded = LatticePropagator.load(str(output / 'propagator.npy'))
    np.testing.assert_array_equal(loaded.data, li.evenodd(prop, False))
    full = np.concatenate(comm.allgather(prop), axis=0)
    i = 1j
    gamma = np.array([
        [[0,0,0,i],[0,0,i,0],[0,-i,0,0],[-i,0,0,0]],
        [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
        [[0,0,i,0],[0,0,0,-i],[-i,0,0,0],[0,i,0,0]],
        [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]]])
    for spin in range(4):
        for color in range(3):
            x = full[..., :, spin, :, color]
            ax = (4 + .05) * x
            for mu in range(4):
                plus = np.roll(x, -1, axis=3-mu)
                minus = np.roll(x, 1, axis=3-mu)
                if mu == 3:
                    plus[-1] *= -1; minus[0] *= -1
                ax -= .5 * (np.einsum('ij,...jc->...ic', np.eye(4)-gamma[mu], plus)
                             + np.einsum('ij,...jc->...ic', np.eye(4)+gamma[mu], minus))
            rhs = np.zeros_like(x)
            rhs[point[3], point[2], point[1], point[0], spin, color] = 1.
            assert np.linalg.norm(ax-rhs) < 1e-8
    # Exercise the in-memory EO output path and normalization as well as CLI lex.
    unit_local = np.broadcast_to(np.eye(3), (*li.size[::-1],4,3,3)).astype(np.complex128).copy()
    with Solver(lat, grid, mass=.05, csw=0., block=(2,2,2,2), threads=2,
                normalization='kappa') as solver:
        solver.load_gauge(unit_local, 'lex'); solver.setup()
        eo, stats = solver.solve_propagator(point, source_scale=2., layout='pyquda')
        expected = loaded.data * (2 * (4 + .05))
        assert np.linalg.norm(eo-expected) / np.linalg.norm(expected) < 2e-7
        assert all(s['true_residual'] <= 1e-8 for s in stats)
    try:
        solve_lime_propagator(path, output, block=(2,2,2,2), point=point, threads=2)
    except RuntimeError as exc:
        assert 'exists' in str(exc)
    else:
        raise AssertionError('must not overwrite existing output')
    if comm.rank == 0:
        assert json.loads((output/'result.json').read_text())['complete']
        print('PASS complete CPU LIME/stout/12-column propagator, unit source, '
              'nonorigin rank/parity, mass/kappa, PyQUDA load, independent residual')
finally:
    comm.Barrier()
    if comm.rank == 0:shutil.rmtree(base)
