"""Frozen real-fixture scalar check; stdlib + byte-only C++ extraction.

Usage: python verify_fixture_propagator.py RUN REFERENCE EXTRACTOR NEW_OUTPUT
Requires saved gauge slabs, a unit point source, mass=-.277, csw=1.160920226,
and 24^3x64. Non-origin sources require use_fixture_source in the report.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

run, reference, extractor, output = map(Path, sys.argv[1:])
output.mkdir(exist_ok=False)
report = json.loads((run / 'result.json').read_text())
assert report['complete'] and report['backend'] in ('arm', 'x86')
assert report['lattice_xyzt'] == [24, 24, 24, 64]
assert report['grid_xyzt'][:3] == [1, 1, 1]
ranks = report['grid_xyzt'][3]
assert ranks > 0 and 64 % ranks == 0
local_t = 64 // ranks
source = report['source_xyzt']
assert isinstance(source, list) and len(source) == 4
assert all(type(value) is int and 0 <= value < extent
           for value, extent in zip(source, report['lattice_xyzt']))
assert report.get('use_fixture_source') is True or source == [0, 0, 0, 0]
assert report['source_scale'] == 1
assert report['normalization'] == 'mass'
assert report['fermion_t_boundary'] == -1 and report['gauge_t_boundary'] == 1
assert report['mass'] == -.277 and report['csw'] == 1.160920226

def header(stream):
    assert stream.read(6) == b'\x93NUMPY'
    major, minor = stream.read(2)
    assert minor == 0 and major in (1, 2)
    length = struct.unpack('<H' if major == 1 else '<I', stream.read(2 if major == 1 else 4))[0]
    meta = ast.literal_eval(stream.read(length).decode('latin1'))
    assert meta['descr'] == '<c16' and not meta['fortran_order']
    return meta

def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(data)
    return value.hexdigest()

prop = run / 'propagator.npy'
with prop.open('rb') as stream:
    assert header(stream)['shape'] == (64, 24, 24, 24, 4, 4, 3, 3)
check = dict(complete=False, run=str(run), reference=str(reference),
             reference_sha256=sha(reference), run_report_sha256=sha(run/'result.json'),
             propagator_sha256=sha(prop), method='byte-only column extraction + independent scalar C++',
             source_xyzt=source, source_scale=1.0, mass=-.277, csw=1.160920226,
             normalization='mass', columns=[])
gauge = output / 'gauge.bin'
with gauge.open('xb') as dest:
    for rank in range(ranks):
        with (run / f'gauge_rank{rank:05d}.npy').open('rb') as stream:
            assert header(stream)['shape'] == (local_t, 24, 24, 24, 4, 3, 3)
            shutil.copyfileobj(stream, dest, 4 * 1024 * 1024)
assert gauge.stat().st_size == 24**3 * 64 * 36 * 16
check['assembled_gauge_sha256'] = sha(gauge)
subprocess.run([str(extractor), str(prop), str(output), str(24**3 * 64)], check=True)
env = dict(os.environ, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1')
rhs = output / 'rhs.bin'
rhs_bytes = 24**3 * 64 * 12 * 16
x, y, z, t = source
source_site = x + 24 * (y + 24 * (z + 24 * t))
for col in range(12):
    with rhs.open('wb') as stream:
        stream.truncate(rhs_bytes)
        stream.seek((source_site * 12 + col) * 16)
        # The independent scalar executable applies M/(4+mass), whereas the
        # production mass-normalized output solves M*x=unit_delta.
        stream.write(struct.pack('<dd', 1 / (4 + report['mass']), 0.0))
    target = output / f'verified{col}'
    with (output / f'column{col}.log').open('w') as log:
        subprocess.run([str(reference), '--gauge', str(gauge), '--source', str(rhs),
                        '--validate-solution', str(output / f'column{col}.bin'),
                        '--dims', '24', '24', '24', '64', '--mass', str(report['mass']),
                        '--csw', str(report['csw']), '--tol', '1e-8', '--out', str(target)],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    residual = float(Path(str(target) + '.residual').read_text())
    assert math.isfinite(residual) and residual <= 1e-8
    check['columns'].append(dict(source_spin=col//3, source_color=col%3, residual=residual))
    (output / 'verification.json').write_text(json.dumps(check, indent=2)+'\n')
    print(col, residual, flush=True)
check['complete'] = True
(output / 'verification.json').write_text(json.dumps(check, indent=2)+'\n')
# Only remove the temporary binaries created in this fresh directory.
for path in [rhs, gauge, *[output / f'column{c}.bin' for c in range(12)],
             *[output / f'verified{c}' for c in range(12)]]:
    path.unlink()
