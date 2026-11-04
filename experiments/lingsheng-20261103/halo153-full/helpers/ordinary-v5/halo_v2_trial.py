"""Prepared independent HaloV2 ordinary full12 group; no build, profile or queue.

Launch directly after external ARM tests and a fresh old052 profile. Each new
benchmark/verification stage uses the pinned derived factory exactly once.
The frozen phase6 source supplies the original bracket/halo adoption gates.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import sys
import time

HEAD='760666c8ac459ef062c749ee7ee9964c99e7c3c8'
OLD_NAME='052-reduce-on'
OLD_LIBRARY='d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82'
PHASE_SHA='3f3537ca6a09fbe6b22ae06e488a5a50f334cc7e374fd7326d345c6113de63e6'
FACTORY_SHA='a07ccf40e3808d8dd7c6480f1a8f511113d4b1d944e28f627fc5cca092a6fe27'
DERIVED_SHA='25b6fb0d171efb12954edbd0941701ac38fdcb954cf1882de443b50e755659a2'
REQUIRED_TEST_STAGES=['configure','build','arm-codegen','arm-unit-ctest','mpi-numerical-ctest','sve-compiled-coarse']+[
    'sve-'+kind+'-vl'+str(width) for width in (16,32,64) for kind in ('dense','ghost-mpi4')]
# Planning floors come from completed103 scopes with extra room. Hard stage
# timeouts are independent bounds; a slow stage may leave the group pending.
GROUP_FLOORS={'a-benchmark':600,'a-verify':300,'candidate-benchmark':700,
    'candidate-verify-off':300,'candidate-verify-on':300,
    'diagnostic-benchmark':600,'diagnostic-verify':300,'b-benchmark':600,'b-verify':300}


def require(value,message):
    if not value:raise RuntimeError(message)


class PendingTime(RuntimeError):pass


def option(argv,name):
    require(argv.count(name)==1 and argv.index(name)+1<len(argv),'Exactly one '+name+' required')
    return argv[argv.index(name)+1]


def safe_relative(value):
    require(isinstance(value,str) and '\\' not in value and not value.startswith('/'),'Unsafe evidence relative path')
    p=Path(value)
    require(not p.is_absolute() and not p.anchor and not p.drive and '..' not in p.parts and str(p) not in ('','.'), 'Unsafe evidence relative path')
    return p


def remaining_floor(completed):
    return sum(value for key,value in GROUP_FLOORS.items() if key not in completed)


def validate_test_contract(state,status,attempt,library_sha):
    """Pure structural checks; the caller verifies every referenced file SHA."""
    require(state.get('complete') is True and state.get('status')=='passed' and state.get('scope')=='full' and
        state.get('full_numerical_complete') is True and state.get('mpi_status')==state.get('sve_matrix_status')=='passed' and
        state.get('arm_codegen_complete') is True and state.get('unit_complete') is True,
        'External proof needs completed full ARM MPI/SVE tests; codegen-only118 is insufficient')
    require(state.get('source_head')==HEAD and state.get('library_sha256')==library_sha and
        attempt.get('snapshot',{}).get('git_head')==HEAD and state.get('snapshot')==attempt.get('snapshot'),
        'External source/library/snapshot identity differs')
    require(status.get('status')=='passed' and status.get('returncode')==0 and status.get('cleanup',{}).get('complete') and
        status.get('host')==state.get('host'), 'External test worker must be closed passed and cleaned')
    for key in REQUIRED_TEST_STAGES:
        row=attempt.get('stages',{}).get(key,{})
        require(row.get('status')=='passed' and row.get('returncode')==0 and row.get('cleanup',{}).get('complete') and
            re.fullmatch('[0-9a-f]{64}',row.get('log_sha256','')), 'External stage not closed passed: '+key)
    validate_sve_matrix(state.get('sve_matrix',{}),library_sha)


def validate_sve_matrix(matrix,library_sha):
    for width in (16,32,64):
        item=matrix.get(str(width),{})
        ranks=item.get('ranks',{})
        require(ranks.get('complete') and ranks.get('library_sha256')==library_sha and
            ranks.get('requested_bytes')==width and len(ranks.get('ranks',[]))==4 and
            {r['rank'] for r in ranks['ranks']}==set(range(4)) and
            all(r['actual_bytes']==width and r.get('inherit_exec') for r in ranks['ranks']) and
            any(row.get('calls',0)>0 and row.get('max_width',0)>1 for row in item.get('actual',[])),
            'Actual per-rank VL/library and grouped calls required for width'+str(width))


class StrictFiles:
    def __init__(self,integrity):self.integrity=integrity
    def sha(self,path,expected=None):
        return self.integrity.read_dual(Path(path),expected)['openssl_sha256']
    def text(self,path,expected=None):
        # Parse the exact bytes whose dual digest was checked, never a second
        # buffered read-to-EOF view of metadata or diagnostic logs.
        path=Path(path)
        require(not path.is_symlink() and path.absolute()==path.resolve(strict=True),'Strict metadata path required')
        fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:
            before=self.integrity.metadata(os.fstat(fd));size=before['bytes']
            require(size<=16*1024**2,'Auxiliary metadata/log exceeds16MiB bound')
            held=[];offset=0
            while offset<size:
                part=os.pread(fd,min(4*1024**2,size-offset),offset)
                require(isinstance(part,bytes) and 0<len(part)<=min(4*1024**2,size-offset),'Metadata pread length contract')
                held.append(part);offset+=len(part)
            require(os.pread(fd,1,size)==b'' and before==self.integrity.metadata(os.fstat(fd))==
                self.integrity.metadata(path.stat()),'Metadata FD/count/EOF identity changed')
        finally:os.close(fd)
        payload=b''.join(held);actual=self.integrity.small_dual(payload)
        require(expected is None or actual==expected,'Metadata expected SHA mismatch: '+str(path))
        return payload.decode('utf-8')
    def read(self,path,expected=None):return json.loads(self.text(path,expected))


def load_source(name,path,expected,strict):
    import types
    payload=strict.text(path,expected)
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(payload,str(path),'exec'),module.__dict__)
    return module


def external_tests(args,strict,ledger):
    state=strict.read(args.tests_state,args.tests_state_sha)
    status=strict.read(args.tests_status,args.tests_status_sha)
    owner=args.root/'campaign-halo-v2/attempts'/state['test_attempt']
    require(ledger.NAME.fullmatch(state['test_attempt']),'Safe external test-attempt required')
    attempt=strict.read(owner/'attempt.json')
    library=Path(state['library'])
    require(library==library.resolve(strict=True) and library.is_relative_to((owner/'build').resolve(strict=True)),
        'Only the canonical already-tested library inside its original build is reusable')
    validate_test_contract(state,status,attempt,args.library_sha)
    argv=status['argv']
    require(option(argv,'--scope')=='full' and option(argv,'--test-attempt')==state['test_attempt'] and
        option(argv,'--expected-entry-sha')==state['controller_sha256'] and
        option(argv,'--expected-manifest-sha')==state['helper_manifest_sha256'] and
        option(argv,'--root')==str(args.root) and
        option(argv,'--state-id')+'-state.json'==args.tests_state.name,
        'External full test task argv is not bound to the supplied state')
    ledger.check_snapshot(owner,attempt)
    strict.sha(library,args.library_sha)
    files={str(args.tests_state):args.tests_state_sha,str(args.tests_status):args.tests_status_sha,
        str(owner/'attempt.json'):strict.sha(owner/'attempt.json'),str(owner/'source-manifest.json'):
        strict.sha(owner/'source-manifest.json',state['snapshot']['source_manifest_sha256'])}
    test_aux=Path(option(argv,'--auxiliary'))
    test_manifest=test_aux/'halo-v2-arm-helpers.json'
    checked_manifest=strict.read(test_manifest,state['helper_manifest_sha256'])
    files[str(test_manifest)]=state['helper_manifest_sha256']
    for name,expected in checked_manifest['files'].items():
        path=test_aux/safe_relative(name);strict.sha(path,expected);files[str(path)]=expected
    for key in REQUIRED_TEST_STAGES:
        row=attempt['stages'][key];path=owner/safe_relative(row['log'])
        strict.sha(path,row['log_sha256']);files[str(path)]=row['log_sha256']
    for relative,expected in state['codegen_files'].items():
        path=args.root/'campaign-halo-v2'/safe_relative(relative);strict.sha(path,expected);files[str(path)]=expected
    codegen=strict.read(owner/'codegen/codegen.json')
    require(codegen.get('complete') and codegen.get('false_path_no_direct_halo_flag_or_batch_call'),
        'Actual compiled false path mechanism gate did not pass')
    return dict(complete=True,kind='External closed ARM CTest/SVE proof; no inherited timing or physical full12 precision',
        library=str(library),library_sha256=args.library_sha,source_head=HEAD,
        source_manifest_sha256=state['snapshot']['source_manifest_sha256'],host=state['host'],
        original_allocation=state['allocation'],original_owner=str(owner),files=files,
        actual_vector_lengths=[16,32,64],test_stages=REQUIRED_TEST_STAGES,
        new_build=False,new_test_execution=False,performance_evidence=False,physical_full12_evidence=False)


def import_historical(args,ledger,strict):
    """Copy original metadata/source/artifact/best bytes; retain their old epoch."""
    origin=args.root/'campaign';destination=args.campaign
    limits=ledger.campaign(origin)[1]
    old,report,_=ledger.checked_attempt(origin,OLD_NAME,limits)
    best=strict.read(origin/'best.json')
    require(best['attempt']==OLD_NAME and report['library_sha256']==OLD_LIBRARY,'Actual main retained best must be old052')
    if not destination.exists():
        ledger.initialize(destination,args.root/'source-halo-v2-760',args.root/'source-halo-v2-760/skills/kunpeng-lqcd-reference',
            limits['input_sha256'],limits['reference_sha256'],baseline_commit=HEAD,
            residual_limit=limits['residual_limit'],solution_limit=limits['solution_relative_error_limit'],
            minimum_gain=limits['minimum_gain'],maximum_spread=limits['maximum_relative_spread'])
    local_limits=ledger.campaign(destination)[1]
    for key in ('input_sha256','reference_sha256','residual_limit','solution_relative_error_limit','minimum_gain',
                'maximum_relative_spread','minimum_steady_samples'):
        require(local_limits[key]==limits[key],'Independent campaign cannot loosen original gate: '+key)
    original=origin/'attempts'/OLD_NAME;imported=destination/'attempts'/OLD_NAME
    proof_path=destination/'old052-import-proof.json'
    if not imported.exists():
        require(not (destination/'best.json').exists() and not proof_path.exists(),'Incomplete historical import; retain and use a new campaign')
        imported.mkdir()
        for name in ('attempt.json','source-manifest.json','source.tar.gz','source.diff','git-status.txt','report.json'):
            shutil.copy2(original/name,imported/name)
        shutil.copytree(original/'source',imported/'source');shutil.copytree(original/'artifacts',imported/'artifacts')
        shutil.copy2(origin/'best.json',destination/'best.json')
        files={}
        for path in sorted(imported.rglob('*')):
            if path.is_file():
                relative=str(path.relative_to(imported));expected=strict.sha(original/relative)
                strict.sha(path,expected);files[relative]=expected
        proof=dict(complete=True,historical_only=True,origin=str(original),imported=str(imported),files=files,
            origin_best=str(origin/'best.json'),original_best_sha256=strict.sha(origin/'best.json'),
            imported_best_sha256=strict.sha(destination/'best.json'),
            original_configuration=report['configuration'],original_source_commit=old['snapshot']['git_head'],
            original_source_manifest_sha256=old['snapshot']['source_manifest_sha256'],library_sha256=OLD_LIBRARY,
            original_absolute_paths_preserved=True,old_timing_not_relabelled=True,no_fresh_test_or_verification_claim=True)
        ledger.atomic(proof_path,proof)
        ledger.event(destination,'import_historical_old052',dict(proof=str(proof_path),sha256=strict.sha(proof_path)))
    proof=strict.read(proof_path)
    require(proof.get('complete') and proof.get('historical_only') and proof['origin']==str(original) and
        proof['original_best_sha256']==proof['imported_best_sha256']==strict.sha(origin/'best.json'),
        'Historical origin/best changed')
    for relative,expected in proof['files'].items():
        strict.sha(original/safe_relative(relative),expected);strict.sha(imported/safe_relative(relative),expected)
    ledger.checked_attempt(destination,OLD_NAME,local_limits)
    return local_limits,proof


class Trial:
    def __init__(self,args,strict,ledger,phase,protocol):
        self.args=args;self.root=args.root;self.source=self.root/'source-halo-v2-760'
        self.campaign=args.campaign;self.strict=strict;self.ledger=ledger;self.phase=phase;self.protocol=protocol
        self.require=require;self.deadline=float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0'))
        self.allocation=os.environ.get('LQCD_OPT_ALLOCATION');self.host=socket.gethostname()
        require(self.allocation and os.environ.get('LQCD_OPT_TASK_ID') and math.isfinite(self.deadline) and self.deadline>time.time(),
            'Owned task and finite safe deadline required')
        require(__import__('platform').machine().lower() in ('aarch64','arm64') and self.host==args.expected_host,
            'Exact allocated ARM compute host required')
        require(ledger.git(self.source,'rev-parse','HEAD')==HEAD and not ledger.git(self.source,'status','--short'),
            'Clean independent760 source required; controller never updates source')
        self.main_best_sha=strict.sha(self.root/'campaign/best.json')
        self.tests=external_tests(args,strict,ledger)
        require(self.tests['host']==self.host,'Native tested binary requires the same compute host; no implicit ISA portability assumption')
        self.profile_path=args.profile_state
        self.profile=strict.read(args.profile_state,args.profile_state_sha)
        status=strict.read(args.profile_status,args.profile_status_sha)
        require(status.get('status')=='passed' and status.get('returncode')==0 and status.get('cleanup',{}).get('complete') and
            status.get('host')==self.host,'Fresh profile queue task must have closed passed and cleaned')
        require(self.profile.get('complete') and self.profile.get('budget',{}).get('complete') and
            self.profile.get('verification',{}).get('passed') and self.profile['verification'].get('columns')==12 and
            self.profile['verification'].get('checksum_audit',{}).get('helper_wrapper_sha256')==DERIVED_SHA and
            self.profile['allocation']==self.allocation and self.profile['host']==self.host and self.profile['best']==OLD_NAME,
            'A fresh same-allocation fully verified derived-helper old052 profile is required')
        profile_report=strict.read(self.profile['report'],self.profile['report_sha256'])
        require(profile_report.get('complete') and profile_report.get('verification')==self.profile['verification'],
            'Fresh profile state/report verification differs')
        self.limits,self.import_proof=import_historical(args,ledger,strict)
        self.parent,self.parent_report,_=ledger.checked_attempt(self.campaign,OLD_NAME,self.limits)
        self.base=deepcopy(self.parent_report['configuration']);self.parent_name=OLD_NAME
        require(self.profile['configuration']==profile_report['configuration']==self.base and
            self.profile['library_sha256']==profile_report['library_sha256']==OLD_LIBRARY and
            self.profile['source_manifest_sha256']==self.parent['snapshot']['source_manifest_sha256'],
            'Fresh profile does not describe exact old052 source/library/configuration')
        require(self.base['batch']==2 and self.base['ranks']==16 and self.base['threads']==32 and
            self.base.get('placement_threads')==self.base.get('setup_threads')==37 and
            self.base['solve_environment'].get('LQCD_COARSE_BATCH_REDUCE')==1 and
            not self.base['solve_environment'].get('LQCD_COARSE_BATCH_HALO',0) and
            not self.base['solve_environment'].get('LQCD_COARSE_CGS2',0) and self.base['solve_environment'].get('LQCD_GCR_FUSED',1) and
            self.base['context_environment'].get('LQCD_COARSE_EO',1), 'Exact retained production resource/algorithm path required')
        for key in phase.STARTUP_KEYS:
            require(not os.environ.get(key) and not self.base['context_environment'].get(key),
                'Ordinary group forbids runtime/preload/debug overrides: '+key)
        self.owner=args.prefix+'-new-off';self.first=args.prefix+'-control-a';self.last=args.prefix+'-control-b'
        self.diag=args.prefix+'-halo-profile';self.cases=phase.comparison_cases(self.base)
        require([c['id'] for c in self.cases]==['new-off','halo-on'],'Only same-hierarchy off/on cases are allowed here')
        self.case_names={'new-off':self.owner,'halo-on':args.prefix+'-halo-on'}
        self.state_path=self.root/(args.prefix+'-state.json')
        identity=dict(controller_sha256=strict.sha(__file__),helper_manifest_sha256=args.expected_manifest_sha,
            frozen_phase6_sha256=PHASE_SHA,factory_sha256=FACTORY_SHA,derived_helper_sha256=DERIVED_SHA,
            source_head=HEAD,tests_state=str(args.tests_state),tests_state_sha256=args.tests_state_sha,
            tests_status_sha256=args.tests_status_sha,tested_library_sha256=args.library_sha,
            profile_state=str(args.profile_state),profile_state_sha256=args.profile_state_sha,
            profile_status_sha256=args.profile_status_sha,allocation=self.allocation,host=self.host,
            main_best_sha256=self.main_best_sha,initial_best=OLD_NAME,initial_configuration=self.base,repeats=7,
            old052_import_proof_sha256=strict.sha(self.campaign/'old052-import-proof.json'))
        if self.state_path.exists():
            require(args.resume and args.resume_reason,'Existing state requires explicit same-epoch resume reason')
            self.state=strict.read(self.state_path)
            require(all(self.state.get(k)==v for k,v in identity.items()),'Controller/source/epoch changed: use new prefix/campaign')
        else:
            require(not args.resume,'Cannot resume nonexistent state')
            self.state=dict(identity,complete=False,status='prepared',ordinary_group_floor_seconds=4000,
                external_ctest_proof=self.tests,completed_budget_scopes=[],main_best_modified=False)
        require(self.best()==(self.state.get('best') if self.state.get('complete') else OLD_NAME),
            'Independent campaign best changed outside this trial')
        self.save()

    def best(self):return self.strict.read(self.campaign/'best.json')['attempt']
    def save(self):self.ledger.atomic(self.state_path,self.state)
    def unchanged(self):
        require(self.strict.sha(self.root/'campaign/best.json')==self.main_best_sha,'Main retained best changed')
        self.strict.sha(__file__,self.state['controller_sha256'])
        self.strict.sha(self.args.auxiliary/'halo-v2-trial-helpers.json',self.args.expected_manifest_sha)
        for relative,expected in self.args.helper_manifest['files'].items():
            self.strict.sha(self.args.auxiliary/safe_relative(relative),expected)
        self.strict.sha(self.tests['library'],self.args.library_sha)
        for path,expected in self.tests['files'].items():self.strict.sha(path,expected)
        self.strict.sha(self.profile_path,self.args.profile_state_sha)

    def require_time(self,seconds):
        remaining=self.deadline-time.time()
        if remaining<seconds:
            self.state.update(complete=False,status='pending',required_seconds=seconds,remaining_seconds=remaining,
                pending_reason='Insufficient remaining same-allocation group/stage budget; no numerical verdict')
            self.save();raise PendingTime(self.state['pending_reason'])

    def proposal(self,name,change,mechanism):
        if (self.campaign/'attempts'/name).exists():return
        history=self.ledger.show_history(self.campaign)
        self.ledger.propose(self.campaign,name,dict(history_read_token=history['history_read_token'],
            bottleneck='Closed103 message reduction without accepted ordinary gain; actual711 off-path control/stack mechanism',
            hypothesis=name+': constant halo-mode specialization preserves GCR work and removes measured static off-path mechanism',
            change=change,mechanism=mechanism,
            history_links=[str(self.profile_path),str(self.args.tests_state),str(self.campaign/'old052-import-proof.json'),
                str(self.root/'103-halo-recovered-state.json'),'docs/coarse-batch-halo-v2.md'],
            retry_conditions='New760 fixed-mode body and completed external ARM tests; explicit new ordinary epoch. No failed stage automatic retry.'))

    def prepare(self,name,change,mechanism,parent=None):
        return self.phase.Phase6.prepare(self,name,change,mechanism,parent)

    def stage(self,name,key,command,timeout,environment=None):
        self.unchanged();path=self.campaign/'attempts'/name
        prior=self.strict.read(path/'attempt.json').get('stages',{}).get(key)
        require(not prior or prior['status']=='passed','Retain failed/running stage; new explicit attempt/group required')
        if prior:timeout=prior['timeout_seconds']
        else:self.require_time(timeout+45)
        result=self.ledger.run_stage(self.campaign,name,key,dict(argv=list(map(str,command)),
            cwd=str(path/'build'),env=environment or {},timeout_seconds=timeout))
        if result['status']=='timeout':
            self.state.update(complete=False,status='pending',timed_out_attempt=name,timed_out_stage=key,
                pending_reason='Bounded stage timeout retained; no numerical verdict. A new explicit group/attempt is required.')
            self.save();raise PendingTime(self.state['pending_reason'])
        require(result['status']=='passed' and result['cleanup']['complete'],'Stage failed; retain all evidence: '+name+'/'+key)
        print('HALO_V2_ORDINARY_STAGE '+json.dumps(dict(attempt=name,stage=key,status='passed',reused=bool(prior))),flush=True)

    def completed_scopes(self):
        mapping={('a',self.first,'benchmark'):'a-benchmark',('a',self.first,'verify-full12'):'a-verify',
            ('candidate',self.owner,'benchmark'):'candidate-benchmark',
            ('candidate',self.owner,'verify-new-off'):'candidate-verify-off',
            ('candidate',self.owner,'verify-halo-on'):'candidate-verify-on',
            ('diagnostic',self.diag,'diagnostic'):'diagnostic-benchmark',
            ('diagnostic',self.diag,'verify-halo-on'):'diagnostic-verify',
            ('b',self.last,'benchmark'):'b-benchmark',('b',self.last,'verify-full12'):'b-verify'}
        completed=[]
        for (_,name,key),scope in mapping.items():
            path=self.campaign/'attempts'/name;record=path/'attempt.json'
            if not record.exists():continue
            row=self.strict.read(record).get('stages',{}).get(key,{})
            if row.get('status')=='passed' and row.get('returncode')==0 and row.get('cleanup',{}).get('complete'):
                self.strict.sha(path/safe_relative(row['log']),row['log_sha256']);completed.append(scope)
        return completed

    def benchmark(self,name,snapshot,library,plan,diagnostic=False):
        path=self.campaign/'attempts'/name;target=path/'plan.json'
        if target.exists():require(self.strict.read(target)==plan,'Immutable plan changed')
        else:self.ledger.atomic(target,plan)
        source=Path(snapshot['source'])
        arguments=['--fixture',self.args.fixture,'--plan',target,'--library',library,'--backend','arm',
            '--output',path/'measurements','--allocation',self.allocation,'--snapshot-sha',snapshot['source_manifest_sha256'],
            '--reference-propagator',self.args.fixture/'propagator.npy','--repeats',str(3 if diagnostic else 7)]
        if diagnostic:arguments.append('--diagnostic')
        key='diagnostic' if diagnostic else 'benchmark'
        argv=[sys.executable,source/'tools/run_numa.py','--threads',str(plan['placement_threads']),'--',
            *self.protocol.benchmark_command(self.args.auxiliary,source/'tools/optimization/bench_full12.py',
                path/'checksum-audit'/key,sys.executable,arguments)]
        environment={k:str(v) for k,v in plan['context_environment'].items()}
        environment.update(LD_PRELOAD='',PERF_COUNTER_ROOT='',LD_DEBUG='',LD_DEBUG_OUTPUT='')
        self.stage(name,key,argv,800 if diagnostic else (1000 if len(plan['cases'])==2 else 850),environment)
        reports={}
        for case in plan['cases']:
            run=path/'measurements'/case['id'];key='verify-'+case['id']
            self.stage(name,key,self.protocol.benchmark_command(self.args.auxiliary,source/'tools/optimization/bench_full12.py',
                path/'checksum-audit'/key,sys.executable,['--verify',run,'--verification-output','independent-derived',
                    '--reference',self.args.reference,'--extractor',self.args.reference.with_name('extract_columns')]),450,
                dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close'))
            report=self.strict.read(run/'result.json')
            require(report['configuration']==self.phase.configuration_for(self.base,plan,case),'Effective recorded plan differs')
            require(report['library_sha256']==self.strict.sha(library),'Measured library differs')
            verification=report.get('verification',{})
            require(verification.get('complete') and verification.get('passed') and verification.get('columns')==12 and
                verification.get('checksum_audit',{}).get('helper_wrapper_sha256')==DERIVED_SHA,
                'Every fresh case needs complete12 independent derived-helper verification')
            steady=[row for row in report['samples'] if not row['warmup']]
            require(len(steady)==(3 if diagnostic else 7) and [row['repeat'] for row in steady]==list(range(1,len(steady)+1)),
                'Expected complete ordinary7/diagnostic3 steady samples and IDs required')
            report_key=name+'/'+case['id'];current=self.strict.sha(run/'result.json')
            recorded=self.state.setdefault('case_report_sha256',{}).get(report_key)
            require(recorded is None or recorded==current,'Previously completed case report changed')
            self.state['case_report_sha256'][report_key]=current;self.save()
            reports[case['id']]=run/'result.json'
        return reports

    def control(self,name):return self.phase.Phase6.control(self,name)

    def diagnostic(self,library):
        if self.state.get('actual_halo_diagnostic'):
            saved=self.state['actual_halo_diagnostic']
            self.strict.sha(saved['report'],saved['report_sha256'])
            self.strict.sha(self.campaign/'attempts'/self.diag/'diagnostic-000.log',saved['diagnostic_log_sha256'])
            return
        snapshot=self.prepare(self.diag,'Separate complete12 halo execution diagnostic',
            'Actual message/byte/independent-GCR counts; instrumentation times never rank',self.case_names['halo-on'])
        report_path=self.benchmark(self.diag,snapshot,library,self.phase.plan_for(self.base,[self.cases[-1]]),True)['halo-on']
        report=self.strict.read(report_path);proof=report['verification']
        log=self.strict.text(self.campaign/'attempts'/self.diag/'diagnostic-000.log')
        rows=[json.loads(v) for v in re.findall(r'native coarse batch halo (\{[^\n]+\})',log)]
        actual=dict(records=len(rows),calls=sum(r['calls'] for r in rows),send_bytes=sum(r['send_bytes'] for r in rows),
            rhs_slots=sum(r['rhs_slots'] for r in rows),max_width=max((r['max_width'] for r in rows),default=0))
        require(actual['calls']>0 and actual['send_bytes']>0 and actual['max_width']>1,'Actual grouped messages required')
        reductions=[json.loads(v) for v in re.findall(r'native coarse batch reduce (\{[^\n]+\})',log)]
        reference_rows=self.profile['budget']['final_verbose_reductions']
        coverage=self.phase.coarse_coverage(reductions);reference=self.phase.coarse_coverage(reference_rows)
        require(coverage['records']>0 and coverage['packed_allreduce_calls']>0,'Actual packed reduction execution required')
        require(not reference['restarts'] or coverage['restarts']>0,'Profile exercised restart; candidate must too')
        require(not reference['different_refresh_counts'] or coverage['different_refresh_counts'],
            'Profile exercised differing refresh counts; candidate must too')
        keys=('nrhs','coarse_it_limit','coarse_tolerance','iterations','restarts','refreshes','capped','reduction_rounds','allreduce_calls')
        old=[{k:r[k] for k in keys} for r in reference_rows]
        new=[{k:r[k] for k in keys} for r in reductions]
        self.state['actual_halo_diagnostic']=dict(actual=actual,coarse_state_coverage=coverage,
            parent_profile_coarse_state_coverage=reference,verification=proof,report=str(report_path),
            independent_gcr_records_equal=old==new,report_sha256=self.strict.sha(report_path),
            diagnostic_log_sha256=self.strict.sha(self.campaign/'attempts'/self.diag/'diagnostic-000.log'),
            note='RHS-equivalent counts are distinct from physical message calls; rank-max timing envelopes are nonadditive and unranked')
        self.ledger.conclude(self.campaign,self.diag,'inconclusive','Verified diagnostic; no ordinary ranking',[str(report_path)])
        self.save()

    def mark(self,*keys):
        self.state['completed_budget_scopes']=sorted(set(self.state['completed_budget_scopes'])|set(keys));self.save()

    def run(self):
        if self.state.get('complete'):self.unchanged();return
        self.state['completed_budget_scopes']=self.completed_scopes();self.save()
        self.require_time(remaining_floor(self.state['completed_budget_scopes'])+45)
        # The reused ELF needs no build recipe. Ordinary child contexts come
        # only from the fixed old052 plan; previous task numerical flags must
        # not affect a new Solver before metadata can expose the difference.
        for key in list(os.environ):
            if key.startswith(('LQCD_','NATIVE_')) and not key.startswith('LQCD_OPT_'):
                os.environ.pop(key,None)
        self.state['status']='running';self.save()
        self.control(self.first);self.mark('a-benchmark','a-verify')
        snapshot=self.prepare(self.owner,'New760 fixed-mode version, same-hierarchy off/on',
            'Entry dispatch to constant halo-mode bodies; reuse exact externally tested native ELF without rebuilding')
        require(snapshot['source_manifest_sha256']==self.tests['source_manifest_sha256'],'Ordinary and tested source snapshots differ')
        library=Path(self.tests['library'])
        self.state['reused_external_library']=dict(path=str(library),sha256=self.args.library_sha,recompiled=False);self.save()
        reports=self.benchmark(self.owner,snapshot,library,self.phase.plan_for(self.base,self.cases))
        self.ledger.ingest(self.campaign,self.owner,reports['new-off'])
        name=self.case_names['halo-on'];self.prepare(name,'Same-hierarchy760 halo-on',
            'Change only dynamic halo flag; retained independent GCR states and zero guesses',self.owner)
        self.ledger.ingest(self.campaign,name,reports['halo-on'])
        self.mark('candidate-benchmark','candidate-verify-off','candidate-verify-on')
        self.diagnostic(library);self.mark('diagnostic-benchmark','diagnostic-verify')
        self.control(self.last);self.mark('b-benchmark','b-verify')
        ordinary=[self.strict.read(self.campaign/'attempts'/name/'report.json') for name in
            [self.first,self.owner,self.case_names['halo-on'],self.last]]
        require(all(row['resources']==ordinary[0]['resources'] for row in ordinary),'Ordinary CPU/NUMA resource masks differ')
        # Reuse frozen3f gates and private-campaign promotion exactly. Never
        # promote main/campaign or interpret the old imported timing as fresh.
        self.phase.Phase6.decide(self)
        self.state.update(main_best_modified=False,main_best_sha256=self.main_best_sha,
            decision_scope='Independent V2 ordinary campaign only; main best unchanged',
            next_candidate={'condition':'Reassess closed profile and mechanism evidence; no bundled workspace optimization'})
        self.unchanged();self.save()
        print('HALO_V2_ORDINARY_COMPLETE '+json.dumps(dict(state=str(self.state_path),best=self.state['best'],winner=self.state['winner'])),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--root',type=Path,default=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103'))
    p.add_argument('--auxiliary',type=Path)
    p.add_argument('--campaign',type=Path)
    p.add_argument('--prefix',default='halo-v2-w7')
    for name in ('profile-state','profile-status','tests-state','tests-status'):p.add_argument('--'+name,type=Path)
    for name in ('profile-state-sha','profile-status-sha','tests-state-sha','tests-status-sha','library-sha',
                 'expected-entry-sha','expected-manifest-sha','expected-host'):p.add_argument('--'+name)
    p.add_argument('--fixture',type=Path,default=Path('/home/share/nsls_lwb/.cache/mg-20261102/propagator'))
    p.add_argument('--reference',type=Path,default=Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'))
    p.add_argument('--resume',action='store_true');p.add_argument('--resume-reason')
    a=p.parse_args()
    if not a.execute:
        print(json.dumps(dict(prepared_only=True,execute=False,new_build=False,new_test_execution=False,
            order=['old052-A','760 same-hierarchy off/on','unranked halo diagnostic','old052-B'],
            ordinary_steady_repeats=7,diagnostic_steady_repeats=3,zero_guesses=True,
            independent12_each_case=True,entry_group_planning_floor_seconds=sum(GROUP_FLOORS.values()),
            original_bracket_and_halo_gates_unchanged=True,main_campaign_untouched=True,
            requirements=['Closed full-scope actual760 ARM CTest/SVE proof,118 codegen alone insufficient',
                'New same-allocation retained052 profile with derived25 helper','Pinned inputs and sufficient whole-group safe time'],
            launch='Direct Python entry only; per-stage factorya07 already supplies the raw wrapper exactly once'),indent=2));return
    require(all(getattr(a,n) for n in ['profile_state','profile_status','tests_state','tests_status','profile_state_sha',
        'profile_status_sha','tests_state_sha','tests_status_sha','library_sha','expected_entry_sha','expected_manifest_sha','expected_host']),
        'All actual external-test, fresh-profile, controller and manifest pins are required')
    require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,50}',a.prefix),'Safe new prefix required')
    require(a.resume==bool(a.resume_reason),'Resume requires an explicit reason')
    a.root=a.root.resolve();a.auxiliary=(a.auxiliary or Path(__file__).parent).resolve()
    a.campaign=(a.campaign or a.root/'campaign-halo-v2-ordinary').resolve()
    require(a.campaign.parent==a.root and a.campaign.name.startswith('campaign-halo-v2-ordinary'),
        'Separate ordinary campaign must be a new named sibling of the protected campaigns')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(a.auxiliary))
    spec=importlib.util.spec_from_file_location('_v2_trial_integrity',a.auxiliary/'file_integrity.py')
    integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity);integrity.known_vectors()
    strict=StrictFiles(integrity);strict.sha(__file__,a.expected_entry_sha)
    manifest_path=a.auxiliary/'halo-v2-trial-helpers.json';a.helper_manifest=strict.read(manifest_path,a.expected_manifest_sha)
    for name,expected in a.helper_manifest['files'].items():strict.sha(a.auxiliary/safe_relative(name),expected)
    phase=load_source('_frozen_halo3f',a.auxiliary/'phase6_halo.py',PHASE_SHA,strict)
    strict.sha(a.auxiliary/'raw_protocol_derived.py',FACTORY_SHA)
    protocol=load_source('_v2_derived_factory',a.auxiliary/'raw_protocol_derived.py',FACTORY_SHA,strict)
    protocol.verify_derived(a.auxiliary)
    sys.path.insert(0,str(a.root/'source-halo-v2-760/tools/optimization'))
    import campaign as ledger
    require(ledger.run_stage.__module__=='campaign' and ledger.run_stage.__name__=='run_stage',
        'Launch directly: an outer raw_controller would double-wrap the already adapted benchmark stages')
    ledger.digest=strict.sha;ledger.read=strict.read
    controller=Trial(a,strict,ledger,phase,protocol)
    ledger.process_tree.enable_subreaper()
    def interrupted(signum,frame):raise KeyboardInterrupt('V2 ordinary signal'+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:controller.run()
    except PendingTime:print('HALO_V2_ORDINARY_PENDING '+json.dumps(controller.state),flush=True)
    except BaseException as error:
        controller.state.update(complete=False,status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=repr(error))
        controller.save();raise


if __name__=='__main__':main()
