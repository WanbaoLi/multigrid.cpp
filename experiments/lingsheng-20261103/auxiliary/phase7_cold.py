#!/usr/bin/env python3
"""Fresh-hierarchy full12 acceptance, separate from the warm campaign objective.

LOCAL PREPARATION ONLY until explicitly run inside an owned compute allocation.
The numerical candidate must already have a measured, independently verified
warm report and a matching passed CTest stage. This controller never edits or
builds numerical source and never calls campaign.promote.
"""
import argparse
from copy import deepcopy
from datetime import datetime
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time

CANONICAL='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
SCOPE='cold_canonical_fixture_to_first12'
ORDER=(('baseline',0),('candidate',0),('candidate',1),('baseline',1),
       ('baseline',2),('candidate',2),('baseline',3))
STARTUP={'LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'}
RESOURCE_KEYS=('threads','batch','ranks','block','seed','placement_threads','setup_threads')
TAG='LQCD_OPT_PHASE7_CHILD'
# Observed complete processes, including strict precision and output checks.
# This is a starting floor with reserve, not an ETA or a sum of timeout caps.
MINIMUM_GROUP_SECONDS=3*650+7*700+300


def require(value,message):
    if not value:raise RuntimeError(message)


def finite(value,positive=False):
    return type(value) in (int,float) and math.isfinite(value) and (value>0 if positive else value>=0)


def summary(values):
    require(values and all(finite(v,True) for v in values),'Finite positive complete12 times required')
    median=statistics.median(values)
    return dict(samples=list(values),median_seconds=median,minimum_seconds=min(values),
        maximum_seconds=max(values),relative_spread=(max(values)-min(values))/median)


def cold_gate(baseline,candidate,minimum_gain=.03,maximum_spread=.10,maximum_drift=.05):
    require(len(baseline)>=4 and len(candidate)>=3,'Four bracketed baseline and three fresh candidate samples required')
    before,after=statistics.median(baseline[:2]),statistics.median(baseline[-2:])
    drift=abs(before-after)/min(before,after)
    edge_drift=abs(baseline[0]-baseline[-1])/min(baseline[0],baseline[-1])
    b,c=summary(baseline),summary(candidate);gain=1-c['median_seconds']/b['median_seconds'];reasons=[]
    if drift>maximum_drift or edge_drift>maximum_drift:reasons.append('Baseline opening/closing drift exceeds5%')
    if max(b['relative_spread'],c['relative_spread'])>maximum_spread:reasons.append('Cold sample spread exceeds10%')
    if gain<minimum_gain:reasons.append('Cold median gain below3%')
    if c['maximum_seconds']>=b['minimum_seconds']:reasons.append('Cold timing ranges overlap')
    return dict(passed=not reasons,reasons=reasons,baseline=b,candidate=c,gain=gain,
        control_median_drift=drift,control_edge_drift=edge_drift,
        scope=SCOPE,cache_claim='Fresh process/hierarchy only; OS/storage caches uncontrolled')


def warm_gate(first,candidate,last,regression_limit=.02,maximum_spread=.10,maximum_drift=.05):
    """Conservative non-regression: every candidate sample fits the2% budget.

    A flat median with broad uncertainty is insufficient. The same routine is
    used for real warm reports after the ledger has validated all12 columns.
    """
    a,c,b=map(summary,(first,candidate,last));reasons=[]
    drift=abs(a['median_seconds']-b['median_seconds'])/min(a['median_seconds'],b['median_seconds'])
    worst=c['maximum_seconds']/min(a['minimum_seconds'],b['minimum_seconds'])-1
    if drift>maximum_drift:reasons.append('Warm control drift exceeds5%')
    if max(a['relative_spread'],b['relative_spread'],c['relative_spread'])>maximum_spread:reasons.append('Warm samples too noisy')
    if worst>regression_limit:reasons.append('Warm2% non-regression not isolated from sample uncertainty')
    return dict(passed=not reasons,reasons=reasons,opening=a,candidate=c,closing=b,
        worst_observed_regression=worst,control_median_drift=drift,regression_limit=regression_limit)


def resource_configuration(cfg):
    result={key:deepcopy(cfg[key]) for key in RESOURCE_KEYS if key in cfg}
    result.setdefault('placement_threads',cfg['threads']);result.setdefault('setup_threads',cfg['threads'])
    return result


def ordinary_configuration(cfg):
    context=cfg['context_environment']
    require(not any(context.get(k) for k in ('PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT')),
        'Ordinary samples exclude profiler/loader tracing')
    preload=str(context.get('LD_PRELOAD',''))
    require(not preload or (len(preload.split())==1 and Path(preload).name.startswith('libgomp.so')),
        'Only an already validated libgomp preload is allowed')


def runtime_family_matches(path,family):
    name=Path(path).name
    if family=='libc.so':
        return bool(re.fullmatch(r'libc(?:\.so(?:\.[0-9]+)*|-[0-9]+(?:\.[0-9]+)*\.so)',name))
    return name.startswith(family)


def ctest_library_binding(build,expected_sha,sha):
    """Resolve only CMake's known build-library alias, retaining both identities.

    Immutable inputs, source manifests, parent artifacts and gold references
    continue through the original strict path rule. The actual CTest object
    must remain a regular file within this exact canonical build directory.
    """
    build=Path(build);canonical=build.resolve(strict=True)
    require(build.is_dir() and build.absolute()==canonical and not build.is_symlink(),
        'CTest build directory must be canonical and must not use symlinks')
    logical=build/'liblqcd_cpu.so';resolved=logical.resolve(strict=True)
    require(resolved.is_relative_to(canonical) and resolved.is_file() and not resolved.is_symlink(),
        'CTest versioned library resolves outside its build directory or is not a regular file')
    actual=sha(resolved)
    require(actual==expected_sha,'CTest build library must match the actual measured candidate bytes')
    return dict(logical_path=str(logical),resolved_path=str(resolved),build_directory=str(canonical),
        sha256=actual,scope='Known CMake VERSION/SOVERSION build artifact only; other path guards unchanged')


def inspect_precision(report):
    v=report.get('verification',{});audit=v.get('checksum_audit',{})
    require(report.get('complete') is True and report.get('measurements_complete') is True and
        report.get('zero_initial_guess') is True,'Complete zero-guess output required')
    require(v.get('complete') is True and v.get('passed') is True and v.get('columns')==12 and
        finite(v.get('max_true_residual')) and v['max_true_residual']<=1e-8 and
        finite(v.get('solution_relative_error')) and v['solution_relative_error']<=1e-6,
        'Independent full12 residual/gold precision failed')
    require(v.get('propagator_sha256')==report.get('propagator_sha256'),'Independent/output identity differs')
    require(audit.get('protocol_version')==4 and audit.get('complete') is True and audit.get('passed') is True and
        audit.get('status')=='passed','Terminal protocol4 full12 proof required')
    errors=v.get('solution_relative_errors',[])
    require(len(errors)==12 and all(finite(e) and e<=1e-6 for e in errors),'All12 solution errors required')
    return v


def inspect_cold(report,parent,host,allocation):
    inspect_precision(report)
    require(report['timing_scope']==SCOPE and report.get('diagnostic') is False,
        'Only ordinary canonical-field fresh-hierarchy first12 timing is accepted')
    require(report['source_manifest_sha256']==parent['source_manifest_sha256'] and
        report['library_sha256']==parent['library_sha256'] and report['configuration']==parent['configuration'],
        'Cold source/library/configuration differs from frozen parent')
    key=report['comparison_key']
    require(key['host']==host and key['allocation']==allocation and key['scope']==SCOPE and
        key['prepared_gauge_manifest_sha256']==CANONICAL,'Cold host/allocation/scope/canonical field differs')
    require(report.get('prepared_gauge_sha256')==CANONICAL and report['input_sha256']==parent['input_sha256'],
        'Cold input/prepared bytes differ')
    samples=report['samples']
    require(len(samples)==1 and samples[0]['repeat']==0 and samples[0]['warmup'] is False,
        'Each cold process must contain exactly its first full12 without warmup')
    require(len(samples[0]['stats'])==12 and all(s['converged'] in (1,True) and finite(s['true_residual']) and
        s['true_residual']<=1e-8 for s in samples[0]['stats']),'Missing/bad cold column statistics')
    wall=report['cold_wall_seconds']
    require(finite(wall,True) and samples[0]['wall_seconds']==wall and finite(report['first12_api_seconds'],True),
        'Use the continuous wall, never a sum of independent phase maxima')
    return wall


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


class ColdAcceptance:
    def __init__(self,args):
        self.args=args;self.root=args.root.resolve();self.campaign=args.campaign.resolve();self.source=args.tools_project.resolve()
        self.aux=args.auxiliary.resolve();self.host=socket.gethostname();self.allocation=os.environ.get('LQCD_OPT_ALLOCATION')
        require(self.allocation and os.environ.get('LQCD_OPT_TASK_ID'),'Owned allocation/task required')
        self.deadline=args.deadline or float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0'))
        require(math.isfinite(self.deadline) and self.deadline>time.time(),'Finite safe allocation deadline required')
        if args.expected_host:require(self.host.split('.')[0]==args.expected_host,'Unexpected host')
        require(re.fullmatch('[a-z0-9][a-z0-9_-]{0,39}',args.prefix),'Safe short prefix required')
        sys.path.insert(0,str(self.aux))
        self.integrity=load('_phase7_integrity',self.aux/'file_integrity.py');self.integrity.known_vectors()
        self.sha=lambda p:self.integrity.read_dual(Path(p))['openssl_sha256']
        sys.path.insert(0,str(self.source/'tools/optimization'));import campaign as ledger;import process_tree
        self.ledger,self.tree=ledger,process_tree
        self.original_digest=ledger.digest;ledger.digest=self.sha  # read boundary only; exact source SHA recorded below
        self.policy=load('_phase7_cold_policy',self.aux/'cold_full12.py')
        self.recipe=load('_phase7_replay_helpers',self.aux/'prepare_best_replay.py')
        self.protocol=load('_phase7_protocol',self.aux/'raw_protocol_v4.py')
        self.raw=load('_phase7_raw_proof',self.aux/'raw_benchmark_v4.py')
        for name,expected in self.protocol.FILES.items():self.integrity.read_dual(self.aux/name,expected)
        self.integrity.read_dual(self.source/'tools/optimization/bench_full12.py',self.protocol.BENCHMARK_SHA)
        self.config=ledger.campaign(self.campaign)[1]
        self.home=(args.output or self.root/(args.prefix+'-cold')).resolve()
        require(not self.home.is_relative_to(self.campaign) and not self.home.is_relative_to(self.source),
            'Cold pointer/state must stay outside warm ledger and source')
        self.path=self.home/'state.json';self.home.mkdir(parents=True,exist_ok=True)
        self.store=(args.store or self.root/'cold-selection').resolve()
        require(not self.store.is_relative_to(self.campaign) and not self.store.is_relative_to(self.source),
            'Cold selection store must stay outside warm ledger and source')
        self.parents={}
        for role,name in [('baseline',args.baseline),('candidate',args.candidate)]:
            data,report,performance=ledger.checked_attempt(self.campaign,name,self.config)
            require(report.get('backend')==args.backend,'Selected parent backend differs from target')
            ordinary_configuration(report['configuration'])
            require(report['comparison_key'].get('prepared_gauge_manifest_sha256')==CANONICAL,'Parent canonical field missing')
            self.parents[role]=dict(attempt=name,configuration=report['configuration'],
                source_manifest_sha256=data['snapshot']['source_manifest_sha256'],library_sha256=report['library_sha256'],
                library=str(self.campaign/'attempts'/name/'artifacts/liblqcd_cpu.so'),input_sha256=report['input_sha256'],
                reference_propagator=report['reference_propagator'],gold_sha=report['verification']['reference_propagator_sha256'],
                extractor_sha=report['verification']['extractor_sha256'],historical_warm=performance)
        require(resource_configuration(self.parents['baseline']['configuration'])==resource_configuration(self.parents['candidate']['configuration']),
            'Freeze identical placement/setup/solve teams, ranks, batch, block and seed')
        require(all(self.parents[r]['gold_sha']==self.parents['baseline']['gold_sha'] for r in self.parents),
            'Same validated gold file required for both candidates')
        test_path=self.campaign/'attempts'/args.candidate_tests;test=ledger.read(test_path/'attempt.json');ledger.check_snapshot(test_path,test)
        require(test['snapshot']['source_manifest_sha256']==self.parents['candidate']['source_manifest_sha256'],
            'Candidate CTest source identity differs')
        test_stages=[s for key,s in test['stages'].items() if 'ctest' in key]
        require(test_stages and all(s['status']=='passed' and self.sha(test_path/s['log'])==s['log_sha256'] for s in test_stages),
            'Matching candidate CTest must actually pass before cold trials')
        ctest_binding=ctest_library_binding(test['snapshot']['build'],self.parents['candidate']['library_sha256'],self.sha)
        helpers=['cold_full12.py','prepare_best_replay.py','raw_cold_adapter.py','raw_protocol_v4.py',
            'phase7_cold_entry.py','phase7_publication.py',*self.protocol.FILES]
        contract=dict(controller_sha256=self.sha(__file__),parents=self.parents,host=self.host,allocation=self.allocation,
            prefix=args.prefix,fixture=str(args.fixture.resolve()),reference=str(args.reference.resolve()),extractor=str(args.extractor.resolve()),
            cold_store=str(self.store),
            inherited_loader_environment={key:os.environ.get(key) for key in
                ('LD_LIBRARY_PATH','OMP_PROC_BIND','OMP_PLACES','OMP_WAIT_POLICY','GOMP_SPINCOUNT','LD_PRELOAD')},
            helpers={name:self.sha(self.aux/name) for name in sorted(set(helpers))},
            bookkeeping={name:self.sha(self.source/'tools/optimization'/name) for name in ['campaign.py','trial.py','bench_full12.py','process_tree.py']},
            patched_callbacks=['campaign.digest only; raw exact-offset dual SHA'],candidate_test_record_sha256=self.sha(test_path/'attempt.json'),
            candidate_test_library_binding=ctest_binding,minimum_group_seconds=MINIMUM_GROUP_SECONDS)
        self.state=ledger.read(self.path) if self.path.exists() else dict(contract=contract,complete=False,status='prepared',
            created=ledger.now(),warm_best_sha256=self.sha(self.campaign/'best.json'),cold_order=list(ORDER),runs={})
        require(self.state['contract']==contract,'Changed source/helpers/host/allocation: retain state and use a new epoch')
        if not self.path.exists():
            names=[args.prefix+'-warm-'+s for s in ('a','c','b')]+[f'{args.prefix}-cold-{role[0]}{index}' for role,index in ORDER]
            require(not any((self.campaign/'attempts'/name).exists() for name in names),'Fresh group IDs must not pre-exist')
        self.save()
        require(self.sha(args.reference)==self.config['reference_sha256'],'Independent scalar reference bytes differ')
        for parent in self.parents.values():
            require(self.sha(args.extractor)==parent['extractor_sha'] and self.sha(parent['reference_propagator'])==parent['gold_sha'],
                'Validated extractor/gold bytes differ')

    def save(self):self.state['updated']=self.ledger.now();self.ledger.atomic(self.path,self.state)

    def unchanged(self):
        require(self.sha(__file__)==self.state['contract']['controller_sha256'],'Controller changed')
        require(self.sha(self.campaign/'best.json')==self.state['warm_best_sha256'],'Warm best changed during cold group')
        for name,value in self.state['contract']['helpers'].items():require(self.sha(self.aux/name)==value,'Helper changed: '+name)
        for name,value in self.state['contract']['bookkeeping'].items():require(self.sha(self.source/'tools/optimization'/name)==value,'Bookkeeping changed: '+name)
        for parent in self.parents.values():require(self.sha(parent['library'])==parent['library_sha256'],'Frozen measured library changed')

    def experience(self,name):
        history=self.ledger.show_history(self.campaign)
        record=dict(time=self.ledger.now(),history_sha256=history['history_read_token'],
            attempts=[{k:r.get(k) for k in ('id','status','proposal','conclusions')} for r in history['attempts']],
            external={str(p.resolve()):self.sha(p) for p in self.args.experience})
        path=self.home/'experience'/f'{name}-{time.time_ns()}.json';self.ledger.atomic(path,record)
        return dict(path=str(path),sha256=self.sha(path))

    def time_for(self,seconds):
        if self.deadline-time.time()>=seconds:return
        self.state.update(complete=False,status='pending',pending_reason='Insufficient safe allocation time; no cross-allocation mixing',required_seconds=seconds)
        self.save();raise RuntimeError(self.state['pending_reason'])

    def propose(self,name,role,change):
        path=self.campaign/'attempts'/name
        if not path.exists():
            self.experience(name);history=self.ledger.show_history(self.campaign)
            self.ledger.propose(self.campaign,name,dict(history_read_token=history['history_read_token'],
                bottleneck='Measured fresh-hierarchy setup cost; actual candidate hypothesis stays in its parent proposal',
                hypothesis=name+': frozen '+role+' reproduces first12 cold cost and full12 precision',change=change,
                mechanism='Independent zero-guess processes, fixed resources and bracketed controls; separate warm non-regression',
                history_links=[str(self.path),str(self.campaign/'attempts'/self.parents[role]['attempt']/'report.json')],
                retry_conditions='Same unchanged epoch resumes only passed stages; failed/interrupted stages retained, new explicit retry/epoch required'))
        return self.ledger.snapshot_from(self.campaign,name,self.parents[role]['attempt'])

    def stage(self,name,key,argv,timeout,env=None):
        self.unchanged();record=self.ledger.read(self.campaign/'attempts'/name/'attempt.json');old=record['stages'].get(key)
        require(not old or old['status']=='passed','Never automatically retry failed/interrupted/running stages')
        if not old:self.time_for(timeout+45)
        request=dict(argv=list(map(str,argv)),cwd=record['snapshot']['build'],env=env or {},timeout_seconds=old['timeout_seconds'] if old else timeout)
        result=self.ledger.run_stage(self.campaign,name,key,request)
        require(result['status']=='passed' and result['cleanup']['complete'],'Stage failed or cleanup incomplete: '+name+'/'+key)
        return result

    def environment(self,parent):
        project=self.campaign/'attempts'/parent['attempt']/'source'
        keys=self.policy.numerical_environment_keys(project)|set(self.recipe.solve_keys(project))|STARTUP
        command=['env']
        for key in sorted(keys):command+=['-u',key]
        command += [key+'='+str(value) for key,value in sorted(parent['configuration']['context_environment'].items())]
        return command+['LQCD_VERBOSE=0','LQCD_HALO_PROFILE=0','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1']

    def plan(self,parent):
        cfg=parent['configuration'];return dict(context_environment=cfg['context_environment'],
            placement_threads=cfg.get('placement_threads',cfg['threads']),setup_threads=cfg.get('setup_threads',cfg['threads']),
            cases=[dict(id='full12',threads=cfg['threads'],batch=cfg['batch'],environment=cfg['solve_environment'])])

    def verify_command(self,name,run):
        p=self.parents['baseline'];wrapper=self.aux/'raw_benchmark_v4.py'
        return [self.args.python,'-u',str(wrapper),'--benchmark',str(self.source/'tools/optimization/bench_full12.py'),
            '--expected-benchmark-sha',self.protocol.BENCHMARK_SHA,'--expected-wrapper-sha',self.protocol.FILES[wrapper.name],
            '--expected-reader-sha',self.protocol.FILES['file_integrity.py'],'--expected-helper-sha',self.protocol.HELPER_SHA,
            '--helper-wrapper',str(self.aux/'raw_scalar_helper.py'),'--expected-helper-wrapper-sha',self.protocol.FILES['raw_scalar_helper.py'],
            '--expected-gold-sha',p['gold_sha'],'--audit-output',str(self.campaign/'attempts'/name/'checksum-audit/independent'),
            '--verify',str(run),'--verification-output','independent','--reference',str(self.args.reference),'--extractor',str(self.args.extractor)]

    def cold(self,role,index):
        name=f'{self.args.prefix}-cold-{role[0]}{index}';parent=self.parents[role];snapshot=self.propose(name,role,'One ordinary fresh canonical-field hierarchy and first full12')
        existing=self.ledger.read(self.campaign/'attempts'/name/'attempt.json')['stages']
        self.time_for(495 if existing.get('ordinary-cold',{}).get('status')=='passed' else 1400)
        path=self.campaign/'attempts'/name;plan=path/'plan.json';value=self.plan(parent)
        if plan.exists():require(self.ledger.read(plan)==value,'Plan changed')
        else:self.ledger.atomic(plan,value)
        run=path/'measurements/cold-first12';project=Path(snapshot['source'])
        adapter=self.aux/'raw_cold_adapter.py'
        command=self.environment(parent)+[self.args.python,str(project/'tools/run_numa.py')]
        if self.args.backend=='x86':command+=['--ranks-per-numa','2']
        command+=['--threads',str(value['placement_threads']),'--',self.args.python,'-u',str(self.aux/'phase7_cold_entry.py'),
            '--adapter',str(adapter),'--publication-output',str(path/'checksum-audit/new-output-publication'),
            '--expected-entry-sha',self.state['contract']['helpers']['phase7_cold_entry.py'],
            '--expected-adapter-sha',self.state['contract']['helpers'][adapter.name],
            '--expected-publication-sha',self.state['contract']['helpers']['phase7_publication.py'],
            '--expected-reader-sha',self.protocol.FILES['file_integrity.py'],'--',
            '--cold-wrapper',str(self.aux/'cold_full12.py'),'--expected-cold-sha',self.state['contract']['helpers']['cold_full12.py'],
            '--expected-reader-sha',self.protocol.FILES['file_integrity.py'],'--expected-adapter-sha',self.state['contract']['helpers'][adapter.name],
            '--audit-output',str(path/'checksum-audit/cold-runtime'),'--','--project',str(project),
            '--source-manifest',str(path/'source-manifest.json'),'--snapshot-sha',snapshot['source_manifest_sha256'],
            '--library',parent['library'],'--expected-library-sha',parent['library_sha256'],'--plan',str(plan),
            '--fixture',str(self.args.fixture),'--reference-propagator',parent['reference_propagator'],
            '--backend',self.args.backend,'--allocation',self.allocation,'--output',str(run)]
        self.stage(name,'ordinary-cold',command,850)
        self.stage(name,'independent',self.verify_command(name,run),450,
            dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close',LD_PRELOAD='',PERF_COUNTER_ROOT='',LD_DEBUG=''))
        report=self.ledger.read(run/'result.json');wall=inspect_cold(report,parent,self.host,self.allocation)
        old=self.state['runs'].get(name)
        if old:require(self.sha(run/'result.json')==old['report_sha256'],'Completed cold report changed on resume')
        self.raw.check_audit_provenance(run,report,self.sha)
        cold_audits={}
        for rank in range(parent['configuration']['ranks']):
            directory=path/'checksum-audit/cold-runtime'/('rank%05d'%rank)
            manifest=self.ledger.read(directory/'manifest.json');provenance=manifest['provenance']
            require(manifest['complete'] and manifest['checks']>0 and manifest['callbacks']==['cold_full12.sha'] and
                provenance['cold_source_sha256']==self.state['contract']['helpers']['cold_full12.py'] and
                provenance['adapter_sha256']==self.state['contract']['helpers']['raw_cold_adapter.py'] and
                provenance['reader_sha256']==self.protocol.FILES['file_integrity.py'] and
                provenance['solver_and_clocks_unchanged'] and provenance['prepared_hash_unchanged'] and
                not provenance['raw_lime_input_hash_inside_cold_clock'], 'Ordinary cold read/timing audit failed')
            for item in manifest['rows']:
                entry=directory/item['path'];require(entry.name==item['path'] and not entry.is_symlink() and
                    self.sha(entry)==item['sha256'],'Cold checksum evidence changed/unsafe')
                row=self.ledger.read(entry)
                require(row['passed'] and row['byte_count_exact'] and row['metadata_stable'] and row['eof_probe_bytes']==0 and
                    row['openssl_sha256']==row['software_sha256'],'Cold read-contract audit failed')
            cold_audits[str(directory/'manifest.json')]=self.sha(directory/'manifest.json')
            publication_dir=path/'checksum-audit/new-output-publication'/('rank%05d'%rank)
            publication_proof=self.ledger.read(publication_dir/'protocol.json')
            require(publication_proof['complete'] and publication_proof['passed'] and
                publication_proof['publication_calls']==(1 if rank==0 else 0) and
                publication_proof['entry_sha256']==self.state['contract']['helpers']['phase7_cold_entry.py'] and
                publication_proof['publication_sha256']==self.state['contract']['helpers']['phase7_publication.py'] and
                publication_proof['frozen_adapter_sha256']==self.state['contract']['helpers']['raw_cold_adapter.py'] and
                publication_proof['reader_sha256']==self.protocol.FILES['file_integrity.py'] and
                publication_proof['frozen_cold_and_clocks_unchanged'],'New-output publication producer identity failed')
            if rank==0:
                receipt=self.ledger.read(publication_dir/'receipt.json')
                require(receipt['complete'] and receipt['passed'] and receipt['full_reads'] in (1,3) and
                    receipt['published_sha256']==report['propagator_sha256'] and not receipt['expected_previously_published'] and
                    not receipt['source_modified'] and not receipt['timestamps_modified'] and not receipt['sleep_used'],
                    'New output did not reach a complete publication pass')
                for item in publication_proof['receipt_snapshots']:
                    entry=publication_dir/item['path'];require(entry.name==item['path'] and not entry.is_symlink() and
                        self.sha(entry)==item['sha256'],'Unpublished/progress receipt changed')
                require(len(publication_proof['receipt_snapshots'])>=2,'Durable first-read and final receipts required')
                if receipt['full_reads']==3:
                    first=receipt['reads'][0]
                    require(not first['strict_pass'] and not first['report']['passed'] and
                        not receipt['first_rejection_accepted'],'First rejected read must remain rejected')
            cold_audits[str(publication_dir/'protocol.json')]=self.sha(publication_dir/'protocol.json')
        proof=self.ledger.read(run/report['verification']['evidence_relative_path'])
        require(proof['complete'] and {(c['source_spin'],c['source_color']) for c in proof['columns']}=={(s,c) for s in range(4) for c in range(3)},'All unique scalar columns required')
        self.state['runs'][name]=dict(role=role,index=index,report=str(run/'result.json'),report_sha256=self.sha(run/'result.json'),
            seconds=wall,resources=report['resources'],source_manifest_sha256=report['source_manifest_sha256'],library_sha256=report['library_sha256'],
            cold_runtime_audit_sha256=cold_audits)
        self.save()
        conclusion='Verified ordinary fresh-hierarchy canonical full12 sample; separate cold scope, not a warm API score or promotion'
        record=self.ledger.read(path/'attempt.json')
        if not any(row['conclusion']==conclusion for row in record.get('conclusions',[])):
            self.ledger.conclude(self.campaign,name,'inconclusive',conclusion,[str(run/'result.json'),str(self.path)])
        return report

    def warm(self):
        reports=[]
        for role,suffix in [('baseline','a'),('candidate','c'),('baseline','b')]:
            name=self.args.prefix+'-warm-'+suffix;parent=self.parents[role];row=self.state.setdefault('warm_runs',{}).setdefault(name,{})
            path=self.campaign/'attempts'/name
            if not (path/'report.json').exists():
                require(not row.get('status') or row['status']=='passed','Interrupted warm child needs explicit recovery, not rerun')
                self.time_for(1100);self.experience(name)
                proposal=self.home/'warm-plans'/(name+'-proposal.json');plan=self.home/'warm-plans'/(name+'-plan.json')
                for target,value in [(plan,self.plan(parent)),(proposal,dict(bottleneck='Cold candidate needs a fresh warm full12 non-regression bracket',
                    hypothesis=name+': setup optimization preserves warm full12 cost',change='Exact frozen parent, separate process and one warmup plus3steady',
                    mechanism='Do not confuse cold-only gain with slower reused-hierarchy solves',history_links=[str(self.path)],
                    retry_conditions='New source/library/allocation epoch or explicitly attributed failed-stage recovery only'))]:
                    if target.exists():require(self.ledger.read(target)==value,'Warm plan/proposal changed')
                    else:self.ledger.atomic(target,value)
                trial=self.source/'tools/optimization/trial.py'
                arguments=['--campaign',str(self.campaign),'--id',name,'--proposal',str(proposal),'--plan',str(plan),
                    '--source-from',parent['attempt'],'--reuse-attempt',parent['attempt'],'--fixture',str(self.args.fixture),
                    '--reference',str(self.args.reference),'--extractor',str(self.args.extractor),'--reference-propagator',parent['reference_propagator'],
                    '--backend',self.args.backend,'--allocation',self.allocation]
                command=self.protocol.command(self.aux,trial,self.sha(trial),name,self.args.python,arguments,
                    framework_tools=self.source/'tools/optimization',gold_sha=parent['gold_sha'])
                environment=dict(os.environ)
                for key in self.policy.numerical_environment_keys(self.campaign/'attempts'/parent['attempt']/'source')|STARTUP:environment.pop(key,None)
                tag=self.tree.new_tag();environment[TAG]=tag;log=self.home/(name+'.log');require(not log.exists(),'Warm child log already exists')
                row.update(status='running',argv=command,tag=tag,started=self.ledger.now());self.save();process=None
                try:
                    with log.open('xb') as stream:
                        process=subprocess.Popen(command,cwd=str(self.root),env=environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                        row['pid']=process.pid;self.save();row['returncode']=process.wait(timeout=1000)
                    row['cleanup']=self.tree.terminate_owned(process,TAG,tag,grace=10)
                    require(row['returncode']==0 and row['cleanup']['complete'],'Warm child failed or cleanup incomplete')
                    row['status']='passed'
                except BaseException as exc:
                    if process:row['cleanup']=self.tree.terminate_owned(process,TAG,tag,grace=10)
                    row.update(status='failed',error=repr(exc));raise
                finally:row['ended']=self.ledger.now();row['log_sha256']=self.sha(log);self.save()
            data,report,performance=self.ledger.checked_attempt(self.campaign,name,self.config)
            if row.get('status')!='passed' and self.args.resume_reason:
                require(row.get('tag') and not self.tree.tagged_processes(TAG,row['tag']),
                    'Prior warm child still alive; no checkpoint adoption')
                require(all(s['status']=='passed' and s.get('cleanup',{}).get('complete') for s in data['stages'].values()),
                    'Interrupted warm run has unfinished/failed stages')
                row.update(status='passed',checkpoint_recovery_reason=self.args.resume_reason,log_sha256=self.sha(self.home/(name+'.log')))
                self.save()
            require(row.get('status')=='passed','Warm report was not created by this controller')
            inspect_precision(report)
            self.raw.check_audit_provenance(path/'measurements/full12',report,self.sha)
            require(report['source_manifest_sha256']==parent['source_manifest_sha256'] and report['library_sha256']==parent['library_sha256'] and
                report['configuration']==parent['configuration'],'Warm parent identity changed')
            require(report['comparison_key']['allocation']==self.allocation and report['comparison_key']['host']==self.host and
                report['comparison_key']['prepared_gauge_manifest_sha256']==CANONICAL,'Warm comparison epoch/input differs')
            require(performance['steady_repeats']==[1,2,3] and len(report['samples'])==4,'Warm1+3 protocol required')
            require(data['stages']['benchmark']['status']==data['stages']['independent']['status']=='passed','Warm numerical stages incomplete')
            reports.append((report,performance))
        require(reports[0][0]['comparison_key']==reports[1][0]['comparison_key']==reports[2][0]['comparison_key'],'Warm keys differ')
        require(reports[0][0]['resources']==reports[1][0]['resources']==reports[2][0]['resources'],'Warm rank masks differ')
        result=warm_gate(*[p['steady_samples'] for _,p in reports]);self.state['warm_assessment']=result;self.save()
        conclusion='Complete independent-process warm bracket for separate cold-objective non-regression; no automatic warm promotion'
        for suffix in ('a','c','b'):
            name=self.args.prefix+'-warm-'+suffix;record=self.ledger.read(self.campaign/'attempts'/name/'attempt.json')
            if not any(row['conclusion']==conclusion for row in record.get('conclusions',[])):
                self.ledger.conclude(self.campaign,name,'inconclusive',conclusion,[str(self.path)])
        return result

    def runtime(self):
        if not self.args.runtime_proof:return dict(passed=False,reasons=['Actual runtime proof missing; measurement retained without adoption'])
        proof=self.ledger.read(self.args.runtime_proof);fingerprint=self.sha(self.args.runtime_proof)
        require(proof.get('complete') is True and proof['host']==self.host and proof['allocation']==self.allocation,
            'Runtime proof belongs to another/incomplete epoch')
        require(proof.get('scope')=='separate warm-process rank0/8 maps; cold loader environment pinned',
            'Runtime proof must state its actual observation scope')
        signatures=[]
        for role,parent in self.parents.items():
            row=proof['parents'][role]
            require(row['library_sha256']==parent['library_sha256'] and row['configuration']==parent['configuration'],
                'Runtime proof parent/configuration differs')
            require({r['rank'] for r in row['ranks']}=={0,8},'Actual runtime maps require both sockets/ranks0 and8')
            expected_loader={key:value for key,value in self.state['contract']['inherited_loader_environment'].items()
                if key in ('LD_LIBRARY_PATH','LD_PRELOAD','OMP_WAIT_POLICY','GOMP_SPINCOUNT')}
            for key in ('LD_PRELOAD','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):expected_loader[key]=None
            expected_loader.update({key:str(value) for key,value in parent['configuration']['context_environment'].items()
                if key in expected_loader})
            require(row.get('loader_environment')==expected_loader,'Observed loader/OpenMP startup environment differs')
            for rank in row['ranks']:
                require(rank.get('captured_during_setup') is True and rank.get('task_owned') is True,'Runtime observations must be task-owned actual setup captures')
                libraries=rank['libraries'];require(libraries,'Actual runtime library map missing')
                for library in libraries:require(self.sha(library['path'])==library['sha256'],'Mapped runtime library bytes changed')
                require(any(Path(v['path']).name.startswith('liblqcd_cpu.so') and v['sha256']==parent['library_sha256'] for v in libraries),
                    'Runtime maps do not identify the actual measured solver library')
                signature={}
                for family in ('libgomp.so','libmpi.so','libstdc++.so','libc.so'):
                    matches={(str(Path(v['path']).resolve()),v['sha256']) for v in libraries if runtime_family_matches(v['path'],family)}
                    require(len(matches)==1,'Runtime proof needs exactly one '+family)
                    signature[family]=sorted(matches)
                signatures.append(signature)
        require(all(value==signatures[0] for value in signatures),'Setup-only comparison must keep the same runtime libraries on both sockets/candidates')
        return dict(passed=True,proof=str(self.args.runtime_proof.resolve()),sha256=fingerprint,
            scope=proof['scope'],limitation='Maps were captured in matched warm processes, not every cold PID; identical epoch/configuration and library bytes are required')

    def run(self):
        if not self.state['runs'] and not self.state.get('warm_runs'):
            # Actual full process costs on Arm: warm~650s, baseline cold650..700s.
            # Three warm +seven cold +300s reserve need a7150s starting floor.
            self.time_for(MINIMUM_GROUP_SECONDS)
        self.unchanged();self.state.update(status='running',complete=False);self.save()
        warm=self.warm();reports=[]
        for role,index in ORDER:reports.append(self.cold(role,index))
        require(all(report['resources']==reports[0]['resources'] for report in reports),'Cold rank CPU/NUMA resources differ')
        cold=cold_gate([r['cold_wall_seconds'] for r,(role,_) in zip(reports,ORDER) if role=='baseline'],
            [r['cold_wall_seconds'] for r,(role,_) in zip(reports,ORDER) if role=='candidate'])
        runtime=self.runtime()
        if 'cold_assessment' in self.state:
            self.state.setdefault('prior_assessments',[]).append({key:deepcopy(self.state[key]) for key in
                ('cold_assessment','warm_assessment','runtime_assessment') if key in self.state})
        eligible=cold['passed'] and warm['passed'] and runtime['passed']
        self.state.update(cold_assessment=cold,runtime_assessment=runtime,measurements_complete=True,
            complete=runtime['passed'],status='eligible' if eligible else ('inconclusive' if runtime['passed'] else 'pending_runtime'))
        self.save();self.unchanged()
        if self.args.adopt and eligible:
            adopt(self,self.parents['candidate'])
        print('COLD_ACCEPTANCE_COMPLETE '+json.dumps(dict(state=str(self.path),status=self.state['status'],cold=cold,warm=warm,runtime=runtime)),flush=True)


def adopt(controller,parent):
    """Independent atomic cold pointer; never call the warm ledger promoter."""
    c=controller;c.store.mkdir(parents=True,exist_ok=True);target=c.store/'best-cold.json';history=c.store/'best-cold-history'
    with c.ledger.locked(c.store):
        if target.exists():
            previous=c.ledger.read(target);base=c.parents['baseline']
            if (previous['attempt']==parent['attempt'] and previous['library_sha256']==parent['library_sha256'] and
                    previous['configuration']==parent['configuration'] and previous['source_manifest_sha256']==parent['source_manifest_sha256'] and
                    previous['state']==str(c.path)):
                require(c.sha(previous['library_path'])==previous['library_sha256'] and
                    c.sha(previous['state_snapshot'])==previous['state_sha256'],'Already adopted cold evidence changed')
                return previous
            require(previous['library_sha256']==base['library_sha256'] and previous['configuration']==base['configuration'],
                'Existing cold best differs from matched baseline; start a group against that exact version')
        artifact=c.store/'cold-artifacts'/parent['library_sha256']/'liblqcd_cpu.so';artifact.parent.mkdir(parents=True,exist_ok=True)
        if artifact.exists():require(c.sha(artifact)==parent['library_sha256'],'Cold retained artifact changed')
        else:shutil.copy2(parent['library'],artifact)
        snapshots=c.store/'cold-decisions';snapshots.mkdir(exist_ok=True)
        state_snapshot=snapshots/(str(time.time_ns())+'-state.json');c.ledger.atomic(state_snapshot,c.state)
        decision=dict(attempt=parent['attempt'],library_sha256=parent['library_sha256'],source_manifest_sha256=parent['source_manifest_sha256'],
            configuration=parent['configuration'],library_path=str(artifact),time=c.ledger.now(),state=str(c.path),
            state_snapshot=str(state_snapshot),state_sha256=c.sha(state_snapshot),
            cold_assessment=c.state['cold_assessment'],warm_assessment=c.state['warm_assessment'],runtime_proof=c.state['runtime_assessment'],
            scope=SCOPE,warm_best_unchanged_sha256=c.state['warm_best_sha256'])
        if target.exists():history.mkdir(exist_ok=True);c.ledger.atomic(history/(str(time.time_ns())+'.json'),c.ledger.read(target))
        c.ledger.atomic(target,decision)
    c.unchanged()


def rollback(store,record,reason,ledger,sha):
    """Restore only a previously accepted cold pointer, retaining both versions."""
    require(reason,'Rollback needs an evidence-based reason');store=Path(store).resolve();record=Path(record).resolve()
    require(record.parent==store/'best-cold-history' and not record.is_symlink(),
        'Rollback target must be a retained previously accepted cold-history record')
    value=ledger.read(record);artifact=Path(value['library_path']);state=Path(value['state_snapshot'])
    require(artifact.is_relative_to(store/'cold-artifacts') and state.is_relative_to(store/'cold-decisions'),
        'Rollback evidence/artifact must belong to this cold store')
    require(sha(artifact)==value['library_sha256'] and sha(state)==value['state_sha256'],'Retained cold proof/library changed')
    proof=ledger.read(state)
    require(proof['complete'] and proof['status']=='eligible' and proof['cold_assessment']['passed'] and
        proof['warm_assessment']['passed'] and proof['runtime_assessment']['passed'],'Target was not a fully accepted cold result')
    with ledger.locked(store):
        old=ledger.read(store/'best-cold.json');ledger.atomic(store/'best-cold-history'/(str(time.time_ns())+'.json'),old)
        decision=dict(value,time=ledger.now(),rollback_reason=reason,rollback_from=old['attempt'],rollback_history_record_sha256=sha(record))
        ledger.atomic(store/'best-cold.json',decision)
    return decision


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','campaign','tools-project','auxiliary','fixture','reference','extractor'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--baseline',required=True);p.add_argument('--candidate',required=True);p.add_argument('--candidate-tests',required=True)
    p.add_argument('--prefix',required=True);p.add_argument('--backend',choices=('arm','x86'),default='arm');p.add_argument('--python',default=sys.executable)
    p.add_argument('--output',type=Path);p.add_argument('--store',type=Path);p.add_argument('--deadline',type=float);p.add_argument('--expected-host');p.add_argument('--runtime-proof',type=Path)
    p.add_argument('--resume-reason',help='Explicit reason to recover a passed child after controller interruption; never retries failed numerical stages')
    p.add_argument('--experience',type=Path,action='append',default=[]);p.add_argument('--adopt',action='store_true')
    p.add_argument('--execute',action='store_true',help='Explicitly run bounded trials; default only prints the protocol')
    return p


def main():
    if sys.argv[1:2]==['rollback']:
        p=argparse.ArgumentParser(description='Restore a retained cold-only selection; warm best is untouched')
        for name in ('store','record','tools-project','auxiliary'):p.add_argument('--'+name,type=Path,required=True)
        p.add_argument('--reason',required=True);args=p.parse_args(sys.argv[2:])
        sys.path.insert(0,str(args.tools_project/'tools/optimization'))
        import campaign as ledger
        integrity=load('_phase7_rollback_integrity',args.auxiliary/'file_integrity.py');integrity.known_vectors()
        sha=lambda p:integrity.read_dual(p)['openssl_sha256']
        print(json.dumps(rollback(args.store,args.record,args.reason,ledger,sha),indent=2));return
    args=parser().parse_args()
    if not args.execute:
        print(json.dumps(dict(prepared_only=True,cold_order=ORDER,warm_order=['baseline','candidate','baseline'],
            candidate_prerequisite='Measured full12 verified attempt plus matching passed CTest; --source-from/build is done by existing trial.py',
            objective=SCOPE,main_warm_best_untouched=True,required_runtime_proof='Actual matched rank0/8 maps or no adoption'),indent=2));return
    controller=ColdAcceptance(args)
    try:controller.run()
    except BaseException as exc:
        if controller.state.get('status')!='pending':controller.state.update(complete=False,status='failed',error=repr(exc));controller.save()
        raise
    finally:controller.ledger.digest=controller.original_digest

if __name__=='__main__':main()
