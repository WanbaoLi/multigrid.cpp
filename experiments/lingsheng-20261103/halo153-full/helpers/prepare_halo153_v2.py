"""Pin a completed prefix and prepare the unexecuted tests after suite timeout."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0, str(ROOT/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
sys.path.insert(0, str(ROOT))
import ctest_remainder_v1 as coverage


def sha(path, expected=None):
    return integrity.read_dual(path, expected)['openssl_sha256']


def read(path, expected=None):
    return json.loads(source_bytes(path, sha(path, expected)))


def main():
    startup = read(ROOT/'worker10-startup.json', 'f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
    assert startup['safe_deadline_epoch']-time.time() >= 4590
    prior_status_path = ROOT/'queue10/148-halo-v2-full-worker10.status.json'
    prior_status = read(prior_status_path)
    assert prior_status['status'] == 'failed' and prior_status['returncode'] == 1 and prior_status['cleanup']['complete'] and not prior_status['cleanup']['surviving_pids']
    state_path = ROOT/'148-halo-v2-full-worker10-state.json'
    prior_state = read(state_path)
    assert prior_state['status'] == 'failed' and prior_state['allocation'] == startup['allocation'] and prior_state['host'] == startup['host']
    directory = ROOT/'campaign-halo-v2/attempts/000-halo-v2-tests'
    record = read(directory/'attempt.json')
    stage = record['stages']['mpi-numerical-ctest']
    assert stage['status'] == 'timeout' and stage['timeout_seconds'] == 1000 and stage['cleanup']['complete'] and not stage['cleanup']['surviving_pids']
    assert all(record['stages'][key]['status'] == 'passed' and record['stages'][key]['cleanup']['complete'] for key in ['configure', 'build', 'arm-codegen', 'arm-unit-ctest'])
    library = Path(prior_state['library'])
    sha(library, 'e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330')
    original = ROOT/'aux-halo-v2-760/arm_halo_v2_qualify.py'
    sha(original, 'd0d910ff0501d6fdb752d1a64ed1aafb934e27aa1d74b5781f8a3071805bfa7d')
    spec = importlib.util.spec_from_file_location('original_qualifier', original)
    qualifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qualifier)
    cache=Path(record['snapshot']['build'])/'CMakeCache.txt'
    commands=[row.split('=',1)[1]for row in cache.read_text().splitlines()if row.startswith('CMAKE_CTEST_COMMAND:INTERNAL=')]
    assert len(commands)==1 and Path(commands[0]).is_file()
    catalog = subprocess.run([commands[0], '--test-dir', record['snapshot']['build'], '--show-only=json-v1', '-R', qualifier.MPI], capture_output=True, check=True, timeout=30)
    names = [row['name'] for row in json.loads(catalog.stdout)['tests']]
    assert len(names) == 13 and len(set(names)) == 13
    log = directory/stage['log']
    text = source_bytes(log, sha(log, stage['log_sha256'])).decode()
    passed = coverage.passed_prefix(text, names)
    remaining = names[len(passed):]
    assert passed[-1] == 'runtime_batch_coarse_reduce' and remaining == ['runtime_batch_coarse_halo', 'mg_tuning']
    output = ROOT/'prepared-halo153-worker10'
    output.mkdir(exist_ok=False)
    integrity.write_private_new(output/'prior-attempt.json', [source_bytes(directory/'attempt.json', sha(directory/'attempt.json'))])
    integrity.write_private_new(output/'catalog.json', [catalog.stdout])
    pins = [dict(path=str(path), sha256=sha(path)) for path in [original, ROOT/'ctest_remainder_v1.py', prior_status_path, state_path,
        output/'prior-attempt.json', output/'catalog.json', log, directory/'source-manifest.json', library,
        Path(record['snapshot']['build'])/'CTestTestfile.cmake']]
    plan = dict(complete=True, id='153-halo-v2-remainder-worker10', scope='full-with-ctest-remainder-v1',
                prior_task='148-halo-v2-full-worker10', original_qualifier=str(original),
                original_qualifier_sha256=sha(original), expected_library_sha256=sha(library),
                prior_stage=stage, prior_log=str(log), prior_log_sha256=sha(log),
                catalog_path=str(output/'catalog.json'), catalog_sha256=sha(output/'catalog.json'),
                all_tests=names, completed_tests=passed, remaining_tests=remaining, pinned_files=pins,
                prior_failure_reason='Whole-suite1000s cap expired after11 complete tests. No failed CTest case; rerun the interrupted12th and run13th.',
                numerical_tests_or_limits_changed=False)
    integrity.write_json_private(output/'recovery-plan.json', plan)
    task = read(ROOT/'prepared-halo148-worker10/task.json')
    argv = list(task['argv'])
    entry = ROOT/'arm_halo_v2_remainder_v1.py'
    argv[2] = str(entry)
    argv[argv.index('--state-id')+1] = plan['id']
    argv[argv.index('--expected-entry-sha')+1] = sha(entry)
    argv += ['--recovery-plan', str(output/'recovery-plan.json'), '--recovery-plan-sha', sha(output/'recovery-plan.json')]
    original_task = dict(task, argv=argv)
    integrity.write_json_private(output/'original-task.json', original_task)
    guard = ROOT/'worker10_live_task_guard_v4.py'
    guard_plan = dict(complete=True, id=plan['id'], guard_sha256=sha(guard), original_task=dict(path=str(output/'original-task.json'), sha256=sha(output/'original-task.json')),
                      original_entry_sha256=sha(entry), task_timeout_seconds=4500, numerical_or_acceptance_gate_changes=False)
    integrity.write_json_private(output/'guard-plan.json', guard_plan)
    wrapped = dict(task, argv=[*argv[:2], str(guard), '--plan', str(output/'guard-plan.json'), '--plan-sha', sha(output/'guard-plan.json')])
    integrity.write_json_private(output/'task.json', wrapped)
    contract = dict(complete=True, id=plan['id'], task_sha256=sha(output/'task.json'), startup_sha256=sha(ROOT/'worker10-startup.json'),
                    dependencies_and_pins=[*pins, *[dict(path=str(path), sha256=sha(path)) for path in [output/'recovery-plan.json', output/'original-task.json',
                        output/'guard-plan.json', guard, entry, ROOT/'campaign/best.json']]], scientific_controller_sha256=sha(entry),
                    state=str(ROOT/(plan['id']+'-state.json')), main_best_modified=False)
    integrity.write_json_private(output/'contract.json', contract)
    print(json.dumps(dict(prepared_not_queued=True, completed_tests=passed, remaining_tests=remaining,
                          contract_sha256=sha(output/'contract.json'), task_sha256=sha(output/'task.json'))), flush=True)


if __name__ == '__main__':
    main()
