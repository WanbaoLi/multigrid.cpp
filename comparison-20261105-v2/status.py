import json,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
rows=[]
for q in('login','compute'):
    for p in sorted((root/(q+'-queue')).glob('*.status.json')):
        r=json.loads(p.read_text());rows.append(dict(queue=q,name=p.name,status=r['status'],elapsed=round(r.get('ended',time.time())-r['started']),cleanup=r.get('cleanup',{}).get('complete')))
for p in sorted((root/'results').glob('*/result.json')):
    r=json.loads(p.read_text());samples=r.get('samples',[])
    rows.append(dict(result=p.parent.name,status=r.get('status',r.get('complete')),samples=[{k:v for k,v in x.items()if k not in('stats','columns')}for x in samples],columns_completed=len(r.get('columns',[]))))
print(json.dumps(rows,indent=2),flush=True)
