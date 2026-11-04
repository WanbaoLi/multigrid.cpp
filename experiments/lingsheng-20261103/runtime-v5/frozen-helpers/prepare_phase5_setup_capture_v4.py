#!/usr/bin/env python3
"""Prepare phase5 v4: unchanged full8 trials, actual synchronous pre-setup maps.

Only preparation output files are written. New worker7 NEW fresh-publication-v2 routing. No queue, ledger, source, scientific
payload or accepted pointer is modified. A future operator publishes task.json
after reviewing contract.json; the dispatch entry rechecks the same guards.
"""
import argparse
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time

import file_integrity as integrity
import raw_cold_adapter as cold
import raw_protocol_publication_v2 as protocol
import raw_protocol_v4 as legacy

CONTROLLER_SHA='84c71468e4bf64da1aa5ea254caf2de65b92531421cbad3a18faf896337f3937'
POLICY_SHA='245ecd8201c1268c8e3a78ba64383ce7dce6334709fe5856deac8033ed39a1de'
COLD_ADAPTER_SHA='c65c2da816c9a68f992a6db4cdbbef98e02954a17015abf8405ea474d780cc69'
FACTORY_SHA='b94f04ff48ebefd075cefe770d49e9b6093f3baa50fc2f8261e73319f1e0fe36'
LEGACY_FACTORY_SHA='1fe892d279305be75f6f814d8e7526d2c09531803ac5ffc6f8483f46b1fd0453'
BUDGET=4700
RESERVE=90
STARTUP_CLEAR=('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT')


def lookup(value,key):
    for part in key.split('.'):
        if not isinstance(value,dict)or part not in value:return None
        value=value[part]
    return value


def finite(value,positive=False):
    return type(value)in(int,float)and math.isfinite(value)and(value>0 if positive else value>=0)


def precision(report):
    proof=report.get('verification',{});audit=proof.get('checksum_audit',{})
    errors=proof.get('solution_relative_errors',[])
    samples=report.get('samples',[])
    return (report.get('complete')is True and report.get('measurements_complete')is True and report.get('zero_initial_guess')is True and
        bool(samples)and all(finite(sample.get('wall_seconds'),True)and len(sample.get('stats',[]))==12 and
            all(stat.get('converged')in(1,True)and finite(stat.get('true_residual'))and stat['true_residual']<=1e-8 for stat in sample['stats'])for sample in samples)and
        proof.get('complete')is True and proof.get('passed')is True and proof.get('columns')==12 and
        finite(proof.get('max_true_residual'))and proof['max_true_residual']<=1e-8 and
        finite(proof.get('solution_relative_error'))and proof['solution_relative_error']<=1e-6 and
        len(errors)==12 and all(finite(value)and value<=1e-6 for value in errors)and
        proof.get('propagator_sha256')==report.get('propagator_sha256')and
        audit.get('protocol_version')==4 and audit.get('complete')is True and audit.get('passed')is True and audit.get('status')=='passed')


def gate(dependency,status,best,startup,manifest,host,allocation,expected_best,now,best_key='best',
         dependency_host_key='host',dependency_allocation_key='allocation'):
    reasons=[]
    if not(dependency.get('complete')is True and dependency.get('status')in('complete','qualified','eligible')):
        reasons.append('Selected predecessor state is not complete')
    cleanup=status.get('cleanup',{})
    if not(status.get('status')=='passed'and type(status.get('returncode'))is int and status['returncode']==0 and cleanup.get('complete')is True and
           cleanup.get('surviving_pids')==[] and status.get('task_tag')):
        reasons.append('Selected predecessor task has not passed with complete owned-process cleanup')
    dependency_host=lookup(dependency,dependency_host_key)
    if not dependency_host or status.get('host')!=dependency_host or not lookup(dependency,dependency_allocation_key):
        reasons.append('Predecessor task/state host differs')
    if lookup(dependency,best_key)!=expected_best or best.get('attempt')!=expected_best:
        reasons.append('Explicit predecessor best/current best differs; choose the new closed predecessor after adoption')
    if not(startup.get('complete')is True and startup.get('host','').split('.')[0]==host and startup.get('allocation')==allocation):
        reasons.append('Explicit worker startup does not match selected host/allocation')
    loader=startup.get('loader_environment',{})
    if not(manifest.get('protocol')=='phase5-single-gomp-search-directory-v1'and manifest.get('complete')is True and
           manifest.get('passed')is True and loader.get('LD_LIBRARY_PATH')==manifest.get('base_ld_library_path')and
           isinstance(loader.get('LD_LIBRARY_PATH'),str)and bool(loader['LD_LIBRARY_PATH'])and not loader.get('LD_PRELOAD')):
        reasons.append('Startup SDK search string differs from the explicit completed runtime manifest, or contains preload')
    binding=manifest.get('worker_startup',{})
    if not(manifest.get('manifest_revision')==3 and manifest.get('other_solver_closure_unchanged')is True and
           binding.get('host')==startup.get('host')and binding.get('allocation')==startup.get('allocation')):
        reasons.append('New runtime manifest must bind this exact inspected worker startup; oldc3f is immutable')
    deadline=startup.get('safe_deadline_epoch')
    remaining=deadline-now if finite(deadline,True)and finite(now)else 0
    if remaining-RESERVE<BUDGET:reasons.append(f'Need{BUDGET}s for all8 fresh trials plus{RESERVE}s reserve; remaining{remaining:.0f}s')
    return dict(passed=not reasons,status='ready'if not reasons else'pending',reasons=reasons,
        remaining_seconds=remaining,task_timeout_seconds=min(6500,max(1,int(remaining)-RESERVE)),
        complete_group_budget_seconds=BUDGET,dispatch_cleanup_reserve_seconds=RESERVE)


def case_ids(prefix,threads):
    if threads not in(32,37):raise ValueError('Frozen c5 supports fine32/37 only')
    other=37 if threads==32 else 32
    return [f'{prefix}-team{threads}-a',f'{prefix}-team{other}',f'{prefix}-team{threads}-b',
        f'{prefix}-sdk-a',f'{prefix}-sdk-passive',f'{prefix}-old-default',f'{prefix}-old-passive',f'{prefix}-sdk-b']


def fresh_paths(root,queue,task_id,prefix,state,audit,threads):
    root,queue,state,audit=map(Path,(root,queue,state,audit));paths=[state,audit]
    for name in case_ids(prefix,threads):
        paths.extend([root/'campaign/attempts'/name,root/'plans'/(name+'.json'),root/'proposals'/(name+'.json')])
        paths.extend((root/'phase5-shim-logs').glob(name+'-*.log'))
    paths.extend((root/'phase5-shim-logs').glob(prefix+'-loader-*.log'))
    paths.extend(queue.glob(task_id+'.*'))
    paths.extend(queue.glob('*.running.json'));paths.extend(queue.glob('*.ready.json'))
    return sorted({str(path)for path in paths if path.exists()or path.is_symlink()})


def read(path,expected=None):
    payload,actual=cold.read_source(Path(path),expected)
    return json.loads(payload),actual


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def build_task(protocol_module,auxiliary,guard,guard_sha,python,contract_path,contract_sha,task_id,
               framework_tools,benchmark_sha,timeout,ld_library_path,runtime_audit_dir):
    argv=protocol_module.command(Path(auxiliary),Path(guard),guard_sha,task_id,python,
        ['--contract',str(contract_path),'--contract-sha',contract_sha],
        framework_tools=Path(framework_tools),benchmark_sha=benchmark_sha)
    base=str(Path(auxiliary)/'raw_controller_publication_v2.py')
    index=argv.index(base)
    argv=[*argv[:index],str(Path(auxiliary)/'raw_controller_setup_capture_v4.py'),
        '--expected-self-sha','151989b219f0ac02a403c1fa98e800bbb028402897a10d8d020136c5b6b76997','--capture-wrapper-sha','cb5a963dd397664393d7efaacc1f5a06f8c8fc270b39a404495a5a75a8092d30','--',*argv[index+1:]]
    return dict(argv=argv,cwd=str(auxiliary),timeout=timeout,environment=dict(LD_LIBRARY_PATH=ld_library_path,
        LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT='',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        LQCD_OPT_CAPTURE_DIR=str(runtime_audit_dir),LQCD_OPT_CAPTURE_BASE_LD=ld_library_path))


def prepare(args):
    for module,expected in ((integrity,legacy.FILES['file_integrity.py']),(cold,COLD_ADAPTER_SHA),
                            (protocol,FACTORY_SHA),(legacy,LEGACY_FACTORY_SHA)):
        integrity.read_dual(Path(module.__file__),expected)
    root=args.root.resolve();aux=args.auxiliary.resolve();queue=args.queue.resolve()
    state=args.state.resolve(strict=False);audit=args.runtime_audit_dir.resolve(strict=False);output=args.output.resolve(strict=False)
    for name in (args.id,args.prefix,args.expected_best,args.dependency_closing_attempt):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',name):raise ValueError('Safe explicit identifiers required')
    if len(args.prefix)>35:raise ValueError('Case prefix must leave space for frozen c5 suffixes')
    if queue.parent!=root:raise ValueError('Explicit queue must be a direct child of root')
    if any(path.is_relative_to(root/'campaign')or path.is_relative_to(root/'source')for path in(state,audit)):
        raise ValueError('Controller state/audit must stay outside campaign and source')
    if state==audit or state.is_relative_to(audit)or audit.is_relative_to(state):raise ValueError('State/audit paths must be distinct')
    if any(output.is_relative_to(path)for path in(root/'campaign',(root/'source').resolve(),queue)):
        raise ValueError('Preparation output must stay outside campaign, source and queue')
    if output.is_relative_to(state)or output.is_relative_to(audit):raise ValueError('Preparation output cannot create a future state/audit path')
    pinned=[]
    def get(path,expected=None):
        value,actual=read(path,expected);pinned.append(dict(path=str(Path(path).resolve()),sha256=actual));return value
    def pin(path,expected=None):
        actual=integrity.read_dual(Path(path),expected)['openssl_sha256'];pinned.append(dict(path=str(Path(path).resolve()),sha256=actual));return actual
    dependency=get(args.dependency_state,args.dependency_state_sha)
    status=get(args.dependency_task_status,args.dependency_task_status_sha)
    startup=get(args.startup_manifest,args.startup_sha)
    manifest=get(args.runtime_manifest,args.runtime_manifest_sha)
    if manifest.get('worker_startup',{}).get('sha256')!=args.startup_sha or manifest.get('worker_startup',{}).get('path')!=str(args.startup_manifest.resolve()):
        raise ValueError('Runtime manifest startup path/SHA differs from selected actual worker')
    best=get(root/'campaign/best.json')
    readiness=gate(dependency,status,best,startup,manifest,args.host,args.allocation,args.expected_best,time.time(),
        args.dependency_best_key,args.dependency_host_key,args.dependency_allocation_key)
    if not readiness['passed']:return dict(status='pending',complete=False,gate=readiness,queue_written=False)
    phase4=get(root/'phase4-state.json')
    if not phase4.get('complete'):return dict(status='pending',complete=False,gate=dict(reasons=['Frozen c5 requires complete phase4 state']),queue_written=False)
    for name,expected in {**legacy.FILES,**protocol.FILES,'raw_protocol_publication_v2.py':FACTORY_SHA,
            'raw_protocol_v4.py':LEGACY_FACTORY_SHA,'raw_cold_adapter.py':COLD_ADAPTER_SHA,'cold_full12.py':POLICY_SHA}.items():pin(aux/name,expected)
    pin(aux/'phase5_validation_shim.py','c5a8a8b3c14d697c9062bf04172e2eb616ffebda66298a99aa123ca80419d9fe')
    pin(aux/'owned_publication_audit_v3.py','1264d37ee7e05ae6247a7770351c426ab3c01324ef14d01f8abe614deb6a9103')
    controller=aux/'phase5_worker7_v3.py';pin(controller,CONTROLLER_SHA)
    shim=load(controller,'portable_worker7_v3');shim.base.check_shim_manifest(manifest,lambda path:integrity.read_dual(path)['openssl_sha256'])
    tools=root/'source/tools/optimization';sys.path.insert(0,str(tools));ledger=importlib.import_module('campaign')
    if Path(ledger.__file__).resolve()!=tools/'campaign.py':raise ValueError('Mixed campaign module; use isolated preparation process')
    ledger.digest=lambda path:integrity.read_dual(Path(path))['openssl_sha256']
    _,limits=ledger.campaign(root/'campaign')
    data,accepted,_=ledger.checked_attempt(root/'campaign',args.expected_best,limits)
    cfg=accepted['configuration']
    if cfg.get('placement_threads',cfg['threads'])!=37 or cfg.get('setup_threads',cfg['threads'])!=37:
        raise ValueError('Frozen c5 requires placement/setup37 already present in accepted configuration')
    shim.base.runtime_variants(cfg,args.prefix,manifest)  # exact twoSDK controls, no added context key
    collisions=fresh_paths(root,queue,args.id,args.prefix,state,audit,cfg['threads'])
    if collisions:return dict(status='pending',complete=False,gate=dict(reasons=['Existing state/case/plan/proposal/log/audit/queue identity'],paths=collisions),queue_written=False)
    diagnostic=get(args.dependency_diagnostic_report,args.dependency_diagnostic_sha)
    described=lookup(dependency,args.dependency_diagnostic_key)
    if not isinstance(described,dict)or described.get('verification')!=diagnostic.get('verification'):
        raise ValueError('Selected diagnostic is not the complete proof retained by the closed predecessor')
    if described.get('report')!=str(args.dependency_diagnostic_report.resolve()):raise ValueError('Predecessor diagnostic path differs')
    if not precision(diagnostic)or diagnostic.get('timing_scope')!='profile_full12_api':raise ValueError('Actual full12 diagnostic precision is incomplete')
    from raw_benchmark_v4 import check_audit_provenance
    check_audit_provenance(args.dependency_diagnostic_report.parent,diagnostic,lambda path:integrity.read_dual(path)['openssl_sha256'])
    _,closing,_=ledger.checked_attempt(root/'campaign',args.dependency_closing_attempt,limits)
    key=closing['comparison_key'];diag_key=diagnostic['comparison_key']
    if any(value['host']!=lookup(dependency,args.dependency_host_key)or value['allocation']!=lookup(dependency,args.dependency_allocation_key)for value in(key,diag_key)):
        raise ValueError('Actual closing control/diagnostic does not belong to the predecessor epoch')
    for name in ('problem','input_sha256','prepared_gauge_manifest_sha256'):
        if any(value.get(name)!=accepted['comparison_key'].get(name)for value in(key,diag_key)):
            raise ValueError('Predecessor diagnostic/closing/current best physical problem differs')
    pin(root/'campaign/attempts'/args.dependency_closing_attempt/'report.json')
    pin(root/'campaign/attempts'/args.expected_best/'report.json')
    pin(root/'campaign/attempts'/args.expected_best/'attempt.json')
    pin(root/'campaign/attempts'/args.expected_best/'source-manifest.json',data['snapshot']['source_manifest_sha256'])
    pin(root/'campaign/attempts'/args.expected_best/'artifacts/liblqcd_cpu.so',accepted['library_sha256'])
    parent_source=Path(data['snapshot']['source']);benchmark_sha=pin(parent_source/'tools/optimization/bench_full12.py')
    pin(parent_source/'benchmarks/runtime/verify_fixture_propagator.py',legacy.HELPER_SHA)
    for name in ('campaign.py','trial.py','process_tree.py'):pin(tools/name)
    policy=load(aux/'cold_full12.py','portable_cold_policy');numerical=sorted(policy.numerical_environment_keys(parent_source))
    expected_cpus=startup.get('before_worker_exec_parent_state',{}).get('cpus',[])
    if len(expected_cpus)<cfg['ranks']*37 or len(set(expected_cpus))!=len(expected_cpus):raise ValueError('Startup resource mask cannot cover fixed c5 placement')
    controller_args=['--root',str(root),'--prefix',args.prefix,'--state',str(state),'--expected-host',args.host,
        '--runtime-shim-manifest',str(args.runtime_manifest.resolve()),'--runtime-shim-manifest-sha',args.runtime_manifest_sha,
        '--runtime-audit-dir',str(audit),'--external-runtime-audit']
    pin(aux/'runtime_benchmark_capture_v4.py','cb5a963dd397664393d7efaacc1f5a06f8c8fc270b39a404495a5a75a8092d30')
    pin(aux/'raw_controller_setup_capture_v4.py','151989b219f0ac02a403c1fa98e800bbb028402897a10d8d020136c5b6b76997')
    guard=Path(__file__).with_name('phase5_worker7_allocation_v3.py').resolve();guard_sha=pin(guard)
    contract=dict(schema='portable-phase5-preparation-v3',complete=True,status='prepared_not_run',
        root=str(root),queue=str(queue),task_id=args.id,prefix=args.prefix,state=str(state),runtime_audit_dir=str(audit),
        host=args.host,allocation=args.allocation,expected_best=args.expected_best,
        safe_deadline_epoch=startup['safe_deadline_epoch'],expected_parent_cpus=expected_cpus,
        startup_ld_library_path=manifest['base_ld_library_path'],startup_clear_keys=list(STARTUP_CLEAR),
        numerical_environment_keys=numerical,resources=cfg,
        predecessor=dict(state=str(args.dependency_state.resolve()),task_status=str(args.dependency_task_status.resolve()),
            diagnostic_report=str(args.dependency_diagnostic_report.resolve()),closing_attempt=args.dependency_closing_attempt,
            best_key=args.dependency_best_key,diagnostic_key=args.dependency_diagnostic_key,
            host_key=args.dependency_host_key,allocation_key=args.dependency_allocation_key),
        controller=dict(path=str(controller),sha256=CONTROLLER_SHA,argv=controller_args),
        case_ids=case_ids(args.prefix,cfg['threads']),pinned_files=pinned,
        budget=readiness,benchmark_sha256=benchmark_sha,guard_sha256=guard_sha,
        preparation_source_sha256=integrity.read_dual(Path(__file__))['openssl_sha256'],
        runtime_capture=dict(protocol='synchronous-before-setup-v4',wrapper_sha256='cb5a963dd397664393d7efaacc1f5a06f8c8fc270b39a404495a5a75a8092d30',
            dispatcher_sha256='151989b219f0ac02a403c1fa98e800bbb028402897a10d8d020136c5b6b76997',capture_point='after gauge load, before original setup',
            captured_during_setup=False,ordinary_solve_observer_running=False))
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    contract_path=output/'contract.json';integrity.write_json_private(contract_path,contract)
    contract_sha=integrity.read_dual(contract_path)['openssl_sha256']
    task=build_task(protocol,aux,guard,guard_sha,args.python,contract_path,contract_sha,args.id,tools,
        benchmark_sha,readiness['task_timeout_seconds'],manifest['base_ld_library_path'],audit)
    integrity.write_json_private(output/'task.json',task)
    return dict(status='prepared_not_run',complete=True,queue_written=False,output=str(output),contract_sha256=contract_sha,
        task_sha256=integrity.read_dual(output/'task.json')['openssl_sha256'],gate=readiness)


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','auxiliary','queue','startup-manifest','state','runtime-audit-dir','dependency-state',
                 'dependency-task-status','dependency-diagnostic-report','runtime-manifest','output'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('startup-sha','host','allocation','id','prefix','expected-best','dependency-state-sha',
                 'dependency-task-status-sha','dependency-diagnostic-sha','dependency-closing-attempt','runtime-manifest-sha','python'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--dependency-best-key',default='best')
    p.add_argument('--dependency-diagnostic-key',default='actual_halo_diagnostic')
    p.add_argument('--dependency-host-key',default='host')
    p.add_argument('--dependency-allocation-key',default='allocation')
    return p


def main():
    args=parser().parse_args()
    for name in ('startup_sha','dependency_state_sha','dependency_task_status_sha','dependency_diagnostic_sha','runtime_manifest_sha'):
        if not re.fullmatch('[0-9a-f]{64}',getattr(args,name)):parser().error('Exact64hex SHA required: '+name)
    try:result=prepare(args)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,AttributeError)as error:
        result=dict(status='pending',complete=False,queue_written=False,reasons=[type(error).__name__+': '+str(error)])
    print(json.dumps(result,indent=2,allow_nan=False),flush=True)


if __name__=='__main__':main()
