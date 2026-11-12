import json,os
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))
name='010-build-outer-option';p=q/(name+'.task.json')
with p.open('x')as f:json.dump(dict(argv=['bash',str(r/'build_outer.sh')],cwd=str(r),timeout=3000),f)
os.link(p,q/(name+'.ready.json'));print('QUEUED_BUILD')
