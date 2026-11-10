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
while not(R/'projector-complete.json').exists():time.sleep(5)
run('030-tile-build',['bash',str(R/'build_tile.sh')],1500)
for mode in ('tile0','tile16','tile64','old-tile-closing'):
 run(mode,[P,'-u',str(R/'measure_tile.py'),mode],1100)
 print('COMPLETE',mode,flush=True)
(R/'tile-complete.json').write_text(json.dumps(dict(complete=True)))
