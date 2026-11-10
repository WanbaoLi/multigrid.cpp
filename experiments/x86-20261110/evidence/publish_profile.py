import json
from pathlib import Path
q=Path('/public2/home/lwb_720/.cache/mg-x86-20261110/queue')
with (q/'001-profile.ready.json').open('x') as f:
 json.dump(dict(argv=['/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python','-u',str(q.parent/'diagnose_v2.py')],cwd=str(q.parent),timeout=750),f)
print('queued profile v2')
