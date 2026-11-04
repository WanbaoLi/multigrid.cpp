"""Worker8 submission v2: authenticated natural-idle or explicit graceful exit.

Default is read-only. Does not authenticate/start the future compute worker;
worker8_login_record.py must bind the actual returned scheduler job afterwards.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import file_integrity as integrity

READER_SHA = '34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427'
SOURCE_READER_SHA = '5691366c7f0dabc0c8714b0732612abb2f0019532fe070168ad2cc88f83867f3'
WORKER_IDENTITIES = ('worker8-allocation.json', 'worker8-allocation-failure.json',
                     'worker8-startup-attempt.json', 'worker8-startup.json',
                     'worker8-startup-failure.json', 'worker8.log')


def require(value, message):
    integrity.require(value, message)


def sha(path, expected=None):
    return integrity.read_dual(Path(path), expected)['openssl_sha256']


def read(path, expected=None):
    from raw_scalar_helper import source_bytes
    value = sha(path, expected)
    return json.loads(source_bytes(path, value))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fresh_worker_namespace(root):
    for name in WORKER_IDENTITIES:
        require(not os.path.lexists(Path(root)/name),
                'Existing worker8 identity; no automatic replacement: '+name)


def submit_once(root, argv, evidence, runner=subprocess.run):
    """Never update an exclusive-created file, and never automatically resubmit."""
    root = Path(root)
    intent = root/'worker8-submission-intent.json'
    result_path = root/'worker8-submission-result.json'
    uncertainty = root/'worker8-submission-uncertain.json'
    for path in (intent, result_path, uncertainty):
        require(not path.exists() and not path.is_symlink(),
                'Existing submission identity; inspect scheduler, never retry automatically: '+str(path))
    record = dict(complete=True, submitted=False, argv=argv, epoch=time.time(),
                  evidence=evidence, result_record=str(result_path))
    integrity.write_json_private(intent, record)
    try:
        result = runner(argv, capture_output=True, text=True, timeout=45)
    except BaseException as error:
        integrity.write_json_private(uncertainty, dict(complete=False,
            submission_result_uncertain=True, intent_sha256=sha(intent),
            exception=repr(error),
            next_action='Inspect scheduler for this exact argv/jobName/user/start window before any new action; no automatic retry.'))
        raise
    result_record = dict(complete=True, submitted=result.returncode == 0,
                         returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                         intent_sha256=sha(intent), epoch=time.time())
    # This is a distinct immutable file. If its publication fails after a
    # successful dsub, intent still prevents a duplicate submission.
    integrity.write_json_private(result_path, result_record)
    return result_record


def validate_plan(root, plan, planner):
    source = Path(plan['source_root'])
    head = plan['expected_source_head']
    require(source.is_absolute() and source == source.resolve(strict=True), 'Canonical source path required')
    require(re.fullmatch('[0-9a-f]{40}', head), 'Exact reviewed source head required')
    expected = planner.plan(str(source), head, str(root))
    for name in ('argv', 'login_record_writer_argv_after_submit', 'previous_job',
                 'allocation', 'queue', 'expected_host', 'wall_seconds', 'safe_reserve_seconds'):
        require(plan.get(name) == expected[name], 'Reviewed worker8 plan differs: '+name)
    require(plan['previous_job'] == '2022100' and plan['queue'] == 'queue8', 'Exact successor identity required')
    require(plan['wrapper_sha256'] == {name:sha(root/name) for name in planner.WRAPPERS},
            'Reviewed worker8 wrapper closure differs')
    return source, head


def validate_exit(root, proof, previous):
    root = Path(root)
    if proof.get('exit_kind') == 'natural-idle':
        require(previous.get('state') == 'SUCCEEDED' and previous.get('exitCode') == 0 and
                previous.get('jobExitCode') == 0 and previous.get('endTime') == proof.get('scheduler_end_time'),
                'Natural exit requires authenticated scheduler success and exact end time')
        log = root/'worker7.log'
        require(sha(log, proof.get('worker_log_sha256')) == proof.get('worker_log_sha256'),
                'Actual natural-exit log SHA required')
        require(log.read_text().strip().splitlines()[-1] == 'Bounded worker finished; no active task',
                'Actual terminal idle marker required; never synthesize STOP')
    else:
        require((root/'queue7/STOP').is_file() and
                'STOP received; queued tasks retained' in (root/'worker7.log').read_text(),
                'Actual graceful worker7 stop marker required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha', required=True)
    parser.add_argument('--wrapper-manifest', type=Path, required=True)
    parser.add_argument('--wrapper-manifest-sha', required=True)
    parser.add_argument('--stop-proof', type=Path, required=True)
    parser.add_argument('--stop-proof-sha', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--expected-entry-sha')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    require(Path(__file__).resolve().parent == root and
            Path(integrity.__file__).resolve() == root/'file_integrity.py', 'Exact deployed reader/entry root required')
    sha(integrity.__file__, READER_SHA)
    sha(root/'raw_scalar_helper.py', SOURCE_READER_SHA)
    integrity.known_vectors()
    manifest = read(args.wrapper_manifest, args.wrapper_manifest_sha)
    for name, row in manifest['files'].items():
        require(re.fullmatch('[a-z0-9][a-z0-9_.-]{0,79}', name) and Path(name).name == name,
                'Wrapper manifest must use plain file names')
        sha(root/name, row['sha256'])
    planner = load('_reviewed_worker8_plan', root/'prepare_worker8.py')
    plan = read(args.plan, args.plan_sha)
    source, head = validate_plan(root, plan, planner)
    actual = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True, timeout=25).strip()
    dirty = subprocess.check_output(['git','-C',str(source),'status','--porcelain'], text=True, timeout=25).strip()
    require(actual == head and not dirty, 'Source must already be clean at the reviewed head; never alter it here')
    stop = read(args.stop_proof, args.stop_proof_sha)
    require(stop.get('complete') is True and stop.get('previous_job') == '2022100' and
            stop.get('worker_stopped') is True and stop.get('all_owned_tasks_cleaned') is True,
            'Actual worker7 stop and owned task cleanup proof required')
    statuses = {str(path):sha(path) for path in sorted((root/'queue7').glob('*.status.json'))}
    require(statuses and stop.get('task_status_sha256') == statuses,
            'Stop proof must bind all actual worker7 task status bytes')
    for name in statuses:
        status = read(name)
        require(status.get('status') in ('passed','failed','timeout') and status.get('task_tag') and
                status.get('cleanup',{}).get('complete') is True and
                status.get('cleanup',{}).get('surviving_pids') == [],
                'Old task is not terminal and cleaned: '+name)
    for queue in ('queue7','queue8'):
        require(not list((root/queue).glob('*.running.json')) and
                not list((root/queue).glob('*.ready.json')), 'Old/pending compute claim in '+queue)
    fresh_worker_namespace(root)
    query = load('_reviewed_worker8_login', root/'worker8_login_record.py')
    previous, query_proof = query.query(shutil.which('djob'), '2022100')
    require(str(previous.get('jobId')) == '2022100' and previous.get('state') in ('SUCCEEDED','FAILED') and previous.get('user') == 'nsls_lwb' and
            previous.get('jobName') == 'mg-opt-worker7' and previous.get('taskExecNodes') == 'cn19483' and
            previous.get('endTime'), 'Actual predecessor scheduler job must be terminal')
    validate_exit(root, stop, previous)
    evidence = dict(plan_sha256=args.plan_sha, wrapper_manifest_sha256=args.wrapper_manifest_sha,
                    stop_proof_sha256=args.stop_proof_sha, source_root=str(source), source_head=head,
                    previous_job={key:previous.get(key) for key in
                                  ('jobId','jobName','state','user','taskExecNodes','startTime','endTime')},
                    predecessor_query=query_proof, task_status_sha256=statuses)
    if not args.execute:
        print(json.dumps(dict(complete=True, ready_not_submitted=True, argv=plan['argv'], evidence=evidence), indent=2))
        return
    require(args.expected_entry_sha, 'Explicit reviewed submission entry SHA required')
    sha(__file__, args.expected_entry_sha)
    result = submit_once(root, plan['argv'], evidence)
    print(json.dumps(result, indent=2), flush=True)
    require(result['submitted'], 'Scheduler submission failed; retain receipts and inspect before any further action')


if __name__ == '__main__':
    main()
