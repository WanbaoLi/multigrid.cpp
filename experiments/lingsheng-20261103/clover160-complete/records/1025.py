"""Four fresh-process full12 Clover comparison; reuse tested campaign/protocol."""
from copy import deepcopy
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
AUX=ROOT/'aux-halo-v2-publication-v5'
HEAD='861613c703117c6b5b671e245a7142e217b09501'
OLD='052-reduce-on'

def qualification_paths(root):
    return (root/'158-clover-arm-qualify-worker13-state.json',
            root/'queue13/158-clover-arm-qualify-worker13.status.json')

def require(v,message):
    if not v:raise RuntimeError(message)

def gate(candidate,first,last,limits):
    drift=abs(first['median']-last['median'])/min(first['median'],last['median'])
    gains=[1-candidate['median']/control['median']for control in(first,last)]
    reasons=[]
    if drift>.05:reasons.append('control drift exceeds5percent')
    if any(v['spread']>limits['maximum_relative_spread']for v in(candidate,first,last)):reasons.append('excessive spread')
    if any(g<limits['minimum_gain']for g in gains):reasons.append('below frozen minimum gain against a control')
    if any(candidate['maximum']>=v['minimum']for v in(first,last)):reasons.append('ranges overlap a control')
    return dict(passed=not reasons,reasons=reasons,gains=gains,control_drift=drift)

def case_plan(base,mode):
    context=deepcopy(base['context_environment'])
    if mode is not None:context['LQCD_ARM_SVE_CLOVER_REUSE']=mode
    return dict(context_environment=context,setup_threads=37,placement_threads=37,
        cases=[dict(id='full12',threads=32,batch=2,environment=deepcopy(base['solve_environment']))])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--expected-self-sha',required=True);args=parser.parse_args()
    sys.dont_write_bytecode=True;sys.path.insert(0,str(AUX))
    import file_integrity as integrity
    import raw_protocol_publication_v2 as protocol
    import halo_v2_trial_publication_v5 as historical
    import owned_publication_audit_v3 as publication
    from raw_scalar_helper import source_bytes
    def sha(p,e=None):return integrity.read_dual(Path(p),e)['openssl_sha256']
    def read(p,e=None):return json.loads(source_bytes(Path(p),sha(p,e)))
    sha(__file__,args.expected_self_sha)
    require(socket.gethostname()=='cn19480'and os.environ.get('LQCD_OPT_TASK_ID'),'Owned compute task required')
    require(os.environ.get('LQCD_OPT_ALLOCATION')=='mg-opt-20261103-worker13','Actual new allocation required')
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH']);require(math.isfinite(deadline)and deadline-time.time()>=6300,'Four complete trial budgets plus cleanup required')
    require(len(os.sched_getaffinity(0))==592 and not any('libgomp.so'in l or'libkupl.so'in l for l in Path('/proc/self/maps').read_text().splitlines()),'Full clean parent required')
    protocol.verify_files(AUX)
    manifest=read(AUX/'halo-v2-trial-publication-v5-helpers.json','684739d825a50e7e7dbb8ab16fa1b2645725abf27a9aa65a42e2ecf3a9117851')
    for name,h in manifest['files'].items():sha(AUX/name,h)
    qstate_path,qstatus_path=qualification_paths(ROOT)
    qualified=read(qstate_path);qstatus=read(qstatus_path)
    require(qualified['complete']and qualified['status']=='passed'and qualified['source_head']==HEAD and qualified['actual_sve_widths']==[16,32,64],'Actual full ARM qualification required')
    require(qstatus['status']=='passed'and qstatus['returncode']==0 and qstatus['cleanup']['complete']and not qstatus['cleanup']['surviving_pids'],'Qualifier must be closed and cleaned')
    require(qualified['allocation']==os.environ['LQCD_OPT_ALLOCATION']and qualified['host']==socket.gethostname(),'Tests on this actual allocation required')
    source=ROOT/'source-clover-reuse-861';tools=source/'tools/optimization';sys.path.insert(0,str(tools));import campaign as ledger
    ledger.digest=sha
    campaign=ROOT/'campaign-clover-reuse-v1';owner=campaign/'attempts/000-arm-clover-tests';record=read(owner/'attempt.json')
    ledger.check_snapshot(owner,record)
    require(record['snapshot']==qualified['snapshot']and record['snapshot']['git_head']==HEAD,'Qualification snapshot differs')
    for s in record['stages'].values():
        require(s['status']=='passed'and s['returncode']==0 and s['cleanup']['complete']and not s['cleanup']['surviving_pids'],'All actual qualified stages must pass')
        sha(owner/s['log'],s['log_sha256'])
    sha(qualified['library'],qualified['library_sha256'])
    strict=historical.StrictFiles(integrity)
    limits,proof=historical.import_historical(SimpleNamespace(root=ROOT,campaign=campaign),ledger,strict)
    parent,parent_report,_=ledger.checked_attempt(campaign,OLD,limits);base=deepcopy(parent_report['configuration'])
    require(base['batch']==2 and base['threads']==32 and base['ranks']==16 and base['setup_threads']==base['placement_threads']==37,'Exact best resources required')
    bestsha=sha(ROOT/'campaign/best.json')
    profile=read(ROOT/'155-best-solve-profile-worker11-state.json')
    require(profile['complete']and profile['verification']['passed']and profile['host']=='cn19486','Completed profile motivates candidate; its timing is not reused')
    statepath=ROOT/'160-clover-full12-worker13-state.json';require(not statepath.exists(),'New identity required; never overwrite failed group')
    state=dict(complete=False,status='running',source_head=HEAD,qualified_library_sha256=qualified['library_sha256'],
        allocation=os.environ['LQCD_OPT_ALLOCATION'],host=socket.gethostname(),outcomes={},best_unchanged=OLD,
        hypothesis='Site-outer Clover reuses six input components across output rows without changing arithmetic order',
        profile_state_sha256=sha(ROOT/'155-best-solve-profile-worker11-state.json'),profile_epoch='Historical diagnostic only; all ordinary controls are fresh',
        history='Read143/150/155 profiles from prior cn19486, HaloV1 off-path regression and154 no adoption. New cn19480 has its own startup/HBW/SVE gate; no cross-node timing comparison is used. Four fresh processes isolate cached Clover flag; no old timing reuse.')
    ledger.atomic(statepath,state)
    reference=Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid');fixture=Path('/home/share/nsls_lwb/.cache/mg-20261102/propagator')
    labels=[('160-clover-control-a',None),('160-clover-new-off',0),('160-clover-new-on',1),('160-clover-control-b',None)]
    try:
        for name,mode in labels:
            require(deadline-time.time()>=1545 and sha(ROOT/'campaign/best.json')==bestsha,'Budget/best changed before next complete case')
            plan=case_plan(base,mode)
            proposal=dict(bottleneck='Profiles143/150/155 fine/local costs; repeated Clover input loads across six rows',
                hypothesis=state['hypothesis'],change='Old accepted052 control'if mode is None else 'Exact861 Clover reuse='+str(mode),
                mechanism='Own hierarchy per fresh process, complete12 zero guesses, warmup plus three steady calls; full independent scalar/gold check',
                history_links=[str(ROOT/'155-best-solve-profile-worker11-state.json'),'docs/arm-clover-reuse-candidate.md',str(ROOT/'v2-w10v5-state.json')],
                retry_conditions='First actually qualified ARM Clover trial; old controls bracket fresh off/on, frozen gates unchanged')
            d=ROOT/'clover-full12-v1-plans';d.mkdir(exist_ok=True);pp=d/(name+'-proposal.json');pl=d/(name+'-plan.json')
            integrity.write_json_private(pp,proposal);integrity.write_json_private(pl,plan)
            argv=['--campaign',campaign,'--id',name,'--proposal',pp,'--plan',pl,
                '--reuse-attempt',OLD if mode is None else '000-arm-clover-tests',
                '--fixture',fixture,'--reference',reference,'--extractor',reference.with_name('extract_columns'),
                '--reference-propagator',fixture/'propagator.npy','--backend','arm','--allocation',state['allocation']]
            if mode is None:argv+=['--source-from',OLD]
            command=protocol.command(AUX,tools/'trial.py',sha(tools/'trial.py'),name,sys.executable,list(map(str,argv)),
                framework_tools=tools,benchmark_sha=protocol.BENCHMARK_SHA,gold_sha=protocol.GOLD_SHA)
            env=dict(os.environ)
            for k in list(env):
                if (k.startswith(('LQCD_','NATIVE_'))and not k.startswith('LQCD_OPT_'))or k in('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):env.pop(k,None)
            env.update(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_PROC_BIND='close')
            with(ROOT/(name+'.log')).open('xb')as output:
                result=subprocess.run(command,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=1500)
            require(result.returncode==0,'Retain failed case; no automatic retry: '+name)
            attempt,report,summary=ledger.checked_attempt(campaign,name,limits);v=report['verification']
            require(v['complete']and v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8 and len(v['solution_relative_errors'])==12 and max(v['solution_relative_errors'])<=1e-6,'All12 scalar and solution checks required')
            require(report['library_sha256']==(parent_report['library_sha256']if mode is None else qualified['library_sha256']),'Actual measured library differs')
            checked=publication.warm(campaign/'attempts'/name,campaign/'attempts'/name/'measurements/full12',report,AUX,sha,manifest['files'])
            ledger.atomic(campaign/'attempts'/name/'publication-closure.json',dict(complete=True,pinned_files=checked))
            times=[s['wall_seconds']for s in report['samples']if not s['warmup']];require(len(times)==3,'Three complete steady calls required')
            value=dict(median=statistics.median(times),minimum=min(times),maximum=max(times),spread=(max(times)-min(times))/statistics.median(times),steady=times,
                scalar_max=v['max_true_residual'],gold_max=v['solution_relative_error'],resources=report['resources'],comparison_key=report['comparison_key'],report_sha256=sha(campaign/'attempts'/name/'report.json'))
            state['outcomes'][name]=value;ledger.atomic(statepath,state);print('CLOVER_FULL12_CASE '+json.dumps(dict(name=name,median=value['median'])),flush=True)
        values=state['outcomes'];first,last=values[labels[0][0]],values[labels[-1][0]]
        require(all(v['resources']==first['resources']and v['comparison_key']==first['comparison_key']for v in values.values()),'Actual resources/physics differ')
        state['assessments']={n:gate(values[n],first,last,limits)for n,_ in labels[1:-1]}
        state.update(complete=True,status='complete',adopted=False,main_best_unchanged=sha(ROOT/'campaign/best.json')==bestsha,
            next='Review actual codegen and ordinary bracket; main best can change only after review of all evidence')
        ledger.atomic(statepath,state);print('CLOVER_FULL12_COMPLETE '+json.dumps(state['assessments']),flush=True)
    except BaseException as error:
        state.update(complete=False,status='failed',error=repr(error));ledger.atomic(statepath,state);raise

if __name__=='__main__':main()
