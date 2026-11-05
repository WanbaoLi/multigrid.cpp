import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4');q=root/'compute-queue';q.mkdir(exist_ok=True)
for mode in('baseline','double-outer','mixed-single'):
    name=mode+'-full12';path=q/(name+'.status.json')
    task=dict(argv=['bash',str(root/'run_outer_mode.sh'),mode],cwd=str(root),timeout=1800)
    assert not list(q.glob(name+'.*'))
    p=q/(name+'.task.json')
    with p.open('x')as f:json.dump(task,f,indent=2)
    os.link(p,q/(name+'.ready.json'))
    while True:
        if path.exists():
            status=json.loads(path.read_text())
            if status['status']!='running':
                assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids'],status
                break
        time.sleep(5)
    print('MODE_COMPLETE',mode,flush=True)
(root/'sequence-complete.json').write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
print('ALL_PRECISION_MODES_COMPLETE',flush=True)
