"""Launch one isolated bounded correctness worker after fresh idle checks."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT=Path('/public2/home/lwb_720/.cache/mg-opt-clover-reuse-v1-20261104')
PYTHON='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
if socket.gethostname().split('.')[0]!='node5005'or len(os.sched_getaffinity(0))!=256 or max(os.getloadavg()[:2])>3:
    raise RuntimeError('Unexpected/restricted/busy node5005; preserve evidence')
sys.path.insert(0,str(ROOT));import file_integrity as integrity
manifest=json.loads((ROOT/'quality-round2-helpers/quality-manifest.json').read_text())
for name,expected in manifest['files'].items():integrity.read_dual(ROOT/'quality-round2-helpers'/name,expected)
other=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal()or int(proc.name)==os.getpid():continue
    try:
        if proc.stat().st_uid!=os.getuid():continue
        comm=(proc/'comm').read_text().strip();cmd=(proc/'cmdline').read_bytes()
        if comm not in('sshd','ssh','bash','sh')and any(t in cmd for t in(b'worker.py',b'ctest',b'cc1plus',b'mpiexec',b'orterun',b'benchmark_')):
            other.append(dict(pid=int(proc.name),comm=comm))
    except OSError:pass
if other:raise RuntimeError('Other owned compute still present: '+str(other))
queue=ROOT/'quality-round2-queue';queue.mkdir(exist_ok=False)
env=dict(os.environ)
for key in list(env):
    if key.startswith('LQCD_')or key in('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):
        env.pop(key,None)
env.update(PATH='/public2/home/lwb_720/miniconda3/envs/pyquda/bin:'+env['PATH'],OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_PROC_BIND='close')
task=dict(argv=[PYTHON,'-u',str(ROOT/'quality-round2-helpers/x86_setup_quality_round2.py')],cwd=str(ROOT),timeout=7500,environment=dict(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
with(queue/'000-correctness.ready.json').open('x')as stream:json.dump(task,stream,indent=2)
worker='/public2/home/lwb_720/.cache/mg-opt-20261103/source/tools/optimization/worker.py'
with(ROOT/'quality-round2-worker.log').open('xb')as stream:
    process=subprocess.Popen([PYTHON,'-u',worker,'--queue',str(queue),'--lifetime','7800','--idle-timeout','120'],
        env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
with(ROOT/'quality-round2-launch.json').open('x')as stream:json.dump(dict(worker_pid=process.pid,host=socket.gethostname(),task=task,
    allowed_cpus=sorted(os.sched_getaffinity(0)),load_average=list(os.getloadavg()),other_compute=[],
    direct_ssh_not_scheduler_exclusive=True,no_physical_performance=True),stream,indent=2)
print(json.dumps(dict(worker_pid=process.pid,queue=str(queue))))
