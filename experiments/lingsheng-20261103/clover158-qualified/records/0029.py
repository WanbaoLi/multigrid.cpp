"""Prepare/run the unchanged Clover qualifier on actual fresh worker13."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-arm-clover-v1'
sys.path.insert(0,str(aux));import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(p,e=None):return integrity.read_dual(p,e)['openssl_sha256']
def read(p,e=None):return json.loads(source_bytes(p,sha(p,e)))
p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');p.add_argument('--plan-sha');p.add_argument('--task-sha');a=p.parse_args()
name='158-clover-arm-qualify-worker13';out=root/'prepared-clover158-worker13';queue=root/'queue13'
startup=root/'worker13-startup.json';start=read(startup)
assert start['complete']and start['scheduler_job']=='2035635'and start['allocation']=='mg-opt-20261103-worker13'and start['host']=='cn19480'
assert start['safe_deadline_epoch']-time.time()>=3690
dependency=root/'queue11/155-best-solve-profile-worker11.status.json';dep=read(dependency)
assert dep['status']=='passed'and dep['returncode']==0 and dep['cleanup']['complete']and not dep['cleanup']['surviving_pids']
manifest=read(aux/'arm-clover-v1-files.json','1836042fc66ce0be549713432d4a007af4e5a148d1c07dd2894ca1eb7d360e47')
pins=[dict(path=str(aux/n),sha256=sha(aux/n,h))for n,h in manifest['files'].items()]
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))and not list(queue.glob(name+'.*'))and not(queue/'STOP').exists()
assert not(root/(name+'-state.json')).exists()and not(root/'campaign-clover-reuse-v1/attempts/000-arm-clover-tests').exists()
if not a.enqueue:
    out.mkdir(exist_ok=False)
    plan=dict(complete=True,prepared_not_queued=True,id=name,scope='arm-clover-full-qualification-v1',
        source_head='861613c703117c6b5b671e245a7142e217b09501',source=str(root/'source-clover-reuse-861'),
        startup=dict(path=str(startup),sha256=sha(startup)),dependency_status=str(dependency),dependency_status_sha256=sha(dependency),
        pinned_files=pins,performance_ranked=False,physical_full12=False,
        history='149 was never executed.155 closed passed on prior cn19486 and is historical motivation only. New cn19480 allocation startup/preflight and fresh target qualification are required; no prior profile timing is reused.')
    integrity.write_json_private(out/'plan.json',plan)
    task=dict(argv=[sys.executable,'-u',str(aux/'arm_clover_qualify_v1.py'),'--plan',str(out/'plan.json'),'--plan-sha',sha(out/'plan.json')],
        cwd=str(aux),timeout=3600,environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT=''))
    integrity.write_json_private(out/'task.json',task)
    print(json.dumps(dict(prepared=True,plan_sha=sha(out/'plan.json'),task_sha=sha(out/'task.json'),not_queued=True)),flush=True)
else:
    assert a.plan_sha and a.task_sha
    plan=read(out/'plan.json',a.plan_sha);task=read(out/'task.json',a.task_sha)
    assert plan['startup']==dict(path=str(startup),sha256=sha(startup))and plan['pinned_files']==pins and plan['id']==name
    sha(dependency,plan['dependency_status_sha256'])
    spec=importlib.util.spec_from_file_location('actual_login',root/'worker13_login_record.py');login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    job,query=login.query(shutil.which('djob'),'2035635');assert job['state']=='RUNNING'and job['exclusive']is True and job['taskExecNodes']=='cn19480'
    beatinfo=integrity.read_dual(queue/'heartbeat.json');beat=read(queue/'heartbeat.json',beatinfo['openssl_sha256'])
    assert time.time()-beatinfo['initial']['mtime_ns']/1e9<15 and len(beat['allowed_cpus'])==592 and beat['host']==start['host']
    assert str(beat['pid'])==job['resGroups'][0]['nodeResUsages'][0]['pids']and sorted(beat['allowed_cpus'])==start['before_worker_exec_parent_state']['cpus']
    with(queue/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker must hold queue lock')
    integrity.write_json_private(root/(name+'-launch.json'),dict(complete=True,id=name,plan_sha256=a.plan_sha,task_sha256=a.task_sha,
        startup_sha256=sha(startup),publisher_sha256=sha(__file__),heartbeat_sha256=beatinfo['openssl_sha256'],scheduler_query=query,epoch=time.time()))
    private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name,launch_sha256=sha(root/(name+'-launch.json')))),flush=True)
