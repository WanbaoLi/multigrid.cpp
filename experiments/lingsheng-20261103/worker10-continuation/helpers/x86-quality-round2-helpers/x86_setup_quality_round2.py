"""Bounded hierarchy-quality comparison on the canonical full12 fixture."""
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import statistics
import subprocess
import sys
root=Path('/public2/home/lwb_720/.cache/mg-opt-clover-reuse-v1-20261104')
aux=root/'quality-round2-helpers';sys.path.insert(0,str(aux))
import file_integrity as integrity
import raw_protocol_publication_v2 as protocol
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path):return json.loads(source_bytes(path,sha(path)))
def gate(candidate,first,last):
    drift=abs(first['median']-last['median'])/min(first['median'],last['median'])
    gains=[1-candidate['median']/v['median']for v in(first,last)]
    return dict(passed=drift<=.05 and all(g>=.03 for g in gains)and
        all(candidate['maximum']<v['minimum']for v in(first,last))and
        all(v['spread']<=.1 for v in(candidate,first,last)),control_drift=drift,gains=gains)
def main():
    assert socket.gethostname().split('.')[0]=='node5005'and os.environ.get('LQCD_OPT_TASK_ID')
    assert len(os.sched_getaffinity(0))==256
    protocol.verify_files(aux)
    helpers=read(aux/'quality-manifest.json')
    for name,expected in helpers['files'].items():sha(aux/name,expected)
    qualified=read(root/'000-summary.json');assert qualified['complete']and qualified['status']=='passed'
    assert qualified['source_commit']=='861613c703117c6b5b671e245a7142e217b09501'
    source=root/'source';tools=source/'tools/optimization';sys.path.insert(0,str(tools));import campaign as ledger
    ledger.digest=sha;campaign=root/'campaign'
    old=Path('/public2/home/lwb_720/.cache/mg-opt-20261103');fixture=old/'fixture-ls-canonical'
    report=read(old/'campaign-canonical/attempts/001-canonical-profile-t12/report.json')
    assert report['verification']['passed']and report['verification']['columns']==12
    benchmark=Path(qualified['snapshot']['source'])/'tools/optimization/bench_full12.py'
    sha(benchmark,'711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1')
    reference=Path('/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid')
    extractor=reference.with_name('extract_columns');gold=Path(report['reference_propagator'])
    cfg=deepcopy(report['configuration']);cfg['context_environment'].update(LQCD_ARM_SVE_CLOVER_REUSE=0,
        LQCD_MG_SETUP_ITERATIONS=3,LQCD_MG_SETUP_SMOOTH=12)
    if (campaign/'attempts/quality-200-control-a/attempt.json').exists():
        old_case=ledger.read(campaign/'attempts/quality-200-control-a/attempt.json')
        if not old_case.get('conclusions'):
            ledger.conclude(campaign,'quality-200-control-a','inconclusive',
                'No numerical run: source_from requires an accepted complete report. New210-213 use fresh source snapshots and reuse only the exact tested binary; no gate or expected digest is relaxed.',
                [str(root/'quality-200-control-a.log')])
    previous=read(root/'quality-v3-summary.json');assert previous['complete']
    assert not any(v['passed']for v in previous['gates'].values())
    tests=ledger.run_stage(campaign,'000-clover-reuse-tests','paper-ctest',dict(argv=['ctest','--test-dir',qualified['snapshot']['build'],
        '--parallel','1','--output-on-failure','-V','-R','^runtime_paper$'],cwd=qualified['snapshot']['build'],timeout_seconds=300,
        env=dict(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')))
    assert tests['status']=='passed'and tests['cleanup']['complete'],'Existing EO/paper numerical prerequisite failed'
    labels=[('quality-230-control-a',2,3,'inverse'),('quality-231-refresh3x2',3,2,'inverse'),('quality-232-paper',2,3,'paper'),('quality-233-control-b',2,3,'inverse')]
    outcomes={}
    for name,passes,updates,mode in labels:
        context=dict(cfg['context_environment'],LQCD_MG_SETUP_PASSES=passes,LQCD_MG_SETUP_ITERATIONS=updates,LQCD_SETUP_UPDATE=mode)
        plan=dict(context_environment=context,setup_threads=16,placement_threads=16,
            cases=[dict(id='full12',threads=12,batch=2,environment=cfg['solve_environment'])])
        proposal=dict(bottleneck='Completed ARM143 shows24-25 outer iterations and repeated SAP/coarse work; history44plans has no explicit setup-quality case',
            hypothesis='Round1 passes4 increased outeriterations23.5 versus21.4; keep total6inverse updates but reorthogonalize/rebuild more frequently (3x2), or change vector update to paper under current EO',
            change='Same validated native binary; passes='+str(passes)+' updates='+str(updates)+' mode='+mode+' smooth12 fixed24vectors',
            mechanism='Fresh hierarchy, same total6updates3x2 versus2x3 isolates recoarsening frequency; EO+paper differs from historical full-block paper failure; controls bracket all new cases',
            history_links=['https://arxiv.org/abs/1303.1377','docs/arm-clover-reuse-candidate.md',str(old/'campaign-canonical/attempts/001-canonical-profile-t12/report.json')],
            retry_of='quality-222-pass4',retry_conditions='Read completed round1 before retry: extra4passes worsened outer convergence; test unchanged6update total with more coarse refreshes, plus different EO+paper mechanism under clarified hierarchy-reuse objective; no old failed output reuse; no ARM speedup inference')
        directory=root/'quality-plans';directory.mkdir(exist_ok=True)
        pp=directory/(name+'-proposal.json');pl=directory/(name+'-plan.json')
        integrity.write_json_private(pp,proposal);integrity.write_json_private(pl,plan)
        argv=[sys.executable,str(tools/'trial.py'),'--campaign',str(campaign),'--id',name,'--proposal',str(pp),'--plan',str(pl),
            '--reuse-attempt','000-clover-reuse-tests',
            '--fixture',str(fixture),'--reference',str(reference),'--extractor',str(extractor),'--reference-propagator',str(gold),
            '--backend','x86','--allocation','node5005-quality-20261104-epoch1']
        # Use the established strict input/output publication and independent
        # scalar helper chain; no numerical or timer function is transformed.
        command=protocol.command(aux,tools/'trial.py',sha(tools/'trial.py'),name,sys.executable,argv[2:],
            framework_tools=tools,benchmark_sha=protocol.BENCHMARK_SHA,gold_sha=sha(gold))
        log=root/(name+'.log')
        env=dict(os.environ)
        for key in list(env):
            if(key.startswith(('LQCD_','NATIVE_'))and not key.startswith('LQCD_OPT_'))or key in('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):
                env.pop(key,None)
        env.update(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_PROC_BIND='close')
        with log.open('xb')as stream:
            result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        assert result.returncode==0,'Retain failed quality trial, no automatic retry'
        limits=ledger.campaign(campaign)[1];_,measured,summary=ledger.checked_attempt(campaign,name,limits)
        v=measured['verification'];assert v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8 and v['solution_relative_error']<=1e-6
        samples=[row for row in measured['samples']if not row['warmup']];times=[row['wall_seconds']for row in samples]
        outcomes[name]=dict(passes=passes,updates_per_pass=updates,setup_mode=mode,median=statistics.median(times),minimum=min(times),maximum=max(times),
            spread=(max(times)-min(times))/statistics.median(times),steady_seconds=times,
            iterations=[[r['iterations']for r in row['stats']]for row in samples],setup_seconds=measured.get('setup_seconds'),
            native_setup_seconds=measured.get('native_setup_seconds'),scalar_max=v['max_true_residual'],gold_max=v['solution_relative_error'],
            report_sha256=sha(campaign/'attempts'/name/'report.json'))
        integrity.write_json_private(root/(name+'-summary.json'),outcomes[name]);print('QUALITY_CASE '+json.dumps(outcomes[name]),flush=True)
    first,last=outcomes[labels[0][0]],outcomes[labels[-1][0]]
    summary=dict(complete=True,scope='Actual repeated canonical full12 x86 quality experiment; no ARM acceptance or main best change',
        outcomes=outcomes,gates={name:gate(outcomes[name],first,last)for name,*_ in labels[1:-1]},
        historical_profile_scope='ARM143 motivates hypothesis only; all performance controls are fresh node5005',
        direct_ssh_not_scheduler_exclusive=True,main_arm_best_unchanged=True)
    integrity.write_json_private(root/'quality-round2-summary.json',summary);print('QUALITY_COMPLETE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
