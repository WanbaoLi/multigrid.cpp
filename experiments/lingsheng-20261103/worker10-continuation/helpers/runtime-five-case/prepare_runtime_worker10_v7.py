"""Prepare fresh runtime-only comparison after a verified retained-best profile."""
import argparse
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import file_integrity as integrity
import raw_protocol_publication_v2 as protocol
from raw_scalar_helper import source_bytes

BUDGET=4800
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def closed(status,expected):
    return(status.get('status')==expected and type(status.get('returncode'))is int and
        (status['returncode']==0 if expected=='passed'else status['returncode']!=0)and bool(status.get('task_tag'))and
        status.get('cleanup',{}).get('complete')is True and status['cleanup'].get('surviving_pids')==[])

def prepare(request):
    root=Path(request['root']).resolve(strict=True);aux=Path(__file__).resolve().parent
    pins=[]
    def get(key):
        row=request[key];value=read(row['path'],row['sha256']);pins.append(row);return value
    startup=get('startup');prior=get('failed_state');prior_status=get('failed_status')
    profile=get('profile_state');profile_status=get('profile_status');wrapper=get('profile_wrapper')
    manifest=get('runtime_manifest');helpers=read(aux/'runtime-worker10-v7-files.json',request['helper_manifest_sha256'])
    best=read(root/'campaign/best.json');name=request['id'];prefix=request['prefix']
    require=integrity.require
    require(name=='147-runtime-only-worker10-v6'and prefix=='p5w10v6','Reviewed concrete fresh identity required')
    require(prior.get('status')=='failed'and prior.get('complete')is False and closed(prior_status,'failed'),'Keep attributed prior failure and require terminal cleanup')
    require(profile.get('complete')is True and closed(profile_status,'passed')and wrapper.get('complete')is True and wrapper.get('passed')is True,
        'Retained-best full12 diagnostic and sampled-call checks must finish first')
    v=profile.get('verification',{})
    require(v.get('complete')is True and v.get('passed')is True and v.get('columns')==12,'New full12 independent precision required')
    require(best['attempt']==prior.get('expected_best')==profile.get('best')=='052-reduce-on','Best changed; prepare a new design')
    require(startup['complete']and profile_status['host']==profile['host']and prior_status['host']==prior['contract']['host'],
        'Each historical predecessor must bind its own actual host; never relabel an old epoch')
    require(request.get('historical_profile_scope')=='hotspot selection only; all five ordinary cases fresh current allocation',
        'Explicit cross-epoch profile scope required; old timings are never controls')
    require(startup['safe_deadline_epoch']-time.time()>=BUDGET+90,'Whole5 runtime-case budget does not fit')
    binding=manifest['worker_startup'];require(all(binding.get(k)==v for k,v in dict(path=request['startup']['path'],sha256=request['startup']['sha256'],
        host=startup['host'],allocation=startup['allocation']).items()),'Runtime manifest belongs to another startup')
    require(manifest['base_ld_library_path']==startup['loader_environment']['LD_LIBRARY_PATH'],'Runtime startup loader differs')
    for file,expected in helpers['files'].items():
        sha(aux/file,expected);pins.append(dict(path=str(aux/file),sha256=expected))
    protocol.verify_files(aux)
    tools=root/'source/tools/optimization';sys.path.insert(0,str(tools));ledger=importlib.import_module('campaign')
    require(Path(ledger.__file__).resolve()==tools/'campaign.py','Wrong campaign module');ledger.digest=sha
    _,limits=ledger.campaign(root/'campaign');data,report,summary=ledger.checked_attempt(root/'campaign',best['attempt'],limits)
    require(profile['library_sha256']==report['library_sha256']and profile['source_manifest_sha256']==report['source_manifest_sha256'],
        'Historical profile must describe exact retained numerical library/source')
    import phase5_runtime_only_v6 as controller
    controller.base.check_shim_manifest(manifest,sha)
    variants=controller.base.runtime_variants(report['configuration'],prefix,manifest);case_ids=[row[0]for row in variants]
    state=root/(name+'-state.json');audit=root/(name+'-runtime-audit');output=Path(request['output']);queue=root/request['queue']
    future=[state,audit,output];future.extend(queue.glob('*.ready.json'));future.extend(queue.glob('*.running.json'));future.extend(queue.glob(name+'.*'))
    for case in case_ids:
        future.extend([root/'campaign/attempts'/case,root/'plans'/(case+'.json'),root/'proposals'/(case+'.json')])
        future.extend((root/'phase5-shim-logs').glob(case+'-*.log'))
    require(not any(path.exists()or path.is_symlink()for path in future),'Used runtime namespace or active task')
    policy_path=aux/'cold_full12.py';sha(policy_path,'245ecd8201c1268c8e3a78ba64383ce7dce6334709fe5856deac8033ed39a1de')
    spec=importlib.util.spec_from_file_location('_existing_numerical_keys',policy_path);policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
    entry=aux/'phase5_runtime_only_v6.py'
    controller_args=['--root',str(root),'--state',str(state),'--prefix',prefix,'--expected-host',startup['host'],
        '--runtime-shim-manifest',request['runtime_manifest']['path'],'--runtime-shim-manifest-sha',request['runtime_manifest']['sha256'],
        '--runtime-audit-dir',str(audit),'--external-runtime-audit']
    contract=dict(schema='runtime-only-scope-v6',complete=True,status='prepared_not_queued',id=name,root=str(root),queue=request['queue'],
        host=startup['host'],allocation=startup['allocation'],expected_best=best['attempt'],request=request,pinned_files=pins,
        expected_parent_cpus=sorted(startup['before_worker_exec_parent_state']['cpus']),startup_ld_library_path=manifest['base_ld_library_path'],
        state=str(state),runtime_audit_dir=str(audit),case_ids=case_ids,task_timeout_seconds=BUDGET,
        numerical_environment_keys=sorted(policy.numerical_environment_keys(Path(data['snapshot']['source']))),
        startup_clear_keys=['LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'],
        controller=dict(path=str(entry),sha256=sha(entry),argv=controller_args),
        prior_failure_retained=True,old_samples_imported=False,historical_profile_scope=request['historical_profile_scope'],numerical_trials_and_decisions_inherited=True)
    output.mkdir(parents=True,exist_ok=False,mode=0o700);integrity.write_json_private(output/'contract.json',contract)
    guard=aux/'runtime_only_scope_v6.py'
    argv=protocol.command(aux,guard,sha(guard),name,request['python'],['--contract',str(output/'contract.json'),
        '--contract-sha',sha(output/'contract.json')],framework_tools=tools,benchmark_sha=protocol.BENCHMARK_SHA)
    at=argv.index(str(aux/'raw_controller_publication_v2.py'))
    argv=[*argv[:at],str(aux/'raw_controller_setup_capture_v6.py'),'--expected-self-sha',sha(aux/'raw_controller_setup_capture_v6.py'),
        '--capture-wrapper-sha',sha(aux/'runtime_benchmark_capture_v6.py'),'--',*argv[at+1:]]
    task=dict(argv=argv,cwd=str(aux),timeout=BUDGET,environment=dict(LD_LIBRARY_PATH=manifest['base_ld_library_path'],
        LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT='',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',LQCD_OPT_CAPTURE_DIR=str(audit),LQCD_OPT_CAPTURE_BASE_LD=manifest['base_ld_library_path']))
    integrity.write_json_private(output/'task.json',task)
    return dict(complete=True,status='prepared_not_queued',case_ids=case_ids,
        contract_sha256=sha(output/'contract.json'),task_sha256=sha(output/'task.json'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha',required=True)
    args=p.parse_args();print(json.dumps(prepare(read(args.request,args.request_sha)),indent=2),flush=True)

if __name__=='__main__':main()
