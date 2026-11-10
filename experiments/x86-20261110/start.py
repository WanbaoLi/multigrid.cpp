import json,os,socket,subprocess
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/mg-x86-20261110');P='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
assert socket.gethostname()=='node5005' and len(os.sched_getaffinity(0))==256
assert max(os.getloadavg()[:2])<3
q=R/'queue';q.mkdir(exist_ok=False)
with(q/'000-profile.ready.json').open('x')as f:json.dump(dict(argv=[P,'-u',str(R/'diagnose.py')],cwd=str(R),timeout=750),f)
env=dict(os.environ,PATH=str(Path(P).parent)+':'+os.environ['PATH'],OPENBLAS_NUM_THREADS='1',OMP_PROC_BIND='close')
with(R/'worker.log').open('x')as f:
 p=subprocess.Popen([P,'-u','/public2/home/lwb_720/.cache/mg-opt-20261103/source/tools/optimization/worker.py','--queue',str(q),'--lifetime','7200','--idle-timeout','1800'],env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(R/'launch.json').write_text(json.dumps(dict(pid=p.pid,host=socket.gethostname(),cpus=sorted(os.sched_getaffinity(0)),load=os.getloadavg())))
print(p.pid)
