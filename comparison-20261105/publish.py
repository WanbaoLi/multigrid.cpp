import argparse,json,os,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('node',choices=['login','compute']);p.add_argument('solver',choices=['ours','pyqcu']);p.add_argument('cores',choices=['128','592']);p.add_argument('mode',choices=['pilot','full']);a=p.parse_args()
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v1');queue=root/(a.node+'-queue');queue.mkdir(exist_ok=True)
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))
if a.node=='login':assert (root/'login-build-passed').exists()and a.cores=='128'
name=a.solver+'-'+a.cores+'-'+a.mode
assert not list(queue.glob(name+'.*'))
task=dict(argv=['bash',str(root/('run_'+a.solver+'.sh')),a.node,a.cores,a.mode],cwd=str(root),timeout=1200 if a.mode=='pilot'else 10500)
path=queue/(name+'.task.json')
with path.open('x')as f:json.dump(task,f,indent=2)
os.link(path,queue/(name+'.ready.json'));print('ENQUEUED',a.node,name)
