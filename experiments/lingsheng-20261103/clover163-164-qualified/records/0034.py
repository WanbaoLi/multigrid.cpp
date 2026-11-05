"""Bind pair-row full12 trial to the actual qualified source and micro evidence."""
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
def read(p,e=None):return json.loads(source_bytes(Path(p),integrity.read_dual(Path(p),e)['openssl_sha256']))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');p.add_argument('--task-sha');a=p.parse_args()
allocation=load('allocation',root/'allocation_contract_v1.py')
context=allocation.load(root/'worker13-startup.json',sha(root/'worker13-startup.json'),root/'worker13_entry.py',root/'worker13-allocation.json')
queue=Path(context['queue']);name='165-clover-full12-worker13';out=root/'prepared-clover165-worker13';entry=root/'clover_pair_full12_worker13_v1.py'
controller=load('actual_pair_driver',entry);qstate,qstatus=controller.qualification_paths(root)
assert qstatus.parent==queue
allocation.dependency(context,'163-clover-pair-qualify-worker13',sha(qstatus),qstate,sha(qstate),'067b28bd787a6428400e23d683596cd2120c5f6a')
micro=root/'clover-micro-164-v2/result.json';microstatus=queue/'164-clover-pair-micro-worker13.status.json'
allocation.dependency(context,'164-clover-pair-micro-worker13',sha(microstatus),micro,sha(micro))
assert read(micro)['full12_metric']is False and read(qstate)['actual_sve_widths']==[16,32,64]
assert read(root/'campaign/best.json')['attempt']=='052-reduce-on'
assert context['safe_deadline_epoch']-time.time()>=6500
assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))and not list(queue.glob(name+'.*'))and not(queue/'STOP').exists()
start=read(root/'worker13-startup.json')
if not a.enqueue:
    out.mkdir(exist_ok=False)
    contract=dict(complete=True,prepared_only=True,id=name,entry_sha256=sha(entry),qualification_state_sha256=sha(qstate),qualification_status_sha256=sha(qstatus),
        micro_result_sha256=sha(micro),micro_status_sha256=sha(microstatus),allocation_contract=context,
        main_best_modified=False,order=['old052-A','067-off','067-on','old052-B'],each_fresh_process=True,
        minimum_gain=.03,max_control_drift=.05,maximum_relative_spread=.1,scalar_limit=1e-8,solution_limit=1e-6,
        retry_of='160-clover-new-on',reason='Actual six-row full12 and local regression; pair-row coefficient stream/pipeline change, with all new source qualification and ordinary controls')
    integrity.write_json_private(out/'contract.json',contract)
    task=dict(argv=[sys.executable,'-u',str(entry),'--expected-self-sha',sha(entry)],cwd=str(root),timeout=6300,
        environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT=''))
    integrity.write_json_private(out/'task.json',task);print(json.dumps(dict(prepared=True,task_sha=sha(out/'task.json'),contract_sha=sha(out/'contract.json'))),flush=True)
else:
    assert a.task_sha;task=read(out/'task.json',a.task_sha);contract=read(out/'contract.json')
    assert contract['allocation_contract']==context
    for path,key in[(entry,'entry_sha256'),(qstate,'qualification_state_sha256'),(qstatus,'qualification_status_sha256'),(micro,'micro_result_sha256'),(microstatus,'micro_status_sha256')]:assert sha(path)==contract[key]
    login=load('actual_login',root/'worker13_login_record.py');job,query=login.query(shutil.which('djob'),context['scheduler_job'])
    assert job['state']=='RUNNING'and job['exclusive']is True and job['taskExecNodes']==context['host']
    info=integrity.read_dual(queue/'heartbeat.json');beat=read(queue/'heartbeat.json')
    assert time.time()-info['initial']['mtime_ns']/1e9<15 and beat['host']==context['host']and beat['allowed_cpus']==context['cpus']
    assert str(beat['pid'])==job['resGroups'][0]['nodeResUsages'][0]['pids']
    with(queue/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker must hold queue lock')
    integrity.write_json_private(root/(name+'-launch.json'),dict(complete=True,id=name,task_sha256=a.task_sha,contract_sha256=sha(out/'contract.json'),publisher_sha256=sha(__file__),scheduler_query=query,heartbeat_sha256=info['openssl_sha256'],epoch=time.time()))
    private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name)),flush=True)
