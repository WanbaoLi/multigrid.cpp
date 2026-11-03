#!/usr/bin/env python3
"""Fresh ordinary DDR010 -> accepted best -> DDR010 final full12 validation.

Independent processes and setup, one warmup plus5(default)/7 steady complete12
solves, frozen scalar references, no perf, no build and no promotion. Required
structural/phase5 completion is explicit. This measures steady full12 API only;
setup/read/stout/first-solution cold metrics remain separate.
"""
import argparse
from copy import deepcopy
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import signal
import socket
import statistics
import subprocess
import sys
import time

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
FIXTURE='/home/share/nsls_lwb/.cache/mg-20261102/propagator'
REFERENCE='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
EXTRACTOR='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
CANONICAL='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
TRIAL_TAG='LQCD_OPT_FINAL_VALIDATION_ID'
STARTUP_KEYS={'LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'}


def sanitized_environment(initial,numerical_keys):
    result=dict(initial)
    for key in numerical_keys|STARTUP_KEYS:
        if key not in {'LQCD_NUMA_NODE','LQCD_CPU_THREADS'} and not key.startswith('LQCD_OPT_'):
            result.pop(key,None)
    return result


def repeat_command(command,repeats):
    """Adapt only the benchmark argv of existing unmodified trial.py."""
    result=deepcopy(command)
    argv=result['argv']
    if not any(Path(value).name=='bench_full12.py' for value in argv) or '--diagnostic' in argv:
        raise ValueError('Final adapter accepts only ordinary full12 benchmark commands')
    if '--repeats' in argv:
        if argv[argv.index('--repeats')+1]!=str(repeats):
            raise ValueError('Original trial repetition count conflicts with frozen final protocol')
    else:
        argv.extend(['--repeats',str(repeats)])
    return result


def run_trial_adapter(argv):
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--repeats',type=int,choices=(5,7),required=True)
    args,remaining=parser.parse_known_args(argv)
    sys.path.insert(0,str(args.trial.resolve().parent))
    ledger=importlib.import_module('campaign')
    original=ledger.run_stage
    def stage(root,name,key,command,*extra,**kwargs):
        return original(root,name,key,repeat_command(command,args.repeats) if key=='benchmark' else command,*extra,**kwargs)
    ledger.run_stage=stage
    saved=sys.argv
    try:
        sys.argv=[str(args.trial),*remaining]
        runpy.run_path(str(args.trial),run_name='__main__')
    finally:
        ledger.run_stage=original
        sys.argv=saved


def overall_gate(best,first,last,limits):
    reasons=[]
    drift=abs(first['median_seconds']-last['median_seconds'])/min(first['median_seconds'],last['median_seconds'])
    if drift>.05:reasons.append('DDR bracket median drift exceeds5%')
    for label,row in [('accepted best',best),('first DDR',first),('last DDR',last)]:
        if row['relative_spread']>limits['maximum_relative_spread']:reasons.append(label+' spread exceeds threshold')
    checks=[]
    for label,control in [('first DDR',first),('last DDR',last)]:
        gain=1-best['median_seconds']/control['median_seconds']
        checks.append(dict(control=label,provisional_gain_not_claimed=gain))
        if gain<limits['minimum_gain']:reasons.append('Gain below campaign minimum against '+label)
        if best['maximum_seconds']>=control['minimum_seconds']:reasons.append('Timing ranges overlap '+label)
        if best['steady_repeats']!=control['steady_repeats']:reasons.append('Repeat IDs differ from '+label)
    reference=statistics.median([first['median_seconds'],last['median_seconds']])
    qualified=None if reasons else dict(reference_ddr_median_seconds=reference,
        relative_wall_reduction=1-best['median_seconds']/reference,speedup=reference/best['median_seconds'])
    return dict(passed=not reasons,reasons=reasons,control_median_drift=drift,
                provisional_checks=checks,qualified_overall_gain=qualified)


def plan_for(cfg):
    return dict(context_environment=deepcopy(cfg['context_environment']),
        placement_threads=cfg.get('placement_threads',cfg['threads']),setup_threads=cfg.get('setup_threads',cfg['threads']),
        cases=[dict(id='full12',threads=cfg['threads'],batch=cfg['batch'],environment=deepcopy(cfg['solve_environment']))])


class FinalValidation:
    def __init__(self,args):
        self.args=args;self.root=args.root.resolve();self.source=self.root/'source';self.campaign=self.root/'campaign'
        sys.path.insert(0,str(self.source/'tools/optimization'))
        self.ledger=importlib.import_module('campaign');self.tree=importlib.import_module('process_tree')
        self.host=socket.gethostname();self.allocation=os.environ['LQCD_OPT_ALLOCATION']
        self.deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
        self.require(math.isfinite(self.deadline) and self.deadline>time.time(),'Finite actual allocation deadline required')
        self.require(os.environ.get(self.tree.TASK_KEY),'Bounded worker task ownership tag required')
        self.require(self.ledger.NAME.fullmatch(args.prefix),'Safe phase prefix required')
        if args.expected_host:self.require(self.host.split('.')[0]==args.expected_host,'Unexpected host')
        self.path=(args.state or self.root/'phase8-final-state.json').resolve()
        self.require(not self.path.is_relative_to(self.campaign) and not self.path.is_relative_to(self.source),
                     'Controller state must stay outside ledger/source')
        phase5=(args.phase5_state or self.root/'phase5-state.json').resolve()
        dependencies=[phase5,*[path.resolve() for path in args.structural_state]]
        for path in dependencies:self.require(self.ledger.read(path).get('complete') is True,'Incomplete prerequisite: '+str(path))
        self.config=self.ledger.campaign(self.campaign)[1]
        self.state=self.ledger.read(self.path) if self.path.exists() else {}
        selected=self.ledger.read(self.campaign/'best.json')
        phase5data=self.ledger.read(phase5)
        self.require(phase5data.get('expected_best',phase5data.get('best'))==selected['attempt'],
                     'Phase5 is not stable on the currently accepted implementation')
        policy_path=args.environment_policy.resolve()
        spec=importlib.util.spec_from_file_location('_phase8_environment_policy',policy_path)
        self.policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.policy)
        contract=dict(controller_sha256=self.ledger.digest(Path(__file__)),host=self.host,allocation=self.allocation,
            repeats=args.repeats,prefix=args.prefix,environment_policy_path=str(policy_path),environment_policy_sha256=self.ledger.digest(policy_path),
            dependencies={str(path):self.ledger.digest(path) for path in dependencies},
            tools={name:self.ledger.digest(self.source/'tools/optimization'/name) for name in ('trial.py','campaign.py','process_tree.py')})
        self.require(not self.state or self.state['contract']==contract,'Changed controller/tools/plans/host/allocation; create a fresh validation epoch')
        if not self.state:
            best_data,best_report,_=self.ledger.checked_attempt(self.campaign,selected['attempt'],self.config)
            ddr_data,ddr_report,_=self.ledger.checked_attempt(self.campaign,'010-baseline',self.config)
            for report in (best_report,ddr_report):
                self.require(report['comparison_key'].get('prepared_gauge_manifest_sha256')==CANONICAL
                    and report['input_sha256']==self.config['input_sha256'] and report['timing_scope']=='full12_api',
                    'Both historical source parents must already identify the canonical field/full12 scope')
            self.require(ddr_report['configuration']['context_environment'].get('LQCD_HBW_ALLOC')=='off'
                and ddr_report['configuration']['context_environment'].get('LQCD_HBM')=='off','010 must remain exact DDR, with both HBW/HBM paths off')
            self.require(self.ledger.digest(REFERENCE)==self.config['reference_sha256'],'Frozen scalar reference changed')
            parents={}
            for name,data,report in [('010-baseline',ddr_data,ddr_report),(selected['attempt'],best_data,best_report)]:
                context=report['configuration']['context_environment']
                self.require(not context.get('PERF_COUNTER_ROOT') and not context.get('LD_DEBUG'),'Accepted parent contains diagnostic settings')
                preload=context.get('LD_PRELOAD','')
                self.require(not preload or (len(preload.split())==1 and Path(preload).name.startswith('libgomp.so')),
                    'Ordinary final validation permits only the accepted libgomp preload')
                self.require(self.ledger.digest(EXTRACTOR)==report['verification']['extractor_sha256'],'Frozen extractor changed')
                baseline=report.get('reference_propagator') or FIXTURE+'/propagator.npy'
                self.require(self.ledger.digest(baseline)==report['verification']['reference_propagator_sha256'],'Validated parent baseline changed')
                parents[name]=dict(configuration=report['configuration'],source_manifest_sha256=data['snapshot']['source_manifest_sha256'],
                    library_sha256=report['library_sha256'],reference_propagator=baseline,reference_propagator_sha256=report['verification']['reference_propagator_sha256'],
                    extractor_sha256=report['verification']['extractor_sha256'],
                    historical_summary=self.ledger.validate_report(report,self.config,data['snapshot']['source_manifest_sha256']))
            self.state=dict(contract=contract,created=self.ledger.now(),complete=False,status='prepared',
                accepted_best_pointer=selected,accepted_best_pointer_sha256=self.ledger.digest(self.campaign/'best.json'),
                parents=parents,trials={},order=[args.prefix+'-ddr-a',args.prefix+'-accepted',args.prefix+'-ddr-b'])
            self.save()
        self.check_frozen()

    def require(self,condition,message):self.ledger.require(condition,message)
    def save(self):self.state['updated']=self.ledger.now();self.ledger.atomic(self.path,self.state)
    def check_frozen(self):
        self.require(self.ledger.digest(Path(__file__))==self.state['contract']['controller_sha256']
            and self.ledger.digest(self.state['contract']['environment_policy_path'])==self.state['contract']['environment_policy_sha256'],
            'Controller/adapter/environment policy changed during validation')
        self.require(self.ledger.digest(self.campaign/'best.json')==self.state['accepted_best_pointer_sha256'],
                     'Accepted best changed during validation; never mix a new best into existing brackets')
        self.require(all(self.ledger.digest(self.source/'tools/optimization'/name)==sha for name,sha in self.state['contract']['tools'].items()),
                     'Bookkeeping source changed during final validation')
        self.require(all(self.ledger.digest(path)==sha for path,sha in self.state['contract']['dependencies'].items()),
                     'Prerequisite phase changed after final validation started')
        self.require(self.ledger.digest(REFERENCE)==self.config['reference_sha256'],'Independent scalar reference changed')
    def pending(self,reason):
        self.state.update(complete=False,status='pending',pending_reason=reason);self.save()
        print('FINAL_VALIDATION_PENDING '+reason,flush=True);return False

    def read_experience(self,name):
        history=self.ledger.show_history(self.campaign)
        proposals=[dict(id=row['id'],status=row['status'],proposal=row['proposal'],conclusions=row.get('conclusions',[]))
                   for row in history['attempts']]
        external={}
        for path in self.args.experience:
            path=path.resolve();path.read_text(encoding='utf-8');external[str(path)]=self.ledger.digest(path)
        value=dict(time=self.ledger.now(),history_sha256=history['history_read_token'],external_experience_sha256=external,
            proposals_and_conclusions=proposals,event_count=len(history['events']),best=history['best'])
        target=self.root/'phase8-experience'/(name+'.json')
        if target.exists():
            # A resume reads current experience again, retaining the earlier read.
            target=target.with_name(name+'-'+str(time.time_ns())+'.json')
        self.ledger.atomic(target,value)
        return dict(path=str(target),sha256=self.ledger.digest(target),history_sha256=history['history_read_token'])

    def report(self,name,parent):
        path=self.campaign/'attempts'/name
        if not (path/'report.json').is_file():return None
        data,report,summary=self.ledger.checked_attempt(self.campaign,name,self.config)
        expected=self.state['parents'][parent]
        self.require(report['configuration']==expected['configuration'] and report['source_manifest_sha256']==expected['source_manifest_sha256']
            and report['library_sha256']==expected['library_sha256'],'Fresh report differs from exact parent source/library/configuration')
        key=report['comparison_key']
        self.require(key['host']==self.host and key['allocation']==self.allocation and key.get('prepared_gauge_manifest_sha256')==CANONICAL
            and key.get('scope')=='full12_api','Fresh report differs from current host/allocation/canonical full12 scope')
        self.require(len(report['samples'])==self.args.repeats+1 and summary['steady_repeats']==list(range(1,self.args.repeats+1))
            and report['samples'][0]['repeat']==0 and report['samples'][0]['warmup'] is True
            and all(row['warmup'] is False for row in report['samples'][1:]),'Wrong fresh warm/steady repetition protocol')
        self.require(self.ledger.object_digest(self.ledger.read(path/'measurements/full12/result.json'))==data['report']['sha256'],
                     'Raw fresh-process result differs from ingested report')
        for stage_name in ('benchmark','independent'):
            stage=data['stages'][stage_name]
            self.require(stage['status']=='passed' and self.ledger.digest(path/stage['log'])==stage['log_sha256'],
                         'Incomplete/changed numerical stage evidence')
        self.require('--repeats' in data['stages']['benchmark']['argv'] and
            data['stages']['benchmark']['argv'][data['stages']['benchmark']['argv'].index('--repeats')+1]==str(self.args.repeats),
            'Actual benchmark command repetition count differs')
        return data,report,summary

    def trial(self,name,parent,role):
        self.check_frozen()
        row=self.state['trials'].setdefault(name,{})
        parent_info=self.state['parents'][parent]
        plan=plan_for(parent_info['configuration'])
        plan_path=self.root/'plans'/(name+'.json');proposal_path=self.root/'proposals'/(name+'.json')
        proposal=dict(bottleneck='Final complete12 API validation after structural and runtime optimization, with fresh matched original-DDR brackets',
            hypothesis=role+': retained accepted implementation reproduces its full12 performance and precision on this allocation',
            change=dict(role=role,parent=parent,source='exact frozen parent, no rebuild',repeats=self.args.repeats),
            mechanism='Independent processes remove alternating-team history; first/last original DDR controls expose timing drift',
            history_links=[str(self.path),str(self.campaign/'attempts'/parent/'report.json'),*map(str,self.args.structural_state)],
            retry_conditions='Read current experience before each trial; never relabel historical timings, overwrite failed data, retry failed stages automatically or promote equivalent code')
        for path,value in [(plan_path,plan),(proposal_path,proposal)]:
            if path.exists():self.require(self.ledger.read(path)==value,'Retained plan/proposal changed')
            else:self.ledger.atomic(path,value)
        hashes=dict(plan=self.ledger.digest(plan_path),proposal=self.ledger.digest(proposal_path))
        self.require(not row.get('hashes') or row['hashes']==hashes,'Plan/proposal hash changed on resume')
        row['hashes']=hashes
        completed=self.report(name,parent)
        if completed:
            self.require(row.get('runs'),'Attempt ID was created outside this final controller; use a new prefix/state')
            row.update(status='measured',report_sha256=completed[0]['report']['sha256']);self.save();return True
        if row.get('status') in {'running','failed','interrupted','cleanup_failed'}:
            self.require(self.args.resume and self.args.resume_reason,'Unfinished controller run requires explicit --resume --resume-reason or fresh attempts')
        record_path=self.campaign/'attempts'/name/'attempt.json'
        if record_path.exists():
            record=self.ledger.read(record_path)
            bad={key:value['status'] for key,value in record.get('stages',{}).items() if value['status']!='passed'}
            self.require(not bad,'Retained failed/unknown stages need explicit framework recovery/new verification NAME; controller never bypasses guards: '+repr(bad))
        required=900 if role.startswith('DDR') else 800
        if self.deadline-time.time()<required:return self.pending(name+': need >='+str(required)+'s for bounded complete process')
        experience=self.read_experience(name)
        self.require(self.ledger.digest(EXTRACTOR)==parent_info['extractor_sha256']
            and self.ledger.digest(parent_info['reference_propagator'])==parent_info['reference_propagator_sha256'],
            'Frozen validated extractor/baseline changed before final trial')
        keys=(self.policy.numerical_environment_keys(self.campaign/'attempts'/parent/'source')|
              self.policy.numerical_environment_keys(self.source)|STARTUP_KEYS)
        env=sanitized_environment(os.environ,keys)
        tag=self.tree.new_tag();env[TRIAL_TAG]=tag
        command=[sys.executable,str(Path(__file__).resolve()),'_trial','--trial',str(self.source/'tools/optimization/trial.py'),
            '--repeats',str(self.args.repeats),'--campaign',str(self.campaign),'--id',name,
            '--proposal',str(proposal_path),'--plan',str(plan_path),'--source-from',parent,'--reuse-attempt',parent,
            '--fixture',FIXTURE,'--reference',REFERENCE,'--extractor',EXTRACTOR,
            '--reference-propagator',parent_info['reference_propagator'],'--backend','arm','--allocation',self.allocation]
        log=self.root/'phase8-logs'/f'{name}-{len(row.get("runs",[])):03d}.log';log.parent.mkdir(parents=True,exist_ok=True)
        self.require(not log.exists(),'Never overwrite final-validation logs')
        run=dict(status='running',started=self.ledger.now(),argv=command,log=str(log),experience=experience,
            timeout_seconds=min(900 if role.startswith('DDR') else 800,self.deadline-time.time()-60),
            owned_tag=tag,cleared_numerical_keys=sorted(keys),resume_reason=self.args.resume_reason)
        row.setdefault('runs',[]).append(run);row.update(status='running',parent=parent,role=role);self.save()
        process=None
        try:
            with log.open('xb') as stream:
                process=subprocess.Popen(command,cwd=str(self.root),env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                run['pid']=process.pid;self.save()
                run['returncode']=process.wait(timeout=run['timeout_seconds']);run['status']='passed' if run['returncode']==0 else 'failed'
        except (subprocess.TimeoutExpired,KeyboardInterrupt) as error:run.update(status='interrupted',error=str(error))
        except Exception as error:run.update(status='failed',error=str(error))
        finally:
            if process:
                run['cleanup']=self.tree.terminate_owned(process,TRIAL_TAG,tag,grace=10)
                if not run['cleanup']['complete']:run['status']='cleanup_failed'
            run.update(ended=self.ledger.now(),log_sha256=self.ledger.digest(log) if log.exists() else None)
            row['status']=run['status'];self.save()
        self.require(run['status']=='passed','Final trial failed/interrupted; keep evidence and use explicit recovery')
        completed=self.report(name,parent);self.require(completed is not None,'Trial returned without a complete registered result')
        row.update(status='measured',report_sha256=completed[0]['report']['sha256']);self.save();return True

    def run(self):
        if self.state['complete']:
            print('FINAL_VALIDATION_ALREADY_COMPLETE '+str(self.path),flush=True);return
        if not self.state['trials'] and self.deadline-time.time()<2200:
            self.pending('Need >=2200s before starting three fresh setup/process/full12 validation trials');return
        first,middle,last=self.state['order'];best=self.state['accepted_best_pointer']['attempt']
        for name,parent,role in [(first,'010-baseline','DDR first control'),(middle,best,'Accepted best validation'),(last,'010-baseline','DDR last control')]:
            if not self.trial(name,parent,role):return
        evidence={name:self.report(name,'010-baseline' if name!=middle else best) for name in self.state['order']}
        reports={name:row[1] for name,row in evidence.items()};summaries={name:row[2] for name,row in evidence.items()}
        self.require(all(report['comparison_key']==reports[first]['comparison_key'] for report in reports.values()),'Final timing comparison keys differ')
        assessment=overall_gate(summaries[middle],summaries[first],summaries[last],self.config)
        self.check_frozen()
        self.state.update(complete=True,status='complete',finished=self.ledger.now(),fresh_validation_attempt=middle,
            historical_best_median_seconds=self.state['parents'][best]['historical_summary']['median_seconds'],
            fresh_final_validation=summaries[middle],fresh_ddr_brackets={first:summaries[first],last:summaries[last]},
            comparison_key=reports[first]['comparison_key'],assessment=assessment,performance_adoption=False,
            measurements={name:dict(report_path=str(self.campaign/'attempts'/name/'report.json'),
                report_sha256=evidence[name][0]['report']['sha256'],source_manifest_sha256=report['source_manifest_sha256'],
                library_sha256=report['library_sha256'],configuration=report['configuration'],samples=report['samples'],
                verification=report['verification']) for name,report in reports.items()})
        for name in self.state['order']:
            text='Final steady full12 validation completed; '+('fresh accepted-best metric' if name==middle else 'fresh original-DDR bracket')+\
                '; no implementation promotion; overall comparison '+('qualified' if assessment['passed'] else 'inconclusive: '+'; '.join(assessment['reasons']))
            record=self.ledger.read(self.campaign/'attempts'/name/'attempt.json')
            if not any(row['conclusion']==text for row in record.get('conclusions',[])):
                self.ledger.conclude(self.campaign,name,'inconclusive',text,[str(self.path),str(self.campaign/'attempts'/name/'report.json')])
        self.save()
        print('FINAL_VALIDATION_COMPLETE '+json.dumps(dict(state=str(self.path),accepted_best=best,fresh_validation_attempt=middle,
            fresh_median_seconds=summaries[middle]['median_seconds'],assessment=assessment,performance_adoption=False)),flush=True)


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if argv and argv[0]=='_trial':return run_trial_adapter(argv[1:])
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--state',type=Path)
    parser.add_argument('--prefix',default='090-final')
    parser.add_argument('--repeats',type=int,choices=(5,7),default=5)
    parser.add_argument('--expected-host')
    parser.add_argument('--phase5-state',type=Path)
    parser.add_argument('--structural-state',type=Path,action='append',required=True,
                        help='Repeat for EVERY completed structural phase state; no guessed stage names')
    parser.add_argument('--experience',type=Path,action='append',default=[])
    parser.add_argument('--environment-policy',type=Path,default=Path(__file__).with_name('cold_full12.py'),
                        help='Read-only numerical-environment policy helper; never modifies or invokes cold measurement')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--resume-reason')
    args=parser.parse_args(argv)
    if args.resume!=bool(args.resume_reason):parser.error('--resume and --resume-reason must be paired')
    phase=FinalValidation(args);phase.tree.enable_subreaper()
    def interrupted(signum,frame):raise KeyboardInterrupt('Final validation signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:phase.run()
    except BaseException as error:
        phase.state.update(complete=False,status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error));phase.save();raise


if __name__=='__main__':main()
