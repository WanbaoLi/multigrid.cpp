import json
from pathlib import Path
r=Path('/public2/home/lwb_720/.cache/mg-x86-20261110')
for p in sorted((r/'queue').glob('*.status.json')):
 s=json.loads(p.read_text());print(p.stem,s['status'],s.get('cleanup',{}).get('complete'))
for mode in ('old-control','new0','new1','new2','old-closing','proj0','proj1','old-projector-closing','tile0','tile16','tile64','old-tile-closing','new2-confirm2','old-final-control'):
 p=r/mode/'full12/result.json'
 if p.exists():
  s=json.loads(p.read_text());v=s.get('verification',{});print(mode,[round(x['wall_seconds'],6)for x in s['samples']],v.get('passed'),v.get('max_true_residual'),flush=True)
