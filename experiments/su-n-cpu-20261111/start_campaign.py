import json,os,socket,subprocess
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/sun-cpu-20261111-v2')
P='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
assert socket.gethostname()=='node5005'and len(os.sched_getaffinity(0))==256 and max(os.getloadavg()[:2])<3
q=R/'queue';q.mkdir(exist_ok=False)
with(q/'000-campaign.ready.json').open('x')as f:json.dump(dict(argv=[P,'-u',str(R/'run_campaign.py')],cwd=str(R),timeout=3300),f)
with(R/'worker.log').open('x')as log:
 p=subprocess.Popen([P,'-u','/public2/home/lwb_720/.cache/mg-opt-20261103/source/tools/optimization/worker.py','--queue',str(q),'--lifetime','4000','--idle-timeout','600'],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
(R/'launch.json').write_text(json.dumps(dict(worker_pid=p.pid,host=socket.gethostname(),cpus=sorted(os.sched_getaffinity(0)),load=os.getloadavg())))
print(p.pid)
