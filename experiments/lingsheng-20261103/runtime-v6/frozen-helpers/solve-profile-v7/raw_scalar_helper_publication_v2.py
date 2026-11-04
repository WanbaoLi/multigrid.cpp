#!/usr/bin/env python3
"""Frozen scalar helper, sha-only AST adapter with fresh scratch publication v2."""
import argparse
import json
from pathlib import Path
import sys

import file_integrity as integrity
import fresh_publication_v2 as fresh
from raw_scalar_helper import source_bytes,transform

PUBLICATION_SHA='9ac768cc695f3a1fc7febe15d28798bd39ef8e925d973b8f07e04bb67e3ea01a'
ORIGINAL_ADAPTER_SHA='5691366c7f0dabc0c8714b0732612abb2f0019532fe070168ad2cc88f83867f3'
ORIGINAL_HELPER_SHA='bc441c56af7ffe65781816c8d18427578e8097f0b35168349a27629655fa2074'


class HelperChecks:
    def __init__(self,audit,expected,publication):
        self.audit=Path(audit);self.expected=expected;self.publication=publication;self.rows=[]

    def __call__(self,path):
        resolved=str(Path(path).resolve(strict=True));index=len(self.rows)
        try:
            if self.publication.contains(path)and resolved not in self.publication.published:
                parent=self.audit/'protocol.json'
                row=self.publication.read(path,self.expected[resolved],fresh.GAUGE_BYTES,
                    parent_protocol=dict(path=str(parent),sha256=integrity.read_dual(parent)['openssl_sha256']))
            else:
                required=2038431872 if Path(path).name=='propagator.npy'else(fresh.GAUGE_BYTES if self.publication.contains(path)else None)
                row=integrity.read_dual(path,self.expected.get(resolved),required,
                    snapshot=self.audit/('hash-%03d-bad-view.bin'%index))
        except integrity.IntegrityError as error:
            integrity.write_json_private(self.audit/('hash-%03d.json'%index),error.report);raise
        self.rows.append(row);integrity.write_json_private(self.audit/('hash-%03d.json'%index),row)
        return row['openssl_sha256']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper',type=Path,required=True);parser.add_argument('--expected-helper-sha',required=True)
    parser.add_argument('--expected-wrapper-sha',required=True);parser.add_argument('--expected-reader-sha',required=True)
    parser.add_argument('--audit-output',type=Path,required=True);parser.add_argument('--expected-propagator-sha',required=True)
    parser.add_argument('--expected-reference-sha',required=True);parser.add_argument('--expected-extractor-sha',required=True)
    parser.add_argument('--expected-gauge-sha',required=True);parser.add_argument('--expected-run-report-sha',required=True)
    args,remaining=parser.parse_known_args()
    if remaining[:1]==['--']:remaining=remaining[1:]
    integrity.require(len(remaining)==4,'Frozen helper needs exactly RUN REFERENCE EXTRACTOR OUTPUT')
    run,reference,extractor,output=map(Path,remaining)
    integrity.require(args.expected_helper_sha==ORIGINAL_HELPER_SHA and args.expected_gauge_sha==fresh.GAUGE_SHA,
                      'Original helper and canonical scratch gauge identity fixed from startup')
    publication=fresh.FreshPublication(output,[dict(relative='gauge.bin',kind='canonical-gauge',
        expected_sha256=args.expected_gauge_sha,bytes=fresh.GAUGE_BYTES)],args.audit_output/'fresh-gauge-publication-v2')
    integrity.known_vectors();integrity.read_dual(__file__,args.expected_wrapper_sha)
    integrity.read_dual(integrity.__file__,args.expected_reader_sha);integrity.read_dual(fresh.__file__,PUBLICATION_SHA)
    integrity.read_dual(source_bytes.__code__.co_filename,ORIGINAL_ADAPTER_SHA)
    source=source_bytes(args.helper,args.expected_helper_sha);tree,proof=transform(source,str(args.helper))
    args.audit_output.mkdir(mode=0o700,parents=True,exist_ok=False)
    proof.update(protocol_version=4,helper_sha256=args.expected_helper_sha,wrapper_sha256=args.expected_wrapper_sha,
        reader_sha256=args.expected_reader_sha,method=integrity.METHOD,helper_source_unchanged=True,
        numerical_commands_unchanged=True,thresholds_unchanged=True,evidence_not_rewritten=True,
        fresh_publication_protocol=fresh.PROTOCOL,fresh_publication_module_sha256=PUBLICATION_SHA,
        original_adapter_sha256=ORIGINAL_ADAPTER_SHA,eligibility=publication.eligibility,
        immutable_files_use_unchanged_strict_reader=True)
    integrity.write_json_private(args.audit_output/'protocol.json',proof)
    expected={str((run/'propagator.npy').resolve()):args.expected_propagator_sha,
        str(reference.resolve()):args.expected_reference_sha,str(extractor.resolve()):args.expected_extractor_sha,
        str((run/'result.json').resolve()):args.expected_run_report_sha,
        str((output/'gauge.bin').resolve()):args.expected_gauge_sha}
    checks=HelperChecks(args.audit_output,expected,publication)
    sys.argv=[str(args.helper),*remaining]
    namespace={'__name__':'__main__','__file__':str(args.helper),'_raw_verified_sha':checks}
    try:
        exec(compile(tree,str(args.helper),'exec'),namespace)
        integrity.require(len(publication.published)==1,'Fresh canonical scratch gauge publication did not complete')
        receipts=[row['fresh_output_publication']for row in checks.rows if 'fresh_output_publication'in row]
        integrity.require(len(receipts)==1 and receipts[0]['complete']and receipts[0]['passed'],'Canonical gauge publication proof missing')
        evidence=output/'verification.json';evidence_sha=integrity.read_dual(evidence)['openssl_sha256']
        manifest=dict(complete=True,passed=True,protocol_version=4,method=integrity.METHOD,
            evidence_sha256=evidence_sha,protocol_sha256=integrity.read_dual(args.audit_output/'protocol.json')['openssl_sha256'],
            fresh_publication_protocol=fresh.PROTOCOL,publication_module_sha256=PUBLICATION_SHA,publications=receipts,
            rows=[dict(path='hash-%03d.json'%i,sha256=integrity.read_dual(args.audit_output/('hash-%03d.json'%i))['openssl_sha256'])
                  for i in range(len(checks.rows))])
        integrity.write_json_private(args.audit_output/'manifest.json',manifest)
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=True,passed=True,protocol_version=4,
            fresh_publication_protocol=fresh.PROTOCOL,publication_module_sha256=PUBLICATION_SHA,
            manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256']))
    except BaseException as error:
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=False,passed=False,protocol_version=4,
            fresh_publication_protocol=fresh.PROTOCOL,error_type=type(error).__name__,message=str(error)));raise


if __name__=='__main__':main()
