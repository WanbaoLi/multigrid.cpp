"""Release only the idle owned worker after154 closes; authenticate its exit."""
import argparse
import fcntl
import importlib.util
import json
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


def read(path):
    return json.loads(source_bytes(path, sha(path)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request-stop', action='store_true')
    parser.add_argument('--write-proof', action='store_true')
    args = parser.parse_args()
    assert not (args.request_stop and args.write_proof)
    queue = ROOT/'queue10'
    assert not list(queue.glob('*.ready.json')) and not list(queue.glob('*.running.json'))
    statuses = {str(p):sha(p) for p in sorted(queue.glob('*.status.json'))}
    assert statuses
    for path in statuses:
        row = read(Path(path))
        assert row['status'] in ('passed', 'failed', 'timeout') and row['task_tag']
        assert row['cleanup']['complete'] and not row['cleanup']['surviving_pids']
    final = read(queue/'154-halo-v2-ordinary-remainder-worker10.status.json')
    assert final['status'] in ('passed', 'failed', 'timeout')
    spec = importlib.util.spec_from_file_location('actual_scheduler', ROOT/'worker10_login_record.py')
    login = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(login)
    job, query = login.query(shutil.which('djob'), '2025061')
    assert str(job['jobId']) == '2025061' and job['jobName'] == 'mg-opt-worker10' and job['user'] == 'nsls_lwb'
    assert job['taskExecNodes'] == 'cn19486' and job['exclusive'] is True
    if args.write_proof:
        assert job['state'] in ('SUCCEEDED', 'FAILED') and job['endTime']
        assert (queue/'STOP').is_file() and 'STOP received; queued tasks retained' in (ROOT/'worker10.log').read_text()
        intent = read(ROOT/'worker10-stop-intent-for-worker11.json')
        assert intent['task_status_sha256'] == statuses
        with (queue/'worker.lock').open() as lock:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        proof = dict(complete=True, previous_job='2025061', worker_stopped=True, all_owned_tasks_cleaned=True,
                     exit_kind='graceful-stop', scheduler_end_time=job['endTime'], scheduler_query=query,
                     task_status_sha256=statuses, worker_log_sha256=sha(ROOT/'worker10.log'), lock_unheld=True,
                     stop_intent_sha256=sha(ROOT/'worker10-stop-intent-for-worker11.json'), epoch=time.time())
        target = ROOT/'worker10-exit-proof-for-worker11.json'
        integrity.write_json_private(target, proof)
        print(json.dumps(dict(complete=True, proof=str(target), sha256=sha(target))), flush=True)
        return
    assert job['state'] == 'RUNNING' and not (queue/'STOP').exists()
    beat_info = integrity.read_dual(queue/'heartbeat.json')
    beat = json.loads(source_bytes(queue/'heartbeat.json', beat_info['openssl_sha256']))
    assert time.time()-beat_info['initial']['mtime_ns']/1e9 < 15 and beat['host'] == 'cn19486'
    previous = read(ROOT/'runtime151-actual-parent-guard.json')
    assert beat['pid'] == previous['parent_pid'] and len(beat['allowed_cpus']) == 592
    with (queue/'worker.lock').open() as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise RuntimeError('Actual old worker must still hold the queue lock')
    record = dict(complete=True, previous_job='2025061', task_status_sha256=statuses,
                  scheduler_query=query, heartbeat_sha256=beat_info['openssl_sha256'], epoch=time.time(),
                  purpose='End the idle original worker after154 and all owned cleanup; no active computation is interrupted')
    if not args.request_stop:
        print(json.dumps(dict(ready_to_stop=True, record=record), indent=2), flush=True)
        return
    integrity.write_json_private(ROOT/'worker10-stop-intent-for-worker11.json', record)
    integrity.write_json_private(queue/'STOP', dict(reason=record['purpose'], epoch=time.time()))
    print(json.dumps(dict(stop_requested=True, owned_queue=str(queue), no_active_task=True)), flush=True)


if __name__ == '__main__':
    main()
