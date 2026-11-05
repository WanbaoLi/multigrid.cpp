"""Review/publish the exact fresh worker11 profile; no source or timer edits."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0, str(ROOT/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes


def sha(path, expected=None):
    return integrity.read_dual(path, expected)['openssl_sha256']


def read(path, expected=None):
    return json.loads(source_bytes(path, sha(path, expected)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--contract-sha', required=True)
    p.add_argument('--task-sha', required=True)
    p.add_argument('--enqueue', action='store_true')
    a = p.parse_args()
    prepared = ROOT/'prepared-profile155-worker11'
    contract = read(prepared/'contract.json', a.contract_sha)
    task = read(prepared/'task.json', a.task_sha)
    startup = read(ROOT/'worker11-startup.json', 'd1682f573747fcdc12003b369a83b64c3a935e7683ae45038e536954a979c859')
    name = '155-best-solve-profile-worker11'
    assert contract['id'] == name and contract['preparation_schema'] == 'new-allocation-profile-v8' and contract['schema'] == 'solve-profile-scope-v7'
    assert contract['host'] == startup['host'] == 'cn19486' and contract['allocation'] == startup['allocation'] == 'mg-opt-20261103-worker11'
    assert contract['queue'] == 'queue11' and contract['ordinary_promotion'] is False and task['timeout'] == 3600
    assert read(ROOT/'campaign/best.json')['attempt'] == contract['expected_best'] == '052-reduce-on'
    assert task['environment']['LD_LIBRARY_PATH'] == startup['loader_environment']['LD_LIBRARY_PATH']
    for row in contract['helper_pins']:
        sha(row['path'], row['sha256'])
    for key in ('startup', 'predecessor_state', 'predecessor_status', 'predecessor_startup'):
        row = contract['request'][key]
        sha(row['path'], row['sha256'])
    sha(ROOT/'prepare_solve_profile_v8.py', contract['preparer_sha256'])
    assert startup['safe_deadline_epoch']-time.time() >= 3690
    assert not any(p.exists() for p in [ROOT/(name+'-state.json'), ROOT/'campaign/attempts'/name, Path(contract['profile_output'])])
    queue = ROOT/'queue11'
    assert not list(queue.glob('*.ready.json')) and not list(queue.glob('*.running.json')) and not list(queue.glob(name+'.*')) and not (queue/'STOP').exists()
    with (queue/'worker.lock').open() as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise RuntimeError('Actual worker11 must hold its queue lock')
    spec = importlib.util.spec_from_file_location('actual_scheduler', ROOT/'worker11_login_record.py')
    login = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login)
    job, query = login.query(shutil.which('djob'), '2026153')
    assert job['state'] == 'RUNNING' and job['taskExecNodes'] == 'cn19486' and job['exclusive'] is True
    heartbeat = integrity.read_dual(queue/'heartbeat.json')
    payload = source_bytes(queue/'heartbeat.json', heartbeat['openssl_sha256'])
    beat = json.loads(payload)
    assert time.time()-heartbeat['initial']['mtime_ns']/1e9 < 15 and beat['host'] == startup['host']
    assert sorted(beat['allowed_cpus']) == startup['before_worker_exec_parent_state']['cpus'] and len(beat['allowed_cpus']) == 592
    assert str(beat['pid']) == job['resGroups'][0]['nodeResUsages'][0]['pids']
    proof = dict(complete=True, id=name, task_sha256=a.task_sha, contract_sha256=a.contract_sha,
                 publisher_sha256=sha(__file__), scheduler_query=query, actual_worker_pid=beat['pid'],
                 startup_sha256=sha(ROOT/'worker11-startup.json'), heartbeat_sha256=heartbeat['openssl_sha256'], epoch=time.time())
    if not a.enqueue:
        print(json.dumps(dict(ready=True, proof=proof), indent=2), flush=True)
        return
    integrity.write_private_new(ROOT/(name+'-heartbeat-at-dispatch.json'), [payload])
    integrity.write_json_private(ROOT/(name+'-launch.json'), proof)
    private = queue/(name+'.task.json')
    integrity.write_json_private(private, task)
    os.link(private, queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True, id=name, launch_sha256=sha(ROOT/(name+'-launch.json')))), flush=True)


if __name__ == '__main__':
    main()
