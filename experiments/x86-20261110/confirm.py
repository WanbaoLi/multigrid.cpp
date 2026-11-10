import json,os,time
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/mg-x86-20261110');q=R/'queue';P='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
def run(name,argv,timeout):
 with(q/(name+'.ready.json')).open('x')as f:json.dump(dict(argv=argv,cwd=str(R),timeout=timeout),f)
 while True:
  path=q/(name+'.status.json')
  if path.exists():
   row=json.loads(path.read_text())
   if row['status']!='running':
    assert row['status']=='passed' and row['cleanup']['complete'] and not row['cleanup']['surviving_pids'],row
    return
  time.sleep(5)
while not(R/'tile-complete.json').exists():time.sleep(5)
for mode in ('new2-confirm2','old-final-control'):
 run(mode,[P,'-u',str(R/'measure.py'),mode],1100)
 print('COMPLETE',mode,flush=True)
(R/'confirmation-complete.json').write_text(json.dumps(dict(complete=True)))
