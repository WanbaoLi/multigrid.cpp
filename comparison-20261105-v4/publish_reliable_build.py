import json,os
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))
p=q/'020-build-reliable.task.json'
with p.open('x')as f:json.dump(dict(argv=['bash',str(r/'build_reliable.sh')],cwd=str(r),timeout=1500),f)
os.link(p,q/'020-build-reliable.ready.json')
print('QUEUED_RELIABLE_BUILD')
