#!/usr/bin/env python3
"""Consume a fresh trusted login allocation record; never query scheduler here."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
import shlex
import socket
import stat
import subprocess
import sys
import time
import traceback

SOURCE_TOOLS = ('tools/optimization/worker.py','tools/optimization/process_tree.py','tools/probe_host.py','tools/run_numa.py','tools/pin_build.py')
HOST = 'cn19486'
ALLOCATION = 'mg-opt-20261103-worker11'
PREVIOUS_JOB = '2025061'
WRAPPERS = ('worker11.sh', 'worker11_entry.py', 'worker11_preflight.py', 'worker11_login_record.py', 'worker11_runtime_probe.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv):
    return subprocess.check_output(argv, text=True, timeout=25)


def epoch(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise RuntimeError('Scheduler timestamp must have an explicit timezone')
    return result.timestamp()


def validate_job(job, root, job_id, host=HOST, source=None, expected_source_head=None):
    if source is None or not re.fullmatch('[0-9a-f]{40}',str(expected_source_head)):
        raise RuntimeError('Explicit reviewed source directory and exact40hex head required')
    if (not str(job_id).isdigit() or str(job_id) == PREVIOUS_JOB or
            str(job.get('jobId')) != str(job_id) or job.get('state') != 'RUNNING' or
            job.get('jobName') != 'mg-opt-worker11' or job.get('user') != 'nsls_lwb' or
            job.get('taskExecNodes') != host or job.get('taskExecNodesCount') != 1 or
            job.get('queue') != 'q_hpcapp' or job.get('account') != 'common' or
            Path(job.get('execPath', '')).resolve() != root or
            shlex.split(job.get('cmd', '')) != ['/bin/bash', str(root/'worker11.sh'),'--source',str(source),'--expected-source-head',expected_source_head]):
        raise RuntimeError('Allocation identity does not match exact reviewed worker11 job')
    groups = job.get('resGroups', [])
    if (job.get('exclusive') is not True or len(groups) != 1 or
            groups[0].get('replica') != 1 or str(groups[0].get('nnodes')) != '1' or
            groups[0].get('resAlloc', {}).get('cpu') != 592 or
            groups[0].get('resAlloc', {}).get('mem') != 480000 or
            groups[0].get('resReq', {}).get('cpu') != 592 or
            groups[0].get('resReq', {}).get('mem') != 480000 or
            groups[0].get('preferNodes') != host or job.get('jobWallClockLimit') != 14400):
        raise RuntimeError('Allocation must have exact exclusive592CPU/480000MB/14400seconds resources')
    usages = groups[0].get('nodeResUsages', [])
    if len(usages) != 1 or usages[0].get('execNode') != host:
        raise RuntimeError('Allocation resource usage node differs from reviewed host')
    return epoch(job['startTime'])


def deadline(job, now):
    hard = epoch(job['startTime']) + job['jobWallClockLimit']
    safe = hard - 300
    lifetime = int(safe-now)
    if lifetime < 600:
        raise RuntimeError('Less than ten minutes remain before safe allocation deadline')
    return hard, safe, lifetime


def validate_record(record, root, now, host=HOST, check_hashes=True, source=None, expected_source_head=None):
    if (record.get('schema') != 'worker11-login-allocation-v1' or record.get('complete') is not True or
            record.get('allocation') != ALLOCATION or record.get('expected_host') != HOST or host != HOST or
            record.get('previous_job') != PREVIOUS_JOB or
            record.get('scheduler_job') != record.get('requested_job_id') or
            record.get('writer_uid') != os.getuid() or not record.get('writer_host', '').startswith('login') or
            not Path(record.get('djob_path', '')).is_absolute()):
        raise RuntimeError('Allocation record is not the trusted exact worker11 login record')
    if (source is None or record.get('source_root')!=str(source) or record.get('expected_source_head')!=expected_source_head
            or set(record.get('source_tools_sha256',{}))!=set(SOURCE_TOOLS)):
        raise RuntimeError('Trusted source path/head/core-tool contract differs from explicit entry arguments')
    queried = record.get('query_epoch')
    if (not isinstance(queried, (int, float)) or not math.isfinite(queried) or
            not -5 <= now-queried <= 600):
        raise RuntimeError('Allocation record is stale or from a future clock')
    job = record['scheduler_authentication']['job']
    start = validate_job(job, root, record['requested_job_id'], host,source,expected_source_head)
    previous = record['scheduler_authentication']['previous']
    if (str(previous.get('jobId')) != PREVIOUS_JOB or previous.get('state') not in ('SUCCEEDED', 'FAILED') or
            previous.get('user') != 'nsls_lwb' or epoch(previous['endTime']) > start):
        raise RuntimeError('Predecessor is not terminal before current allocation starts')
    hard, safe, _ = deadline(job, now)
    if (not start <= queried < hard or record.get('scheduler_start_epoch') != start or
            record.get('scheduler_hard_end_epoch') != hard or record.get('safe_deadline_epoch') != safe):
        raise RuntimeError('Trusted record deadline differs from scheduler start and14400second limit')
    if set(record.get('wrapper_sha256', {})) != set(WRAPPERS):
        raise RuntimeError('Trusted record does not bind every worker11 wrapper')
    if check_hashes:
        for name, expected in record['wrapper_sha256'].items():
            if sha(root/name) != expected:
                raise RuntimeError('Worker11 wrapper differs from login authentication record: '+name)
    if check_hashes:
        for name,expected in record['source_tools_sha256'].items():
            if sha(source/name)!=expected:raise RuntimeError('Reviewed source core tool changed: '+name)
    return job


def read_record(path, wait_seconds=180):
    # Wait only for first atomic publication. An invalid published record is a
    # preserved failure, never an implicit retry or an overwrite request.
    stop = time.monotonic()+wait_seconds
    while not path.exists() and not path.is_symlink():
        if time.monotonic() >= stop:
            raise RuntimeError('Trusted login allocation record absent after bounded180second wait')
        time.sleep(min(2, max(0, stop-time.monotonic())))
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != os.getuid() or
            info.st_mode & 0o077 or info.st_size > 1024**2):
        raise RuntimeError('Trusted allocation record must be same-user regular private file')
    return json.loads(path.read_text())


def affinity_sha(cpus):
    return hashlib.sha256(json.dumps(sorted(cpus), separators=(',', ':')).encode()).hexdigest()


def parent_state(expected):
    cpus = sorted(os.sched_getaffinity(0))
    loaded = [line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
              if 'libgomp.so' in line or 'libkupl.so' in line]
    if cpus != expected or len(cpus) != 592 or loaded:
        raise RuntimeError('Parent affinity changed or parallel runtime loaded into worker parent')
    return dict(cpus=cpus, affinity_sha256=affinity_sha(cpus), gomp_kupl_loaded=False)


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--previous-job', choices=[PREVIOUS_JOB], required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--expected-source-head',required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source = args.source.resolve(strict=True)
    if not re.fullmatch('[0-9a-f]{40}',args.expected_source_head):raise RuntimeError('Exact reviewed40hex source head required')
    host = socket.gethostname().split('.')[0]
    if host != HOST or os.environ.get('LQCD_OPT_ALLOCATION') != ALLOCATION:
        raise RuntimeError('Unreviewed host or allocation; no automatic fallback')
    original_cpus = sorted(os.sched_getaffinity(0))
    # No ctypes/OpenMP/KUPL library loading in this process, including probes.
    original_state = parent_state(original_cpus)
    record_path = root/'worker11-allocation.json'
    record = read_record(record_path)
    job = validate_record(record, root, time.time(), host,source=source,expected_source_head=args.expected_source_head)
    head = run(['git', '-C', str(source), 'rev-parse', 'HEAD']).strip()
    if head != args.expected_source_head or run(['git', '-C', str(source), 'status', '--porcelain']).strip():
        raise RuntimeError('Exactly clean explicitly reviewed source head required; preserve active source')
    spec = importlib.util.spec_from_file_location('worker11_process_tree', source/'tools/optimization/process_tree.py')
    process_tree = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(process_tree)
    retained = []
    for queue in ('queue2', 'queue3', 'queue4', 'queue5', 'queue6', 'queue7', 'queue8', 'queue9', 'queue10'):
        for claim in sorted((root/queue).glob('*.running.json')):
            state = json.loads(claim.with_name(claim.name.replace('.running.json', '.status.json')).read_text())
            tag = state.get('task_tag')
            if (not tag or process_tree.tagged_processes(process_tree.TASK_KEY, tag) or
                    state.get('status') in ('running', 'cleanup_failed') or
                    not state.get('cleanup', {}).get('complete')):
                raise RuntimeError('Prior claim requires explicit cleanup inspection: '+str(claim))
            retained.append(dict(path=str(claim), status=state['status'], cleanup=state['cleanup']))
    hard, safe, _ = deadline(job, time.time())
    os.environ['LQCD_OPT_DEADLINE_EPOCH'] = str(safe)
    startup = dict(complete=False, host=host, allocation=ALLOCATION, scheduler_job=record['scheduler_job'],
        previous_job=args.previous_job, source_root=str(source),expected_source_head=args.expected_source_head,source_head=head,
        source_tools_sha256=record.get('source_tools_sha256',{}), allocation_record_sha256=sha(record_path),
        worker_sha256=sha(source/'tools/optimization/worker.py'), entry_sha256=sha(__file__),
        scheduler_hard_end_epoch=hard, safe_deadline_epoch=safe, retained_prior_claims=retained,
        original_parent_state=original_state,
        runtime_scope='Runtime loader probe executes only in separate child; benchmark needs own maps audit',
        loader_environment={k:os.environ.get(k) for k in ['LD_LIBRARY_PATH','LD_PRELOAD','OMP_WAIT_POLICY','GOMP_SPINCOUNT']})
    write_new(root/'worker11-startup-attempt.json', startup)
    try:
        startup['before_preflight_parent_state'] = parent_state(original_cpus)
        subprocess.run([sys.executable, str(root/'worker11_preflight.py'), '--root', str(root),
            '--expected-affinity-sha256', affinity_sha(original_cpus),'--source',str(source)], check=True)
        startup['after_preflight_parent_state'] = parent_state(original_cpus)
        preflight = json.loads((root/'worker11-preflight/result.json').read_text())
        if preflight.get('complete') is not True or preflight.get('passed') is not True:
            raise RuntimeError('Preflight did not finish all host/runtime/HBW gates')
        _, _, lifetime = deadline(job, time.time())
        startup.update(complete=True, preflight_sha256=sha(root/'worker11-preflight/result.json'),
            before_worker_exec_parent_state=parent_state(original_cpus))
        write_new(root/'worker11-startup.json', startup)
    except BaseException as error:
        startup.update(complete=False, error=repr(error), traceback=traceback.format_exc(),
            failed_parent_cpus=sorted(os.sched_getaffinity(0)))
        write_new(root/'worker11-startup-failure.json', startup)
        raise
    os.execv(sys.executable, [sys.executable, '-u', str(source/'tools/optimization/worker.py'),
        '--queue', str(root/'queue10'), '--lifetime', str(lifetime), '--idle-timeout', '3600'])


if __name__ == '__main__':
    main()
