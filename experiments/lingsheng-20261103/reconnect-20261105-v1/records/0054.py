#!/usr/bin/env python3
"""Execute a SHA-pinned scalar helper with only its sha function body replaced.

All other AST nodes, physics checks, column extraction and scalar C++ commands
remain identical. This wrapper never edits the frozen helper or its evidence.
"""
import argparse
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import file_integrity as integrity


def source_bytes(path,expected):
    path=Path(path);fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_BINARY',0))
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes']
        integrity.require(size<=1024**2,'Helper source unexpectedly large')
        data=os.pread(fd,size,0)
        integrity.require(len(data)==size and os.pread(fd,1,size)==b'' and
                          integrity.metadata(os.fstat(fd))==before==integrity.metadata(path.stat()),
                          'Helper source raw-read contract failed')
    finally:os.close(fd)
    integrity.require(integrity.small_dual(data)==expected,'Frozen helper full-file SHA differs')
    return data


def transform(source,filename):
    original=ast.parse(source,filename=filename)
    matches=[(i,node) for i,node in enumerate(original.body) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='sha']
    integrity.require(len(matches)==1 and isinstance(matches[0][1],ast.FunctionDef),'Exactly one synchronous sha function required')
    index,function=matches[0]
    integrity.require(len(function.args.args)==1 and not function.args.vararg and not function.args.kwarg,
                      'Unexpected helper sha signature')
    changed=deepcopy(original)
    replacement=changed.body[index]
    replacement.body=[ast.Return(value=ast.Call(func=ast.Name(id='_raw_verified_sha',ctx=ast.Load()),
        args=[ast.Name(id=function.args.args[0].arg,ctx=ast.Load())],keywords=[]))]
    ast.fix_missing_locations(changed)
    def remainder(tree):
        copy=deepcopy(tree);copy.body=[node for i,node in enumerate(copy.body) if i!=index]
        return ast.dump(copy,include_attributes=False)
    before,after=remainder(original),remainder(changed)
    integrity.require(before==after,'Non-sha AST nodes changed')
    a,b=deepcopy(function),deepcopy(replacement);a.body=[];b.body=[]
    integrity.require(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'SHA signature/decorators changed')
    return changed,dict(complete=True,only_sha_body_changed=True,
        original_ast_sha256=integrity.small_dual(ast.dump(original,include_attributes=False).encode()),
        transformed_ast_sha256=integrity.small_dual(ast.dump(changed,include_attributes=False).encode()),
        unchanged_nodes_original_sha256=integrity.small_dual(before.encode()),
        unchanged_nodes_transformed_sha256=integrity.small_dual(after.encode()),
        original_sha_ast_sha256=integrity.small_dual(ast.dump(function,include_attributes=False).encode()))


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
    integrity.known_vectors();integrity.read_dual(Path(__file__),args.expected_wrapper_sha)
    integrity.read_dual(Path(integrity.__file__),args.expected_reader_sha)
    source=source_bytes(args.helper,args.expected_helper_sha);tree,proof=transform(source,str(args.helper))
    args.audit_output.mkdir(mode=0o700,parents=True,exist_ok=False)
    proof.update(protocol_version=4,helper_sha256=args.expected_helper_sha,wrapper_sha256=args.expected_wrapper_sha,
        reader_sha256=args.expected_reader_sha,method=integrity.METHOD,helper_source_unchanged=True,
        numerical_commands_unchanged=True,thresholds_unchanged=True,evidence_not_rewritten=True)
    integrity.write_json_private(args.audit_output/'protocol.json',proof)
    expected={str((run/'propagator.npy').resolve()):args.expected_propagator_sha,
        str(reference.resolve()):args.expected_reference_sha,str(extractor.resolve()):args.expected_extractor_sha,
        str((run/'result.json').resolve()):args.expected_run_report_sha,
        str((output/'gauge.bin').resolve()):args.expected_gauge_sha}
    rows=[]
    def raw_sha(path):
        resolved=str(Path(path).resolve(strict=True));index=len(rows)
        try:
            row=integrity.read_dual(path,expected.get(resolved),
                2038431872 if Path(path).name=='propagator.npy' else None,
                snapshot=args.audit_output/('hash-%03d-bad-view.bin'%index))
        except integrity.IntegrityError as exc:
            integrity.write_json_private(args.audit_output/('hash-%03d.json'%index),exc.report)
            raise
        rows.append(row);integrity.write_json_private(args.audit_output/('hash-%03d.json'%index),row)
        return row['openssl_sha256']
    sys.argv=[str(args.helper),*remaining]
    namespace={'__name__':'__main__','__file__':str(args.helper),'_raw_verified_sha':raw_sha}
    try:
        exec(compile(tree,str(args.helper),'exec'),namespace)
        # No helper-produced evidence byte is modified after its execution.
        evidence=output/'verification.json';evidence_sha=integrity.read_dual(evidence)['openssl_sha256']
        manifest=dict(complete=True,passed=True,protocol_version=4,method=integrity.METHOD,
            evidence_sha256=evidence_sha,protocol_sha256=integrity.read_dual(args.audit_output/'protocol.json')['openssl_sha256'],
            rows=[dict(path='hash-%03d.json'%i,sha256=integrity.read_dual(args.audit_output/('hash-%03d.json'%i))['openssl_sha256'])
                  for i in range(len(rows))])
        integrity.write_json_private(args.audit_output/'manifest.json',manifest)
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=True,passed=True,protocol_version=4,
            manifest_sha256=integrity.read_dual(args.audit_output/'manifest.json')['openssl_sha256']))
    except BaseException as exc:
        integrity.write_json_private(args.audit_output/'status.json',dict(complete=False,passed=False,protocol_version=4,
            error_type=type(exc).__name__,message=str(exc)))
        raise


if __name__=='__main__':main()
