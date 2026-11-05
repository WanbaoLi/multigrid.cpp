"""Fresh ordinary task after158; never dispatch during qualification."""
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
def sha(p,e=None):return integrity.read_dual(Path(p),e)['openssl_sha256']
def read(p,e=None):return json.loads(source_bytes(Path(p),sha(p,e)))
p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');p.add_argument('--task-sha');a=p.parse_args()
queue=root/'queue13';name='159-clover-full12-worker13';out=root/'prepared-clover159-worker13'
start=read(root/'worker13-startup.json');statuspath=queue/'158-clover-arm-qualify-worker13.status.json';status=read(statuspath)
statepath=root/'158-clover-arm-qualify-worker13-state.json';state=read(statepath)
assert start['complete']and start['scheduler_job']=='2035635'and start['host']=='cn19480'and start['allocation']=='mg-opt-20261103-worker13'
assert state['complete']and state['status']=='passed'and state['allocation']==start['allocation']and state['actual_sve_widths']==[16,32,64]
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert start['safe_deadline_epoch']-time.time()>=6500
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))and not list(queue.glob(name+'.*'))and not(queue/'STOP').exists()
entry=root/'clover_full12_worker13_v1.py'
if not a.enqueue:
    out.mkdir(exist_ok=False)
    contract=dict(complete=True,prepared_only=True,id=name,entry_sha256=sha(entry),qualification_state_sha256=sha(statepath),
        qualification_status_sha256=sha(statuspath),startup_sha256=sha(root/'worker13-startup.json'),performance_ranked=False,
        main_best_modified=False,order=['old052-A','861-off','861-on','old052-B'],each_fresh_process=True,
        minimum_gain=.03,max_control_drift=.05,maximum_relative_spread=.1,scalar_limit=1e-8,solution_limit=1e-6)
    integrity.write_json_private(out/'contract.json',contract)
    task=dict(argv=[sys.executable,'-u',str(entry),'--expected-self-sha',sha(entry)],cwd=str(root),timeout=6300,
        environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT=''))
    integrity.write_json_private(out/'task.json',task)
    print(json.dumps(dict(prepared=True,task_sha=sha(out/'task.json'),contract_sha=sha(out/'contract.json'))),flush=True)
else:
    assert a.task_sha
    task=read(out/'task.json',a.task_sha);contract=read(out/'contract.json')
    sha(entry,contract['entry_sha256']);sha(statepath,contract['qualification_state_sha256']);sha(statuspath,contract['qualification_status_sha256'])
    sha(root/'worker13-startup.json',contract['startup_sha256'])
    spec=importlib.util.spec_from_file_location('actual_login',root/'worker13_login_record.py');login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    job,query=login.query(shutil.which('djob'),'2035635');assert job['state']=='RUNNING'and job['exclusive']is True and job['taskExecNodes']=='cn19480'
    info=integrity.read_dual(queue/'heartbeat.json');beat=read(queue/'heartbeat.json',info['openssl_sha256'])
    assert time.time()-info['initial']['mtime_ns']/1e9<15 and beat['host']=='cn19480'and len(beat['allowed_cpus'])==592
    assert str(beat['pid'])==job['resGroups'][0]['nodeResUsages'][0]['pids']
    with(queue/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker must hold queue lock')
    integrity.write_json_private(root/(name+'-launch.json'),dict(complete=True,id=name,task_sha256=a.task_sha,contract_sha256=sha(out/'contract.json'),
        publisher_sha256=sha(__file__),scheduler_query=query,heartbeat_sha256=info['openssl_sha256'],epoch=time.time()))
    private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name,launch_sha256=sha(root/(name+'-launch.json')))),flush=True)
