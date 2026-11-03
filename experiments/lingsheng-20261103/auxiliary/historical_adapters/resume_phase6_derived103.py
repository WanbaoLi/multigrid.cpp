"""Explicit phase6 continuation after a rejected newly assembled scratch gauge.

Original100 queue/state/stage/logs stay failed and unchanged. Passed numerical
stages keep their exact old commands. Only new verifier stages use the pinned
derived-output helper; all original timings and expected payload SHA stay fixed.
"""
import argparse
from copy import deepcopy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import signal
from types import SimpleNamespace
import sys
import time

import file_integrity as integrity
import raw_protocol_v4 as protocol
import raw_controller_v4 as adapter

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
PHASE_SHA='3f3537ca6a09fbe6b22ae06e488a5a50f334cc7e374fd7326d345c6113de63e6'
SOURCE='71160fac57d577d27423527e6b577c0593940d35'
ORIGINAL='100-phase6-halo-worker6'
OWNER='100-halo-new-off'

def read(path):return json.loads(Path(path).read_text())
def sha(path,expected=None):return integrity.read_dual(Path(path),expected)['openssl_sha256']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--helper',type=Path,required=True);p.add_argument('--helper-sha',required=True)
    p.add_argument('--publication',type=Path,required=True);p.add_argument('--publication-sha',required=True)
    p.add_argument('--original-state-sha',required=True);p.add_argument('--expected-entry-sha',required=True)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    integrity.known_vectors();sha(__file__,args.expected_entry_sha)
    sha(args.helper,args.helper_sha);sha(args.publication,args.publication_sha)
    for name,expected in protocol.FILES.items():sha(R/name,expected)
    sha(R/'phase6_halo.py',PHASE_SHA)
    sys.path.insert(0,str(R/'source/tools/optimization'));ledger=importlib.import_module('campaign')
    original_state_path=R/'100-halo-state.json';sha(original_state_path,args.original_state_sha)
    original=read(original_state_path);queue_status_path=R/'queue6'/(ORIGINAL+'.status.json');status=read(queue_status_path)
    integrity.require(status['status']=='failed' and status['returncode']!=0 and status['cleanup']['complete'] and
        original.get('complete') is False and original['status']=='failed' and
        original['source_head']==SOURCE and original['allocation']=='mg-opt-20261103-worker6',
        'Exact closed failed100 epoch required')
    integrity.require(os.environ.get('LQCD_OPT_ALLOCATION')==original['allocation'] and
        os.environ.get('LQCD_OPT_TASK_ID') and __import__('socket').gethostname()==original['host'],
        'Same owned compute allocation required')
    integrity.require(ledger.git(R/'source','rev-parse','HEAD')==SOURCE and
        not ledger.git(R/'source','status','--short'),'Reviewed source must stay clean711')
    old_owner=read(R/'campaign/attempts'/OWNER/'attempt.json')
    required=['configure','build','arm-ctest','sve-compiled-coarse','benchmark']
    required += ['sve-'+kind+'-vl'+str(width) for width in (16,32,64) for kind in ('dense','ghost-mpi4')]
    frozen_stages={}
    for name in ('100-halo-control-a',OWNER):
        record=read(R/'campaign/attempts'/name/'attempt.json')
        for key,value in record['stages'].items():
            if value['status']=='passed':
                integrity.require(sha(R/'campaign/attempts'/name/value['log'])==value['log_sha256'],'Passed log changed')
                frozen_stages[(name,key)]=deepcopy(value)
    integrity.require(all((OWNER,key) in frozen_stages for key in required) and
        all(('100-halo-control-a',key) in frozen_stages for key in ('benchmark','verify-full12')),
        'All original build/38CTest/SVE3/ordinary samples and controlA must already pass')
    failed=old_owner['stages']['verify-new-off']
    integrity.require(failed['status']=='failed' and failed['cleanup']['complete'] and
        sha(R/'campaign/attempts'/OWNER/failed['log'])==failed['log_sha256'],'Original verifier failure changed')
    failed_hash_path=R/'campaign/attempts'/OWNER/'checksum-audit/verify-new-off/helper/hash-003.json'
    bad=read(failed_hash_path)
    integrity.require(bad['passed'] is False and bad['byte_count_exact'] and bad['eof_probe_bytes']==0 and
        bad['read_bytes']==509607936 and bad['openssl_sha256']==bad['software_sha256']==bad['expected_sha256']==
        '126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834' and
        bad['initial']==bad['fd_before'] and bad['fd_after']==bad['path_after'] and
        all(bad['initial'][k]==bad['fd_after'][k] for k in ('dev','inode','bytes')) and
        bad['metadata_stable'] is False,'Only the documented freshly written scratch timestamp failure qualifies')
    home=R/'103-halo-recovery';contract_path=home/'contract.json';state_path=R/'103-halo-recovered-state.json'
    runs=R/'campaign/attempts'/OWNER/'measurements'
    current_reports={case:read(runs/case/'result.json') for case in ('new-off','halo-on')}
    if contract_path.exists():
        contract=read(contract_path)
        integrity.require(contract['entry_sha256']==args.expected_entry_sha and
            contract['helper_sha256']==args.helper_sha and contract['publication_sha256']==args.publication_sha and
            contract['original_state_sha256']==args.original_state_sha,'Recovery protocol identity changed')
    else:
        contract=dict(entry_sha256=args.expected_entry_sha,helper=str(args.helper),helper_sha256=args.helper_sha,
            publication=str(args.publication),publication_sha256=args.publication_sha,original_state_sha256=args.original_state_sha,
            original_queue_status_sha256=sha(queue_status_path),original_failure_hash_sha256=sha(failed_hash_path),
            original_failure_log_sha256=failed['log_sha256'],allocation=original['allocation'],host=original['host'],
            case_report_sha256={case:sha(runs/case/'result.json') for case in current_reports},
            original_measurements={case:{k:v for k,v in report.items() if k!='verification'} for case,report in current_reports.items()},
            rationale='Fresh self-produced scratch gauge already matched the fixed canonical SHA; keep first timestamp rejection, '
                'require two subsequent complete strict stable reads before accepting scratch publication. '
                'Immutable inputs/gold/prop checks and all12 scalar/gold gates remain unchanged. '
                'No passed timing, test, original state or original failure is rewritten.')
        home.mkdir(mode=0o700,exist_ok=False);integrity.write_json_private(contract_path,contract)
    if args.check:
        print('PHASE6_DERIVED_RECOVERY_PREFLIGHT_PASSED '+json.dumps(dict(passed_original_stages=len(frozen_stages),home=str(home))),flush=True)
        return
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
    integrity.require(deadline-time.time()>=2400,'Need2400s for remaining strict verification, diagnostic and oldB')
    if not state_path.exists():
        copy=deepcopy(original);copy['original_failure']=dict(state=str(original_state_path),sha256=args.original_state_sha,
            error=copy.pop('error',None));copy['derived_output_recovery']=dict(contract=str(contract_path),sha256=sha(contract_path))
        ledger.atomic(state_path,copy)
    base_stage=ledger.run_stage
    options=SimpleNamespace(entry=R/'phase6_halo.py',entry_sha=PHASE_SHA,framework_tools=R/'source/tools/optimization',
        audit_root=home/'runtime-adapter',wrapper=R/'raw_benchmark_v4.py',wrapper_sha=protocol.FILES['raw_benchmark_v4.py'],
        reader_sha=protocol.FILES['file_integrity.py'],adapter_sha=protocol.FILES['raw_controller_v4.py'],
        benchmark_sha=protocol.BENCHMARK_SHA,gold_sha=protocol.GOLD_SHA,helper_sha=protocol.HELPER_SHA,
        helper_wrapper=R/'raw_scalar_helper.py',helper_wrapper_sha=protocol.FILES['raw_scalar_helper.py'])
    adapter.install(options)
    def stage(campaign,name,key,command,*extra,**kwargs):
        request=adapter.transform_stage(options,campaign,name,key,command)
        if (name,key) not in frozen_stages and '--verify' in request['argv']:
            argv=request['argv'];argv[argv.index('--helper-wrapper')+1]=str(args.helper)
            argv[argv.index('--expected-helper-wrapper-sha')+1]=args.helper_sha
            if name==OWNER and key=='verify-new-off-derived-retry1':
                argv += ['--retry-existing-verification-sha',contract['case_report_sha256']['new-off']]
        return base_stage(campaign,name,key,request,*extra,**kwargs)
    ledger.run_stage=stage
    spec=importlib.util.spec_from_file_location('frozen_phase6_recovery',R/'phase6_halo.py')
    phase=importlib.util.module_from_spec(spec);spec.loader.exec_module(phase)
    old_stage=phase.Phase6.stage;old_time=phase.Phase6.require_time
    def selected_stage(self,name,key,command,timeout,environment=None):
        if name==OWNER and key=='verify-new-off':
            key='verify-new-off-derived-retry1';command=[*command,'--verification-output','independent-derived-retry1']
        return old_stage(self,name,key,command,timeout,environment)
    def remaining_time(self,seconds):
        # The full6600s entry budget included already passed tests/first control.
        return old_time(self,2400 if seconds==6600 else seconds)
    phase.Phase6.stage=selected_stage;phase.Phase6.require_time=remaining_time
    controller=phase.Phase6(SimpleNamespace(root=R,state=state_path,profile_state=R/'090-best-profile-worker6-state.json',
        prefix='100-halo',repeats=7,deadline=deadline))
    ledger.process_tree.enable_subreaper()
    def interrupted(signum,frame):raise KeyboardInterrupt('Explicit phase6 derived continuation interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:
        controller.run()
        for case,expected in contract['original_measurements'].items():
            report=read(runs/case/'result.json')
            integrity.require({k:v for k,v in report.items() if k!='verification'}==expected,'Original timing/physical fields changed')
        sha(original_state_path,args.original_state_sha)
        current=read(R/'campaign/attempts'/OWNER/'attempt.json')
        integrity.require(current['stages']['verify-new-off']==failed,'Original failed stage changed')
        for (name,key),value in frozen_stages.items():
            integrity.require(read(R/'campaign/attempts'/name/'attempt.json')['stages'][key]==value,'Original passed stage changed')
        controller.state['derived_output_recovery']['complete']=True;controller.save()
        print('PHASE6_DERIVED_RECOVERY_COMPLETE '+json.dumps(dict(state=str(state_path),best=controller.state['best'],
            winner=controller.state['winner'],original100_remains_failed=True)),flush=True)
    except BaseException as error:
        if controller.state.get('status')!='blocked':
            controller.state.update(complete=False,status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=repr(error))
            controller.save()
        raise

if __name__=='__main__':main()
