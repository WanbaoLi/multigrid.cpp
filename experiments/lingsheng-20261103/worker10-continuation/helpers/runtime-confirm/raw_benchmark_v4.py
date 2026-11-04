#!/usr/bin/env python3
"""One raw-checksum adapter for frozen full12 benchmarks and independent verification.

Only bench.sha is patched. Solver/timing/sample/source contracts remain frozen.
Per-rank audit files are written outside every timed solve and frozen source tree.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from copy import deepcopy

import file_integrity as integrity


def guarded_report(initial,candidate,prior_sha,status,error=None):
    """Every nonterminal publication remains independently non-acceptable."""
    result=deepcopy(initial)
    result['verification']=dict(complete=False,passed=False,candidate_verification=deepcopy(candidate),
        checksum_audit=dict(protocol_version=4,complete=False,passed=False,status=status,
                           method=integrity.METHOD,prior_report_sha256=prior_sha))
    if error is not None:
        result['verification']['checksum_audit'].update(error_type=type(error).__name__,message=str(error))
    return result


def resource_gate(payload_bytes,retain_bytes):
    integrity.require(retain_bytes>=payload_bytes,'Full mismatch-view retention budget required')
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            integrity.require(int(line.split()[1])*1024>=retain_bytes+256*1024**2,
                              'Insufficient memory for bounded mismatch capture')
            return
    raise RuntimeError('MemAvailable resource check unavailable')


class RawSHA:
    def __init__(self,output,expected,sizes,retain_bytes):
        self.output=Path(output);self.expected={str(Path(k).resolve()):v for k,v in expected.items()}
        self.sizes={str(Path(k).resolve()):v for k,v in sizes.items()}
        self.retain_bytes=retain_bytes;self.rows=[]

    def __call__(self,path):
        resolved=str(Path(path).resolve(strict=True));index=len(self.rows)
        required=self.sizes.get(resolved,2038431872 if Path(path).name=='propagator.npy' else None)
        try:
            row=integrity.read_dual(path,self.expected.get(resolved),required,
                capture_limit=self.retain_bytes,snapshot=self.output/('hash-%03d-bad-view.bin'%index))
        except integrity.IntegrityError as exc:
            row=exc.report;self.rows.append(row)
            integrity.write_json_private(self.output/('hash-%03d.json'%index),row)
            raise
        self.rows.append(row);integrity.write_json_private(self.output/('hash-%03d.json'%index),row)
        return row['openssl_sha256']

    def manifest(self):
        return dict(complete=bool(self.rows) and all(v['passed'] for v in self.rows),method=integrity.METHOD,
            block_bytes=integrity.BLOCK,rows=[dict(path='hash-%03d.json'%i,
                sha256=integrity.read_dual(self.output/('hash-%03d.json'%i))['openssl_sha256'])
                for i in range(len(self.rows))])


def check_audit_provenance(run,report,sha):
    """Read-only check of a completed raw proof, using the caller's raw SHA."""
    run=Path(run).resolve();verification=report['verification'];audit=verification['checksum_audit']
    integrity.require(audit['method']==integrity.METHOD,'Raw checksum proof method required')
    integrity.require(audit.get('protocol_version')==4 and audit.get('complete') is True and audit.get('passed') is True and
                      audit.get('status')=='passed','Terminal v4 checksum status required')
    manifest_path=Path(audit['manifest_path'])
    attempt=run.parent.parent
    integrity.require(manifest_path.name=='manifest.json' and not manifest_path.is_symlink() and
                      manifest_path.resolve()==manifest_path and attempt in manifest_path.parents,
                      'Raw checksum evidence must remain inside its attempt')
    integrity.require(sha(manifest_path)==audit['manifest_sha256'],'Raw checksum manifest changed')
    protocol_path=manifest_path.parent/'protocol.json'
    integrity.require(sha(protocol_path)==audit['protocol_sha256'],'Raw checksum protocol changed')
    protocol=json.loads(protocol_path.read_text());manifest=json.loads(manifest_path.read_text())
    integrity.require(protocol['complete'] and protocol['method']==integrity.METHOD and
        protocol['wrapper_sha256']==audit['wrapper_sha256'] and protocol['raw_reader_sha256']==audit['raw_reader_sha256'] and
        protocol['benchmark_sha256']==audit['benchmark_sha256'] and protocol['identity']==audit['independent_modules'],
        'Raw protocol identity changed')
    helper_root=manifest_path.parent/'helper'
    integrity.require(sha(helper_root/'manifest.json')==audit['helper_manifest_sha256'] and
                      sha(helper_root/'protocol.json')==audit['helper_protocol_sha256'] and
                      sha(helper_root/'status.json')==audit['helper_status_sha256'],'Helper audit artifacts changed')
    helper_status=json.loads((helper_root/'status.json').read_text());helper_protocol=json.loads((helper_root/'protocol.json').read_text())
    integrity.require(helper_status['complete'] and helper_status['passed'] and helper_protocol['only_sha_body_changed'] and
        helper_protocol['unchanged_nodes_original_sha256']==helper_protocol['unchanged_nodes_transformed_sha256'] and
        helper_protocol['helper_sha256']==audit['helper_sha256'] and helper_protocol['wrapper_sha256']==audit['helper_wrapper_sha256'],
        'Helper AST/checksum proof incomplete')
    helper_manifest=json.loads((helper_root/'manifest.json').read_text())
    integrity.require(helper_manifest['complete'] and helper_manifest['passed'] and
        helper_manifest['evidence_sha256']==verification['evidence_sha256'] and
        helper_status['manifest_sha256']==audit['helper_manifest_sha256'] and
        len({v['path'] for v in helper_manifest['rows']})==len(helper_manifest['rows']), 'Helper manifest incomplete/changed')
    for item in helper_manifest['rows']:
        path=helper_root/item['path']
        integrity.require(path.name==item['path'] and sha(path)==item['sha256'],'Helper read-proof artifact changed')
        row=json.loads(path.read_text())
        integrity.require(row['complete'] and row['passed'] and row['metadata_stable'] and row['byte_count_exact'] and
            row['eof_probe_bytes']==0 and row['openssl_sha256']==row['software_sha256'], 'Helper read contract failed')
    integrity.require(manifest['complete'] and manifest['method']==integrity.METHOD and
        len({v['path'] for v in manifest['rows']})==len(manifest['rows']),'Raw manifest incomplete/duplicate')
    payloads={}
    for item in manifest['rows']:
        path=manifest_path.parent/item['path']
        integrity.require(path.name==item['path'] and not path.is_symlink() and sha(path)==item['sha256'],
                          'Unsafe/changed raw checksum record')
        row=json.loads(path.read_text())
        integrity.require(row['complete'] and row['passed'] and row['metadata_stable'] and row['byte_count_exact'] and
            row['eof_probe_bytes']==0 and row['same_immutable_bytes'] and row['openssl_sha256']==row['software_sha256'],
            'Raw checksum record failed')
        payloads.setdefault(row['path'],[]).append(row)
    for path,expected in [(run/'propagator.npy',verification['propagator_sha256']),
                          (Path(report['reference_propagator']),verification['reference_propagator_sha256'])]:
        rows=payloads.get(str(path),[])
        integrity.require(len(rows)>=2 and all(v['read_bytes']==2038431872 and v['expected_sha256']==
            v['openssl_sha256']==expected for v in rows),'Original/gold PRE+POST raw proof missing')
    return audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark',type=Path,required=True);parser.add_argument('--audit-output',type=Path,required=True)
    parser.add_argument('--expected-benchmark-sha',required=True);parser.add_argument('--expected-propagator-sha')
    parser.add_argument('--expected-gold-sha');parser.add_argument('--payload-bytes',type=int,default=2038431872)
    parser.add_argument('--expected-wrapper-sha',required=True);parser.add_argument('--expected-reader-sha',required=True)
    parser.add_argument('--expected-helper-sha',required=True);parser.add_argument('--helper-wrapper',type=Path,required=True)
    parser.add_argument('--expected-helper-wrapper-sha',required=True)
    parser.add_argument('--retry-existing-verification-sha',help='Explicit prior failed-report SHA; preserved before new protocol')
    parser.add_argument('--retain-mib',type=int,default=2200)
    args,remaining=parser.parse_known_args()
    verifying='--verify' in remaining
    if verifying:
        integrity.require('--verification-output' in remaining and '--diagnostic' not in remaining,
                          'Fresh explicit precision-only verification command required')
        run=Path(remaining[remaining.index('--verify')+1]).resolve(strict=True)
        initial=json.loads((run/'result.json').read_text())
        integrity.require(not initial.get('verification',{}).get('complete') or args.retry_existing_verification_sha,
                          'A completed old verification needs explicit retained failed-report identity')
        if args.retry_existing_verification_sha:
            integrity.read_dual(run/'result.json',args.retry_existing_verification_sha)
        args.expected_propagator_sha=args.expected_propagator_sha or initial['propagator_sha256']
        integrity.require(initial['propagator_sha256']==args.expected_propagator_sha,'Stored original expected SHA changed')
        gold=Path(initial['reference_propagator'])
        integrity.require(args.expected_gold_sha,'Frozen gold SHA must be recorded explicitly for verification')
    else:
        integrity.require('--output' in remaining and '--fixture' in remaining,'Full12 benchmark arguments required')
        initial=None
    identity=integrity.known_vectors();resource_gate(args.payload_bytes,args.retain_mib*1024**2)
    integrity.require(integrity.read_dual(args.benchmark, args.expected_benchmark_sha)['passed'],'Frozen verifier source differs')
    integrity.read_dual(Path(__file__),args.expected_wrapper_sha)
    integrity.read_dual(Path(integrity.__file__),args.expected_reader_sha)
    helper=args.benchmark.resolve().parents[2]/'benchmarks/runtime/verify_fixture_propagator.py'
    integrity.read_dual(helper,args.expected_helper_sha)
    integrity.read_dual(args.helper_wrapper,args.expected_helper_wrapper_sha)
    rank_text=os.environ.get('OMPI_COMM_WORLD_RANK','0')
    integrity.require(rank_text.isdecimal() and 0<=int(rank_text)<1024,'Invalid MPI rank identity')
    rank=int(rank_text)
    if not verifying:
        # Parent directory is an auxiliary audit root, separate from --output.
        args.audit_output.mkdir(mode=0o700,parents=True,exist_ok=True)
        integrity.require(not args.audit_output.is_symlink(),'Audit root must be regular')
        args.audit_output=args.audit_output/('rank%05d'%rank)
    args.audit_output.mkdir(mode=0o700,parents=True,exist_ok=False)
    expected={args.benchmark:args.expected_benchmark_sha};sizes={}
    if verifying:
        expected.update({run/'propagator.npy':args.expected_propagator_sha,gold:args.expected_gold_sha})
        expected.update({run/('gauge_rank%05d.npy'%r):value for r,value in initial['output_gauge_files']})
        sizes.update({run/'propagator.npy':args.payload_bytes,gold:args.payload_bytes})
    hasher=RawSHA(args.audit_output,expected,sizes,args.retain_mib*1024**2)
    provenance=dict(complete=True,method=integrity.METHOD,identity=identity,
        wrapper_sha256=integrity.read_dual(Path(__file__))['openssl_sha256'],
        raw_reader_sha256=integrity.read_dual(Path(integrity.__file__))['openssl_sha256'],
        benchmark_sha256=args.expected_benchmark_sha,payload_bytes=args.payload_bytes,
        source_unchanged=True,numerical_thresholds_unchanged=True,prior_failure_root_cause='unresolved',
        mode='verification' if verifying else 'benchmark',rank=rank,
        protocol_version=4,helper_sha256=args.expected_helper_sha,helper_wrapper_sha256=args.expected_helper_wrapper_sha,
        timing_contract='Checksum callback only; full12 API clocks/samples unchanged; checksum/output outside timed API')
    integrity.write_json_private(args.audit_output/'protocol.json',provenance)
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('frozen_raw_audited_bench',args.benchmark)
    bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
    original_sha=bench.sha;bench.sha=hasher
    original_atomic=bench.atomic;original_subprocess=bench.subprocess
    candidate=[None];helper_calls=[]
    if verifying:
        # Preserve prior report BYTES before changing only its verification field.
        from raw_scalar_helper import source_bytes
        prior_bytes=source_bytes(run/'result.json',integrity.read_dual(run/'result.json')['openssl_sha256'])
        integrity.write_private_new(args.audit_output/'prior-result.json',[prior_bytes])
        prior_sha=integrity.read_dual(args.audit_output/'prior-result.json')['openssl_sha256']
        pending=guarded_report(initial,None,prior_sha,'running')
        original_atomic(run/'result.json',pending)
        def pending_atomic(path,value):
            if Path(path).resolve()==(run/'result.json').resolve() and value.get('verification',{}).get('complete'):
                candidate[0]=deepcopy(value['verification'])
                guarded=guarded_report(value,candidate[0],prior_sha,'pending_final_checks')
                return original_atomic(path,guarded)
            return original_atomic(path,value)
        bench.atomic=pending_atomic
        class RoutedSubprocess:
            def __getattr__(self,name):return getattr(original_subprocess,name)
            def run(self,argv,*positional,**kwargs):
                expected=[sys.executable,str(helper),str(run),str(Path(remaining[remaining.index('--reference')+1]).resolve()),
                    str(Path(remaining[remaining.index('--extractor')+1]).resolve()),
                    str(run/remaining[remaining.index('--verification-output')+1])]
                integrity.require(list(argv)==expected,'Unexpected helper subprocess command; strict routing refused')
                report_now=integrity.read_dual(run/'result.json')['openssl_sha256']
                call=[sys.executable,str(args.helper_wrapper),'--helper',str(helper),
                    '--expected-helper-sha',args.expected_helper_sha,'--expected-wrapper-sha',args.expected_helper_wrapper_sha,
                    '--expected-reader-sha',args.expected_reader_sha,'--audit-output',str(args.audit_output/'helper'),
                    '--expected-propagator-sha',args.expected_propagator_sha,
                    '--expected-reference-sha',hasher(expected[3]),'--expected-extractor-sha',hasher(expected[4]),
                    '--expected-gauge-sha',initial['comparison_key']['prepared_gauge_manifest_sha256'],
                    '--expected-run-report-sha',report_now,'--',*expected[2:]]
                integrity.require(not helper_calls,'Exactly one fresh helper invocation required')
                helper_calls.append(call)
                integrity.write_json_private(args.audit_output/'helper-call.json',dict(complete=True,protocol_version=4,
                    original_argv=expected,actual_argv=call,helper_sha256=args.expected_helper_sha,
                    helper_wrapper_sha256=args.expected_helper_wrapper_sha,reader_sha256=args.expected_reader_sha))
                return original_subprocess.run(call,*positional,**kwargs)
        bench.subprocess=RoutedSubprocess()
    sys.argv=[str(args.benchmark),*remaining]
    try:
        bench.main()
        if not verifying:
            manifest=hasher.manifest();integrity.require(manifest['complete'],'Raw benchmark checksum audit incomplete')
            integrity.write_json_private(args.audit_output/'manifest.json',manifest)
            print('RAW_BENCHMARK_CHECKSUM_COMPLETE '+json.dumps(dict(rank=rank,checks=len(hasher.rows),
                audit_manifest=str(args.audit_output/'manifest.json'),
                manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256'],
                wrapper_sha256=provenance['wrapper_sha256'],raw_reader_sha256=provenance['raw_reader_sha256'])),flush=True)
            return
        measured=json.loads((run/'result.json').read_text());verification=candidate[0]
        integrity.require(verification is not None and len(helper_calls)==1,'Final guarded verification candidate missing')
        integrity.require({k:v for k,v in initial.items() if k!='verification'}==
                          {k:v for k,v in measured.items() if k!='verification'},'Original measurement fields changed')
        integrity.require(verification['complete'] and verification['passed'] and verification['columns']==12 and
                          verification['propagator_sha256']==args.expected_propagator_sha and
                          verification['reference_propagator_sha256']==args.expected_gold_sha,
                          'Original frozen helper/solution identities or full12 verification failed')
        manifest=hasher.manifest();integrity.require(manifest['complete'],'Raw checksum audit incomplete')
        integrity.write_json_private(args.audit_output/'manifest.json',manifest)
        helper_status=json.loads((args.audit_output/'helper/status.json').read_text())
        helper_protocol=json.loads((args.audit_output/'helper/protocol.json').read_text())
        integrity.require(helper_status['complete'] and helper_status['passed'] and helper_protocol['only_sha_body_changed'] and
            helper_protocol['unchanged_nodes_original_sha256']==helper_protocol['unchanged_nodes_transformed_sha256'],
            'Actual helper AST/reader protocol failed')
        helper_manifest=json.loads((args.audit_output/'helper/manifest.json').read_text())
        integrity.require(helper_manifest['complete'] and helper_manifest['passed'] and
            helper_manifest['evidence_sha256']==verification['evidence_sha256'], 'Helper evidence must retain its produced SHA')
        verification['checksum_audit']=dict(protocol_version=4,complete=True,passed=True,status='passed',
            method=integrity.METHOD,wrapper_sha256=provenance['wrapper_sha256'],
            raw_reader_sha256=provenance['raw_reader_sha256'],benchmark_sha256=args.expected_benchmark_sha,
            manifest_path=str(args.audit_output/'manifest.json'),
            manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256'],
            protocol_sha256=integrity.read_dual(args.audit_output/'protocol.json')['openssl_sha256'],
            independent_modules=identity,prior_failure_root_cause='unresolved',prior_report_sha256=prior_sha,
            helper_sha256=args.expected_helper_sha,helper_wrapper_sha256=args.expected_helper_wrapper_sha,
            helper_manifest_sha256=integrity.read_dual(args.audit_output/'helper/manifest.json')['openssl_sha256'],
            helper_protocol_sha256=integrity.read_dual(args.audit_output/'helper/protocol.json')['openssl_sha256'],
            helper_status_sha256=integrity.read_dual(args.audit_output/'helper/status.json')['openssl_sha256'],
            helper_call_sha256=integrity.read_dual(args.audit_output/'helper-call.json')['openssl_sha256'])
        measured['verification']=verification
        original_atomic(run/'result.json',measured)
        print('RAW_AUDITED_VERIFY_COMPLETE '+json.dumps(dict(checks=len(hasher.rows),
            manifest_sha256=verification['checksum_audit']['manifest_sha256'])),flush=True)
    except BaseException as exc:
        integrity.write_json_private(args.audit_output/'failure.json',dict(complete=False,error_type=type(exc).__name__,
            message=str(exc),method=integrity.METHOD,completed_checks=len(hasher.rows),numerical_acceptance=False))
        if verifying:
            failed=guarded_report(initial,candidate[0],prior_sha,'failed',exc)
            original_atomic(run/'result.json',failed)
        raise
    finally:
        bench.sha=original_sha;bench.atomic=original_atomic;bench.subprocess=original_subprocess


if __name__=='__main__':main()
