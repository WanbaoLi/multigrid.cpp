"""Use fresh CPU activity to distinguish own decaying load from current work."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
root=Path('/public2/home/lwb_720/.cache/mg-opt-clover-reuse-v1-20261104');aux=root/'quality-round2-helpers'
python='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python';sys.path.insert(0,str(aux));import file_integrity as integrity
assert socket.gethostname().split('.')[0]=='node5005'and len(os.sched_getaffinity(0))==256
manifest=json.loads((aux/'quality-manifest.json').read_text())
for name,expected in manifest['files'].items():integrity.read_dual(aux/name,expected)
prior=json.loads((root/'quality-v3-queue/000-correctness.status.json').read_text())
assert prior['status']=='passed'and prior['cleanup']['complete']and not prior['cleanup']['surviving_pids']
assert not list((root/'quality-v3-queue').glob('*.running.json'))
active=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal()or int(proc.name)==os.getpid():continue
    try:
        if proc.stat().st_uid!=os.getuid():continue
        comm=(proc/'comm').read_text().strip();cmd=(proc/'cmdline').read_bytes()
        if comm not in('sshd','ssh','bash','sh')and any(t in cmd for t in(b'worker.py',b'ctest',b'cc1plus',b'mpiexec',b'orterun',b'benchmark_')):
            active.append(dict(pid=int(proc.name),comm=comm))
    except OSError:pass
assert not active,'Other owned compute remains'
def cpu():return [int(v)for v in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
before=cpu();time.sleep(4);after=cpu();delta=[b-a for a,b in zip(before,after)]
busy=1-(delta[3]+delta[4])/sum(delta)
assert busy<.03 and os.getloadavg()[0]<3,'Current node activity is not idle'
schedule=subprocess.run(['squeue','-h','-w','node5005'],capture_output=True,text=True,timeout=15)
assert schedule.returncode==0 and not schedule.stdout.strip(),'Scheduled workload present'
queue=root/'quality-round2-queue';queue.mkdir(exist_ok=False)
env=dict(os.environ)
for key in list(env):
    if key.startswith('LQCD_')or key in('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):env.pop(key,None)
env.update(PATH='/public2/home/lwb_720/miniconda3/envs/pyquda/bin:'+env['PATH'],OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_PROC_BIND='close')
task=dict(argv=[python,'-u',str(aux/'x86_setup_quality_round2.py')],cwd=str(root),timeout=7500,environment=dict(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
integrity.write_json_private(queue/'000-correctness.ready.json',task)
with(root/'quality-round2-worker.log').open('xb')as stream:
    process=subprocess.Popen([python,'-u','/public2/home/lwb_720/.cache/mg-opt-20261103/source/tools/optimization/worker.py',
        '--queue',str(queue),'--lifetime','7800','--idle-timeout','120'],env=env,stdin=subprocess.DEVNULL,
        stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
proof=dict(worker_pid=process.pid,task=task,host=socket.gethostname(),allowed_cpus=sorted(os.sched_getaffinity(0)),
    load_average=list(os.getloadavg()),current_four_second_busy_fraction=busy,other_owned_compute=active,scheduled_jobs=0,
    predecessor_status_sha256=integrity.read_dual(root/'quality-v3-queue/000-correctness.status.json')['openssl_sha256'],
    prior_start_refusal_retained=True,resource_change='Replace stale5minute load gate by four-second activity plus1minute load, no other owned compute and empty scheduler',
    numerical_or_performance_gate_changes=False,direct_ssh_not_scheduler_exclusive=True)
integrity.write_json_private(root/'quality-round2-launch.json',proof);print(json.dumps(proof),flush=True)
