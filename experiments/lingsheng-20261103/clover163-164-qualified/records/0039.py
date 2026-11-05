"""Prepare/queue diagnosis only once the ordinary group has fully closed."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(p):return integrity.read_dual(Path(p))['openssl_sha256']
def read(p):return json.loads(source_bytes(Path(p),sha(p)))
p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');a=p.parse_args()
spec=importlib.util.spec_from_file_location('allocation',root/'allocation_contract_v1.py');allocation=importlib.util.module_from_spec(spec);spec.loader.exec_module(allocation)
context=allocation.load(root/'worker13-startup.json',sha(root/'worker13-startup.json'),root/'worker13_entry.py',root/'worker13-allocation.json')
queue=Path(context['queue']);name='164-clover-pair-micro-worker13'
sp=queue/'163-clover-pair-qualify-worker13.status.json';st=root/'163-clover-pair-qualify-worker13-state.json'
allocation.dependency(context,'163-clover-pair-qualify-worker13',sha(sp),st,sha(st))
state=read(st);assert state['complete']and state['status']=='passed'
assert context['safe_deadline_epoch']-time.time()>=700
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))and not list(queue.glob(name+'.*'))
assert not(root/'clover-micro-164-v2').exists()
task=dict(argv=[sys.executable,'-u',str(root/'clover_pair_micro_task_v1.py')],cwd=str(root),timeout=600,environment=dict(LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT=''))
proof=dict(complete=True,id=name,diagnostic_only=True,entry_sha256=sha(root/'clover_pair_micro_task_v1.py'),micro_source_sha256=sha(root/'clover_reuse_micro.cpp'),
    dependency_state_sha256=sha(st),dependency_status_sha256=sha(sp),allocation_contract=context,epoch=time.time())
if not a.enqueue:
    print(json.dumps(dict(ready=True,task=task,entry_sha256=proof['entry_sha256'],micro_source_sha256=proof['micro_source_sha256'],
        dependency_state_sha256=proof['dependency_state_sha256'],queue=context['queue'],host=context['host'],deadline=context['safe_deadline_epoch']),indent=2));sys.exit()
spec=importlib.util.spec_from_file_location('actual_login',root/'worker13_login_record.py');login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
job,query=login.query(shutil.which('djob'),context['scheduler_job']);assert job['state']=='RUNNING'and job['exclusive']is True and job['taskExecNodes']==context['host']
info=integrity.read_dual(queue/'heartbeat.json');beat=read(queue/'heartbeat.json')
assert time.time()-info['initial']['mtime_ns']/1e9<15 and beat['allowed_cpus']==context['cpus']and str(beat['pid'])==job['resGroups'][0]['nodeResUsages'][0]['pids']
with(queue/'worker.lock').open()as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:pass
    else:raise RuntimeError('Actual worker lock not held')
proof.update(scheduler_query=query,heartbeat_sha256=info['openssl_sha256']);integrity.write_json_private(root/(name+'-launch.json'),proof)
private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
print(json.dumps(dict(enqueued=True,diagnostic_only=True,id=name)),flush=True)
