#!/usr/bin/env python3
"""Login-only scheduler authentication and one atomic private worker7 record."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


def jobs(payload):
    if payload.get('code') != 'success':
        raise RuntimeError('Scheduler query did not return success')
    data = payload['data']
    return data['successData'] if isinstance(data, dict) else data


def query(path, job_id):
    result = subprocess.run([path, '-J', '-l', str(job_id)], capture_output=True, text=True, check=True, timeout=25)
    payload = json.loads(result.stdout)
    values = jobs(payload)
    if len(values) != 1 or str(values[0]['jobId']) != str(job_id):
        raise RuntimeError('Scheduler did not return exactly requested jobID')
    return values[0], dict(argv=[path, '-J', '-l', str(job_id)], request_id=payload.get('requestId'), code=payload['code'])


def publish(path, record):
    temporary = path.with_name('.'+path.name+'.tmp-'+str(os.getpid()))
    # Hard-link publication is atomic and refuses to overwrite a prior record.
    # Both names are in the same shared directory/filesystem.
    descriptor = os.open(temporary, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(record, stream, indent=2, allow_nan=False); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o400)
        os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--job', required=True, help='Exact ID returned by reviewed worker7 dsub submission')
    parser.add_argument('--wait-seconds', type=int, default=900, help='Bounded login monitoring of pending job, default900seconds')
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--expected-source-head',required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source = args.source.resolve(strict=True)
    head = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=25).strip()
    dirty = subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True,timeout=25).strip()
    if head != args.expected_source_head or dirty:
        raise RuntimeError('Login source must already be clean at the explicit reviewed head; writer never updates it')
    if not 0 <= args.wait_seconds <= 14400:
        parser.error('wait-seconds must be between0and14400')
    host = socket.gethostname().split('.')[0]
    if not host.startswith('login'):
        raise RuntimeError('Scheduler record writer must run on actual login node')
    path = shutil.which('djob')
    if path is None:
        raise RuntimeError('Login PATH does not provide djob; do not guess compute CLI path')
    output = root/'worker7-allocation.json'
    if output.exists() or output.is_symlink():
        raise RuntimeError('Prior worker7 allocation record retained; do not overwrite')
    spec = importlib.util.spec_from_file_location('worker7_login_validation', root/'worker7_entry.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    stop = time.monotonic()+args.wait_seconds
    while True:
        job, query_data = query(path, args.job)
        if job.get('state') == 'RUNNING':
            break
        if job.get('state') not in ('PENDING', 'SCHEDULED') or time.monotonic() >= stop:
            raise RuntimeError('Requested worker7 job did not reach RUNNING within bounded login monitoring')
        time.sleep(min(5, max(0, stop-time.monotonic())))
    previous, previous_query = query(path, module.PREVIOUS_JOB)
    queried = time.time()
    start = module.validate_job(job, root, args.job,source=source,expected_source_head=args.expected_source_head)
    hard, safe, _ = module.deadline(job, queried)
    # Only scheduler authentication fields are retained, never environment dumps.
    keys = ('jobId','jobName','state','user','cmd','execPath','queue','account','exclusive','taskExecNodes',
            'taskExecNodesCount','startTime','endTime','jobWallClockLimit','resGroups','submitNode')
    auth = dict(job={k:job[k] for k in keys if k in job},
        previous={k:previous[k] for k in keys if k in previous}, job_query=query_data, previous_query=previous_query)
    record = dict(source_root=str(source),expected_source_head=args.expected_source_head,
        source_tools_sha256={name:module.sha(source/name)for name in module.SOURCE_TOOLS},schema='worker7-login-allocation-v1', complete=True, allocation=module.ALLOCATION,
        expected_host=module.HOST, scheduler_job=str(args.job), requested_job_id=str(args.job),
        previous_job=module.PREVIOUS_JOB, writer_host=host, writer_uid=os.getuid(), djob_path=path,
        query_epoch=queried, scheduler_start_epoch=start, scheduler_hard_end_epoch=hard, safe_deadline_epoch=safe,
        scheduler_authentication=auth, wrapper_sha256={name:module.sha(root/name) for name in module.WRAPPERS})
    module.validate_record(record, root, queried,source=source,expected_source_head=args.expected_source_head)
    publish(output, record)
    print(json.dumps(dict(complete=True, record=str(output), sha256=module.sha(output), scheduler_job=args.job,
        expected_host=module.HOST, safe_deadline_epoch=safe, djob_path=path)))


if __name__ == '__main__':
    main()
