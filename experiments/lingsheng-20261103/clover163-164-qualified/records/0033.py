"""Prepare fresh coherent-source qualification after completed Clover review."""
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
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');p.add_argument('--task-sha');a=p.parse_args()
allocation=load('allocation_contract',root/'allocation_contract_v1.py')
context=allocation.load(root/'worker13-startup.json',sha(root/'worker13-startup.json'),root/'worker13_entry.py',root/'worker13-allocation.json')
queue=Path(context['queue']);name='163-clover-pair-qualify-worker13';out=root/'prepared-clover163-worker13'
dependency_state=root/'clover-micro-161-v1/result.json';dependency_status=queue/'161-clover-reuse-micro-worker13.status.json'
allocation.dependency(context,'161-clover-reuse-micro-worker13',sha(dependency_status),dependency_state,sha(dependency_state))
prior=read(dependency_state);assert prior['complete']and prior['status']=='passed'
assert prior['full12_metric']is False, 'Micro diagnosis is never a ranking'
assert read(root/'campaign/best.json')['attempt']=='052-reduce-on'
assert context['safe_deadline_epoch']-time.time()>=3690
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))and not list(queue.glob(name+'.*'))and not(queue/'STOP').exists()
startup=root/'worker13-startup.json';start=read(startup)
if not a.enqueue:
    out.mkdir(exist_ok=False)
    entry=root/'arm_clover_pair_qualify_v1.py';aux=root/'aux-arm-clover-v1'
    manifest=read(aux/'arm-clover-v1-files.json','1836042fc66ce0be549713432d4a007af4e5a148d1c07dd2894ca1eb7d360e47')
    pins=[dict(path=str(aux/n),sha256=sha(aux/n,h))for n,h in manifest['files'].items()]
    pins.extend(dict(path=str(root/n),sha256=sha(root/n))for n in('arm_clover_pair_qualify_v1.py','file_integrity.py','raw_scalar_helper.py','phase6_sve_probe.py'))
    plan=dict(complete=True,prepared_not_queued=True,id=name,scope='arm-clover-full-qualification-v1',source=str(root/'source-clover-pair-067'),
        source_head='067b28bd787a6428400e23d683596cd2120c5f6a',startup=dict(path=str(startup),sha256=sha(startup)),
        dependency_status=str(dependency_status),dependency_state_sha256=sha(dependency_state),dependency_status_sha256=sha(dependency_status),
        pinned_files=pins,performance_ranked=False,physical_full12=False,allocation_contract=context,
        reason='Closed160 six-row ordinary slowdown; completed161 micro attributes source reuse. Qualify two-row grouping067 with independent chains; preserve all original failures and arithmetic order.')
    integrity.write_json_private(out/'plan.json',plan)
    task=dict(argv=[sys.executable,'-u',str(entry),'--plan',str(out/'plan.json'),'--plan-sha',sha(out/'plan.json')],cwd=str(root),timeout=3600,
        environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT=''))
    integrity.write_json_private(out/'task.json',task);print(json.dumps(dict(prepared=True,task_sha=sha(out/'task.json'),plan_sha=sha(out/'plan.json'))),flush=True)
else:
    assert a.task_sha;task=read(out/'task.json',a.task_sha);plan=read(out/'plan.json')
    assert plan['allocation_contract']==context
    for row in plan['pinned_files']:sha(row['path'],row['sha256'])
    sha(dependency_state,plan['dependency_state_sha256']);sha(dependency_status,plan['dependency_status_sha256'])
    login=load('actual_login',root/'worker13_login_record.py');job,query=login.query(shutil.which('djob'),context['scheduler_job'])
    assert job['state']=='RUNNING'and job['exclusive']is True and job['taskExecNodes']==context['host']
    info=integrity.read_dual(queue/'heartbeat.json');beat=read(queue/'heartbeat.json',info['openssl_sha256'])
    assert time.time()-info['initial']['mtime_ns']/1e9<15 and sorted(beat['allowed_cpus'])==context['cpus']and beat['host']==context['host']
    assert str(beat['pid'])==job['resGroups'][0]['nodeResUsages'][0]['pids']
    with(queue/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker must hold queue lock')
    integrity.write_json_private(root/(name+'-launch.json'),dict(complete=True,id=name,task_sha256=a.task_sha,plan_sha256=sha(out/'plan.json'),
        publisher_sha256=sha(__file__),scheduler_query=query,heartbeat_sha256=info['openssl_sha256'],epoch=time.time()))
    private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name)),flush=True)
