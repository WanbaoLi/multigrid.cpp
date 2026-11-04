#!/usr/bin/env python3
"""Explicit external runtime adapter for frozen controllers/trial.py.

It records wrapper/reader SHA in each actual ledger stage argv, forwards child
trial.py through itself, and strengthens imported bench.sha for cached checks.
No frozen source file, solver, timing clock or stored expected digest is edited.
"""
import argparse
from copy import deepcopy
import importlib
import importlib.machinery
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import uuid

import file_integrity as integrity
import raw_benchmark_v4 as raw_benchmark


def transform_stage(options,campaign,name,stage,command):
    result=deepcopy(command);argv=result.get('argv',[])
    matches=[i for i,v in enumerate(argv) if Path(v).name=='bench_full12.py']
    if not matches:return result
    integrity.require(len(matches)==1,'Ambiguous benchmark entry in stage argv')
    index=matches[0];target=argv[index]
    audit=Path(campaign)/'attempts'/name/'checksum-audit'/stage
    prefix=[str(options.wrapper),'--benchmark',target,'--audit-output',str(audit),
            '--expected-benchmark-sha',options.benchmark_sha,'--expected-wrapper-sha',options.wrapper_sha,
            '--expected-reader-sha',options.reader_sha]
    prefix+=['--expected-helper-sha',options.helper_sha,'--helper-wrapper',str(options.helper_wrapper),
             '--expected-helper-wrapper-sha',options.helper_wrapper_sha]
    remaining=argv[index+1:]
    if '--verify' in remaining:
        prefix+=['--expected-gold-sha',options.gold_sha]
        if '--verification-output' not in remaining:remaining=[*remaining,'--verification-output','independent']
    result['argv']=[*argv[:index],*prefix,*remaining]
    return result


def child_trial_command(options,argv):
    if not isinstance(argv,(list,tuple)) or not all(isinstance(v,str) for v in argv):return argv
    matches=[i for i,v in enumerate(argv) if Path(v).name=='trial.py']
    if not matches:return argv
    integrity.require(len(matches)==1,'Ambiguous child trial entry')
    index=matches[0];target=Path(argv[index])
    entry_sha=integrity.read_dual(target)['openssl_sha256']
    forwarding=[str(Path(__file__).resolve()),'--entry',str(target),'--entry-sha',entry_sha,
        '--framework-tools',str(options.framework_tools),'--audit-root',str(options.audit_root),
        '--wrapper',str(options.wrapper),'--wrapper-sha',options.wrapper_sha,'--reader-sha',options.reader_sha,
        '--benchmark-sha',options.benchmark_sha,'--gold-sha',options.gold_sha,
        '--adapter-sha',options.adapter_sha,'--',*argv[index+1:]]
    boundary=forwarding.index('--')
    forwarding[boundary:boundary]=['--helper-sha',options.helper_sha,'--helper-wrapper',str(options.helper_wrapper),
                                  '--helper-wrapper-sha',options.helper_wrapper_sha]
    return [*argv[:index],*forwarding]


def install(options):
    integrity.known_vectors()
    integrity.read_dual(Path(__file__),options.adapter_sha)
    integrity.read_dual(options.wrapper,options.wrapper_sha)
    integrity.read_dual(options.helper_wrapper,options.helper_wrapper_sha)
    integrity.require(Path(raw_benchmark.__file__).resolve()==options.wrapper.resolve(),
                      'Imported raw wrapper differs from the explicit recorded wrapper')
    integrity.read_dual(Path(integrity.__file__),options.reader_sha)
    integrity.read_dual(options.entry,options.entry_sha)
    options.audit_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    integrity.require(not options.audit_root.is_symlink(),'Auxiliary driver audit root must be regular')
    protocol=options.audit_root/('adapter-%d-%s.json'%(os.getpid(),uuid.uuid4().hex))
    integrity.write_json_private(protocol,dict(complete=True,adapter_sha256=options.adapter_sha,
        reader_sha256=options.reader_sha,wrapper_sha256=options.wrapper_sha,entry=str(options.entry),
        helper_sha256=options.helper_sha,helper_wrapper_sha256=options.helper_wrapper_sha,
        entry_sha256=options.entry_sha,benchmark_sha256=options.benchmark_sha,method=integrity.METHOD,
        scope='Runtime checksum/child-dispatch adapter only; frozen sources and numerical/timing paths untouched'))
    sys.path.insert(0,str(options.framework_tools))
    ledger=importlib.import_module('campaign')
    run_stage=ledger.run_stage
    def strengthened_stage(campaign,name,stage,command,*args,**kwargs):
        return run_stage(campaign,name,stage,transform_stage(options,campaign,name,stage,command),*args,**kwargs)
    ledger.run_stage=strengthened_stage
    popen=subprocess.Popen
    def dispatch(argv,*args,**kwargs):return popen(child_trial_command(options,argv),*args,**kwargs)
    subprocess.Popen=dispatch
    # Imported frozen bench modules are used for read-only cached proof checks by
    # setup controllers. Only that module's sha callback is replaced after a
    # source-SHA check; direct benchmark/verify commands use logged stage argv.
    execute=importlib.machinery.SourceFileLoader.exec_module
    def load(loader,module):
        path=Path(getattr(loader,'path',''))
        selected=path.name=='bench_full12.py'
        if selected:integrity.read_dual(path,options.benchmark_sha)
        execute(loader,module)
        if selected:
            original=module.sha;observations=[];cache_root=[None]
            def raw_sha(target):
                if cache_root[0] is None:
                    cache_root[0]=options.audit_root/('cached-%d-%s'%(os.getpid(),uuid.uuid4().hex))
                    cache_root[0].mkdir(mode=0o700)
                output=cache_root[0]/('hash-%03d.json'%len(observations))
                try:
                    row=integrity.read_dual(target,expected_size=2038431872 if Path(target).name=='propagator.npy' else None,
                        snapshot=cache_root[0]/('hash-%03d-bad-view.bin'%len(observations)))
                except integrity.IntegrityError as exc:
                    integrity.write_json_private(output,exc.report)
                    raise
                observations.append(row)
                integrity.write_json_private(output,row)
                print('RAW_CACHED_CHECKSUM '+json.dumps(dict(artifact=str(output),passed=True,
                    adapter_sha256=options.adapter_sha,reader_sha256=options.reader_sha)),flush=True)
                return row['openssl_sha256']
            module.sha=raw_sha
            original_cached=module.check_cached_verification
            def cached(run,report,reference,extractor):
                result=original_cached(run,report,reference,extractor)
                raw_benchmark.check_audit_provenance(run,report,raw_sha)
                return result
            module.check_cached_verification=cached
            module._raw_checksum_adapter=dict(method=integrity.METHOD,adapter_sha256=options.adapter_sha,
                wrapper_sha256=options.wrapper_sha,reader_sha256=options.reader_sha,original_sha=original,
                observations=observations)
    importlib.machinery.SourceFileLoader.exec_module=load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry',type=Path,required=True);parser.add_argument('--entry-sha',required=True)
    parser.add_argument('--framework-tools',type=Path,required=True);parser.add_argument('--audit-root',type=Path,required=True)
    parser.add_argument('--wrapper',type=Path,required=True);parser.add_argument('--wrapper-sha',required=True)
    parser.add_argument('--reader-sha',required=True);parser.add_argument('--adapter-sha',required=True)
    parser.add_argument('--benchmark-sha',required=True);parser.add_argument('--gold-sha',required=True)
    parser.add_argument('--helper-sha',required=True);parser.add_argument('--helper-wrapper',type=Path,required=True)
    parser.add_argument('--helper-wrapper-sha',required=True)
    options,remaining=parser.parse_known_args()
    if remaining[:1]==['--']:remaining=remaining[1:]
    integrity.require(options.entry.resolve()!=Path(__file__).resolve(),'Adapter cannot target itself')
    sys.dont_write_bytecode=True
    install(options)
    sys.argv=[str(options.entry),*remaining]
    runpy.run_path(str(options.entry),run_name='__main__')


if __name__=='__main__':main()
