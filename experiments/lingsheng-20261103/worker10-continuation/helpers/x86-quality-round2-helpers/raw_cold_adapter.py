#!/usr/bin/env python3
"""External cold/setup-profile checksum callbacks; frozen solver and clocks stay intact."""
import argparse
import ast
import importlib.machinery
import json
import os
from pathlib import Path
import runpy
import sys
import traceback

import file_integrity as integrity


def read_source(path,expected=None):
    """Obtain small executable source via explicit offsets, never read-to-EOF."""
    path=Path(path).resolve(strict=True);parts=[];fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0))
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes']
        integrity.require(size<=4*1024**2,'Auxiliary executable source exceeds explicit4MiB cap')
        offset=0
        while offset<size:
            want=min(integrity.BLOCK,size-offset);part=os.pread(fd,want,offset)
            integrity.require(isinstance(part,bytes) and 0<len(part)<=want,'Executable source read length failed')
            parts.append(part);offset+=len(part)
        integrity.require(os.pread(fd,1,size)==b'' and integrity.metadata(os.fstat(fd))==before==integrity.metadata(path.stat()),
                          'Executable source identity/count/EOF failed')
    finally:os.close(fd)
    payload=b''.join(parts);actual=integrity.small_dual(payload)
    integrity.require(expected is None or actual==expected,'Frozen executable source SHA changed: '+str(path))
    return payload,actual


def ast_proof(payload,excluded=()):
    tree=ast.parse(payload)
    selected=[node.name for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in excluded]
    integrity.require(set(selected)==set(excluded),'Expected callback definitions missing/duplicate')
    tree.body=[node for node in tree.body if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name not in excluded]
    return integrity.small_dual(ast.dump(tree,annotate_fields=True,include_attributes=False).encode())


def execute_source(path,expected,name,namespace=None):
    payload,actual=read_source(path,expected)
    scope=namespace if namespace is not None else {}
    scope.update(__name__=name,__file__=str(Path(path).resolve()),__package__='')
    exec(compile(payload,str(Path(path).resolve()),'exec'),scope)
    return scope,payload,actual


class CallbackAudit:
    def __init__(self,output,expected=None,retain_bytes=2200*1024**2):
        self.output=Path(output);self.expected={str(Path(k).resolve()):v for k,v in (expected or {}).items()}
        self.retain_bytes=retain_bytes;self.rows=[];self.callbacks=[]

    def callback(self,label):
        self.callbacks.append(label)
        def sha(path):
            index=len(self.rows);target=Path(path).resolve(strict=True)
            required=2038431872 if target.name=='propagator.npy' else None
            try:
                row=integrity.read_dual(target,self.expected.get(str(target)),required,
                    capture_limit=self.retain_bytes,snapshot=self.output/('hash-%05d-bad-view.bin'%index))
            except integrity.IntegrityError as error:
                row=dict(error.report,callback=label);self.rows.append(row)
                integrity.write_json_private(self.output/('hash-%05d.json'%index),row);raise
            row=dict(row,callback=label);self.rows.append(row)
            integrity.write_json_private(self.output/('hash-%05d.json'%index),row)
            return row['openssl_sha256']
        return sha

    def finish(self,success,provenance,error=None):
        manifest=dict(complete=bool(success) and all(r['passed'] for r in self.rows),method=integrity.METHOD,
            callbacks=self.callbacks,checks=len(self.rows),provenance=provenance,error=error,
            rows=[dict(path='hash-%05d.json'%i,sha256=integrity.read_dual(self.output/('hash-%05d.json'%i))['openssl_sha256']) for i in range(len(self.rows))])
        integrity.write_json_private(self.output/'manifest.json',manifest)
        return integrity.read_dual(self.output/'manifest.json')['openssl_sha256']


def option_value(argv,name):
    integrity.require(argv.count(name)==1 and argv.index(name)+1<len(argv),'Exactly one '+name+' required')
    return argv[argv.index(name)+1]


def run(options,remaining):
    integrity.known_vectors()
    integrity.read_dual(Path(__file__),options.expected_adapter_sha)
    integrity.read_dual(Path(integrity.__file__),options.expected_reader_sha)
    cold=options.cold_wrapper.resolve(strict=True)
    read_source(cold,options.expected_cold_sha)
    output=Path(option_value(remaining,'--output')).resolve()
    audit_root=options.audit_output.resolve()
    integrity.require(not audit_root.is_relative_to(output) and not output.is_relative_to(audit_root),'Audit/output trees must be separate')
    rank_text=os.environ.get('OMPI_COMM_WORLD_RANK','0')
    integrity.require(rank_text.isdecimal() and 0<=int(rank_text)<1024,'Explicit OpenMPI rank identity required')
    audit_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    integrity.require(not audit_root.is_symlink(),'Regular auxiliary audit root required')
    directory=audit_root/('rank%05d'%int(rank_text));directory.mkdir(mode=0o700,exist_ok=False)
    expected={cold:options.expected_cold_sha}
    for flag,sha_flag in [('--library','--expected-library-sha'),('--source-manifest','--snapshot-sha')]:
        expected[Path(option_value(remaining,flag))]=option_value(remaining,sha_flag)
    if '--gauge' in remaining:expected[Path(option_value(remaining,'--gauge'))]=option_value(remaining,'--expected-input-sha') if '--expected-input-sha' in remaining else '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30'
    audit=CallbackAudit(directory,expected,options.retain_mib*1024**2)
    provenance=dict(method=integrity.METHOD,adapter_sha256=options.expected_adapter_sha,reader_sha256=options.expected_reader_sha,
        cold_source=str(cold),cold_source_sha256=options.expected_cold_sha,rank=int(rank_text),
        prepared_hash_unchanged=True,solver_and_clocks_unchanged=True,patched_functions=[],source_proofs=[],
        raw_lime_input_hash_inside_cold_clock='--gauge' in remaining,
        timing_note='Canonical-memory hash unchanged. Raw-LIME file dual SHA remains inside original input_sha_seconds; both platforms need same protocol. Audit/artifact hashes outside API, profiler decode/runtime hashes remain diagnostic setup wrapper costs.')
    payload,_=read_source(cold,options.expected_cold_sha)
    provenance['source_proofs'].append(dict(path=str(cold),source_sha256=options.expected_cold_sha,excluded_callbacks=['sha'],
        original_other_ast_sha256=ast_proof(payload,['sha']),executed_other_ast_sha256=ast_proof(payload,['sha'])))
    original_runpy=runpy.run_path;original_loader=importlib.machinery.SourceFileLoader.exec_module
    dispatched=[];helper_loaded=[];success=False;failure=None;saved_argv=sys.argv
    def execute_cold():
        scope,_,_=execute_source(cold,options.expected_cold_sha,'_raw_frozen_cold')
        scope['sha']=audit.callback('cold_full12.sha');provenance['patched_functions'].append('cold_full12.sha')
        scope['main']()
        return scope
    try:
        if options.profile_setup:
            profile=options.profile_setup.resolve(strict=True);helper=options.profile_helper.resolve(strict=True)
            integrity.require(option_value(remaining,'--cold-wrapper')==str(cold) and option_value(remaining,'--profile-helper')==str(helper),'Profile arguments must identify exact frozen cold/helper paths')
            read_source(profile,options.expected_profile_sha);hp,_=read_source(helper,options.expected_profile_helper_sha)
            provenance.update(profile_source=str(profile),profile_source_sha256=options.expected_profile_sha,
                profile_helper=str(helper),profile_helper_sha256=options.expected_profile_helper_sha,
                runpy_dispatch='Only exact cold_full12 target; profile setup method/perf sampling/clock bodies unchanged')
            provenance['source_proofs'].append(dict(path=str(helper),source_sha256=options.expected_profile_helper_sha,excluded_callbacks=['sha'],
                original_other_ast_sha256=ast_proof(hp,['sha']),executed_other_ast_sha256=ast_proof(hp,['sha'])))
            pp,_=read_source(profile,options.expected_profile_sha);provenance['source_proofs'].append(dict(path=str(profile),excluded_callbacks=[],source_sha256=options.expected_profile_sha,
                original_other_ast_sha256=ast_proof(pp),executed_other_ast_sha256=ast_proof(pp)))
            def load(loader,module):
                path=Path(getattr(loader,'path','')).resolve()
                if path!=helper:return original_loader(loader,module)
                execute_source(helper,options.expected_profile_helper_sha,module.__name__,module.__dict__)
                module.sha=audit.callback('profile_full12.sha');helper_loaded.append(str(path));provenance['patched_functions'].append('profile_full12.sha')
            def dispatch(path,*args,**kwargs):
                if Path(path).resolve()!=cold:return original_runpy(path,*args,**kwargs)
                integrity.require(not args and kwargs.get('run_name')=='__main__','Unexpected frozen cold runpy calling convention')
                dispatched.append(str(cold));integrity.require(len(dispatched)==1,'Exactly one cold entry per profile')
                return execute_cold()
            importlib.machinery.SourceFileLoader.exec_module=load;runpy.run_path=dispatch
            sys.argv=[str(profile),*remaining]
            scope,_,_=execute_source(profile,options.expected_profile_sha,'_raw_frozen_profile_setup')
            returned=scope['main']()
            integrity.require(returned in (0,None) and len(dispatched)==len(helper_loaded)==1,'Profile entry/helper did not complete exact cold dispatch')
        else:
            sys.argv=[str(cold),*remaining];execute_cold()
        success=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc());raise
    finally:
        sys.argv=saved_argv;runpy.run_path=original_runpy;importlib.machinery.SourceFileLoader.exec_module=original_loader
        integrity.write_json_private(directory/'protocol.json',dict(complete=success,**provenance))
        manifest_sha=audit.finish(success,provenance,failure)
        print('RAW_COLD_CHECKSUM_AUDIT '+json.dumps(dict(complete=success,rank=int(rank_text),manifest=str(directory/'manifest.json'),manifest_sha256=manifest_sha,patched_functions=provenance['patched_functions'])),flush=True)


def main():
    argv=sys.argv[1:];integrity.require('--' in argv,'Explicit -- before unchanged frozen entry arguments required')
    index=argv.index('--');outer,remaining=argv[:index],argv[index+1:]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cold-wrapper',type=Path,required=True);p.add_argument('--expected-cold-sha',required=True)
    p.add_argument('--expected-reader-sha',required=True);p.add_argument('--expected-adapter-sha',required=True)
    p.add_argument('--audit-output',type=Path,required=True);p.add_argument('--retain-mib',type=int,default=2200)
    p.add_argument('--profile-setup',type=Path);p.add_argument('--expected-profile-sha')
    p.add_argument('--profile-helper',type=Path);p.add_argument('--expected-profile-helper-sha')
    options=p.parse_args(outer)
    integrity.require(not options.profile_setup or all([options.expected_profile_sha,options.profile_helper,options.expected_profile_helper_sha]),'Profile requires all explicit source identities')
    sys.dont_write_bytecode=True;run(options,remaining)


if __name__=='__main__':main()
