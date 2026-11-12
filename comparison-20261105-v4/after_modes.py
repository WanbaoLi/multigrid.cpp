import json,os,time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
while not(r/'validated-complete.json').exists():time.sleep(5)
assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))
p=q/'original-control.task.json'
with p.open('x')as f:json.dump(dict(argv=['bash',str(r/'run_original.sh')],cwd=str(r),timeout=1800),f)
os.link(p,q/'original-control.ready.json')
print('QUEUED_ORIGINAL_CONTROL',flush=True)
