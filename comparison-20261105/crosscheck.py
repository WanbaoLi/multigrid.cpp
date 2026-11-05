import argparse,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('node');p.add_argument('cores');p.add_argument('--mode',default='pilot');a=p.parse_args()
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v1/results')
ours=root/f'{a.node}-{a.cores}-ours-{a.mode}';pyqcu=root/f'{a.node}-{a.cores}-pyqcu-{a.mode}'
ra=json.loads((ours/'result.json').read_text());rb=json.loads((pyqcu/'result.json').read_text())
assert ra['complete']and rb['status']=='PASS'
grid=rb['grid'];ranks=int(np.prod(grid));expected=4 if a.cores=='128'else 16;assert ranks==expected
x=np.concatenate([np.load(ours/f'column0-rank{i:05d}.npy')for i in range(ranks)])
y=np.empty_like(x);local=[n//r for n,r in zip([24,24,24,64],grid)]
for rank in range(ranks):
    coords=np.unravel_index(rank,grid,order='C');starts=[c*n for c,n in zip(coords,local)]
    slices=tuple(slice(starts[d],starts[d]+local[d])for d in(3,2,1,0))
    y[slices]=np.load(pyqcu/f'column0-rank{rank:05d}.npy')
error=float(np.linalg.norm((x-y).ravel())/np.linalg.norm(x.ravel()))
result=dict(node=a.node,cores=a.cores,mode=a.mode,relative_solution_error=error,limit=1e-8,passed=np.isfinite(error)and error<=1e-8)
path=root/f'{a.node}-{a.cores}-crosscheck-{a.mode}.json';assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert result['passed'],'The two solutions differ; do not rank before attributing convention differences'
