"""Resume ordered measurements; existing failures block without overwriting."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2');py=sys.executable
def read(p):return json.loads(p.read_text())
def wait(node,name):
    path=root/(node+'-queue')/(name+'.status.json')
    while True:
        if path.exists():
            r=read(path)
            if r['status']!='running':
                assert r['status']=='passed'and r.get('returncode')==0 and r['cleanup']['complete']and not r['cleanup']['surviving_pids'],(node,name,r)
                return
        time.sleep(10)
def launch(node,solver,cores):
    name=f'{solver}-{cores}-full';q=root/(node+'-queue')
    if not any(q.glob(name+'.*')):
        subprocess.run([py,str(root/'publish.py'),node,solver,str(cores),'full'],check=True)
    wait(node,name)
    print('CLOSED',node,name,flush=True)
node=sys.argv[1]
if node=='login':
    wait(node,'ours-128-pilot');wait(node,'pyqcu-128-pilot')
    subprocess.run([py,str(root/'crosscheck.py'),node,'128'],check=True)
    for solver,cores in(('ours',128),('pyqcu',128)):launch(node,solver,cores)
else:
    wait(node,'pyqcu-128-pilot')
    for solver,cores in(('ours',128),('pyqcu',128),('ours',592),('pyqcu',592)):launch(node,solver,cores)
for cores in(('128',)if node=='login'else('128','592')):
    subprocess.run([py,str(root/'crosscheck.py'),node,cores,'--mode','full'],check=True)
(root/(node+'-sequence-complete.json')).write_text(json.dumps(dict(complete=True,epoch=time.time()))+'\n')
print('SEQUENCE_COMPLETE',node,flush=True)
