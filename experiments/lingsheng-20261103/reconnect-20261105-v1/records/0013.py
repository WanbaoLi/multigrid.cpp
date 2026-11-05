"""Prepare a fresh actual-allocation profile after a terminal predecessor; never enqueue."""
import argparse
import importlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time

FROZEN_AUX=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103/aux-solve-profile-v7')
sys.path.insert(0,str(FROZEN_AUX))
import file_integrity as integrity
import raw_protocol_publication_v2 as protocol
from raw_scalar_helper import source_bytes

BUDGET=3600
RESERVE=90
POST_SHA='4b903cf20ec4845e3be402c740a503915fd1ed0fbd186008f879f5d38dfafc97'


def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']


def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))


def readiness(state,status,startup,best,now,previous):
    reasons=[]
    terminal=(status.get('status')=='passed'and status.get('returncode')==0 and state.get('complete')is True and state.get('status')=='complete')or(
        status.get('status')in('failed','timeout')and type(status.get('returncode'))is int and status['returncode']!=0 and state.get('status')in('failed','interrupted','pending'))
    if not terminal:reasons.append('Closed predecessor scope required; no active/pending task is reclassified')
    if not(status.get('task_tag')and status.get('cleanup',{}).get('complete')is True and status.get('cleanup',{}).get('surviving_pids')==[]):
        reasons.append('Every owned predecessor process must be cleaned')
    retained={state.get('expected_best'),state.get('best'),state.get('initial_best')}
    if best.get('attempt')not in retained:reasons.append('Current accepted best is not bound to predecessor state')
    if not(startup.get('complete')is True and previous.get('complete')is True and
        startup.get('previous_job')==str(previous.get('scheduler_job'))and startup.get('allocation')!=previous.get('allocation')and
        state.get('allocation')==previous.get('allocation')and
        state.get('host')==status.get('host')==previous.get('host')==startup.get('host')):
        reasons.append('New actual allocation must follow the authenticated predecessor on this same target host')
    deadline=startup.get('safe_deadline_epoch',0)
    remaining=deadline-now if type(deadline)in(int,float)and math.isfinite(deadline)else 0
    if remaining<BUDGET+RESERVE:reasons.append('Need3600s diagnostic budget plus90s reserve')
    return dict(passed=not reasons,reasons=reasons,remaining_seconds=remaining,task_timeout_seconds=BUDGET,
        original_trial_stage_caps_preserved=True,predecessor_scope_status=state.get('status'),
        prior_failure_not_reclassified=True,new_allocation=True,old_performance_samples_imported=False,
        purpose='New unranked profile of the actual accepted best; predecessor measurements retain their old epoch')


def prepare(request):
    root=Path(request['root']).resolve(strict=True);aux=FROZEN_AUX
    output=Path(request['output']).resolve();profile=Path(request['profile_output']).resolve()
    name=request['id'];integrity.require(re.fullmatch('[a-z0-9][a-z0-9_-]{0,79}',name),'Safe new profile ID required')
    startup=read(request['startup']['path'],request['startup']['sha256'])
    state=read(request['predecessor_state']['path'],request['predecessor_state']['sha256'])
    previous=read(request['predecessor_startup']['path'],request['predecessor_startup']['sha256'])
    status=read(request['predecessor_status']['path'],request['predecessor_status']['sha256'])
    best=read(root/'campaign/best.json')
    gate=readiness(state,status,startup,best,time.time(),previous)
    if not gate['passed']:return dict(complete=False,status='pending',gate=gate)
    manifest=read(aux/'solve-profile-v7-files.json',request['helper_manifest_sha256'])
    for path,expected in manifest['files'].items():sha(aux/path,expected)
    protocol.verify_files(aux);sha(aux/'post_phase4_profile.py',POST_SHA)
    future=[output,profile,root/(name+'-state.json'),root/'campaign/attempts'/name,
            root/'plans'/(name+'.json'),root/'proposals'/(name+'.json')]
    queue=root/request['queue']
    future.extend(queue.glob(name+'.*'));future.extend(queue.glob('*.ready.json'));future.extend(queue.glob('*.running.json'))
    integrity.require(not any(path.exists()or path.is_symlink()for path in future),'Existing/pending identity; explicit recovery required')
    tools=root/'source/tools/optimization';sys.path.insert(0,str(tools))
    ledger=importlib.import_module('campaign')
    integrity.require(Path(ledger.__file__).resolve()==tools/'campaign.py','Wrong campaign module')
    ledger.digest=sha
    _,limits=ledger.campaign(root/'campaign')
    data,report,summary=ledger.checked_attempt(root/'campaign',best['attempt'],limits)
    args=['--root',str(root),'--id',name,'--retry-of',request.get('retry_of','150-best-solve-profile-worker10')]
    policy_path=aux/'cold_full12.py'
    sha(policy_path,'245ecd8201c1268c8e3a78ba64383ce7dce6334709fe5856deac8033ed39a1de')
    spec=importlib.util.spec_from_file_location('_existing_numerical_environment_keys',policy_path)
    policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
    numerical=sorted(policy.numerical_environment_keys(Path(data['snapshot']['source'])))
    pins=[dict(path=str(aux/path),sha256=expected)for path,expected in manifest['files'].items()]
    contract=dict(preparation_schema='new-allocation-profile-v8',preparer_sha256=sha(__file__),schema='solve-profile-scope-v7',complete=True,status='prepared_not_queued',id=name,
        root=str(root),queue=request['queue'],host=startup['host'],allocation=startup['allocation'],
        expected_best=best['attempt'],library_sha256=report['library_sha256'],source_manifest_sha256=report['source_manifest_sha256'],
        request=request,gate=gate,helper_manifest_sha256=request['helper_manifest_sha256'],helper_pins=pins,
        expected_parent_cpus=sorted(startup['before_worker_exec_parent_state']['cpus']),
        startup_ld_library_path=startup['loader_environment']['LD_LIBRARY_PATH'],profile_output=str(profile),
        numerical_environment_keys=numerical,task_timeout_seconds=BUDGET,
        startup_clear_keys=['LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'],
        controller=dict(path=str(aux/'post_phase4_profile.py'),sha256=POST_SHA,argv=args),
        ordinary_promotion=False,actual_profiled_stats_checked=True,
        independent_output_scope='last light diagnostic full12 sample; actual final sampled call additionally checks true-residual stats')
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    integrity.write_json_private(output/'contract.json',contract)
    guard=aux/'solve_profile_scope_v7.py';guard_sha=manifest['files']['solve_profile_scope_v7.py']
    argv=protocol.command(aux,guard,guard_sha,name,request['python'],
        ['--contract',str(output/'contract.json'),'--contract-sha',sha(output/'contract.json')],
        framework_tools=tools,benchmark_sha=protocol.BENCHMARK_SHA)
    original=str(aux/'raw_controller_publication_v2.py');index=argv.index(original)
    argv=[*argv[:index],str(aux/'raw_controller_solve_profile_v7.py'),
        '--expected-self-sha',manifest['files']['raw_controller_solve_profile_v7.py'],
        '--profile-wrapper-sha',manifest['files']['profile_benchmark_publication_v7.py'],'--',*argv[index+1:]]
    task=dict(argv=argv,cwd=str(aux),timeout=BUDGET,environment=dict(
        LD_LIBRARY_PATH=startup['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',
        PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT='',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        LQCD_OPT_SOLVE_PROFILE_OUTPUT=str(profile)))
    integrity.write_json_private(output/'task.json',task)
    return dict(complete=True,status='prepared_not_queued',contract_sha256=sha(output/'contract.json'),
                task_sha256=sha(output/'task.json'),gate=gate)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha',required=True);args=p.parse_args()
    result=prepare(read(args.request,args.request_sha));print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
