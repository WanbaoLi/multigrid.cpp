"""Publish the reviewed fresh five-case bracket in its actual new allocation."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');q=root/'queue10';name='151-runtime-confirm-worker10-v7'
sys.path.insert(0,str(root/'aux-runtime-confirm-v7'));import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def main():
    p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');args=p.parse_args()
    prepared=root/'prepared-runtime151-worker10'
    contract=read(prepared/'contract.json','3771f64210cea527c4dce99aea96a7ec48c6783e921e466047a24a4f31662798')
    task=read(prepared/'task-live-guard-v2.json','e6f774f3c2d4aba90fe2f9363f053e765e6a3a0198c6bb93921166e62073762c')
    assert task['timeout']==3000 and len(contract['case_ids'])==3 and contract['host']=='cn19486'
    assert contract['allocation']=='mg-opt-20261103-worker10'and contract['old_samples_imported']is False
    for row in contract['pinned_files']:sha(row['path'],row['sha256'])
    request=contract['request']
    for key in ('startup','runtime_manifest','smoke_status','smoke_result','smoke_maps','failed_state','failed_status'):read(request[key]['path'],request[key]['sha256'])
    status=read(request['smoke_status']['path'],request['smoke_status']['sha256'])
    smoke=read(request['smoke_result']['path'],request['smoke_result']['sha256'])
    assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
    assert smoke['complete']and smoke['passed']and smoke['ranks']==16
    maps=read(request['smoke_maps']['path'],smoke['maps_sha256'])
    assert maps['complete']and maps['allocation']==contract['allocation']and maps['host']==contract['host']
    assert len(smoke['actual_old_gomp'])==2 and all(r['sha256']=='252cbdb01681c56080bba6a94d3461bf5704a03f987a42517341ad464d19da27'for r in smoke['actual_old_gomp'])
    previous=read(request['failed_status']['path'],request['failed_status']['sha256'])
    phase=read(request['failed_state']['path'],request['failed_state']['sha256'])
    assert previous['status']=='passed'and previous['cleanup']['complete']and not previous['cleanup']['surviving_pids']
    assert phase['complete']and phase['groups']['runtime']['runtime_audit']['complete']
    assert any(row['control_median_drift']>.05 for row in phase['groups']['runtime']['assessments'].values())
    assert read(root/'campaign/best.json')['attempt']==contract['expected_best']=='052-reduce-on'
    assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(name+'.*'))
    assert not(q/'STOP').exists()and 'Bounded worker finished'not in(root/'worker10.log').read_text()
    hb=integrity.read_dual(q/'heartbeat.json');hbytes=source_bytes(q/'heartbeat.json',hb['openssl_sha256']);heartbeat=json.loads(hbytes)
    mtime=hb['initial']['mtime_ns']/1e9
    assert time.time()-mtime<15 and heartbeat['host']=='cn19486'and sorted(heartbeat['allowed_cpus'])==contract['expected_parent_cpus']and len(heartbeat['allowed_cpus'])==592
    with(q/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker lock not held')
    spec=importlib.util.spec_from_file_location('actual_worker10_scheduler',root/'worker10_login_record.py')
    login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    record=read(root/'worker10-allocation.json','a454a02d3ce61c75edec6a54fba4c190e81d5006a2402328b33d7ffada015085')
    job=record['scheduler_authentication']['job']
    failure=read(root/'runtime151-control-plane-query-evidence.json','1f0508aba032581e7efbd8afa77a9e253cdf13558563cfd71fdd417df83eaccc')
    assert failure.get('error')=='TimeoutExpired'and failure['read_only']is True
    sha(root/'worker10_live_parent_guard_v1.py','63d2cd54b0246e8ffee9e0e524fd300fe25059e2e25b4e25cbce7747394c00f6')
    assert str(root/'worker10_live_parent_guard_v1.py')in task['argv']
    query=dict(method='Initial authenticated allocation plus fresh idle worker heartbeat/held lock and mandatory actual parent identity guard before any computation',
        current_scheduler_query='unavailable; timed out',query_failure_evidence_sha256='1f0508aba032581e7efbd8afa77a9e253cdf13558563cfd71fdd417df83eaccc',
        initial_allocation_sha256='a454a02d3ce61c75edec6a54fba4c190e81d5006a2402328b33d7ffada015085',
        actual_parent_guard=str(root/'runtime151-actual-parent-guard.json'),initial_query_epoch=record['query_epoch'])
    assert job['state']=='RUNNING'and job['taskExecNodes']=='cn19486'and job['exclusive']is True
    startup=read(request['startup']['path'],request['startup']['sha256'])
    assert startup['safe_deadline_epoch']-time.time()>=task['timeout']+90
    proof=dict(complete=True,id=name,task_sha256=sha(prepared/'task-live-guard-v2.json'),contract_sha256=sha(prepared/'contract.json'),
        publisher_sha256=sha(__file__),scheduler_query=query,heartbeat_sha256=hb['openssl_sha256'],
        smoke_status_sha256=request['smoke_status']['sha256'],smoke_maps_sha256=smoke['maps_sha256'],
        expected_best=contract['expected_best'],case_ids=contract['case_ids'],historical_profile_not_a_timing_control=True,epoch=time.time())
    if not args.enqueue:print(json.dumps(dict(ready=True,proof=proof),indent=2));return
    assert time.time()-mtime<15
    integrity.write_private_new(root/'runtime151-heartbeat-at-dispatch.json',[hbytes])
    integrity.write_json_private(root/'runtime151-launch.json',proof)
    private=q/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,q/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name,launch_sha256=sha(root/'runtime151-launch.json'))),flush=True)
if __name__=='__main__':main()
