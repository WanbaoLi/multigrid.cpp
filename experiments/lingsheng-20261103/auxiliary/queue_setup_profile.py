#!/usr/bin/env python3
"""Bounded serial cold/setup task controller; --emit-task prints, never enqueues.

ARM: require phase4 complete plus an explicit completed after-attempt (e.g. the
reviewed053 ID), select/freeze current best, profile setup19Hz on ranks0/8 and
verify full12 afterwards. x86 --ordinary uses canonical fixture without perf.
No raw-x86 LIME run, source update, numerical edit, or performance promotion.
"""
import argparse
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shlex
import socket
import sys
import time

ARM_ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ARM_ROOT)
    p.add_argument('--campaign',type=Path)
    p.add_argument('--aux-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--backend',choices=['arm','x86'],default='arm')
    p.add_argument('--id',default='054-setup-profile')
    p.add_argument('--after-attempt',required=True)
    p.add_argument('--ordinary',action='store_true',help='No perf; required for x86 and optional for fresh ordinary ARM cold samples')
    p.add_argument('--python',default=sys.executable)
    p.add_argument('--allocation')
    p.add_argument('--deadline-epoch',type=float)
    p.add_argument('--task-timeout',type=int,default=1000)
    p.add_argument('--dependency-state',type=Path,help='Completed diagnostic state (default ROOT/053-state.json when not ingested)')
    p.add_argument('--emit-task',action='store_true')
    return p


def task_record(args):
    argv=[args.python,(args.aux_dir/'queue_setup_profile.py').as_posix(),'--root',args.root.as_posix(),
        '--aux-dir',args.aux_dir.as_posix(),'--backend',args.backend,'--id',args.id,
        '--after-attempt',args.after_attempt,'--python',args.python,'--task-timeout',str(args.task_timeout)]
    for flag,value in [('--campaign',args.campaign),('--allocation',args.allocation),('--deadline-epoch',args.deadline_epoch),
                       ('--dependency-state',args.dependency_state)]:
        if value is not None:argv += [flag,value.as_posix() if isinstance(value,Path) else str(value)]
    if args.ordinary:argv += ['--ordinary']
    return dict(argv=argv,cwd=args.root.as_posix(),timeout=args.task_timeout)


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependency_report(ledger,campaign,name,config,host,allocation,backend,state_path,verifier_path):
    path=campaign/'attempts'/name
    record=ledger.read(path/'attempt.json')
    if record.get('report'):
        _,report,_=ledger.checked_attempt(campaign,name,config)
        return report,dict(kind='ingested ordinary report',rank_eligible=True)
    # A diagnostic is a valid sequencing dependency, never an accepted score.
    state=ledger.read(state_path)
    ledger.require(state.get('complete') is True and state.get('cleanup',{}).get('complete') is True,
                   'Diagnostic dependency state/cleanup incomplete')
    ledger.require(state.get('host')==host and state.get('allocation')==allocation,'Diagnostic state belongs to another host/allocation')
    ledger.check_snapshot(path,record)
    report_path=Path(state['report']).resolve()
    ledger.require(report_path==(path/'measurements/full12/result.json').resolve() and not report_path.is_symlink(),
                   'Diagnostic dependency report must be its own regular full12 output')
    ledger.require(ledger.digest(report_path)==state['report_sha256'],'Diagnostic dependency report SHA changed')
    report=ledger.read(report_path)
    validation=report.get('verification',{})
    ledger.require(report.get('complete') is True and report.get('measurements_complete') is True
        and report.get('timing_scope')=='profile_full12_api','Dependency must remain explicitly diagnostic')
    ledger.require(validation==state['verification'] and validation.get('complete') is True and validation.get('passed') is True
        and validation.get('columns')==12 and validation.get('reference_sha256')==config['reference_sha256']
        and math.isfinite(validation['max_true_residual']) and 0<=validation['max_true_residual']<=1e-8
        and math.isfinite(validation.get('solution_relative_error',float('inf')))
        and validation['solution_relative_error']<=1e-6,'Diagnostic independent full12 precision contract failed')
    ledger.require(report['source_manifest_sha256']==record['snapshot']['source_manifest_sha256']==state['source_manifest_sha256']
        and report['library_sha256']==state['library_sha256']
        and report['input_sha256']==config['input_sha256'],'Diagnostic source/library/input identity differs')
    ledger.require(ledger.digest(report['library_path'])==report['library_sha256'],'Diagnostic measured library changed')
    ledger.require(report['samples'] and all(len(row['stats'])==12 and all(s['converged']
        and math.isfinite(s['true_residual']) and 0<=s['true_residual']<=1e-8 for s in row['stats'])
        for row in report['samples']),'Diagnostic samples lack complete12 residuals')
    verifier=load('_cold_dependency_verifier',verifier_path)
    reference_root=(Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation') if backend=='arm'
                    else Path('/public2/home/lwb_720/.cache/mg-20261102/source/build/validation'))
    verifier.check_cached_verification(report_path.parent,report,reference_root/'multigrid',reference_root/'extract_columns')
    evidence_path=verifier.verification_evidence_path(report_path.parent,
        validation.get('evidence_relative_path','independent/verification.json'))
    evidence=ledger.read(evidence_path)
    columns=evidence.get('columns',[])
    ledger.require(evidence.get('complete') is True and len(columns)==12
        and {(row['source_spin'],row['source_color']) for row in columns}=={(s,c) for s in range(4) for c in range(3)}
        and all(math.isfinite(row['residual']) and 0<=row['residual']<=1e-8 for row in columns),
        'Diagnostic independent evidence does not cover all12 columns')
    return report,dict(kind='validated diagnostic sequencing only',rank_eligible=False,
        state_path=str(state_path),state_sha256=ledger.digest(state_path),report_sha256=state['report_sha256'])


def execute(args):
    root=args.root.resolve();tools=root/'source';aux=args.aux_dir.resolve()
    sys.path.insert(0,str(tools/'tools/optimization'))
    ledger=importlib.import_module('campaign')
    campaign=(args.campaign or root/('campaign' if args.backend=='arm' else 'campaign-canonical')).resolve()
    host=socket.gethostname()
    expected_host='cn19483' if args.backend=='arm' else 'node5005'
    ledger.require(host.split('.')[0]==expected_host,'Unexpected compute node; use a separately reviewed task epoch')
    if args.backend=='arm':
        ledger.require(ledger.read(root/'phase4-state.json').get('complete'),'Phase4 must complete before setup profile')
    allocation=args.allocation or os.environ.get('LQCD_OPT_ALLOCATION')
    ledger.require(allocation,'Explicit allocation/comparison identity required')
    if args.backend=='arm':
        ledger.require(os.environ.get('LQCD_OPT_ALLOCATION')==allocation,'ARM worker allocation identity mismatch')
    deadline=args.deadline_epoch or float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH',time.time()+args.task_timeout-60))
    ledger.require(math.isfinite(deadline) and deadline>time.time(),'Finite future task/allocation deadline required')
    deadline=min(deadline,time.time()+args.task_timeout-30)
    config=ledger.campaign(campaign)[1]
    dependency,dependency_evidence=dependency_report(ledger,campaign,args.after_attempt,config,host,allocation,args.backend,
        args.dependency_state or root/'053-state.json',tools/'tools/optimization/bench_full12.py')
    ledger.require(dependency['comparison_key']['host']==host,'Dependency belongs to another host')
    if args.backend=='arm':
        ledger.require(dependency['comparison_key']['allocation']==allocation,
            'ARM sequencing dependency belongs to another allocation; no relabeling')
    attempt=campaign/'attempts'/args.id
    state_path=attempt/'cold-task-state.json'
    files=[Path(__file__).resolve(),aux/'cold_full12.py',aux/'profile_setup.py',aux/'prepare_best_replay.py',
        tools/'tools/optimization/campaign.py',tools/'tools/optimization/process_tree.py',
        tools/'tools/optimization/profile_full12.py',tools/'tools/optimization/bench_full12.py']
    contract=dict(host=host,allocation=allocation,backend=args.backend,ordinary=args.ordinary,
        after_attempt=args.after_attempt,dependency=dependency_evidence,
        helper_sha256={str(path):ledger.digest(path) for path in files})
    state=ledger.read(state_path) if state_path.exists() else {}
    ledger.require(not state or state['contract']==contract,'Retained task/source/helpers/host/allocation contract changed')
    if state.get('complete'):
        print('COLD_TASK_ALREADY_COMPLETE '+args.id,flush=True);return
    prior=ledger.read(attempt/'attempt.json') if (attempt/'attempt.json').exists() else {}
    cold_stage='cold-ordinary' if args.ordinary else 'cold-setup-profile'
    required=240 if prior.get('stages',{}).get(cold_stage,{}).get('status')=='passed' else 900
    if deadline-time.time()<required:
        pending=root/(args.id+'-pending.json')
        ledger.atomic(pending,dict(complete=False,status='pending',reason=f'Need >={required}s before remaining cold/setup/verification work',
                                  host=host,allocation=allocation,remaining_seconds=deadline-time.time()))
        print('COLD_TASK_PENDING '+str(pending),flush=True);return
    if not state:
        parent=ledger.read(campaign/'best.json')['attempt']
        parent_data,parent_report,_=ledger.checked_attempt(campaign,parent,config)
        ledger.require(parent_report['backend']==args.backend,'Selected best backend differs')
        if not attempt.exists():
            history=ledger.show_history(campaign)
            ledger.propose(campaign,args.id,dict(history_read_token=history['history_read_token'],
                bottleneck='Fresh hierarchy setup observed around207s while first12 API around16s; global basis/coarse work may be duplicated',
                hypothesis='Actual setup profile identifies coarse assembly versus basis orthogonalization/allocation cost before any distributed change',
                change='Auxiliary first-setup19Hz cycles sampling on ranks0/8' if not args.ordinary else 'Ordinary canonical-fixture fresh hierarchy first12 sample',
                mechanism='Continuous cold stage walls plus actual method/loaded-library/CPU/fault/RSS evidence; retain one full12 independent precision check',
                history_links=[str(root/'phase4-state.json'),str(campaign/'attempts'/args.after_attempt/'report.json'),
                    str(campaign/'attempts'/parent/'report.json')],
                retry_conditions='Fresh snapshot/output; no automatic failed/interrupted stage retry or reference/hash rewrite; profile times are unranked'))
        snapshot=ledger.snapshot_from(campaign,args.id,parent)
        state=dict(contract=contract,parent=parent,source_manifest_sha256=snapshot['source_manifest_sha256'],
            library_sha256=parent_report['library_sha256'],complete=False,status='prepared',created=ledger.now())
        ledger.atomic(state_path,state)
    parent=state['parent']
    # Preparation creates only scripts/selection, never executes numerical work.
    recipes=root/'cold-task-recipes'/args.id
    if not (recipes/'selection.json').exists():
        ledger.require(not recipes.exists(),'Incomplete recipe preparation retained; inspect and use new attempt')
        prepare=load('_cold_recipe_prepare',aux/'prepare_best_replay.py')
        fixture=(Path('/home/share/nsls_lwb/.cache/mg-20261102/propagator') if args.backend=='arm'
                 else root/'fixture-ls-canonical')
        gauge=(Path('/home/share/nsls_lwb/.cache/multigrid-arm-20261025/configuration24.lime') if args.backend=='arm'
               else Path('/public2/home/lwb_720/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime'))
        prepare.main(['--tools-project',str(tools),'--campaign',str(campaign),'--attempt',parent,
            '--fixture',str(fixture),'--gauge',str(gauge),'--backend',args.backend,'--allocation',allocation,
            '--output',str(recipes),'--python',args.python,'--cold-wrapper',str(aux/'cold_full12.py')])
    selection=ledger.read(recipes/'selection.json')
    cfg=selection['configuration'];plan=ledger.read(recipes/'plan.json')
    ledger.require(selection['selected_attempt']==parent and selection['source_manifest_sha256']==state['source_manifest_sha256']
        and selection['library_sha256']==state['library_sha256'],'Frozen recipe selection differs from task')
    numerical=load('_cold_numerical_policy',aux/'cold_full12.py').numerical_environment_keys(attempt/'source')
    remove=numerical|{'LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'}
    environment=['env']
    for key in sorted(remove):environment+=['-u',key]
    environment += [key+'='+str(value) for key,value in sorted(cfg['context_environment'].items())]
    environment += ['LQCD_VERBOSE=0','LQCD_HALO_PROFILE=0','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1']
    command=environment+[args.python,str(attempt/'source/tools/run_numa.py')]
    if args.backend=='x86':command += ['--ranks-per-numa','2']
    command += ['--threads',str(plan['placement_threads']),'--',args.python,'-u']
    if args.ordinary:
        command += [str(aux/'cold_full12.py')]
    else:
        command += [str(aux/'profile_setup.py'),'--cold-wrapper',str(aux/'cold_full12.py'),
            '--profile-helper',str(tools/'tools/optimization/profile_full12.py'),
            '--profile-output',str(attempt/'setup-profile'),'--frequency','19','--diagnostic']
    run=attempt/'measurements/cold-first12'
    command += ['--project',str(attempt/'source'),'--source-manifest',str(attempt/'source-manifest.json'),
        '--snapshot-sha',state['source_manifest_sha256'],'--library',selection['library'],
        '--expected-library-sha',state['library_sha256'],'--plan',str(recipes/'plan.json'),
        '--fixture',selection['fixture'],'--reference-propagator',selection['reference_propagator'],
        '--backend',args.backend,'--allocation',allocation,'--output',str(run)]
    script=recipes/'run-reviewed-cold-task.sh'
    text='#!/bin/bash\nset -eo pipefail\nsource '+shlex.quote(str(recipes/'site-environment.sh'))+'\n'+shlex.join(command)+'\n'
    if script.exists():ledger.require(script.read_text()==text,'Retained launch script changed')
    else:script.write_text(text)
    frozen={str(path):ledger.digest(path) for path in [recipes/'selection.json',recipes/'plan.json',script,recipes/'site-environment.sh']}
    ledger.require(not state.get('recipe_sha256') or state['recipe_sha256']==frozen,'Recipe files changed after checkpoint')
    state['recipe_sha256']=frozen;ledger.atomic(state_path,state)
    def stage(name,argv,timeout,env):
        request=dict(argv=list(map(str,argv)),cwd=str(attempt/'build'),env=env,timeout_seconds=timeout)
        previous=state.setdefault('stage_commands',{}).get(name)
        if previous:
            ledger.require(all(previous[key]==request[key] for key in ('argv','cwd','env')),'Resumed stage argv/environment changed')
            request=previous  # passed command identity includes its original timeout
        else:
            ledger.require(timeout>0,'No bounded time remains for stage')
            state['stage_commands'][name]=request;ledger.atomic(state_path,state)
        result=ledger.run_stage(campaign,args.id,name,request)
        state.update(status=result['status'],last_stage=name);ledger.atomic(state_path,state)
        ledger.require(result['status']=='passed','Retained failed/unknown stage requires explicit recovery; no automatic retry')
    stage(cold_stage,
          ['/bin/bash',script],min(650,deadline-time.time()-260),{})
    if deadline-time.time()<240:
        state.update(status='pending_precision',complete=False,reason='Insufficient time for independent scalar12; no completed cold/profile acceptance')
        ledger.atomic(state_path,state);print('COLD_TASK_PENDING_PRECISION '+args.id,flush=True);return
    # Always use the recorded unchanged independent executables and baseline.
    for key,expected_key in [('reference','reference_sha256'),('extractor','extractor_sha256'),('reference_propagator','reference_propagator_sha256')]:
        ledger.require(ledger.digest(selection[key])==selection[expected_key],'Frozen reference evidence changed')
    verify=tools/'tools/optimization/bench_full12.py'
    stage('independent',[args.python,verify,'--verify',run,'--reference',selection['reference'],'--extractor',selection['extractor']],
        min(360,deadline-time.time()-45),dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close',
            OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',LD_PRELOAD='',PERF_COUNTER_ROOT='',LD_DEBUG=''))
    report=ledger.read(run/'result.json')
    for key,expected_key in [('reference','reference_sha256'),('extractor','extractor_sha256'),('reference_propagator','reference_propagator_sha256')]:
        ledger.require(ledger.digest(selection[key])==selection[expected_key],'Frozen reference evidence changed after verification')
    expected_scope=('cold_canonical_fixture_to_first12' if args.ordinary else 'profile_cold_canonical_fixture_to_first12')
    validation=report['verification']
    ledger.require(report['timing_scope']==expected_scope and len(report['samples'])==1
        and report['configuration']==selection['configuration']
        and len(report['samples'][0]['stats'])==12 and validation['complete'] and validation['passed']
        and validation['reference_sha256']==config['reference_sha256'] and validation['columns']==12
        and validation['max_true_residual']<=1e-8 and validation.get('solution_relative_error',float('inf'))<=1e-6,
        'Cold/profile full12 independent precision contract failed')
    ledger.require(ledger.read(campaign/'best.json')['attempt']==parent,'Best changed outside serial task; preserve evidence for review')
    conclusion=('Ordinary canonical-fixture fresh-hierarchy sample' if args.ordinary else 'Unranked setup profile')+\
        ' complete with independent scalar12 and solution checks; separate cold scope, no steady API promotion or distributed setup implementation'
    existing=ledger.read(attempt/'attempt.json')
    if not any(row['conclusion']==conclusion for row in existing.get('conclusions',[])):
        ledger.conclude(campaign,args.id,'inconclusive',conclusion,[str(run/'result.json'),str(state_path)])
    state.update(complete=True,status='complete',finished=ledger.now(),report_sha256=ledger.digest(run/'result.json'),
        scope=expected_scope,verification=validation,performance_adoption=False)
    ledger.atomic(state_path,state)
    print('COLD_TASK_COMPLETE '+json.dumps(dict(id=args.id,scope=expected_scope,cold_wall_seconds=report['cold_wall_seconds'],
        first12_api_seconds=report['first12_api_seconds'],verification=validation,performance_adoption=False)),flush=True)


def main(argv=None):
    args=parser().parse_args(argv)
    if args.backend=='x86' and not args.ordinary:
        parser().error('x86 task is ordinary canonical cold; no unnecessary raw mismatch/profile run')
    if not 900<=args.task_timeout<=1800:
        parser().error('Task timeout must be bounded900..1800s')
    if args.emit_task:
        print(json.dumps(task_record(args),indent=2));return
    execute(args)


if __name__=='__main__':main()
