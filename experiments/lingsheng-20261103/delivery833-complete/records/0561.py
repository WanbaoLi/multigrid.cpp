"""Two fresh processes on deliverable source; actual full12 timing and accuracy."""
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
ROOT=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105')
OLD=Path('/public2/home/lwb_720/.cache/mg-opt-20261103')
AUX=Path('/public2/home/lwb_720/.cache/mg-opt-clover-reuse-v1-20261104/quality-v3-helpers')
def main():
    assert socket.gethostname()=='node5005'and os.environ.get('LQCD_OPT_TASK_ID')and len(os.sched_getaffinity(0))==256
    sys.path.insert(0,str(AUX));import file_integrity as integrity
    import raw_protocol_publication_v2 as protocol
    from raw_scalar_helper import source_bytes
    def sha(p,e=None):return integrity.read_dual(Path(p),e)['openssl_sha256']
    def read(p):return json.loads(source_bytes(Path(p),sha(p)))
    protocol.verify_files(AUX)
    helpers=read(AUX/'quality-manifest.json')
    for name,h in helpers['files'].items():sha(AUX/name,h)
    q=read(ROOT/'000-summary.json');qs=read(ROOT/'queue/000-correctness.status.json')
    assert q['complete']and q['status']=='passed'and q['source_commit']=='833f8732f6b06e370074efbb610fc7a85fe11a46'
    assert qs['status']=='passed'and qs['cleanup']['complete']and not qs['cleanup']['surviving_pids']
    source=ROOT/'source';tools=source/'tools/optimization';sys.path.insert(0,str(tools));import campaign as ledger
    ledger.digest=sha;camp=ROOT/'campaign'
    parent=read(OLD/'campaign-canonical/attempts/001-canonical-profile-t12/report.json')
    cfg=deepcopy(parent['configuration']);assert cfg['threads']==12 and cfg['batch']==2 and cfg['ranks']==16
    assert cfg.get('placement_threads',16)==16 and cfg.get('setup_threads',16)==16
    gold=Path(parent['reference_propagator']);assert sha(gold)=='57fd4bf992784af092dced0a8f84b8b7383b28e5be1014fab3a2bedee079a0bd'
    reference=Path('/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid')
    outcomes={}
    for name in('100-delivery-full12-a','101-delivery-full12-b'):
        plan=dict(context_environment=cfg['context_environment'],setup_threads=16,placement_threads=16,
            cases=[dict(id='full12',threads=12,batch=2,environment=cfg['solve_environment'])])
        proposal=dict(bottleneck='Final coherent source needs measured same-physics node5005 comparison',
            hypothesis='Accepted052 numerical source restored in delivery833 retains prior x86 performance and independent accuracy',
            change='Fresh hierarchy on qualified exact833 build; current x86 default2x3 setup and retained resource plan',
            mechanism='Two independent fresh processes, one full12 warmup plus3steady each; all12 scalar/gold verification',
            history_links=['docs/optimization-progress-20261104.md',str(OLD/'campaign-canonical/attempts/001-canonical-profile-t12/report.json')],
            retry_conditions='New delivery source and new ordinary epoch; no old timings reused')
        pp=ROOT/(name+'-proposal.json');pl=ROOT/(name+'-plan.json');integrity.write_json_private(pp,proposal);integrity.write_json_private(pl,plan)
        argv=['--campaign',camp,'--id',name,'--proposal',pp,'--plan',pl,'--reuse-attempt','000-delivery-tests',
            '--fixture',OLD/'fixture-ls-canonical','--reference',reference,'--extractor',reference.with_name('extract_columns'),
            '--reference-propagator',gold,'--backend','x86','--allocation','node5005-delivery-20261105-epoch1']
        command=protocol.command(AUX,tools/'trial.py',sha(tools/'trial.py'),name,sys.executable,list(map(str,argv)),
            framework_tools=tools,benchmark_sha=protocol.BENCHMARK_SHA,gold_sha=sha(gold))
        env=dict(os.environ)
        for key in list(env):
            if(key.startswith(('LQCD_','NATIVE_'))and not key.startswith('LQCD_OPT_'))or key in('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):env.pop(key,None)
        env.update(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_PROC_BIND='close')
        with(ROOT/(name+'.log')).open('xb')as output:r=subprocess.run(command,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=1800)
        assert r.returncode==0,'Retain failed trial and use explicit new attempt after attribution'
        _,report,_=ledger.checked_attempt(camp,name,ledger.campaign(camp)[1]);v=report['verification']
        assert v['complete']and v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8 and len(v['solution_relative_errors'])==12 and max(v['solution_relative_errors'])<=1e-6
        assert report['library_sha256']==q['library_sha256']and report['configuration']==cfg
        times=[s['wall_seconds']for s in report['samples']if not s['warmup']];assert len(times)==3
        outcomes[name]=dict(median=statistics.median(times),steady=times,scalar_max=v['max_true_residual'],gold_max=v['solution_relative_error'],
            setup_seconds=report.get('setup_seconds'),native_setup_seconds=report.get('native_setup_seconds'),
            source_manifest_sha256=report['source_manifest_sha256'],library_sha256=report['library_sha256'],report_sha256=sha(camp/'attempts'/name/'report.json'))
        integrity.write_json_private(ROOT/(name+'-summary.json'),outcomes[name]);print('DELIVERY_FULL12_CASE '+json.dumps(outcomes[name]),flush=True)
    medians=[v['median']for v in outcomes.values()];drift=abs(medians[0]-medians[1])/min(medians)
    result=dict(complete=True,outcomes=outcomes,control_drift=drift,stable=drift<=.05,main_arm_best_unchanged=True,
        direct_ssh_not_scheduler_exclusive=True,scope='Final exact delivery source full12 node5005 comparison; all physics/tolerance identical, machine-specific stored references')
    integrity.write_json_private(ROOT/'full12-summary.json',result);print('DELIVERY_FULL12_COMPLETE '+json.dumps(result),flush=True)
if __name__=='__main__':main()
