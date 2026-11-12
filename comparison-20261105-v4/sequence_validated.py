import json,os,sys,time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
build=q/'010-build-outer-option.status.json'
while True:
    if build.exists():
        status=json.loads(build.read_text())
        if status['status']!='running':
            assert status['status']=='passed'and status['cleanup']['complete'],status;break
    time.sleep(5)
assert(r/'outer-build-passed').exists()
for mode in('baseline-v2','double-outer-v2','mixed-single-v2'):
    name=mode+'-full12';p=q/(name+'.task.json')
    with p.open('x')as f:json.dump(dict(argv=['bash',str(r/'run_outer_validated.sh'),mode],cwd=str(r),timeout=1800),f)
    os.link(p,q/(name+'.ready.json'))
    while True:
        path=q/(name+'.status.json')
        if path.exists():
            s=json.loads(path.read_text())
            if s['status']!='running':
                assert s['status']=='passed'and s['cleanup']['complete']and not s['cleanup']['surviving_pids'],s;break
        time.sleep(5)
    print('VALIDATED_OUTER_MODE_COMPLETE',mode,flush=True)
(r/'validated-complete.json').write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
