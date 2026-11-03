#!/usr/bin/env python3
"""Explicit precision-only recovery; preserve the failed057 evidence and expected SHA."""
import argparse
from copy import deepcopy
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import _sha256

ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ID = '057-best-profile-worker5'
EXPECTED = '805ebc992752c4127c342c40b491d897a2451b8095adab4a553eb172ba2507a0'
BEST = '052-reduce-on'
SOURCE = '78b429dc13a8b113792aa45bd27fc93134a8c4b39359da9ade05558c93d590ae'
LIBRARY = 'd8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82'
CONTROLLER = '4b903cf20ec4845e3be402c740a503915fd1ed0fbd186008f879f5d38dfafc97'
BENCH = '711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'
REFERENCE = Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid')
REFERENCE_SHA = '1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c'
EXTRACTOR = REFERENCE.with_name('extract_columns')
EXTRACTOR_SHA = 'efd900b99630c3cf2ea4ba285b38a5a123faa8e9d5d7cbbaf0f3169a8a58cc5b'
REASON = ('Explicit precision-only retry after retained060/061 read-only diagnostics reproduced '
          'the unchanged original expected digest with Python OpenSSL, software SHA256 and GNU '
          'on the original/snapshot and pinned CPUs0/304. Prior mismatch remains unexplained. '
          'No benchmark rerun, payload write, expected-digest change or ranking acceptance.')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def stat(value):
    return dict(dev=value.st_dev, inode=value.st_ino, bytes=value.st_size,
                mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns)


def fd_hash(path, expected):
    """Both implementations receive identical immutable chunk bytes from one FD."""
    crypto, portable = hashlib.sha256(), _sha256.sha256()
    with path.open('rb') as stream:
        before = stat(os.fstat(stream.fileno()))
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            crypto.update(chunk)
            portable.update(chunk)
        after = stat(os.fstat(stream.fileno()))
    result = dict(path=str(path), before=before, after=after,
                  path_after=stat(path.stat()), openssl_sha256=crypto.hexdigest(),
                  software_sha256=portable.hexdigest(), expected_sha256=expected,
                  original_open_mode='rb', timestamp=time.time())
    require(before == after == result['path_after'], 'Payload metadata changed while hashing')
    require(crypto.hexdigest() == portable.hexdigest() == expected,
            'Unchanged expected digest did not match both same-byte FD hashes')
    return result


def preconditions(root, ledger, check_host=False):
    campaign = root / 'campaign'
    _, config = ledger.campaign(campaign)
    best = ledger.read(campaign / 'best.json')
    require(best['attempt'] == BEST, 'Best pointer changed; do not recover under changed identity')
    _, ordinary, summary = ledger.checked_attempt(campaign, BEST, config)
    attempt = campaign / 'attempts' / ID
    data = ledger.read(attempt / 'attempt.json')
    ledger.check_snapshot(attempt, data)
    original_path = root / (ID + '-state.json')
    state = ledger.read(original_path)
    report_path = attempt / 'measurements/full12/result.json'
    report = ledger.read(report_path)
    require(not (attempt / 'seal.json').exists() and 'report' not in data,
            'Diagnostic must remain unsealed and unranked')
    require(state['best'] == BEST and state['cleanup']['complete'] and
            state['controller_sha256'] == CONTROLLER, 'Original diagnostic state identity changed')
    require(ledger.digest(root / 'post_phase4_profile.py') == CONTROLLER,
            'Original profile controller changed')
    require(ledger.digest(root / 'source/tools/optimization/bench_full12.py') == BENCH,
            'Recovery verification driver changed')
    require(ledger.digest(REFERENCE) == REFERENCE_SHA and ledger.digest(EXTRACTOR) == EXTRACTOR_SHA,
            'Frozen scalar reference/extractor changed')
    for record in (state, report, ordinary):
        require(record['library_sha256'] == LIBRARY and record['source_manifest_sha256'] == SOURCE,
                'Source/library identity changed')
        require(record['configuration'] == state['configuration'], 'Retained configuration changed')
    require(report['propagator_sha256'] == EXPECTED and report['measurements_complete'] and
            report['complete'] and report['timing_scope'] == 'profile_full12_api',
            'Original diagnostic measurement contract changed')
    key = report['comparison_key']
    require(key['allocation'] == state['allocation'] == 'mg-opt-20261103-worker5' and
            key['host'] == state['host'] == 'cn19483' and
            key['prepared_gauge_manifest_sha256'] == '126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834' and
            key['input_sha256'] == config['input_sha256'],
            'Original host/allocation/canonical gauge contract changed')
    if check_host:
        require(platform.node() == state['host'] and os.environ.get('LQCD_OPT_ALLOCATION') == state['allocation'],
                'Recovery must run in the same worker5 allocation and host')
        require(os.environ.get('LQCD_OPT_TASK_ID'), 'Owned worker task tag required')
        require(float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH', '0')) - time.time() >= 720,
                'Insufficient bounded worker allocation time')
    stages = data['stages']
    require(stages['benchmark']['status'] == 'passed' and stages['benchmark']['cleanup']['complete'],
            'Benchmark incomplete or still owns processes')
    failed = stages['independent']
    require(failed['status'] == 'failed' and failed['cleanup']['complete'] and
            failed['log_sha256'] == ledger.digest(attempt / failed['log']),
            'Original failed precision evidence changed')
    require('expected ' + EXPECTED + ' actual f2683361d06ec92878d9d94e69635ddced9e97f7b99105a83b9046f5e687a019'
            in (attempt / failed['log']).read_text(), 'Expected original failure missing')
    evidence = {}
    for number, task in [('060', '060-hash-057-visibility'), ('061', '061-hash-057-crosscpu')]:
        status_path = root / 'queue5' / (task + '.status.json')
        status = ledger.read(status_path)
        require(status['status'] == 'passed' and status['returncode'] == 0 and
                status['cleanup']['complete'] and status['host'] == state['host'],
                'Hash diagnostic task did not pass with cleanup')
        directory = root / ('hash-diagnostic' + number + '-057')
        result = ledger.read(directory / 'result.json')
        require(result['complete'] and result['passed'], 'Hash diagnostic result incomplete')
        if number == '060':
            require(result['expected_sha256'] == EXPECTED and result['original'] == str(report_path.with_name('propagator.npy')) and
                    result['original_unchanged_metadata'] and result['snapshot_matches_first_read'] and
                    result['original_rounds'] == 2 and result['snapshot_preserved'] and
                    result['expected_sha_changed'] is False and result['solver_executed'] is False,
                    '060 retained diagnosis contract changed')
        else:
            require(result['cpus'] == [0, 304] and result['original_before'] == result['original_after'] and
                    result['snapshot_before'] == result['snapshot_after'] and
                    result['original_path'] == str(report_path.with_name('propagator.npy')),
                    '061 pinned diagnosis identity changed')
        for name in result['rows']:
            require(Path(name).name == name and not (directory / name).is_symlink(), 'Unsafe diagnostic row')
            row = ledger.read(directory / name)
            require(row['matches_original_expected'] and row['fd_metadata_stable'] and
                    row['all_same_byte_hashes_agree'] and row['all_three_whole_digests_agree'] and
                    row['expected_sha256'] == row['openssl_sha256'] == row['portable_same_bytes_sha256'] ==
                    row['gnu_separate_read_sha256'] == EXPECTED, 'Diagnostic row hash agreement missing')
            evidence[str(directory / name)] = ledger.digest(directory / name)
        evidence[str(directory / 'result.json')] = ledger.digest(directory / 'result.json')
        evidence[str(status_path)] = ledger.digest(status_path)
    return config, best, ordinary, summary, data, state, report, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only metadata and frozen-source preflight, no payload/solver')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'source/tools/optimization'))
    ledger = importlib.import_module('campaign')
    config, best, ordinary, summary, data, original, report, evidence = preconditions(ROOT, ledger, not args.check)
    if args.check:
        print('RECOVERY_PREFLIGHT_PASSED ' + json.dumps(dict(best=BEST, diagnostic=ID, evidence_files=len(evidence))))
        return
    attempt = ROOT / 'campaign/attempts' / ID
    run = attempt / 'measurements/full12'
    output = ROOT / (ID + '-recovered-state.json')
    progress = ROOT / (ID + '-precision-retry1-progress.json')
    require(not output.exists() and not progress.exists(), 'Recovery already registered; inspect retained state; never automatically rerun')
    require('independent-retry1' not in data['stages'] and not (run / 'independent-retry1').exists(),
            'Fresh explicit verification directory/stage required')
    baseline_sha = ordinary['verification']['reference_propagator_sha256']
    require(report['reference_propagator'] == ordinary['reference_propagator'] and
            ledger.digest(Path(report['reference_propagator'])) == baseline_sha, 'Frozen solution reference changed')
    original_state_sha = ledger.digest(ROOT / (ID + '-state.json'))
    frozen_failed = deepcopy(data['stages']['independent'])
    frozen_benchmark = deepcopy(data['stages']['benchmark'])
    initial_report = deepcopy(report)
    state = dict(complete=False, status='running', reason=REASON,
                 original_state_sha256=original_state_sha, original_failed_stage=frozen_failed,
                 diagnostic_evidence_sha256=evidence, recovery_driver_sha256=ledger.digest(Path(__file__)),
                 original_report_sha256=ledger.digest(run / 'result.json'), best_pointer_sha256=ledger.digest(ROOT / 'campaign/best.json'))
    ledger.atomic(progress, state)
    state['before_fd_hash'] = fd_hash(run / 'propagator.npy', EXPECTED)
    ledger.atomic(progress, state)
    command = dict(argv=[sys.executable, str(ROOT / 'source/tools/optimization/bench_full12.py'),
                        '--verify', str(run), '--verification-output', 'independent-retry1',
                        '--reference', str(REFERENCE), '--extractor', str(EXTRACTOR)],
                   cwd=str(attempt / 'build'), env=dict(OMP_NUM_THREADS='4', OMP_PLACES='cores', OMP_PROC_BIND='close'),
                   timeout_seconds=600)
    stage = ledger.run_stage(ROOT / 'campaign', ID, 'independent-retry1', command)
    state['new_stage'] = stage
    ledger.atomic(progress, state)
    require(stage['status'] == 'passed' and stage['cleanup']['complete'], 'Retry failed; retained as failure, no recovery acceptance')
    state['after_fd_hash'] = fd_hash(run / 'propagator.npy', EXPECTED)
    require(state['before_fd_hash']['before'] == state['after_fd_hash']['after'], 'Payload metadata changed during verification')
    current = ledger.read(attempt / 'attempt.json')
    require(current['stages']['independent'] == frozen_failed and current['stages']['benchmark'] == frozen_benchmark,
            'Original failed/benchmark stage was changed')
    require(ledger.digest(attempt / frozen_failed['log']) == frozen_failed['log_sha256'] and
            ledger.digest(ROOT / (ID + '-state.json')) == original_state_sha and
            ledger.digest(ROOT / 'campaign/best.json') == state['best_pointer_sha256'],
            'Original state/log or best pointer changed')
    measured = ledger.read(run / 'result.json')
    require({k:v for k,v in measured.items() if k != 'verification'} ==
            {k:v for k,v in initial_report.items() if k != 'verification'}, 'Precision retry changed measurement fields')
    verification = measured['verification']
    require(verification['complete'] and verification['passed'] and verification['columns'] == 12 and
            verification['evidence_relative_path'] == 'independent-retry1/verification.json' and
            verification['propagator_sha256'] == EXPECTED and verification['reference_sha256'] == REFERENCE_SHA and
            verification['extractor_sha256'] == EXTRACTOR_SHA and verification['reference_propagator_sha256'] == baseline_sha,
            'Full12 frozen precision identities missing')
    residual = verification['max_true_residual']
    errors = verification['solution_relative_errors']
    require(math.isfinite(residual) and 0 <= residual <= 1e-8 and len(errors) == 12 and
            all(math.isfinite(v) and 0 <= v <= 1e-6 for v in errors), 'Strict scalar/reference precision failed')
    independent = ledger.read(run / verification['evidence_relative_path'])
    require(independent['complete'] and len(independent['columns']) == 12 and
            {(v['source_spin'],v['source_color']) for v in independent['columns']} ==
            {(s,c) for s in range(4) for c in range(3)} and
            all(math.isfinite(v['residual']) and 0 <= v['residual'] <= 1e-8 for v in independent['columns']) and
            ledger.digest(run / verification['evidence_relative_path']) == verification['evidence_sha256'],
            'Independent evidence must contain all twelve unique columns')
    sys.path.insert(0, str(ROOT))
    budget = importlib.import_module('post_phase4_profile').profile_budget(
        (attempt / frozen_benchmark['log']).read_text(), measured, summary,
        config['minimum_gain'], normal_comparison_key=ordinary['comparison_key'])
    require(budget['complete'], 'Actual profile grouping incomplete')
    preconditions(ROOT, ledger, False)
    state.update(complete=True, status='passed', verification=verification, budget=budget,
                 report=str(run / 'result.json'), report_sha256=ledger.digest(run / 'result.json'),
                 failed_hash_log_sha256=frozen_failed['log_sha256'],
                 scope='Recovered independent precision for an unranked existing diagnostic; never an ordinary benchmark')
    recovered = dict(original, **state)
    ledger.atomic(output, recovered)
    ledger.atomic(progress, state)
    ledger.conclude(ROOT / 'campaign', ID, 'inconclusive',
        'Diagnostic-only: explicit retry1 passed all12 scalar/reference gates after retained unexplained hash failure. '
        'Profile may guide experiments; no ingest/promotion and no ordinary performance claim.',
        [str(output), str(run / verification['evidence_relative_path']), str(attempt / frozen_failed['log'])])
    print('PROFILE057_PRECISION_RECOVERED ' + json.dumps(dict(state=str(output), report_sha256=state['report_sha256'],
          max_true_residual=residual, solution_relative_error=max(errors), ranked=False)), flush=True)


if __name__ == '__main__':
    main()
