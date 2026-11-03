#!/usr/bin/env python3
"""Explicit precision retry2 with stronger same-byte dual-implementation SHA256."""
import argparse
from copy import deepcopy
import importlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
REASON = ('Explicit audited precision retry2: all saved-artifact, reference and evidence SHA256 '
          'checks use OpenSSL plus independent CPython software on identical immutable 4MiB '
          'chunks, stable FD/path metadata and exact byte counts. This strengthens checksum '
          'evidence while retaining original expectations and strict12-column scalar1e-8/gold1e-6 '
          'thresholds. Original8MiB CLI mismatches remain unexplained, not classified as a '
          'hardware, filesystem or crypto-engine defect. No performance rerun or ranking.')
GOLD = '31d5cb29eeaa2714b4db003424da1215668d369288a6706bff03a1e0fb2e71cd'
STAGE = 'independent-audited-retry2'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def dependencies(root, ledger, old):
    require(ledger.digest(root / 'recover_profile057.py') ==
            '1cfea9042c7063000f57ef82fbc724f52ff460b758aad0a984111a43f31e8401',
            'Original recovery driver changed')
    evidence = {}
    state060 = ledger.read(root / 'hash-diagnostic060-057/result.json')['original_stat']
    for number, name in [('075','075-hash-minimal-repro'),('076','076-hash-exact-cli')]:
        task = root / 'queue5' / (name + '.status.json')
        row = ledger.read(task)
        require(row['status'] == 'passed' and row['returncode'] == 0 and row['cleanup']['complete'] and
                row['host'] == 'cn19483', 'New checksum diagnosis did not pass with cleanup')
        directory = root / ('hash-diagnostic' + number + '-057')
        result = ledger.read(directory / 'result.json')
        require(result['complete'] and result['diagnostic_only'] and result['numerical_acceptance'] is False,
                'Diagnosis completeness/scope changed')
        if number == '075':
            require(not result['any_expected_mismatch'] and not result['any_same_bytes_implementation_disagreement'] and
                    result['original_before']['path_stat'] == result['original_after']['path_stat'] == state060 and
                    len(result['rows']) == 4, '075 original bytes or diagnostic scope changed')
            for case in result['rows']:
                require(case['first'] == case['retained'] == case['same_bytes_software'] == old.EXPECTED and
                        case['same_bytes_agree'] and case['all_match_expected'], '075 digest agreement missing')
                value = ledger.read(directory / case['case'] / 'result.json')
                require(value['complete'] and value['all_digests_match_expected'] and
                        value['read_bytes'] == 2038431872 and value['fd_evidence']['before']['stat'] ==
                        value['fd_evidence']['after']['stat'] == state060 and
                        value['bench_file_software_sha256'] == old.BENCH, '075 detailed retained-byte evidence changed')
                evidence[str(directory / case['case'] / 'result.json')] = ledger.digest(directory / case['case'] / 'result.json')
        else:
            require(not result['any_PREhash_reproduced'] and result['original_after'] == state060 and
                    len(result['results']) == 2, '076 diagnostic result changed')
            for case in result['results']:
                require(case['verdict'] == 'saved_hashes_passed_then_reference_sentinel' and case['returncode'] != 0 and
                        case['original_after'] == state060 and case['output_still_absent'], '076 did not stop at negative-control sentinel')
                log = directory / (case['case'] + '.log')
                require(ledger.digest(log) == case['log_sha256'] and
                        'FileNotFoundError' in log.read_text() and '/multigrix' in log.read_text(), '076 expected sentinel log changed')
                evidence[str(log)] = ledger.digest(log)
        evidence[str(directory / 'result.json')] = ledger.digest(directory / 'result.json')
        evidence[str(task)] = ledger.digest(task)
    a = root / 'campaign/attempts' / old.ID
    data = ledger.read(a / 'attempt.json')
    first = data['stages']['independent-retry1']
    require(first['status'] == 'failed' and first['cleanup']['complete'] and
            ledger.digest(a / first['log']) == first['log_sha256'] and
            'expected ' + old.EXPECTED + ' actual f2683361d06ec92878d9d94e69635ddced9e97f7b99105a83b9046f5e687a019'
            in (a / first['log']).read_text(), 'Retry1 failed evidence changed')
    benchmark = data['stages']['benchmark']
    require(ledger.digest(a / benchmark['log']) == benchmark['log_sha256'], 'Original benchmark log changed')
    evidence[str(a / first['log'])] = first['log_sha256']
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / 'source/tools/optimization'))
    sys.path.insert(0, str(ROOT))
    ledger = importlib.import_module('campaign')
    old = importlib.import_module('recover_profile057')
    audit = importlib.import_module('audited_verify')
    config, best, normal, summary, data, original, measured, evidence = old.preconditions(ROOT, ledger, False)
    base_evidence = deepcopy(evidence)
    extra_evidence = dependencies(ROOT, ledger, old)
    evidence.update(extra_evidence)
    require(normal['verification']['reference_propagator_sha256'] == GOLD and
            normal['reference_propagator'] == measured['reference_propagator'], 'Frozen gold reference changed')
    require(not measured['verification'].get('complete'), 'A new protocol cannot silently reuse already complete verification')
    audit.vectors()
    audit.resource_gate(2038431872, 2200 * 1024**2)
    if args.check:
        print('AUDITED_RECOVERY_PREFLIGHT_PASSED ' + json.dumps(dict(evidence_files=len(evidence), method=audit.METHOD)),flush=True)
        return
    require(os.environ.get('LQCD_OPT_ALLOCATION') == original['allocation'] and
            __import__('platform').node() == original['host'] and os.environ.get('LQCD_OPT_TASK_ID'),
            'Same owned worker5 allocation required')
    require(float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0')) - time.time() >= 1000,
            'Need >=1000 seconds remaining before audited precision retry')
    attempt = ROOT / 'campaign/attempts' / old.ID
    run = attempt / 'measurements/full12'
    output = ROOT / (old.ID + '-recovered-state.json')
    progress = ROOT / (old.ID + '-precision-audited-retry2-progress.json')
    require(not output.exists() and not progress.exists() and STAGE not in data['stages'] and
            not (run / 'independent-retry2').exists() and not (run / 'sha-audit-retry2').exists(),
            'Fresh retry2 protocol required; retained state is never automatically retried')
    frozen_stages = deepcopy(data['stages'])
    original_sha = ledger.digest(ROOT / (old.ID + '-state.json'))
    original_retry1_progress_sha = ledger.digest(ROOT / (old.ID + '-precision-retry1-progress.json'))
    best_sha = ledger.digest(ROOT / 'campaign/best.json')
    identity = dict(original_state_sha256=original_sha, original_retry1_progress_sha256=original_retry1_progress_sha,
                    original_report_sha256=ledger.digest(run / 'result.json'), best_pointer_sha256=best_sha,
                    recovery_driver_sha256=ledger.digest(Path(__file__)), checksum_wrapper_sha256=ledger.digest(ROOT / 'audited_verify.py'),
                    diagnostic_evidence_sha256=evidence, explicit_retry_reason=REASON)
    progress_state = dict(identity, complete=False, status='running', started=ledger.now())
    ledger.atomic(progress, progress_state)
    command = dict(argv=[sys.executable, '-u', str(ROOT / 'audited_verify.py'),
        '--benchmark', str(ROOT / 'source/tools/optimization/bench_full12.py'), '--expected-benchmark-sha', old.BENCH,
        '--audit-output', str(run / 'sha-audit-retry2'), '--expected-propagator-sha', old.EXPECTED,
        '--expected-gold-sha', GOLD, '--verify', str(run), '--verification-output', 'independent-retry2',
        '--reference', str(old.REFERENCE), '--extractor', str(old.EXTRACTOR)], cwd=str(attempt / 'build'),
        env=dict(OMP_NUM_THREADS='4', OMP_PLACES='cores', OMP_PROC_BIND='close'), timeout_seconds=900)
    try:
        stage = ledger.run_stage(ROOT / 'campaign', old.ID, STAGE, command)
        progress_state['stage'] = stage
        require(stage['status'] == 'passed' and stage['cleanup']['complete'], 'Audited precision stage failed; no acceptance')
        after = ledger.read(run / 'result.json')
        require({k:v for k,v in measured.items() if k != 'verification'} ==
                {k:v for k,v in after.items() if k != 'verification'}, 'Original measurement fields changed')
        validation = after['verification']
        require(validation['complete'] and validation['passed'] and validation['columns'] == 12 and
                validation['evidence_relative_path'] == 'independent-retry2/verification.json' and
                validation['propagator_sha256'] == old.EXPECTED and validation['reference_propagator_sha256'] == GOLD and
                validation['reference_sha256'] == old.REFERENCE_SHA and validation['extractor_sha256'] == old.EXTRACTOR_SHA,
                'Original full12 reference identities changed')
        errors = validation['solution_relative_errors']
        require(math.isfinite(validation['max_true_residual']) and 0 <= validation['max_true_residual'] <= 1e-8 and
                len(errors) == 12 and all(math.isfinite(v) and 0 <= v <= 1e-6 for v in errors), 'Strict precision gates failed')
        independent = ledger.read(run / validation['evidence_relative_path'])
        require(independent['complete'] and independent['propagator_sha256'] == old.EXPECTED and
                independent['reference_sha256'] == old.REFERENCE_SHA and len(independent['columns']) == 12 and
                {(v['source_spin'],v['source_color']) for v in independent['columns']} == {(s,c) for s in range(4) for c in range(3)} and
                all(math.isfinite(v['residual']) and 0 <= v['residual'] <= 1e-8 for v in independent['columns']),
                'All twelve unique independent scalar columns required')
        require(audit.bytes_sha((run / validation['evidence_relative_path']).read_bytes()) == validation['evidence_sha256'],
                'Independent scalar evidence SHA changed')
        checksum = validation['checksum_audit']
        manifest_path = run / 'sha-audit-retry2/manifest.json'
        require(checksum['wrapper_sha256'] == identity['checksum_wrapper_sha256'] and
                checksum['benchmark_sha256'] == old.BENCH and checksum['method'] == audit.METHOD and
                checksum['manifest_path'] == str(manifest_path) and
                audit.bytes_sha(manifest_path.read_bytes()) == checksum['manifest_sha256'], 'Audit provenance changed')
        manifest = ledger.read(manifest_path)
        require(manifest['complete'] and manifest['method'] == audit.METHOD and manifest['block_bytes'] == 4 * 1024**2,
                'Whole audit incomplete')
        payload_checks = {}
        for item in manifest['rows']:
            path = manifest_path.parent / item['path']
            require(path.name == item['path'] and not path.is_symlink() and
                    audit.bytes_sha(path.read_bytes()) == item['sha256'], 'Unsafe or changed checksum evidence')
            row = ledger.read(path)
            require(row['complete'] and row['passed'] and row['metadata_stable'] and row['same_immutable_bytes'] and
                    row['openssl_sha256'] == row['software_sha256'] and row['read_bytes'] == row['fd_before']['bytes'],
                    'Checksum FD or same-byte agreement missing')
            payload_checks.setdefault(row['path'], []).append(row)
        for path, expected in [(run / 'propagator.npy',old.EXPECTED), (Path(after['reference_propagator']),GOLD)]:
            rows = payload_checks.get(str(path), [])
            require(len(rows) >= 2 and all(v['read_bytes'] == 2038431872 and
                    v['expected_sha256'] == v['openssl_sha256'] == expected for v in rows) and
                    all(v['fd_before'] == rows[0]['fd_before'] == v['path_after'] for v in rows),
                    'Both full original/gold PRE+POST same-byte checks and unchanged metadata required')
        current = ledger.read(attempt / 'attempt.json')
        require(all(current['stages'].get(k) == v for k,v in frozen_stages.items()) and
                ledger.digest(ROOT / (old.ID + '-state.json')) == original_sha and
                ledger.digest(ROOT / (old.ID + '-precision-retry1-progress.json')) == original_retry1_progress_sha and
                ledger.digest(ROOT / 'campaign/best.json') == best_sha and
                ledger.digest(Path(__file__)) == identity['recovery_driver_sha256'] and
                ledger.digest(ROOT / 'audited_verify.py') == identity['checksum_wrapper_sha256'],
                'Old evidence, recovery tools or best pointer changed')
        require(old.preconditions(ROOT, ledger, False)[-1] == base_evidence, '060/061 evidence changed')
        require(dependencies(ROOT, ledger, old) == extra_evidence, 'Diagnostic dependencies changed')
        profile = importlib.import_module('post_phase4_profile')
        budget = profile.profile_budget((attempt / frozen_stages['benchmark']['log']).read_text(), after, summary,
                                        config['minimum_gain'], normal_comparison_key=normal['comparison_key'])
        require(budget['complete'], 'Profile grouping incomplete')
        record = dict(original, **identity, complete=True, status='passed', budget=budget, verification=validation,
                      report=str(run/'result.json'), report_sha256=ledger.digest(run/'result.json'),
                      scope='Unranked diagnostic precision recovery only; no ordinary benchmark or ranking',
                      recovery_stage=stage, failed_hash_log_sha256=frozen_stages['independent']['log_sha256'],
                      failed_retry1_log_sha256=frozen_stages['independent-retry1']['log_sha256'])
        ledger.atomic(output, record)
        ledger.conclude(ROOT/'campaign', old.ID, 'inconclusive',
            'Diagnostic-only audited retry2 passed unchanged all12 precision and original SHA gates. '
            'Old8MiB discrepancies remain unexplained. No ingest/promotion or ordinary performance claim.',
            [str(output), str(manifest_path), str(run/validation['evidence_relative_path'])])
        progress_state.update(complete=True, status='passed', recovered_state=str(output), report_sha256=record['report_sha256'])
        print('PROFILE057_AUDITED_PRECISION_RECOVERED ' + json.dumps(dict(state=str(output),
            max_true_residual=validation['max_true_residual'], solution_relative_error=max(errors), ranked=False)),flush=True)
    except BaseException as exc:
        progress_state.update(complete=False, status='failed', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        progress_state['ended'] = ledger.now()
        ledger.atomic(progress, progress_state)


if __name__ == '__main__':
    main()
