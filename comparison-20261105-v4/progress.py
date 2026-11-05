import json,time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4')
for p in sorted((r/'compute-queue').glob('*.status.json')):
    x=json.loads(p.read_text());print(p.name,x['status'],round(x.get('ended',time.time())-x['started']),x.get('cleanup',{}).get('complete'))
for p in sorted((r/'results').glob('*/result.json')):
    x=json.loads(p.read_text());print(p.parent.name,x.get('complete'),[(s['native_api_seconds'],[q['iterations']for q in s['stats']],max(q['true_residual']for q in s['stats']))for s in x.get('samples',[])])
