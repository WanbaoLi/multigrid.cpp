import json, os, time
from pathlib import Path
r=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=r/'compute-queue'
def run(task, argv, timeout):
    p=q/(task+'.task.json')
    with p.open('x') as f:
        json.dump(dict(argv=argv,cwd=str(r),timeout=timeout),f)
    os.link(p,q/(task+'.ready.json'))
    while True:
        p=q/(task+'.status.json')
        if p.exists():
            s=json.loads(p.read_text())
            if s['status']!='running':
                assert s['status']=='passed' and s['cleanup']['complete'] and not s['cleanup']['surviving_pids'],s
                break
        time.sleep(5)
    print('SAP_TASK_COMPLETE',task,flush=True)
assert not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json'))
run('040-build-sap',['bash',str(r/'build_sap.sh')],1500)
for mode in ('sap-control','sap-compact','sap-columns'):
    run(mode,['bash',str(r/'run_sap.sh'),mode],1800)
(r/'sap-complete.json').write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
