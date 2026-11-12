import json, os, time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
while not (r/'sap-complete.json').exists():
    time.sleep(5)
p=q/'060-independent-sap.task.json'
with p.open('x') as f:
    json.dump(dict(argv=['bash','-c','source '+str(r/'ours_env.sh')+'; "$FAIR_PYTHON" -u '+str(r/'validate_sap.py')],cwd=str(r),timeout=1800),f)
os.link(p,q/'060-independent-sap.ready.json')
