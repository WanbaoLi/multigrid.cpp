"""Outside-clock all-column comparison and independent scalar residual check."""
import hashlib, json, math, os, struct, subprocess
from pathlib import Path
import numpy as np

root = Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4')
out = root / 'reliable-validation'
out.mkdir(exist_ok=False)
reference = Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid')
assert hashlib.sha256(reference.read_bytes()).hexdigest() == '1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c'
summary = dict(complete=False, comparisons=[], independent=[])
for mode in ('reliable-off', 'reliable-on'):
    report = json.loads((root/'results'/mode/'result.json').read_text())
    assert report['complete'] and len(report['samples'][0]['stats']) == 12
    assert all(s['true_residual'] <= 1e-8 for s in report['samples'][0]['stats'])
    sums, norms = np.zeros(12), np.zeros(12)
    for rank in range(16):
        base = np.load(root/'results/original-control'/f'propagator-rank{rank:05d}.npy', mmap_mode='r')
        candidate = np.load(root/'results'/mode/f'propagator-rank{rank:05d}.npy', mmap_mode='r')
        for spin in range(4):
            for color in range(3):
                x, y = base[..., :, spin, :, color], candidate[..., :, spin, :, color]
                col = spin*3+color
                sums[col] += np.sum(np.abs(x-y)**2)
                norms[col] += np.sum(np.abs(x)**2)
    errors = np.sqrt(sums/norms)
    assert np.max(errors) <= 1e-6
    summary['comparisons'].append(dict(mode=mode, relative_solution_errors=errors.tolist(),
        native_api_seconds=report['samples'][0]['native_api_seconds']))

gauge = out/'gauge.bin'
# Scalar reference consumes site-major untwisted links; it applies its own APBC.
g = np.load(root/'input/gauge-untwisted.npy', mmap_mode='r')
assert g.shape == (64,24,24,24,4,3,3) and g.dtype == np.complex128
g.tofile(gauge)
summary['gauge_sha256'] = hashlib.sha256(gauge.read_bytes()).hexdigest()
rhs, column = out/'rhs.bin', out/'column.bin'
env = dict(os.environ, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1')
for col in range(12):
    with column.open('wb') as stream:
        for rank in range(16):
            prop = np.load(root/'results/reliable-on'/f'propagator-rank{rank:05d}.npy', mmap_mode='r')
            np.ascontiguousarray(prop[..., :, col//3, :, col%3]).tofile(stream)
    with rhs.open('wb') as stream:
        stream.truncate(24**3*64*12*16)
        stream.seek(col*16)
        stream.write(struct.pack('<dd', 1/(4-.277), 0))
    target = out/f'checked-{col:02d}'
    with (out/f'column-{col:02d}.log').open('w') as log:
        subprocess.run([str(reference),'--gauge',str(gauge),'--source',str(rhs),
            '--validate-solution',str(column),'--dims','24','24','24','64',
            '--mass','-.277','--csw','1.160920226','--tol','1e-8','--out',str(target)],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    residual = float(Path(str(target)+'.residual').read_text())
    assert math.isfinite(residual) and residual <= 1e-8
    summary['independent'].append(dict(column=col, residual=residual))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SCALAR_COLUMN',col,residual,flush=True)
summary['complete'] = True
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for path in (gauge,rhs,column):
    path.unlink()
