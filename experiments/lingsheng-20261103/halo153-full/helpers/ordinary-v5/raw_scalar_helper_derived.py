#!/usr/bin/env python3
"""Pinned original scalar helper; sha-only AST adapter with fresh-gauge publication.

Only absent-at-CLI-start OUTPUT/gauge.bin can use the separately audited bounded
publication protocol. Propagator, rank gauge inputs, gold and executable checks
remain the unchanged strict raw reader; numerical commands/thresholds untouched.
"""
import argparse
import json
from pathlib import Path
import sys

import file_integrity as integrity
import derived_publication as derived
from raw_scalar_helper import source_bytes,transform

DERIVED_MODULE_SHA='83b790954b64b0ae7ae8e71ed2978b752f30477bafd7fa48cdfd6ef548b683a6'
ORIGINAL_ADAPTER_SHA='5691366c7f0dabc0c8714b0732612abb2f0019532fe070168ad2cc88f83867f3'
ORIGINAL_HELPER_SHA='bc441c56af7ffe65781816c8d18427578e8097f0b35168349a27629655fa2074'
CANONICAL_GAUGE_SHA='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
GAUGE_BYTES=509607936


class HelperChecks:
    def __init__(self,audit,expected,publication):
        self.audit=Path(audit);self.expected=expected;self.publication=publication;self.rows=[]

    def __call__(self,path):
        resolved=str(Path(path).resolve(strict=True));index=len(self.rows)
        try:
            if resolved==str(self.publication.path):
                row=self.publication.read()
            else:
                row=integrity.read_dual(path,self.expected.get(resolved),
                    2038431872 if Path(path).name=='propagator.npy'else None,
                    snapshot=self.audit/('hash-%03d-bad-view.bin'%index))
        except integrity.IntegrityError as error:
            integrity.write_json_private(self.audit/('hash-%03d.json'%index),error.report)
            raise
        self.rows.append(row)
        integrity.write_json_private(self.audit/('hash-%03d.json'%index),row)
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
    integrity.require(len(remaining)==4,'Original helper needs exactly RUN REFERENCE EXTRACTOR OUTPUT')
    run,reference,extractor,output=map(Path,remaining)
    integrity.require(args.expected_helper_sha==ORIGINAL_HELPER_SHA and args.expected_gauge_sha==CANONICAL_GAUGE_SHA,
                      'Frozen original helper and canonical prepared gauge digest required from startup')
    # Eligibility is captured before source loading, audit creation or helper exec.
    publication=derived.FreshDerivedPublication(output,args.expected_gauge_sha,GAUGE_BYTES,
                                               args.audit_output/'derived-gauge-publication')
    integrity.known_vectors();integrity.read_dual(Path(__file__),args.expected_wrapper_sha)
    integrity.read_dual(Path(integrity.__file__),args.expected_reader_sha)
    integrity.read_dual(Path(derived.__file__),DERIVED_MODULE_SHA)
    integrity.read_dual(Path(source_bytes.__code__.co_filename),ORIGINAL_ADAPTER_SHA)
    source=source_bytes(args.helper,args.expected_helper_sha);tree,proof=transform(source,str(args.helper))
    args.audit_output.mkdir(mode=0o700,parents=True,exist_ok=False)
    proof.update(protocol_version=4,helper_sha256=args.expected_helper_sha,wrapper_sha256=args.expected_wrapper_sha,
        reader_sha256=args.expected_reader_sha,method=integrity.METHOD,helper_source_unchanged=True,
        numerical_commands_unchanged=True,thresholds_unchanged=True,evidence_not_rewritten=True,
        derived_publication_protocol_version=1,derived_publication_module_sha256=DERIVED_MODULE_SHA,
        original_adapter_sha256=ORIGINAL_ADAPTER_SHA,derived_publication_method=derived.METHOD,
        derived_publication_eligibility=publication.eligibility,immutable_files_use_unchanged_strict_reader=True)
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
        integrity.require(publication.used,'Frozen helper did not validate its fresh assembled gauge')
        publication_path=publication.audit/'publication.json'
        publication_proof=json.loads(publication_path.read_text())
        integrity.require(publication_proof['complete'] and publication_proof['passed'],
                          'Fresh gauge publication proof incomplete; scalar checks cannot override it')
        evidence=output/'verification.json';evidence_sha=integrity.read_dual(evidence)['openssl_sha256']
        manifest=dict(complete=True,passed=True,protocol_version=4,method=integrity.METHOD,
            evidence_sha256=evidence_sha,protocol_sha256=integrity.read_dual(args.audit_output/'protocol.json')['openssl_sha256'],
            derived_publication=dict(protocol_version=1,module_sha256=DERIVED_MODULE_SHA,
                path=str(publication_path),sha256=integrity.read_dual(publication_path)['openssl_sha256'],
                full_proof=publication_proof),
            rows=[dict(path='hash-%03d.json'%i,sha256=integrity.read_dual(args.audit_output/('hash-%03d.json'%i))['openssl_sha256'])
                  for i in range(len(checks.rows))])
        integrity.write_json_private(args.audit_output/'manifest.json',manifest)
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=True,passed=True,protocol_version=4,
            derived_publication_protocol_version=1,derived_publication_module_sha256=DERIVED_MODULE_SHA,
            manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256']))
    except BaseException as error:
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=False,passed=False,protocol_version=4,
            derived_publication_protocol_version=1,error_type=type(error).__name__,message=str(error)))
        raise


if __name__=='__main__':main()
