"""Review or publish the exact prepared152 task into the existing owned queue."""
import argparse
import fcntl
import json
import os
from pathlib import Path
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract-sha', required=True)
    parser.add_argument('--task-sha', required=True)
    parser.add_argument('--enqueue', action='store_true')
    args = parser.parse_args()
    prepared = ROOT/'prepared-halo152-worker10'
    contract = read(prepared/'contract.json', args.contract_sha)
    task = read(prepared/'task.json', args.task_sha)
    name = '152-halo-v2-ordinary-worker10'
    assert contract['complete'] and contract['id'] == name and contract['task_sha256'] == args.task_sha
    assert contract['ordinary_repeats'] == 7 and contract['main_best_modified'] is False and task['timeout'] == 4500
    for row in contract['dependencies_and_pins']:
        sha(row['path'], row['sha256'])
    startup = read(ROOT/'worker10-startup.json', contract['startup_sha256'])
    assert startup['host'] == 'cn19486' and startup['allocation'] == 'mg-opt-20261103-worker10'
    assert startup['safe_deadline_epoch']-time.time() >= 4590
    assert task['environment']['LD_LIBRARY_PATH'] == startup['loader_environment']['LD_LIBRARY_PATH']
    assert task['argv'][2] == str(ROOT/'worker10_live_task_guard_v3.py')
    plan = read(prepared/'guard-plan.json')
    assert plan['id'] == name and plan['task_timeout_seconds'] == task['timeout'] and plan['numerical_or_acceptance_gate_changes'] is False
    original = read(plan['original_task']['path'], plan['original_task']['sha256'])
    assert {k:v for k,v in original.items() if k != 'argv'} == {k:v for k,v in task.items() if k != 'argv'}
    assert original['argv'][2] == str(ROOT/'aux-halo-v2-publication-v4/halo_v2_trial_publication_v4.py')
    assert sha(original['argv'][2], plan['original_entry_sha256']) == contract['scientific_controller_sha256']
    queue = ROOT/'queue10'
    assert not list(queue.glob('*.ready.json')) and not list(queue.glob('*.running.json')) and not list(queue.glob(name+'.*'))
    assert not (queue/'STOP').exists() and 'Bounded worker finished' not in (ROOT/'worker10.log').read_text()
    assert not Path(contract['campaign']).exists() and not Path(contract['state']).exists()
    heartbeat = integrity.read_dual(queue/'heartbeat.json')
    payload = source_bytes(queue/'heartbeat.json', heartbeat['openssl_sha256'])
    beat = json.loads(payload)
    stamp = heartbeat['initial']['mtime_ns']/1e9
    assert time.time()-stamp < 15 and beat['host'] == startup['host']
    assert sorted(beat['allowed_cpus']) == startup['before_worker_exec_parent_state']['cpus'] and len(beat['allowed_cpus']) == 592
    with (queue/'worker.lock').open() as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise RuntimeError('Actual original worker must hold its queue lock')
    allocation = read(ROOT/'worker10-allocation.json', 'a454a02d3ce61c75edec6a54fba4c190e81d5006a2402328b33d7ffada015085')
    job = allocation['scheduler_authentication']['job']
    prior = read(ROOT/'runtime151-actual-parent-guard.json')
    assert job['exclusive'] is True and job['state'] == 'RUNNING' and job['taskExecNodes'] == startup['host']
    assert prior['complete'] and prior['parent_pid'] == beat['pid'] and prior['allocation'] == startup['allocation']
    proof = dict(complete=True, id=name, task_sha256=args.task_sha, contract_sha256=args.contract_sha,
                 publisher_sha256=sha(__file__), actual_entry_parent_guard=True,
                 scheduler_query='Original authenticated allocation; fresh idle heartbeat and held lock. Live original-parent proof mandatory at entry; current scheduler query unavailable.',
                 original_allocation_sha256=sha(ROOT/'worker10-allocation.json'), heartbeat_sha256=heartbeat['openssl_sha256'],
                 best_sha256=sha(ROOT/'campaign/best.json'), epoch=time.time())
    if not args.enqueue:
        print(json.dumps(dict(ready=True, proof=proof), indent=2), flush=True)
        return
    assert time.time()-stamp < 15
    integrity.write_private_new(ROOT/(name+'-heartbeat-at-dispatch.json'), [payload])
    integrity.write_json_private(ROOT/(name+'-launch.json'), proof)
    private = queue/(name+'.task.json')
    integrity.write_json_private(private, task)
    os.link(private, queue/(name+'.ready.json'))
    print(json.dumps(dict(enqueued=True, id=name, launch_sha256=sha(ROOT/(name+'-launch.json')))), flush=True)


if __name__ == '__main__':
    main()
