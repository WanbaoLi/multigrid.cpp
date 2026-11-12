import json,os,time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
p=q/'020-build-reliable.status.json'
while True:
    if p.exists():
        s=json.loads(p.read_text())
        if s['status']!='running':assert s['status']=='passed'and s['cleanup']['complete'],s;break
    time.sleep(5)
for mode in('reliable-off','reliable-on'):
    p=q/(mode+'.task.json')
    with p.open('x')as f:json.dump(dict(argv=['bash',str(r/'run_reliable.sh'),mode],cwd=str(r),timeout=1800),f)
    os.link(p,q/(mode+'.ready.json'))
    while True:
        p=q/(mode+'.status.json')
        if p.exists():
            s=json.loads(p.read_text())
            if s['status']!='running':assert s['status']=='passed'and s['cleanup']['complete']and not s['cleanup']['surviving_pids'],s;break
        time.sleep(5)
    print('RELIABLE_CASE_COMPLETE',mode,flush=True)
(r/'reliable-complete.json').write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
