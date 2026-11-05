import json,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
for node in('login','compute'):
    for p in sorted((root/(node+'-queue')).glob('*.status.json')):
        r=json.loads(p.read_text())
        if r['status']=='running':print(node,p.stem,'RUNNING',round(time.time()-r['started']))
    for p in sorted((root/'results').glob(node+'-*-full/result.json')):
        r=json.loads(p.read_text());samples=r.get('samples',[])
        print(p.parent.name,'status',r.get('status',r.get('complete')),'columns',len(r.get('columns',[])),
            'calls',len(samples),'native',[round(s.get('native_api_seconds',s.get('native_seconds')),4)for s in samples])
    p=root/(node+'-sequence-complete.json')
    if p.exists():print(node,'SEQUENCE_COMPLETE')
