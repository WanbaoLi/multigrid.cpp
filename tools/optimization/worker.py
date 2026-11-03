#!/usr/bin/env python3
"""Durable bounded single-node queue worker; no shell evaluation of tasks."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time


def atomic(path, record):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(record, indent=2, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class WorkerInterrupted(KeyboardInterrupt):
    def __init__(self, signum):
        super().__init__(f'Worker received signal {signum}')
        self.signum = signum


def interrupted(signum, frame):
    raise WorkerInterrupted(signum)


def validate_task(record, lifetime):
    timeout = float(record['timeout'])
    if not math.isfinite(timeout) or timeout <= 0 or timeout > lifetime:
        raise RuntimeError('Task timeout outside finite worker lifetime')
    argv = record.get('argv')
    if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) and arg for arg in argv):
        raise RuntimeError('Task argv must be a nonempty string argument array')
    if not isinstance(record.get('environment', {}), dict):
        raise RuntimeError('Task environment must be an object')
    return timeout


def terminate_group(process, grace=10):
    """Terminate/reap before another task can start, including stubborn children."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--lifetime', type=int, default=6900)
    parser.add_argument('--idle-timeout', type=int, default=600)
    args = parser.parse_args()
    if args.lifetime <= 0 or args.idle_timeout <= 0:
        parser.error('lifetime and idle-timeout must be positive')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    root = args.queue.resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / 'worker.lock'
    import fcntl
    with lock.open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = active = time.monotonic()
        while True:
            now = time.monotonic()
            atomic(root / 'heartbeat.json', dict(host=socket.gethostname(), pid=os.getpid(),
                elapsed=now-started, idle=now-active, allowed_cpus=sorted(os.sched_getaffinity(0))))
            if (root / 'STOP').exists():
                print('STOP received; queued tasks retained', flush=True)
                break
            tasks = sorted(root.glob('*.ready.json'))
            if tasks:
                task_path = tasks[0]
                record = json.loads(task_path.read_text())
                timeout = validate_task(record, args.lifetime)
                if now-started+timeout > args.lifetime:
                    print('Insufficient allocation time; task retained', flush=True)
                    break
                claimed = task_path.with_name(task_path.name.replace('.ready.json','.running.json'))
                task_path.rename(claimed)
                status = dict(task=str(claimed), host=socket.gethostname(), started=time.time(),
                              argv=record['argv'], status='running')
                status_path = task_path.with_name(task_path.name.replace('.ready.json','.status.json'))
                atomic(status_path, status)
                logfile = task_path.with_name(task_path.name.replace('.ready.json','.log'))
                env = dict(os.environ, **{k:str(v) for k,v in record.get('environment',{}).items()})
                process = None
                try:
                    with logfile.open('xb') as stream:
                        process = subprocess.Popen(record['argv'], cwd=record.get('cwd'), env=env,
                            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                        status['pid'] = process.pid
                        atomic(status_path, status)
                        try:
                            result = process.wait(timeout=timeout)
                            status.update(returncode=result, status='passed' if result==0 else 'failed')
                        except subprocess.TimeoutExpired:
                            terminate_group(process)
                            status.update(status='timeout', returncode=process.returncode)
                except BaseException as exc:
                    if process:
                        terminate_group(process)
                    status.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed', error=repr(exc))
                    if isinstance(exc,KeyboardInterrupt):
                        raise
                finally:
                    status['ended'] = time.time()
                    atomic(status_path, status)
                    # Preserve an interrupted claim for explicit inspection/retry;
                    # a normal failure/timeout is terminal and gets an immutable
                    # finished marker. Never silently turn a killed allocation
                    # into an absent task.
                    if status['status'] != 'interrupted':
                        claimed.rename(claimed.with_name(claimed.name.replace('.running.json','.finished.json')))
                active = time.monotonic()
                print(json.dumps(status), flush=True)
                continue
            # Check completion before idle expiry; pending tasks are never lost.
            if now-started >= args.lifetime or now-active >= args.idle_timeout:
                print('Bounded worker finished; no active task', flush=True)
                break
            time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except WorkerInterrupted as exc:
        print(str(exc), flush=True)
        sys.exit(128 + exc.signum)
