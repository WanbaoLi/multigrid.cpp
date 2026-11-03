#!/usr/bin/env python3
"""Compose raw_controller_v4 with explicit derived cold bash/entry dispatch."""
import argparse
from copy import deepcopy
import importlib
import importlib.machinery
import json
import os
from pathlib import Path
import shlex
import sys

import file_integrity as integrity
import raw_cold_adapter as cold


def adapter_command(options,original,stage_audit):
    def same(value,path):
        return str(value)==str(path.resolve()) or (Path(value).name==path.name and Path(value).resolve()==path.resolve())
    def python_entry(index):
        previous=index-1
        while previous>=0 and original[previous] in ('-u','-B','-I','-E','-s','-S','-O','-OO'):previous-=1
        return previous>=0 and Path(original[previous]).name.startswith('python')
    matches=[(i,'cold') for i,v in enumerate(original) if python_entry(i) and same(v,options.cold_source)]
    matches += [(i,'profile') for i,v in enumerate(original) if python_entry(i) and same(v,options.profile_source)]
    integrity.require(len(matches)==1,'Derived cold command must identify exactly one frozen entry')
    index,kind=matches[0]
    prefix=[str(options.cold_adapter),'--cold-wrapper',str(options.cold_source.resolve()),
        '--expected-cold-sha',options.expected_cold_sha,'--expected-reader-sha',options.reader_sha,
        '--expected-adapter-sha',options.cold_adapter_sha,'--audit-output',str(stage_audit)]
    if kind=='profile':prefix += ['--profile-setup',str(options.profile_source.resolve()),
        '--expected-profile-sha',options.expected_profile_sha,'--profile-helper',str(options.profile_helper.resolve()),
        '--expected-profile-helper-sha',options.expected_profile_helper_sha]
    return [*original[:index],*prefix,'--',*original[index+1:]],kind


def transform_bash(options,campaign,name,stage,command):
    result=deepcopy(command);argv=result.get('argv',[])
    if len(argv)!=2 or Path(argv[0]).name!='bash':return result,None
    script=Path(argv[1]).resolve();payload,source_sha=cold.read_source(script)
    text=payload.decode();targets=(str(options.cold_source),str(options.profile_source))
    if not any(target in text for target in targets):return result,None
    lines=text.splitlines()
    integrity.require(len(lines)==4 and lines[0]=='#!/bin/bash' and lines[1]=='set -eo pipefail',
                      'Only the reviewed four-line generated cold shell is supported')
    bootstrap=shlex.split(lines[2]);integrity.require(len(bootstrap)==2 and bootstrap[0]=='source','Explicit site bootstrap required')
    original=shlex.split(lines[3]);integrity.require(not set(original)&{'|','||','&&',';','&','>','<'},'Cold shell command must be one argv, no operators')
    stage_audit=Path(campaign)/'attempts'/name/'checksum-audit'/stage/'cold-runtime'
    replacement,kind=adapter_command(options,original,stage_audit)
    derived_text='\n'.join([*lines[:3],shlex.join(replacement)])+'\n'
    key=integrity.small_dual(derived_text.encode())
    derived=script.with_name(script.stem+'.raw-'+key[:16]+'.sh')
    if derived.exists():
        data,_=cold.read_source(derived,key);integrity.require(data==derived_text.encode(),'Retained derived cold shell changed')
    else:integrity.write_private_new(derived,[derived_text.encode()])
    result['argv']=[argv[0],str(derived)]
    proof=dict(kind=kind,original_script=str(script),original_script_sha256=source_sha,
        derived_script=str(derived),derived_script_sha256=key,original_inner_argv=original,derived_inner_argv=replacement,
        actual_stage_argv=result['argv'],bootstrap=bootstrap[1],bootstrap_sha256=integrity.read_dual(bootstrap[1])['openssl_sha256'],
        cold_adapter_sha256=options.cold_adapter_sha,reader_sha256=options.reader_sha,
        original_entry_args_unchanged=True,placement_environment_timeout_unchanged=True)
    return result,proof


def run(options,remaining):
    integrity.known_vectors();integrity.read_dual(Path(__file__),options.controller_sha)
    integrity.read_dual(Path(integrity.__file__),options.reader_sha)
    integrity.read_dual(options.cold_adapter,options.cold_adapter_sha)
    integrity.require(Path(cold.__file__).resolve()==options.cold_adapter.resolve(),'Imported cold adapter differs from explicit wrapper')
    for path,expected in [(options.base_controller,options.base_sha),(options.cold_source,options.expected_cold_sha),
        (options.profile_source,options.expected_profile_sha),(options.profile_helper,options.expected_profile_helper_sha),
        (options.prepare_source,options.prepare_sha),(options.campaign_source,options.campaign_sha)]:cold.read_source(path,expected)
    options.audit_root.mkdir(mode=0o700,parents=True,exist_ok=True)
    directory=options.audit_root/('cold-controller-%d'%os.getpid());directory.mkdir(mode=0o700,exist_ok=False)
    audit=cold.CallbackAudit(directory,{options.prepare_source:options.prepare_sha,options.campaign_source:options.campaign_sha})
    proofs=[];patches=[];dispatches=[];restores=[]
    targets={options.prepare_source.resolve():('sha',options.prepare_sha,'prepare_best_replay.sha'),
             options.campaign_source.resolve():('digest',options.campaign_sha,'campaign.digest')}
    loader=importlib.machinery.SourceFileLoader.exec_module
    def load(source_loader,module):
        path=Path(getattr(source_loader,'path','')).resolve()
        if path not in targets:return loader(source_loader,module)
        function,expected,label=targets[path]
        _,payload,_=cold.execute_source(path,expected,module.__name__,module.__dict__)
        old=getattr(module,function);restores.append((module,function,old));setattr(module,function,audit.callback(label));patches.append(label)
        fingerprint=cold.ast_proof(payload,[function])
        proofs.append(dict(path=str(path),source_sha256=expected,excluded_callbacks=[function],original_other_ast_sha256=fingerprint,executed_other_ast_sha256=fingerprint))
    importlib.machinery.SourceFileLoader.exec_module=load
    sys.path.insert(0,str(options.campaign_source.parent))
    ledger=importlib.import_module('campaign')
    integrity.require(Path(ledger.__file__).resolve()==options.campaign_source.resolve(),'Wrong campaign module imported')
    # If campaign was already imported, explicitly apply only its file callback.
    if not any(module is ledger for module,_,_ in restores):
        payload,_=cold.read_source(options.campaign_source,options.campaign_sha)
        restores.append((ledger,'digest',ledger.digest));ledger.digest=audit.callback('campaign.digest');patches.append('campaign.digest')
        fingerprint=cold.ast_proof(payload,['digest']);proofs.append(dict(path=str(options.campaign_source),source_sha256=options.campaign_sha,excluded_callbacks=['digest'],original_other_ast_sha256=fingerprint,executed_other_ast_sha256=fingerprint))
    original_stage=ledger.run_stage
    def stage(campaign,name,label,command,*args,**kwargs):
        request,proof=transform_bash(options,campaign,name,label,command)
        if proof:
            record=directory/('bash-dispatch-%03d.json'%len(dispatches));integrity.write_json_private(record,proof);dispatches.append(proof)
        return original_stage(campaign,name,label,request,*args,**kwargs)
    ledger.run_stage=stage
    saved_argv=sys.argv;success=False;failure=None
    try:
        scope,_,_=cold.execute_source(options.base_controller,options.base_sha,'_unchanged_raw_base_controller')
        sys.argv=[str(options.base_controller),*remaining];scope['main']();success=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        sys.argv=saved_argv;ledger.run_stage=original_stage;importlib.machinery.SourceFileLoader.exec_module=loader
        for module,function,original in reversed(restores):setattr(module,function,original)
        provenance=dict(controller_sha256=options.controller_sha,reader_sha256=options.reader_sha,base_controller_sha256=options.base_sha,
            cold_adapter_sha256=options.cold_adapter_sha,patched_functions=patches,source_proofs=proofs,
            bash_dispatches=dispatches,numerical_solver_clocks_and_memory_prepared_hash_unchanged=True)
        integrity.write_json_private(directory/'protocol.json',dict(complete=success,**provenance))
        manifest=audit.finish(success,provenance,failure)
        print('RAW_COLD_CONTROLLER_COMPLETE '+json.dumps(dict(complete=success,manifest=str(directory/'manifest.json'),manifest_sha256=manifest,derived_cold_stages=len(dispatches))),flush=True)


def main():
    argv=sys.argv[1:];integrity.require('--' in argv,'Explicit -- before unchanged base controller arguments required')
    index=argv.index('--');p=argparse.ArgumentParser(description=__doc__)
    for name in ['base-controller','cold-adapter','cold-source','profile-source','profile-helper','prepare-source','campaign-source','audit-root']:
        p.add_argument('--'+name,type=Path,required=True)
    for name in ['base-sha','cold-adapter-sha','expected-cold-sha','expected-profile-sha','expected-profile-helper-sha','prepare-sha','campaign-sha','reader-sha','controller-sha']:
        p.add_argument('--'+name,required=True)
    options=p.parse_args(argv[:index]);sys.dont_write_bytecode=True;run(options,argv[index+1:])


if __name__=='__main__':main()
