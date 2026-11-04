"""Small state-only progress; no payload, environment or numerical code read."""
import argparse
import json
from pathlib import Path
import time

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);args=p.parse_args()
assert not args.state.is_symlink()and args.state.stat().st_size<2*1024**2
state=json.loads(args.state.read_text());groups={}
for key,group in state.get('groups',{}).items():
    trials=[]
    for name,row in group.get('trials',{}).items():
        last=(row.get('runs')or[{}])[-1]
        trials.append(dict(id=name,status=row.get('status'),started=last.get('started'),ended=last.get('ended'),
                           returncode=last.get('returncode')))
    groups[key]=dict(status=group.get('status'),complete=group.get('complete'),
        decision=group.get('decision'),assessments=group.get('assessments'),trials=trials)
print(json.dumps(dict(complete=state.get('complete'),status=state.get('status'),
    expected_best=state.get('expected_best'),groups=groups,observed_epoch=time.time()),indent=2))
