import json,subprocess,sys,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v3')
for solver in('ours','pyqcu'):
    name=solver+'-592-full';queue=root/'compute-queue'
    if not list(queue.glob(name+'.*')):subprocess.run([sys.executable,str(root/'publish.py'),'compute',solver,'592','full'],check=True)
    path=queue/(name+'.status.json')
    while True:
        if path.exists():
            r=json.loads(path.read_text())
            if r['status']!='running':
                assert r['status']=='passed'and r['cleanup']['complete']and not r['cleanup']['surviving_pids'],r
                break
        time.sleep(5)
    print('COMPLETED',name,flush=True)
(queue/'STOP').write_text('One complete12 per solver finished; release allocation\n')
(root/'compute-complete.json').write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
