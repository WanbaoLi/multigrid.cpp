"""Prepare an unchanged full12 V2 trial only after current profile/full ARM tests."""
import json
from pathlib import Path
import sys
import time

V5_MANIFEST_SHA='684739d825a50e7e7dbb8ab16fa1b2645725abf27a9aa65a42e2ecf3a9117851'
V5_ENTRY_SHA='a9afbc64994d5c48587d09e27f70dd74cd797516feb4c7adcf1ec45a6e61bb59'
ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0, str(ROOT/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes


def sha(path, expected=None):
    return integrity.read_dual(path, expected)['openssl_sha256']


def read(path, expected=None):
    return json.loads(source_bytes(path, sha(path, expected)))


def main():
    startup = read(ROOT/'worker10-startup.json', 'f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
    assert startup['safe_deadline_epoch']-time.time() >= 4290
    best = read(ROOT/'campaign/best.json')
    assert best['attempt'] == '052-reduce-on'
    profile_path = ROOT/'150-best-solve-profile-worker10-state.json'
    tests_path = ROOT/'153-halo-v2-remainder-worker10-state.json'
    profile, tests = read(profile_path), read(tests_path)
    assert profile['complete'] and profile['budget']['complete'] and profile['verification']['passed'] and profile['verification']['columns'] == 12
    assert profile['best'] == best['attempt'] and profile['allocation'] == tests['allocation'] == startup['allocation']
    assert profile['host'] == tests['host'] == startup['host']
    assert tests['complete'] and tests['status'] == 'passed' and tests['full_numerical_complete'] and tests['scope'] == 'full'
    assert tests['library_sha256'] == 'e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330'
    pins = []
    for name in ['150-best-solve-profile-worker10', '153-halo-v2-remainder-worker10']:
        path = ROOT/'queue10'/(name+'.status.json')
        status = read(path)
        assert status['status'] == 'passed' and status['returncode'] == 0 and status['cleanup']['complete'] and not status['cleanup']['surviving_pids']
        pins.append(dict(path=str(path), sha256=sha(path)))
    aux = ROOT/'aux-halo-v2-publication-v5'
    manifest_path = aux/'halo-v2-trial-publication-v5-helpers.json'
    manifest_sha = V5_MANIFEST_SHA
    manifest = read(manifest_path, manifest_sha)
    for name, expected in manifest['files'].items():
        sha(aux/name, expected)
    entry = aux/'halo_v2_trial_publication_v5.py'
    entry_sha = sha(entry, V5_ENTRY_SHA)
    name = '154-halo-v2-ordinary-remainder-worker10'
    prefix = 'v2-w10v5'
    campaign = ROOT/'campaign-halo-v2-ordinary-w10v4'
    output = ROOT/'prepared-halo154-worker10'
    assert not campaign.exists() and not (ROOT/(prefix+'-state.json')).exists() and not output.exists()
    assert not list((ROOT/'queue10').glob('*.running.json')) and not list((ROOT/'queue10').glob('*.ready.json'))
    python = '/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
    argv = [python, '-u', str(entry), '--execute', '--root', str(ROOT), '--auxiliary', str(aux),
            '--campaign', str(campaign), '--prefix', prefix, '--profile-state', str(profile_path),
            '--profile-state-sha', sha(profile_path), '--profile-status', pins[0]['path'],
            '--profile-status-sha', pins[0]['sha256'], '--tests-state', str(tests_path),
            '--tests-state-sha', sha(tests_path), '--tests-status', pins[1]['path'],
            '--tests-status-sha', pins[1]['sha256'], '--library-sha', tests['library_sha256'],
            '--expected-entry-sha', entry_sha, '--expected-manifest-sha', manifest_sha,
            '--expected-host', startup['host']]
    task = dict(argv=argv, cwd=str(aux), timeout=4200, environment=dict(
        LD_LIBRARY_PATH=startup['loader_environment']['LD_LIBRARY_PATH'], LD_PRELOAD='', LD_DEBUG='',
        LD_DEBUG_OUTPUT='', PERF_COUNTER_ROOT='', OMP_WAIT_POLICY='', GOMP_SPINCOUNT='',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    output.mkdir(exist_ok=False)
    original = output/'original-task.json'
    integrity.write_json_private(original, task)
    guard = ROOT/'worker10_live_task_guard_v4.py'
    plan = dict(complete=True, id=name, guard_sha256=sha(guard), original_task=dict(path=str(original), sha256=sha(original)),
                original_entry_sha256=entry_sha, task_timeout_seconds=4200, numerical_or_acceptance_gate_changes=False)
    integrity.write_json_private(output/'guard-plan.json', plan)
    wrapped = dict(task, argv=[python, '-u', str(guard), '--plan', str(output/'guard-plan.json'),
                               '--plan-sha', sha(output/'guard-plan.json')])
    integrity.write_json_private(output/'task.json', wrapped)
    pins.extend(dict(path=str(path), sha256=sha(path)) for path in [profile_path, tests_path, ROOT/'campaign/best.json',
        manifest_path, guard, original, output/'guard-plan.json'])
    contract = dict(complete=True, prepared_not_queued=True, id=name, prefix=prefix, campaign=str(campaign),
                    state=str(ROOT/(prefix+'-state.json')), startup_sha256=sha(ROOT/'worker10-startup.json'),
                    task_sha256=sha(output/'task.json'), dependencies_and_pins=pins, remaining_floor_seconds=4290,
                    scientific_controller_sha256=entry_sha, main_best_modified=False, ordinary_repeats=7,
                    comparison='Fresh old052 A / V2 same-hierarchy off,on / unranked halo diagnostic / fresh old052 B')
    integrity.write_json_private(output/'contract.json', contract)
    print(json.dumps(dict(prepared_not_queued=True, task_sha256=sha(output/'task.json'),
                          contract_sha256=sha(output/'contract.json'))), flush=True)


if __name__ == '__main__':
    main()
