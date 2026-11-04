"""Publish exactly the reviewed prepared full8 task after actual capture smoke."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

import file_integrity as integrity
from raw_scalar_helper import source_bytes

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ID='141-phase5-worker8-v5'
CONTRACT_SHA='f3e9d9f163f22a6e8c64ba53c9675962c8945abb274b813f9665cb318d161bc2'
TASK_SHA='cb8c432f5d10c4d73744e4870dae0c7efe9563fee93965d6aca92731275f01c2'


def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']


def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--enqueue',action='store_true')
    parser.add_argument('--expected-self-sha',required=True);args=parser.parse_args()
    sha(__file__,args.expected_self_sha)
    q=ROOT/'queue8';prepared=ROOT/'prepared-phase5-worker8-v5-141'
    contract=read(prepared/'contract.json',CONTRACT_SHA);task=read(prepared/'task.json',TASK_SHA)
    assert contract['task_id']==ID and len(contract['case_ids'])==8
    assert '--external-runtime-audit'in contract['controller']['argv']
    assert task['timeout']==6500 and task['environment']['LQCD_OPT_CAPTURE_DIR']==contract['runtime_audit_dir']
    assert contract['runtime_capture']['captured_during_setup']is False
    for row in contract['pinned_files']:sha(row['path'],row['sha256'])
    assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(ID+'.*'))
    assert not (q/'STOP').exists()and 'Bounded worker finished'not in(ROOT/'worker8.log').read_text()
    heartbeat_read=integrity.read_dual(q/'heartbeat.json')
    heartbeat_sha=heartbeat_read['openssl_sha256']
    heartbeat_bytes=source_bytes(q/'heartbeat.json',heartbeat_sha)
    heartbeat=json.loads(heartbeat_bytes)
    heartbeat_mtime=heartbeat_read['initial']['mtime_ns']/1e9
    assert time.time()-heartbeat_mtime<15 and len(heartbeat['allowed_cpus'])==592
    assert heartbeat['host']=='cn19483'and sorted(heartbeat['allowed_cpus'])==sorted(contract['expected_parent_cpus'])
    with (q/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Actual worker lock must still be held')
    spec=importlib.util.spec_from_file_location('worker8_login',ROOT/'worker8_login_record.py')
    login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    job,query=login.query(shutil.which('djob'),'2023152')
    assert job['state']=='RUNNING'and job['taskExecNodes']=='cn19483'and job['exclusive']is True
    assert contract['safe_deadline_epoch']-time.time()>=task['timeout']+90
    smoke=read(q/'139d-capture-v5-sdk-worker8.status.json')
    assert smoke['status']=='passed'and smoke['returncode']==0 and smoke['cleanup']['complete']and smoke['cleanup']['surviving_pids']==[]
    result=read(ROOT/'runtime-capture-v5-sdk-smoke-worker8/result.json')
    assert result['complete']and result['passed']and result['ranks']==16
    maps=read(ROOT/'runtime-capture-v5-sdk-smoke-worker8/maps.json',result['maps_sha256'])
    assert maps['complete']and maps['completed_before_steady']and {r['rank']for r in maps['ranks']}=={0,8}
    assert maps['captured_during_setup']is False and maps['ordinary_solve_observer_running']is False
    assert maps['actual_runtime_environment_not_normalized']is True
    assert maps['observed_fixed_mpi_prefix']=='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/hmpi/bisheng/release/hmpi/lib:'*2
    assert maps['library_sha256']=='d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82'
    proof=dict(complete=True,prepared_contract_sha256=CONTRACT_SHA,task_sha256=TASK_SHA,
        publisher_sha256=args.expected_self_sha,scheduler_query=query,
        actual_capture_smoke_status_sha256=sha(q/'139d-capture-v5-sdk-worker8.status.json'),
        actual_capture_result_sha256=sha(ROOT/'runtime-capture-v5-sdk-smoke-worker8/result.json'),
        actual_capture_maps_sha256=result['maps_sha256'],fresh_idle_heartbeat_sha256=heartbeat_sha,
        fresh_idle_heartbeat_snapshot=str(ROOT/'phase5-worker8-v5-141-heartbeat-at-dispatch.json'),
        expected_best=contract['expected_best'],case_ids=contract['case_ids'],epoch=time.time())
    if not args.enqueue:
        print(json.dumps(dict(ready=True,proof=proof),indent=2));return
    assert time.time()-heartbeat_mtime<15
    integrity.write_private_new(ROOT/'phase5-worker8-v5-141-heartbeat-at-dispatch.json',[heartbeat_bytes])
    integrity.write_json_private(ROOT/'phase5-worker8-v5-141-launch.json',proof)
    private=q/(ID+'.task.json');integrity.write_json_private(private,task)
    os.link(private,q/(ID+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=ID,launch_sha256=sha(ROOT/'phase5-worker8-v5-141-launch.json'))),flush=True)


if __name__=='__main__':main()
