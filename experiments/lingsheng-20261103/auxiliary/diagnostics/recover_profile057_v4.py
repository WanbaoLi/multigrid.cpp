#!/usr/bin/env python3
"""Explicit raw-reader precision retry4; keep all previous failed records."""
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
REASON = ('Explicit protocol4 retry: pinned scalar-helper AST replaces only sha body; all other AST nodes, '
          'physics/thresholds/scalar C++/extractor remain unchanged. The prior086 failed report/evidence '
          'is preserved verbatim and never accepted. Parent/helper checks use raw os.open(O_RDONLY) '
          'and os.pread use explicit offsets and min(block,remaining), reject oversized/empty reads, '
          'require exact total byte count and an empty one-byte EOF probe, with stable FD/path identity '
          'and independent OpenSSL/software SHA256 on same immutable bytes. Original expected hashes '
          'and strict12-column scalar1e-8/gold1e-6 thresholds remain. Prior buffered8MiB mismatches '
          'and080 overlong received view remain retained; no claim of an operating-system cause/fix. '
          'No performance rerun or ranking.')
GOLD = '31d5cb29eeaa2714b4db003424da1215668d369288a6706bff03a1e0fb2e71cd'
STAGE = 'independent-raw-scalar-audited-retry4'
HELPER_SHA='bc441c56af7ffe65781816c8d18427578e8097f0b35168349a27629655fa2074'
PRIOR_REPORT_SHA='3b207cb9a7fbc78293fe4b9eea0d29ff976b388d0b9c7d7fca704023212a3b60'


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


def reviewed_reader_proof(root,ledger,audit,path,expected_sha,old,status_path=None):
    """Explicit SHA argument binds the exact085 proof reviewed before deployment."""
    require(path.resolve()==root/'read-contract085-057/result.json' and not path.is_symlink(),
            'Reviewed085 result must be the exact diagnostic artifact')
    require(audit.read_dual(path,expected_sha)['passed'],'Reviewed reader-proof SHA changed')
    proof=ledger.read(path)
    require(proof['complete'] and proof['diagnostic_only'] and proof['numerical_acceptance'] is False and
            proof['solver_executed'] is False and proof['source_modified'] is False and
            proof['original_before']==proof['original_after'],'085 scope or original metadata changed')
    prefix=proof['prefixes'];require(prefix['all_match_expected'],'085 logical-prefix digest mismatch')
    for name in ['original','badview']:
        row=prefix[name]
        require(row['complete'] and row['read_bytes']==2038431872 and
                row['openssl']==row['software']==old.EXPECTED and row['fd_before']==row['fd_after'],
                '085 explicit-offset original/bad-view prefix proof incomplete')
    require(prefix['original']['path']==str(root/'campaign/attempts'/old.ID/'measurements/full12/propagator.npy') and
            prefix['original']['fd_before']==proof['original_before'],'085 original path/identity is not the retained057 file')
    for name in ['gnu_original','gnu_badview']:
        row=prefix[name]
        require(row['head_returncode']==row['sha_returncode']==0 and row['sha256']==old.EXPECTED and
                row['requested_prefix_bytes']==2038431872,'085 independent GNU prefix proof failed')
    tail=proof['exact_tail_eof'];raw=proof.get('raw_eof',{})
    require(tail['tail_requested']==tail['tail_returned']==128 and tail['eof_requested']==1 and
            tail['eof_offset']==2038431872 and tail['eof_returned']==0 and tail['fd_before']==tail['fd_after'],
            '085 exact tail/EOF contract failed')
    require(raw.get('complete') and raw['read_bytes']==2038431872 and raw['openssl']==raw['software']==old.EXPECTED and
            raw['fd_before']==raw['fd_after']==proof['original_before'] and
            raw['last_two_reads'][-1]['returned']==0,'085 unbuffered EOF proof incomplete')
    status_path=status_path or root/'queue5/085-read-contract.status.json'
    require(status_path.parent in [root/'queue5',root/'queue6'] and status_path.name=='085-read-contract.status.json' and
            not status_path.is_symlink(),'Unexpected085 worker status artifact')
    require(status_path.is_file(),'085 queue cleanup status required')
    status=ledger.read(status_path)
    require(status['status'] in ['passed','failed'] and status['host']=='cn19483' and status['cleanup']['complete'],
            '085 task incomplete or cleanup uncertain')
    return {str(path):expected_sha,str(status_path):audit.read_dual(status_path)['openssl_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--reader-proof',type=Path,required=True)
    parser.add_argument('--reader-proof-sha',required=True)
    parser.add_argument('--reader-task-status',type=Path)
    parser.add_argument('--allocation',default='mg-opt-20261103-worker5')
    parser.add_argument('--validation-retry-reason',help='Required explicit changed-resource justification when allocation differs')
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / 'source/tools/optimization'))
    sys.path.insert(0, str(ROOT))
    ledger = importlib.import_module('campaign')
    old = importlib.import_module('recover_profile057')
    audit = importlib.import_module('file_integrity')
    raw_wrapper = importlib.import_module('raw_benchmark_v4')
    config, best, normal, summary, data, original, measured, evidence = old.preconditions(ROOT, ledger, False)
    base_evidence = deepcopy(evidence)
    extra_evidence = dependencies(ROOT, ledger, old)
    evidence.update(extra_evidence)
    reader_evidence=reviewed_reader_proof(ROOT,ledger,audit,args.reader_proof,args.reader_proof_sha,old,args.reader_task_status)
    evidence.update(reader_evidence)
    prior_audited=data['stages']['independent-audited-retry2']
    require(prior_audited['status']=='failed' and prior_audited['cleanup']['complete'] and
            audit.read_dual(ROOT/'campaign/attempts'/old.ID/prior_audited['log'],prior_audited['log_sha256'])['passed'],
            '080 failed stage/log changed')
    failed_audit_path=ROOT/'campaign/attempts'/old.ID/'measurements/full12/sha-audit-retry2/hash-000.json'
    failed_audit=ledger.read(failed_audit_path)
    require(failed_audit['passed'] is False and failed_audit['read_bytes']==2039480320 and
            failed_audit['required_bytes']==2038431872 and failed_audit['expected_sha256']==old.EXPECTED and
            failed_audit['openssl_sha256']==failed_audit['software_sha256']==
            '72c89829160a9f338c57a731b2d5ff7512f10a43123200925f7977742655f80f' and
            failed_audit['initial']==failed_audit['fd_before']==failed_audit['fd_after']==failed_audit['path_after'],
            '080 failed read-contract evidence changed')
    evidence[str(failed_audit_path)]=audit.read_dual(failed_audit_path)['openssl_sha256']
    require(normal['verification']['reference_propagator_sha256'] == GOLD and
            normal['reference_propagator'] == measured['reference_propagator'], 'Frozen gold reference changed')
    require(measured['verification'].get('propagator_sha256') == 'baa183b8a54b2bb5a145f5677e3f3c6cc1b5fd32e80acbae8dee60162de24712', 'Explicit prior086 failed-helper evidence identity required')
    run_prior=ROOT/'campaign/attempts'/old.ID/'measurements/full12'
    audit.read_dual(run_prior/'result.json',PRIOR_REPORT_SHA)
    audit.read_dual(ROOT/'source/benchmarks/runtime/verify_fixture_propagator.py',HELPER_SHA)
    frozen3={'raw_benchmark.py':'3fc83559b17ad33ac940d6cb193756f8f56c385096f55938a9fbd6ac1f462237',
             'raw_controller.py':'6e7b377a165cf5d6f35fc6e12346aa6f2e201bcd2092493b2bfcb99a279cc08b',
             'recover_profile057_v3.py':'32b8eaa1940bef20db7850858e52aae3f1f02ee0c3e09d921a2bd389b73aa0cd'}
    for name,expected_sha in frozen3.items():
        audit.read_dual(ROOT/name,expected_sha);evidence[str(ROOT/name)]=expected_sha
    prior3=data['stages']['independent-raw-audited-retry3']
    require(prior3['status']=='failed' and prior3['cleanup']['complete'], '086 prior failed stage must remain failed/cleaned')
    prior3log=ROOT/'campaign/attempts'/old.ID/prior3['log']
    evidence[str(prior3log)]=audit.read_dual(prior3log,prior3['log_sha256'])['openssl_sha256']
    audit.known_vectors()
    raw_wrapper.resource_gate(2038431872, 2200 * 1024**2)
    if args.check:
        print('AUDITED_RECOVERY_PREFLIGHT_PASSED ' + json.dumps(dict(evidence_files=len(evidence), method=audit.METHOD)),flush=True)
        return
    require(args.allocation==original['allocation'] or args.validation_retry_reason,
            'Changed validation allocation requires an explicit retry reason')
    require(os.environ.get('LQCD_OPT_ALLOCATION') == args.allocation and
            __import__('platform').node() == original['host'] and os.environ.get('LQCD_OPT_TASK_ID'),
            'Same owned worker5 allocation required')
    require(float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0')) - time.time() >= 1000,
            'Need >=1000 seconds remaining before audited precision retry')
    attempt = ROOT / 'campaign/attempts' / old.ID
    run = attempt / 'measurements/full12'
    output = ROOT / (old.ID + '-recovered-state.json')
    progress = ROOT / (old.ID + '-precision-raw-audited-retry4-progress.json')
    require(not output.exists() and not progress.exists() and STAGE not in data['stages'] and
            not (run / 'independent-retry4').exists() and not (run / 'sha-raw-audit-retry4').exists(),
            'Fresh retry4 protocol required; retained state is never automatically retried')
    frozen_stages = deepcopy(data['stages'])
    original_sha = ledger.digest(ROOT / (old.ID + '-state.json'))
    original_retry1_progress_sha = ledger.digest(ROOT / (old.ID + '-precision-retry1-progress.json'))
    original_retry2_progress_sha = audit.read_dual(ROOT/(old.ID+'-precision-audited-retry2-progress.json'))['openssl_sha256']
    best_sha = ledger.digest(ROOT / 'campaign/best.json')
    identity = dict(original_state_sha256=original_sha, original_retry1_progress_sha256=original_retry1_progress_sha,
                    original_retry2_progress_sha256=original_retry2_progress_sha,
                    original_report_sha256=ledger.digest(run / 'result.json'), best_pointer_sha256=best_sha,
                    recovery_driver_sha256=ledger.digest(Path(__file__)), checksum_wrapper_sha256=ledger.digest(ROOT / 'raw_benchmark_v4.py'),
                    raw_reader_sha256=audit.read_dual(ROOT/'file_integrity.py')['openssl_sha256'],
                    helper_sha256=HELPER_SHA,helper_wrapper_sha256=audit.read_dual(ROOT/'raw_scalar_helper.py')['openssl_sha256'],
                    prior086_report_sha256=PRIOR_REPORT_SHA,
                    validation_allocation=args.allocation,validation_retry_reason=args.validation_retry_reason,
                    diagnostic_evidence_sha256=evidence, explicit_retry_reason=REASON)
    progress_state = dict(identity, complete=False, status='running', started=ledger.now())
    ledger.atomic(progress, progress_state)
    command = dict(argv=[sys.executable, '-u', str(ROOT / 'raw_benchmark_v4.py'),
        '--benchmark', str(ROOT / 'source/tools/optimization/bench_full12.py'), '--expected-benchmark-sha', old.BENCH,
        '--expected-wrapper-sha',identity['checksum_wrapper_sha256'],'--expected-reader-sha',identity['raw_reader_sha256'],
        '--expected-helper-sha',HELPER_SHA,'--helper-wrapper',str(ROOT/'raw_scalar_helper.py'),
        '--expected-helper-wrapper-sha',identity['helper_wrapper_sha256'],'--retry-existing-verification-sha',PRIOR_REPORT_SHA,
        '--audit-output', str(run / 'sha-raw-audit-retry4'), '--expected-propagator-sha', old.EXPECTED,
        '--expected-gold-sha', GOLD, '--verify', str(run), '--verification-output', 'independent-retry4',
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
                validation['evidence_relative_path'] == 'independent-retry4/verification.json' and
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
        require(audit.read_dual(run / validation['evidence_relative_path'])['openssl_sha256'] == validation['evidence_sha256'],
                'Independent scalar evidence SHA changed')
        checksum = validation['checksum_audit']
        require(checksum.get('protocol_version')==4 and checksum.get('complete') and checksum.get('passed') and
                checksum.get('status')=='passed' and checksum['helper_sha256']==HELPER_SHA and
                checksum['helper_wrapper_sha256']==identity['helper_wrapper_sha256'], 'Terminal protocol4/helper identity required')
        manifest_path = run / 'sha-raw-audit-retry4/manifest.json'
        require(checksum['wrapper_sha256'] == identity['checksum_wrapper_sha256'] and
                checksum['raw_reader_sha256']==identity['raw_reader_sha256'] and
                checksum['benchmark_sha256'] == old.BENCH and checksum['method'] == audit.METHOD and
                checksum['manifest_path'] == str(manifest_path) and
                audit.read_dual(manifest_path)['openssl_sha256'] == checksum['manifest_sha256'], 'Audit provenance changed')
        manifest = ledger.read(manifest_path)
        require(manifest['complete'] and manifest['method'] == audit.METHOD and manifest['block_bytes'] == 4 * 1024**2,
                'Whole audit incomplete')
        protocol_path=manifest_path.parent/'protocol.json'
        require(audit.read_dual(protocol_path)['openssl_sha256']==checksum['protocol_sha256'],
                'Raw protocol evidence SHA changed')
        protocol=ledger.read(protocol_path)
        require(protocol['complete'] and protocol['method']==audit.METHOD and
                protocol['wrapper_sha256']==checksum['wrapper_sha256'] and
                protocol['raw_reader_sha256']==checksum['raw_reader_sha256'] and
                protocol['benchmark_sha256']==old.BENCH and protocol['identity']==checksum['independent_modules'] and
                protocol['identity']['openssl_module']=='_hashlib' and
                protocol['identity']['software_module'] in ['_sha256','_sha2'], 'Raw protocol identity changed')
        raw_wrapper.check_audit_provenance(run,after,lambda path:audit.read_dual(path)['openssl_sha256'])
        require(audit.read_dual(manifest_path.parent/'prior-result.json',PRIOR_REPORT_SHA)['passed'],
                'Original086 failed report snapshot changed')
        require(len({v['path'] for v in manifest['rows']})==len(manifest['rows']),
                'Duplicate audit records cannot stand in for PRE/POST checks')
        payload_checks = {}
        for item in manifest['rows']:
            path = manifest_path.parent / item['path']
            require(path.name == item['path'] and not path.is_symlink() and
                    audit.read_dual(path)['openssl_sha256'] == item['sha256'], 'Unsafe or changed checksum evidence')
            row = ledger.read(path)
            require(row['complete'] and row['passed'] and row['metadata_stable'] and row['byte_count_exact'] and
                    row['eof_probe_bytes']==0 and row['original_open_mode']=='O_RDONLY' and row['same_immutable_bytes'] and
                    row['openssl_sha256'] == row['software_sha256'] and row['read_bytes'] == row['fd_before']['bytes'],
                    'Checksum FD or same-byte agreement missing')
            payload_checks.setdefault(row['path'], []).append(row)
        for path, expected in [(run / 'propagator.npy',old.EXPECTED), (Path(after['reference_propagator']),GOLD)]:
            rows = payload_checks.get(str(path), [])
            require(len(rows) >= 2 and all(v['read_bytes'] == 2038431872 and
                    v['expected_sha256'] == v['openssl_sha256'] == expected for v in rows) and
                    all(v['fd_before'] == rows[0]['fd_before'] == v['path_after'] for v in rows),
                    'Both full original/gold PRE+POST same-byte checks and unchanged metadata required')
            if path==run/'propagator.npy':
                proof_before=ledger.read(args.reader_proof)['original_before']
                require(rows[0]['fd_before']=={k:proof_before[k] for k in rows[0]['fd_before']},
                        'Retry4 original FD identity differs from the reviewed085 proof')
        current = ledger.read(attempt / 'attempt.json')
        require(all(current['stages'].get(k) == v for k,v in frozen_stages.items()) and
                ledger.digest(ROOT / (old.ID + '-state.json')) == original_sha and
                ledger.digest(ROOT / (old.ID + '-precision-retry1-progress.json')) == original_retry1_progress_sha and
                audit.read_dual(ROOT/(old.ID+'-precision-audited-retry2-progress.json'))['openssl_sha256']==original_retry2_progress_sha and
                ledger.digest(ROOT / 'campaign/best.json') == best_sha and
                ledger.digest(Path(__file__)) == identity['recovery_driver_sha256'] and
                ledger.digest(ROOT / 'raw_benchmark_v4.py') == identity['checksum_wrapper_sha256'] and
                audit.read_dual(ROOT/'file_integrity.py')['openssl_sha256']==identity['raw_reader_sha256'],
                'Old evidence, recovery tools or best pointer changed')
        require(old.preconditions(ROOT, ledger, False)[-1] == base_evidence, '060/061 evidence changed')
        require(dependencies(ROOT, ledger, old) == extra_evidence, 'Diagnostic dependencies changed')
        require(reviewed_reader_proof(ROOT,ledger,audit,args.reader_proof,args.reader_proof_sha,old,args.reader_task_status)==reader_evidence,
                'Reviewed085 evidence changed')
        profile = importlib.import_module('post_phase4_profile')
        budget = profile.profile_budget((attempt / frozen_stages['benchmark']['log']).read_text(), after, summary,
                                        config['minimum_gain'], normal_comparison_key=normal['comparison_key'])
        require(budget['complete'], 'Profile grouping incomplete')
        record = dict(original, **identity, complete=True, status='passed', budget=budget, verification=validation,
                      report=str(run/'result.json'), report_sha256=ledger.digest(run/'result.json'),
                      scope='Unranked diagnostic precision recovery only; no ordinary benchmark or ranking',
                      recovery_stage=stage, failed_hash_log_sha256=frozen_stages['independent']['log_sha256'],
                      failed_retry1_log_sha256=frozen_stages['independent-retry1']['log_sha256'])
        record['failed_audited_retry2_log_sha256']=frozen_stages['independent-audited-retry2']['log_sha256']
        record['failed_raw_retry3_log_sha256']=frozen_stages['independent-raw-audited-retry3']['log_sha256']
        ledger.atomic(output, record)
        ledger.conclude(ROOT/'campaign', old.ID, 'inconclusive',
            'Diagnostic-only raw-reader retry4 passed unchanged all12 precision and original SHA/count/EOF gates. '
            'Prior buffered-read discrepancies remain retained. No ingest/promotion or ordinary performance claim.',
            [str(output), str(manifest_path), str(run/validation['evidence_relative_path'])])
        progress_state.update(complete=True, status='passed', recovered_state=str(output), report_sha256=record['report_sha256'])
        print('PROFILE057_RAW_AUDITED_PRECISION_RECOVERED ' + json.dumps(dict(state=str(output),
            max_true_residual=validation['max_true_residual'], solution_relative_error=max(errors), ranked=False)),flush=True)
    except BaseException as exc:
        progress_state.update(complete=False, status='failed', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        progress_state['ended'] = ledger.now()
        ledger.atomic(progress, progress_state)


if __name__ == '__main__':
    main()
