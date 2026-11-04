#!/usr/bin/env python3
"""Post-profile, bounded full12 halo trial in the existing main ledger.

Preparation never queues, fetches, merges or edits source. The operator first
finishes phase4 and the fresh retained-best profile, then fast-forwards source
to the separately reviewed71160fa bundle. This controller verifies that exact
clean HEAD. Existing snapshots/libraries remain immutable and rollback-capable.
"""
import argparse
import ast
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import sys
import time

HEAD='71160fac57d577d27423527e6b577c0593940d35'
DEFAULT_ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
FIXTURE='/home/share/nsls_lwb/.cache/mg-20261102/propagator'
REFERENCE='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
EXTRACTOR='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
TEST_REGEX='^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning|coarse_batch_reduce_.*|coarse_batch_halo_.*|batch12_coarse_(reduce|halo)_mpi[24]|runtime_batch_coarse_reduce)$'
STARTUP_KEYS=('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT')


def plan_for(base, cases):
    return dict(context_environment=deepcopy(base['context_environment']),
        placement_threads=base.get('placement_threads',base['threads']),
        setup_threads=base.get('setup_threads',base['threads']),cases=deepcopy(cases))


def case_for(base, name, updates=None):
    environment=deepcopy(base['solve_environment'])
    environment.update(updates or {})
    return dict(id=name,threads=base['threads'],batch=base['batch'],environment=environment)


def comparison_cases(base):
    cases=[case_for(base,'new-off')]
    if not base['solve_environment'].get('LQCD_COARSE_BATCH_REDUCE',0):
        cases.append(case_for(base,'reduce-only',{'LQCD_COARSE_BATCH_REDUCE':1}))
    cases.append(case_for(base,'halo-on',{'LQCD_COARSE_BATCH_REDUCE':1,'LQCD_COARSE_BATCH_HALO':1}))
    return cases


def configuration_for(base, plan, case):
    result=deepcopy(base)
    result.update(context_environment=deepcopy(plan['context_environment']),
        solve_environment=deepcopy(case['environment']),threads=case['threads'],batch=case['batch'])
    for key in ('placement_threads','setup_threads'):
        result.pop(key,None)
        if plan[key]!=case['threads']:result[key]=plan[key]
    return result


def bracket_gate(candidate, first, last, limits):
    reasons=[]
    drift=abs(first['median_seconds']-last['median_seconds'])/min(first['median_seconds'],last['median_seconds'])
    if drift>.05:reasons.append('Fresh control medians drift by more than5%')
    for label,value in (('candidate',candidate),('first control',first),('last control',last)):
        if value['relative_spread']>limits['maximum_relative_spread']:reasons.append(label+' is too noisy')
    gains=[]
    for label,control in (('first',first),('last',last)):
        gain=1-candidate['median_seconds']/control['median_seconds']
        gains.append(gain)
        if gain<limits['minimum_gain']:reasons.append('Gain below threshold against '+label+' control')
        if candidate['maximum_seconds']>=control['minimum_seconds']:reasons.append('Timing ranges overlap '+label+' control')
        if candidate['steady_repeats']!=control['steady_repeats']:reasons.append('Steady repeat IDs differ from '+label+' control')
    return dict(passed=not reasons,reasons=reasons,gains=gains,control_median_drift=drift)


def halo_effect_gate(halo, reduction, maximum_spread=.1):
    # The overall old-best gain still needs the campaign threshold. This gate
    # isolates a positive halo increment on the same binary/hierarchy without
    # attributing reduction-only or code-layout gains to halo batching.
    gain=1-halo['median_seconds']/reduction['median_seconds']
    return dict(passed=gain>0 and halo['relative_spread']<=maximum_spread and
                reduction['relative_spread']<=maximum_spread and
                halo['maximum_seconds']<reduction['minimum_seconds'] and
                halo['steady_repeats']==reduction['steady_repeats'],gain=gain,
                reason='Halo must have a positive, separated range against new-code reduce-only')


def solve_keys(path):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and
            target.id=='SOLVE_TUNING_KEYS' for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError('Missing literal SOLVE_TUNING_KEYS')


def coarse_coverage(rows):
    return dict(records=len(rows),packed_allreduce_calls=sum(row['allreduce_calls'] for row in rows),
        restarts=sum(sum(row['restarts']) for row in rows),
        refreshes=sum(sum(row['refreshes']) for row in rows),
        capped=sum(sum(row['capped']) for row in rows),
        maximum_iterations=max((value for row in rows for value in row['iterations']),default=0),
        different_iteration_counts=any(len(set(row['iterations']))>1 for row in rows),
        different_restart_counts=any(len(set(row['restarts']))>1 for row in rows),
        different_refresh_counts=any(len(set(row['refreshes']))>1 for row in rows))


class Phase6:
    def __init__(self,args):
        self.args=args
        self.root=args.root.resolve()
        self.source=self.root/'source'
        sys.path.insert(0,str(self.source/'tools/optimization'))
        self.ledger=importlib.import_module('campaign')
        self.require=self.ledger.require
        self.require(platform.machine().lower() in ('aarch64','arm64') and
                     platform.node().startswith('cn'),'Allocated Arm compute node required')
        self.require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,50}',args.prefix),'Invalid prefix')
        self.require(self.ledger.read(self.root/'phase4-state.json').get('complete'),'Phase4 is incomplete')
        self.allocation=os.environ.get('LQCD_OPT_ALLOCATION')
        self.require(self.allocation,'Explicit allocation identity required')
        self.deadline=args.deadline or float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0'))
        self.campaign=self.root/'campaign'
        _,self.limits=self.ledger.campaign(self.campaign)
        self.profile_path=(args.profile_state or self.root/'053-best-profile-state.json').resolve()
        self.profile=self.ledger.read(self.profile_path)
        self.require(self.profile.get('complete') and self.profile.get('budget',{}).get('complete') and
                     self.profile.get('verification',{}).get('passed'),'Fresh053 diagnostic and parsed budget must be complete')
        self.require(self.profile['allocation']==self.allocation and self.profile['host']==platform.node(),
                     'New allocation needs a new retained-best profile; never relabel old profile evidence')
        self.require(self.ledger.digest(self.profile['report'])==self.profile['report_sha256'],
                     'Frozen profile report changed')
        self.require(self.ledger.git(self.source,'rev-parse','HEAD')==HEAD and
                     not self.ledger.git(self.source,'status','--short'),
                     'After earlier controllers finish, source must already be the clean reviewed71160fa checkout; this script never updates it')
        self.state_path=(args.state or self.root/(args.prefix+'-state.json')).resolve()
        self.require(not self.state_path.is_relative_to(self.source) and
                     not self.state_path.is_relative_to(self.campaign),'State must stay outside frozen/source trees')
        existing=self.ledger.read(self.state_path) if self.state_path.exists() else None
        parent=existing['initial_best'] if existing else self.best()
        self.parent,self.parent_report,_=self.ledger.checked_attempt(self.campaign,parent,self.limits)
        self.base=deepcopy(self.parent_report['configuration'])
        self.require(self.profile['best']==parent and self.profile['configuration']==self.base and
                     self.profile['library_sha256']==self.parent_report['library_sha256'],
                     'The profile must describe exactly the frozen parent source/library/configuration')
        self.require(self.base['batch']>1 and not self.base['solve_environment'].get('LQCD_COARSE_CGS2',0) and
                     self.base['solve_environment'].get('LQCD_GCR_FUSED',1) and
                     self.base['context_environment'].get('LQCD_COARSE_EO',1),
                     'Retained configuration is outside the supported independent-RHS halo path')
        self.require(not self.base['solve_environment'].get('LQCD_COARSE_BATCH_HALO',0),
                     'This first comparison requires a parent with halo batching disabled')
        self.require(not any(self.base['context_environment'].get(key) for key in
                     ('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT')),
                     'Profile-free ordinary comparison requires no preload/debug context')
        self.startup={key:os.environ.get(key) for key in STARTUP_KEYS}
        for key,value in self.startup.items():
            self.require(not value or str(self.base['context_environment'].get(key,''))==value,
                         'Undeclared startup override: '+key)
        identity=dict(controller_sha256=self.ledger.digest(Path(__file__)),source_head=HEAD,
            sve_probe_sha256=self.ledger.digest(Path(__file__).with_name('phase6_sve_probe.py')),
            initial_best=parent,initial_configuration=self.base,
            initial_source_manifest_sha256=self.parent['snapshot']['source_manifest_sha256'],
            initial_library_sha256=self.parent_report['library_sha256'],
            profile_state=str(self.profile_path),profile_state_sha256=self.ledger.digest(self.profile_path),
            allocation=self.allocation,host=platform.node(),repeats=args.repeats,startup=self.startup)
        self.state=existing or dict(identity,complete=False,status='prepared')
        self.require(all(self.state.get(key)==value for key,value in identity.items()),
                     'Controller/source/allocation/plan identity changed; retain old records and use a new prefix')
        if self.state.get('complete'):
            self.require(self.best()==self.state['best'],'Global best changed after this completed phase')
        else:self.require(self.best()==parent,'Global best changed while the phase was incomplete')
        self.parent_name=parent
        self.owner=args.prefix+'-new-off'
        self.first=args.prefix+'-control-a'
        self.last=args.prefix+'-control-b'
        self.diag=args.prefix+'-halo-profile'
        self.cases=comparison_cases(self.base)
        self.case_names={case['id']:(self.owner if case['id']=='new-off' else args.prefix+'-'+case['id'])
                         for case in self.cases}

    def best(self):return self.ledger.read(self.campaign/'best.json')['attempt']
    def save(self):self.ledger.atomic(self.state_path,self.state)

    def require_time(self,seconds):
        remaining=self.deadline-time.time()
        if remaining<seconds:
            self.state.update(complete=False,status='blocked',pending_reason='Insufficient allocation time',
                              required_seconds=seconds,remaining_seconds=remaining)
            self.save()
            raise RuntimeError('Insufficient bounded allocation time; preserve checkpoints and start fresh matched controls in a new allocation')

    def proposal(self,name,change,mechanism):
        path=self.campaign/'attempts'/name
        if not path.exists():
            history=self.ledger.show_history(self.campaign)
            self.ledger.propose(self.campaign,name,dict(bottleneck='Actual053 retained-best coarse communication profile',
                hypothesis=name+': same-stage active RHS messages reduce repeated starts without changing independent GCR states',
                change=change,mechanism=mechanism,
                history_links=[str(self.profile_path),str(self.campaign/'attempts'/self.parent_name/'report.json'),
                               'docs/coarse-batch-halo-candidate.md'],
                retry_conditions='New reviewed71160fa source, actual Arm tests and fresh controls; profile hints never rank or prove a speedup',
                history_read_token=history['history_read_token']))

    def prepare(self,name,change,mechanism,parent=None):
        self.proposal(name,change,mechanism)
        return (self.ledger.snapshot_from(self.campaign,name,parent) if parent else
                self.ledger.snapshot(self.campaign,name))

    def stage(self,name,key,command,timeout,environment=None):
        self.require_time(35)
        self.require(self.ledger.digest(Path(__file__).with_name('phase6_sve_probe.py'))==
                     self.state['sve_probe_sha256'],'SVE probe changed after checkpoint')
        path=self.campaign/'attempts'/name
        data=self.ledger.read(path/'attempt.json')
        prior=data.get('stages',{}).get(key)
        self.require(not prior or prior['status']=='passed',
                     'Retain failed/interrupted/running stage; no automatic retry: '+name+'/'+key)
        if prior:
            # Preserve the exact recorded timeout on a passed checkpoint.
            timeout=prior['timeout_seconds']
        else:timeout=min(timeout,self.deadline-time.time()-30)
        value=self.ledger.run_stage(self.campaign,name,key,dict(argv=list(map(str,command)),
            cwd=data['snapshot']['build'],env=environment or {},timeout_seconds=timeout))
        print('PHASE6_STAGE '+json.dumps(dict(attempt=name,stage=key,status=value['status'])),flush=True)
        if value['status']=='timeout':
            self.state.update(complete=False,status='blocked',pending_reason='Stage execution budget exhausted; no numerical verdict',
                              timed_out_attempt=name,timed_out_stage=key)
            self.save()
        self.require(value['status']=='passed','Stage failed; preserve all outputs: '+name+'/'+key)

    def build(self,snapshot):
        source,build=Path(snapshot['source']),Path(snapshot['build'])
        command=['cmake','-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release',
            '-DLQCD_BUILD_RUNTIME=ON','-DMULTIGRID_NATIVE=ON','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
            '-DMPI_C_COMPILER='+str(shutil.which('mpicc')),
            '-DMPI_CXX_COMPILER='+str(shutil.which('mpicxx')),'-DLQCD_TEST_PYTHON='+sys.executable]
        if os.environ.get('LQCD_MPI_FLAGS'):command.append('-DLQCD_MPI_FLAGS='+os.environ['LQCD_MPI_FLAGS'])
        if os.environ.get('LQCD_EXPERIMENT_KUPL_ROOT'):
            command+=['-DLQCD_KUPL_HBW=ON','-DLQCD_KUPL_ROOT='+os.environ['LQCD_EXPERIMENT_KUPL_ROOT']]
        if os.environ.get('LQCD_EXPERIMENT_CXX_RUNTIME'):
            runtime=Path(os.environ['LQCD_EXPERIMENT_CXX_RUNTIME']).resolve()
            self.require((runtime/'libstdc++.so').is_file(),'Requested C++ runtime missing')
            flags=f'-L{runtime} -Wl,-rpath,{runtime}'
            command+=['-DCMAKE_EXE_LINKER_FLAGS='+flags,'-DCMAKE_SHARED_LINKER_FLAGS='+flags]
        self.stage(self.owner,'configure',command,180)
        self.stage(self.owner,'build',['cmake','--build',build,'-j','16'],600)
        environment={key:str(value) for key,value in self.base['context_environment'].items()}
        environment.update(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',
                           LQCD_COARSE_BATCH_REDUCE='0',LQCD_COARSE_BATCH_HALO='0',LD_PRELOAD='',PERF_COUNTER_ROOT='')
        environment['CTEST_PARALLEL_LEVEL']='1'
        self.stage(self.owner,'arm-ctest',['ctest','--test-dir',build,'--parallel','1',
            '--output-on-failure','-V','-R',TEST_REGEX],3000,environment)
        self.sve_matrix(snapshot,build/'liblqcd_cpu.so')
        return build/'liblqcd_cpu.so'

    def sve_matrix(self,snapshot,library):
        source,build=Path(snapshot['source']),Path(snapshot['build'])
        probe=Path(__file__).with_name('phase6_sve_probe.py').resolve()
        self.stage(self.owner,'sve-compiled-coarse',[sys.executable,probe,
            '--audit-build',build,'--source',source],90)
        flags=[value for value in os.environ.get('LQCD_MPI_FLAGS','').split(';') if value]
        self.require(flags,'Explicit native MPI test placement flags required')
        environment={key:str(value) for key,value in self.base['context_environment'].items()}
        environment.update(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',
            LQCD_CPU_LIBRARY=str(library),LQCD_ARM_COARSE_SVE='1',LQCD_COARSE_FUSED='1',
            LQCD_HALO_OVERLAP='1',LQCD_COARSE_SPATIAL_OVERLAP='1',
            LQCD_TEST_COARSE_HALO_SMOKE='0',LD_PRELOAD='',PERF_COUNTER_ROOT='')
        for width in (16,32,64):
            self.stage(self.owner,'sve-dense-vl'+str(width),[sys.executable,
                source/'tools/run_sve_vl.py','--bytes',str(width),'--',build/'coarse_kernel_test'],90,environment)
            command=[str(shutil.which('mpiexec')),*flags,'-n','4',sys.executable,
                source/'tools/run_sve_vl.py','--bytes',str(width),'--',sys.executable,probe,
                '--expected-bytes',str(width),'--test',source/'tests/runtime/test_coarse_batch_reduce.py']
            self.stage(self.owner,'sve-ghost-mpi4-vl'+str(width),command,900,environment)
            log=(self.campaign/'attempts'/self.owner/('sve-ghost-mpi4-vl'+str(width)+'-000.log')).read_text()
            rows=[json.loads(value) for value in re.findall(r'PHASE6_SVE_RANKS_COMPLETE (\{[^\n]+\})',log)]
            actual=[json.loads(value) for value in re.findall(r'COARSE_BATCH_HALO_DIAGNOSTIC (\{[^\n]+\})',log)]
            self.require(len(rows)==1 and rows[0].get('complete') and
                         rows[0]['library_sha256']==self.ledger.digest(library) and
                         rows[0]['requested_bytes']==width and len(rows[0]['ranks'])==4 and
                         {row['rank'] for row in rows[0]['ranks']}==set(range(4)) and
                         all(row['actual_bytes']==width for row in rows[0]['ranks']) and
                         any(row['calls']>0 for row in actual),
                         'Actual per-rank vector length, packed calls and all12 oracle pass are required')
            self.state.setdefault('arm_sve_execution',{})[str(width)]=dict(
                rank_check=rows[0],actual_halo_diagnostics=actual,
                scope='Existing dense-tail unit plus MPI4 full1/2/4/12-column independent oracle with new SVE ghost helper')
            self.save()

    def benchmark(self,name,snapshot,library,plan,diagnostic=False):
        path=self.campaign/'attempts'/name
        target=path/'plan.json'
        if target.exists():self.require(self.ledger.read(target)==plan,'Immutable plan changed')
        else:self.ledger.atomic(target,plan)
        source=Path(snapshot['source'])
        command=[sys.executable,source/'tools/run_numa.py','--threads',str(plan['placement_threads']),'--',
            sys.executable,'-u',source/'tools/optimization/bench_full12.py','--fixture',FIXTURE,
            '--plan',target,'--library',library,'--backend','arm','--output',path/'measurements',
            '--allocation',self.allocation,'--snapshot-sha',snapshot['source_manifest_sha256'],
            '--reference-propagator',FIXTURE+'/propagator.npy','--repeats',str(3 if diagnostic else self.args.repeats)]
        if diagnostic:command.append('--diagnostic')
        environment={key:str(value) for key,value in plan['context_environment'].items()}
        environment.update(LD_PRELOAD='',PERF_COUNTER_ROOT='',LD_DEBUG='',LD_DEBUG_OUTPUT='')
        self.stage(name,'diagnostic' if diagnostic else 'benchmark',command,1800,environment)
        reports={}
        for case in plan['cases']:
            run=path/'measurements'/case['id']
            self.stage(name,'verify-'+case['id'],[sys.executable,source/'tools/optimization/bench_full12.py',
                '--verify',run,'--reference',REFERENCE,'--extractor',EXTRACTOR],1200,
                dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close'))
            report=self.ledger.read(run/'result.json')
            self.require(report['configuration']==configuration_for(self.base,plan,case),
                         'Effective resource/solver configuration differs from the plan')
            reports[case['id']]=run/'result.json'
        return reports

    def control(self,name):
        snapshot=self.prepare(name,'Fresh retained-best control with complete12 independent validation',
            'Bracket allocation drift using the exact old source/library/configuration',self.parent_name)
        library=self.campaign/'attempts'/self.parent_name/'artifacts/liblqcd_cpu.so'
        self.require(self.ledger.digest(library)==self.parent_report['library_sha256'],'Frozen control library changed')
        reports=self.benchmark(name,snapshot,library,plan_for(self.base,[case_for(self.base,'full12')]))
        self.ledger.ingest(self.campaign,name,reports['full12'])

    def diagnostic(self,library):
        parent=self.case_names['halo-on']
        snapshot=self.prepare(self.diag,'Separate real-input halo execution diagnostic',
            'Verify actual packed MPI calls/bytes on full12; no perf/PMPI and no ranking',parent)
        report_path=self.benchmark(self.diag,snapshot,library,
            plan_for(self.base,[self.cases[-1]]),diagnostic=True)['halo-on']
        report=self.ledger.read(report_path)
        proof=report.get('verification',{})
        self.require(report.get('complete') and proof.get('passed') and proof.get('columns')==12,
                     'Candidate diagnostic needs all12 independent precision gates')
        log=(self.campaign/'attempts'/self.diag/'diagnostic-000.log').read_text()
        rows=[json.loads(value) for value in re.findall(r'native coarse batch halo (\{[^\n]+\})',log)]
        actual=dict(records=len(rows),calls=sum(row['calls'] for row in rows),
            send_bytes=sum(row['send_bytes'] for row in rows),rhs_slots=sum(row['rhs_slots'] for row in rows),
            max_width=max((row['max_width'] for row in rows),default=0))
        self.require(actual['calls']>0 and actual['send_bytes']>0 and actual['max_width']>1,
                     'Flags do not prove execution: real-input merged MPI counters are required')
        reductions=[json.loads(value) for value in re.findall(r'native coarse batch reduce (\{[^\n]+\})',log)]
        coverage=coarse_coverage(reductions)
        reference=coarse_coverage(self.profile['budget']['final_verbose_reductions'])
        self.require(coverage['records']>0 and coverage['packed_allreduce_calls']>0,
                     'Real-input packed reduction execution is also required')
        self.require(not reference['restarts'] or coverage['restarts']>0,
                     'The retained profile exercised restart; candidate needs actual restart precision evidence too')
        self.require(not reference['different_refresh_counts'] or coverage['different_refresh_counts'],
                     'The retained profile exercised differing refresh counts; candidate must exercise them before adoption')
        self.state['actual_halo_diagnostic']=dict(actual=actual,coarse_state_coverage=coverage,
            parent_profile_coarse_state_coverage=reference,verification=proof,report=str(report_path))
        self.ledger.conclude(self.campaign,self.diag,'inconclusive','Verified real-input diagnostic; profile times are not ranked',[str(report_path)])
        self.save()

    def decide(self):
        self.require(self.best()==self.parent_name,'Global best changed outside this phase')
        names=[self.first,*self.case_names.values(),self.last]
        evidence={name:self.ledger.checked_attempt(self.campaign,name,self.limits) for name in names}
        first,last=evidence[self.first],evidence[self.last]
        self.require(all(value[1]['comparison_key']==first[1]['comparison_key'] for value in evidence.values()),
                     'Ordinary comparison keys differ')
        assessments={name:bracket_gate(evidence[name][2],first[2],last[2],self.limits)
                     for name in self.case_names.values()}
        reduce_name=self.case_names.get('reduce-only',self.owner)
        halo_name=self.case_names['halo-on']
        effect=halo_effect_gate(evidence[halo_name][2],evidence[reduce_name][2],self.limits['maximum_relative_spread'])
        self.state.update(assessments=assessments,halo_increment=effect)
        eligible=[name for name,value in assessments.items() if value['passed'] and
                  (name!=halo_name or effect['passed'])]
        if eligible:
            winner=min(eligible,key=lambda name:evidence[name][2]['median_seconds'])
            self.state['promotion']=self.ledger.promote(self.campaign,winner,against=self.last)
        else:winner=None
        for name,value in assessments.items():
            if name!=winner:
                self.ledger.conclude(self.campaign,name,'inconclusive',
                    'Not adopted: '+('; '.join(value['reasons']) or
                    ('halo increment not isolated' if name==halo_name and not effect['passed'] else 'another correct candidate was faster')),
                    [str(self.state_path),str(self.campaign/'attempts'/name/'report.json')])
        self.state.update(complete=True,status='complete',best=self.best(),winner=winner,
            next_candidate=dict(change='Reuse per-RHS Schur fields and pointer capacities without retaining an initial guess',
                condition='Only after profile shows message counts/waits decreased but coarse wall time stays flat and allocation/growth evidence fills the gap; fused mode has the clearest source-level allocation regression',
                evidence_needed=['actual allocation/growth counters or a scoped allocation profile','coarse-stage versus halo-region changes','all12 independent residual and solution gates'],
                fallback='If waits reflect arrival skew or the affected region is small, reassess worker progress/load balance instead of repeating arbitrary batch/iteration parameters'))
        self.save()

    def run(self):
        if self.state.get('complete'):
            print('PHASE6_ALREADY_COMPLETE '+json.dumps(self.state),flush=True)
            return
        # No registered attempt or build on worker2 when its remaining budget
        # cannot cover tests, ordinary brackets, separate diagnostic and verify.
        self.require_time(6600)
        self.require(self.profile['budget']['roi_hint']=='worth_bounded_trial',
                     'Observed profile lowers this candidate priority; retain the hint and reassess before spending a new build, without claiming a hard speedup bound')
        for key in solve_keys(self.source/'python/lqcd_cpu/propagator.py'):os.environ.pop(key,None)
        self.state.update(status='running',profile_budget=self.profile['budget'])
        self.save()
        self.control(self.first)
        snapshot=self.prepare(self.owner,'New reviewed code with halo flag disabled plus matched dynamic cases',
            'Separate code layout, reduction-only and halo effects; all dynamic cases share one hierarchy')
        library=self.build(snapshot)
        self.require_time(2400+300*(len(self.cases)-2))
        plan=plan_for(self.base,self.cases)
        reports=self.benchmark(self.owner,snapshot,library,plan)
        # Verify every case before ingesting any candidate or changing best.
        self.ledger.ingest(self.campaign,self.owner,reports['new-off'])
        for case in self.cases[1:]:
            name=self.case_names[case['id']]
            self.prepare(name,'Matched dynamic '+case['id']+' on the same new binary/hierarchy',
                'Keep placement/setup/fine teams and zero guesses fixed; change only recorded solve flags',self.owner)
            self.ledger.ingest(self.campaign,name,reports[case['id']])
        self.require_time(1500)
        self.diagnostic(library)
        self.require_time(850)
        self.control(self.last)
        self.decide()
        print('PHASE6_COMPLETE '+json.dumps(dict(best=self.state['best'],winner=self.state['winner'],state=str(self.state_path))),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--state',type=Path)
    parser.add_argument('--profile-state',type=Path)
    parser.add_argument('--prefix',default='070-halo')
    parser.add_argument('--repeats',type=int,default=7)
    parser.add_argument('--deadline',type=float)
    args=parser.parse_args()
    if args.repeats<3:parser.error('At least3 complete12 steady samples required')
    phase=Phase6(args)
    phase.ledger.process_tree.enable_subreaper()
    def interrupted(signum,frame):raise KeyboardInterrupt('Phase6 interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    try:phase.run()
    except BaseException as error:
        if phase.state.get('status')!='blocked':
            phase.state.update(complete=False,status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error))
            phase.save()
        raise


if __name__=='__main__':main()
