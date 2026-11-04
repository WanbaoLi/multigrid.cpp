"""Publish one exact reviewed successor task after complete owned cleanup."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');q=root/'queue10';sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def closed(name):
    path=q/(name+'.status.json');row=read(path)
    assert row['status']=='passed'and type(row['returncode'])is int and row['returncode']==0 and row['task_tag']
    assert row['cleanup']['complete']and row['cleanup']['surviving_pids']==[]
    return dict(path=str(path),sha256=sha(path),task_tag=row['task_tag'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--kind',choices=['profile150','halo148','clover149'],required=True)
    p.add_argument('--task-sha',required=True);p.add_argument('--contract-sha',required=True);p.add_argument('--enqueue',action='store_true');a=p.parse_args()
    startup=read(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
    phase=read(root/'151-runtime-confirm-worker10-v7-state.json');dependencies=[closed('151-runtime-confirm-worker10-v7')]
    assert phase['complete']and phase['status']=='complete'and phase['groups']['runtime']['runtime_audit']['complete']
    best=read(root/'campaign/best.json');assert best['attempt']==phase['expected_best']
    if a.kind=='profile150':
        name='150-best-solve-profile-worker10';prepared=root/'prepared-profile150-worker10'
        contract=read(prepared/'contract.json',a.contract_sha);task=read(prepared/'task.json',a.task_sha)
        assert contract['ordinary_promotion']is False and contract['expected_best']==best['attempt']and task['timeout']==3600
        assert contract['host']==startup['host']and contract['allocation']==startup['allocation']
        for row in contract['helper_pins']:sha(row['path'],row['sha256'])
        for key in('startup','phase5_state','phase5_status'):
            row=contract['request'][key];sha(row['path'],row['sha256'])
        future=[root/(name+'-state.json'),root/'campaign/attempts'/name,Path(contract['profile_output'])]
    elif a.kind=='halo148':
        name='148-halo-v2-full-worker10';prepared=root/'prepared-halo148-worker10'
        contract=read(prepared/'preparation.json',a.contract_sha);task=read(prepared/'task.json',a.task_sha)
        dependencies.append(closed('150-best-solve-profile-worker10'))
        profile=read(root/'150-best-solve-profile-worker10-state.json')
        assert profile['complete']and profile['verification']['passed']and profile['verification']['columns']==12
        assert profile['best']==best['attempt']and profile['allocation']==startup['allocation']and profile['budget']['complete']
        assert task['timeout']==4500 and '--scope'in task['argv']and task['argv'][task['argv'].index('--scope')+1]=='full'
        entry=Path(task['argv'][2]);sha(entry,'d0d910ff0501d6fdb752d1a64ed1aafb934e27aa1d74b5781f8a3071805bfa7d')
        assert contract['prior_library_sha256']=='e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330'
        future=[root/(name+'-state.json')]
    else:
        name='149-clover-arm-qualify-worker10';prepared=root/'prepared-clover149-worker10'
        contract=read(prepared/'plan.json',a.contract_sha);task=read(prepared/'task.json',a.task_sha)
        dependencies.append(closed('148-halo-v2-full-worker10'))
        assert contract['scope']=='arm-clover-full-qualification-v1'and contract['physical_full12']is False and task['timeout']==3600
        for row in contract['pinned_files']:sha(row['path'],row['sha256'])
        future=[root/(name+'-state.json'),root/'campaign-clover-reuse-v1/attempts/000-arm-clover-tests']
    assert startup['host']=='cn19486'and startup['allocation']=='mg-opt-20261103-worker10'
    assert task['environment']['LD_LIBRARY_PATH']==startup['loader_environment']['LD_LIBRARY_PATH']
    assert startup['safe_deadline_epoch']-time.time()>=task['timeout']+90
    assert not any(path.exists()or path.is_symlink()for path in future)
    assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(name+'.*'))
    assert not(q/'STOP').exists()and 'Bounded worker finished'not in(root/'worker10.log').read_text()
    heartbeat=integrity.read_dual(q/'heartbeat.json');payload=source_bytes(q/'heartbeat.json',heartbeat['openssl_sha256'])
    h=json.loads(payload);stamp=heartbeat['initial']['mtime_ns']/1e9
    assert time.time()-stamp<15 and h['host']==startup['host']and sorted(h['allowed_cpus'])==startup['before_worker_exec_parent_state']['cpus']and len(h['allowed_cpus'])==592
    with(q/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker lock must remain held')
    spec=importlib.util.spec_from_file_location('actual_scheduler',root/'worker10_login_record.py')
    login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login);job,query=login.query(shutil.which('djob'),'2025061')
    assert job['state']=='RUNNING'and job['taskExecNodes']==startup['host']and job['exclusive']is True
    proof=dict(complete=True,id=name,task_sha256=a.task_sha,contract_sha256=a.contract_sha,publisher_sha256=sha(__file__),
        dependencies=dependencies,expected_best=best['attempt'],best_sha256=sha(root/'campaign/best.json'),scheduler_query=query,
        heartbeat_sha256=heartbeat['openssl_sha256'],epoch=time.time())
    if not a.enqueue:print(json.dumps(dict(ready=True,proof=proof),indent=2));return
    assert time.time()-stamp<15
    integrity.write_private_new(root/(name+'-heartbeat-at-dispatch.json'),[payload])
    integrity.write_json_private(root/(name+'-launch.json'),proof)
    private=q/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,q/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name,launch_sha256=sha(root/(name+'-launch.json')))),flush=True)
if __name__=='__main__':main()
