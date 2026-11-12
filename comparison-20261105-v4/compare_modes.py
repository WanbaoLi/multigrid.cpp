import json
from pathlib import Path
import numpy as np
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');rows=[]
base=r/'results/baseline-v2'
for mode in('baseline-v2','double-outer-v2','mixed-single-v2'):
    p=r/'results'/mode/'result.json'
    if not p.exists():continue
    report=json.loads(p.read_text())
    if not report['complete']:continue
    sample=report['samples'][0];stats=sample['stats'];assert len(stats)==12 and all(s['true_residual']<=1e-8 for s in stats)
    row=dict(mode=mode,native_api_seconds=sample['native_api_seconds'],python_api_seconds=sample['api_seconds'],
        internal_seconds=sample['internal_seconds'],iterations=[s['iterations']for s in stats],residual=max(s['true_residual']for s in stats),
        library_sha256=report['library_sha256'])
    if mode!='baseline-v2':
        sums=np.zeros(12);norms=np.zeros(12)
        for rank in range(16):
            a=np.load(base/f'propagator-rank{rank:05d}.npy',mmap_mode='r');b=np.load(p.parent/f'propagator-rank{rank:05d}.npy',mmap_mode='r')
            for spin in range(4):
                for color in range(3):
                    x=np.asarray(a[:,:,:,:,:,spin,:,color]);y=np.asarray(b[:,:,:,:,:,spin,:,color]);j=spin*3+color
                    sums[j]+=np.sum(np.abs(x-y)**2);norms[j]+=np.sum(np.abs(x)**2)
        errors=np.sqrt(sums/norms);assert np.max(errors)<=1e-6
        row['solution_errors']=errors.tolist()
    rows.append(row)
out=dict(complete=len(rows)==3,rows=rows)
if out['complete']:
    target=r/'precision-summary.json';assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2),flush=True)
