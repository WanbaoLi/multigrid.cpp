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

import file_integrity as integrity


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
    parser.add_argument('--retain-mib',type=int,default=2200)
    args,remaining=parser.parse_known_args()
    verifying='--verify' in remaining
    if verifying:
        integrity.require('--verification-output' in remaining and '--diagnostic' not in remaining,
                          'Fresh explicit precision-only verification command required')
        run=Path(remaining[remaining.index('--verify')+1]).resolve(strict=True)
        initial=json.loads((run/'result.json').read_text())
        integrity.require(not initial.get('verification',{}).get('complete'),'Fresh protocol cannot silently reuse cached verification')
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
        timing_contract='Checksum callback only; full12 API clocks/samples unchanged; checksum/output outside timed API')
    integrity.write_json_private(args.audit_output/'protocol.json',provenance)
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('frozen_raw_audited_bench',args.benchmark)
    bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
    original_sha=bench.sha;bench.sha=hasher
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
        measured=json.loads((run/'result.json').read_text());verification=measured['verification']
        integrity.require({k:v for k,v in initial.items() if k!='verification'}==
                          {k:v for k,v in measured.items() if k!='verification'},'Original measurement fields changed')
        integrity.require(verification['complete'] and verification['passed'] and verification['columns']==12 and
                          verification['propagator_sha256']==args.expected_propagator_sha and
                          verification['reference_propagator_sha256']==args.expected_gold_sha,
                          'Original frozen helper/solution identities or full12 verification failed')
        manifest=hasher.manifest();integrity.require(manifest['complete'],'Raw checksum audit incomplete')
        integrity.write_json_private(args.audit_output/'manifest.json',manifest)
        verification['checksum_audit']=dict(method=integrity.METHOD,wrapper_sha256=provenance['wrapper_sha256'],
            raw_reader_sha256=provenance['raw_reader_sha256'],benchmark_sha256=args.expected_benchmark_sha,
            manifest_path=str(args.audit_output/'manifest.json'),
            manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256'],
            protocol_sha256=integrity.read_dual(args.audit_output/'protocol.json')['openssl_sha256'],
            independent_modules=identity,prior_failure_root_cause='unresolved')
        bench.atomic(run/'result.json',measured)
        print('RAW_AUDITED_VERIFY_COMPLETE '+json.dumps(dict(checks=len(hasher.rows),
            manifest_sha256=verification['checksum_audit']['manifest_sha256'])),flush=True)
    except BaseException as exc:
        integrity.write_json_private(args.audit_output/'failure.json',dict(complete=False,error_type=type(exc).__name__,
            message=str(exc),method=integrity.METHOD,completed_checks=len(hasher.rows),numerical_acceptance=False))
        raise
    finally:bench.sha=original_sha


if __name__=='__main__':main()
