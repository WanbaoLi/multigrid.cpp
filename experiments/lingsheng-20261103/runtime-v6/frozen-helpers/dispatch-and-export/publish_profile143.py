"""Publish only the reviewed diagnostic task; no scientific comparison recovery."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).parent/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes

root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');q=root/'queue8';name='143-best-solve-profile-worker8'
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--enqueue',action='store_true');args=parser.parse_args()
    prepared=root/'prepared-solve-profile-v7-143'
    contract=read(prepared/'contract.json','b9b57abad66e8700c533401f40f5d1d0077a92d63103f79372e4485f9203e4dc')
    task=read(prepared/'task.json','4e7d16c2d29d8b65c8d87cc5236373cbb2d4f73bf644affa80214029b92b509f')
    assert task['timeout']==3600 and contract['ordinary_promotion']is False
    assert contract['host']=='cn19483'and contract['allocation']=='mg-opt-20261103-worker8'
    for row in contract['helper_pins']:sha(row['path'],row['sha256'])
    request=contract['request']
    for key in ('startup','phase5_state','phase5_status'):read(request[key]['path'],request[key]['sha256'])
    assert read(root/'campaign/best.json')['attempt']==contract['expected_best']=='052-reduce-on'
    assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(name+'.*'))
    assert not(q/'STOP').exists()and 'Bounded worker finished'not in(root/'worker8.log').read_text()
    probe=read(q/'142-old-runtime-environment-probe.status.json')
    assert probe['status']=='passed'and probe['returncode']==0 and probe['cleanup']['complete']and not probe['cleanup']['surviving_pids']
    hb=integrity.read_dual(q/'heartbeat.json');hbytes=source_bytes(q/'heartbeat.json',hb['openssl_sha256'])
    heartbeat=json.loads(hbytes);mtime=hb['initial']['mtime_ns']/1e9
    assert time.time()-mtime<15 and heartbeat['host']==contract['host']
    assert sorted(heartbeat['allowed_cpus'])==contract['expected_parent_cpus']and len(heartbeat['allowed_cpus'])==592
    with(q/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Worker lock is not held')
    spec=importlib.util.spec_from_file_location('actual_worker8_scheduler',root/'worker8_login_record.py')
    login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    job,query=login.query(shutil.which('djob'),'2023152')
    assert job['state']=='RUNNING'and job['taskExecNodes']=='cn19483'and job['exclusive']is True
    startup=read(request['startup']['path'],request['startup']['sha256'])
    assert startup['safe_deadline_epoch']-time.time()>=task['timeout']+90
    proof=dict(complete=True,id=name,task_sha256=sha(prepared/'task.json'),contract_sha256=sha(prepared/'contract.json'),
        publisher_sha256=sha(__file__),scheduler_query=query,heartbeat_sha256=hb['openssl_sha256'],
        preceding_phase_status='failed; retained unchanged',probe_status_sha256=sha(q/'142-old-runtime-environment-probe.status.json'),
        expected_best=contract['expected_best'],unranked=True,epoch=time.time())
    if not args.enqueue:print(json.dumps(dict(ready=True,proof=proof),indent=2));return
    assert time.time()-mtime<15
    integrity.write_private_new(root/'solve-profile143-heartbeat-at-dispatch.json',[hbytes])
    integrity.write_json_private(root/'solve-profile143-launch.json',proof)
    private=q/(name+'.task.json');integrity.write_json_private(private,task)
    os.link(private,q/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=name,launch_sha256=sha(root/'solve-profile143-launch.json'))),flush=True)

if __name__=='__main__':main()
