"""Bounded evidence-driven next phase; no candidate is adopted without gates."""
import json, os, subprocess, sys
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
source=root/'source'; ledger_root=root/'campaign'
sys.path.insert(0,str(source/'tools/optimization'))
import campaign as ledger
state_path=root/'phase2-state.json'
state=ledger.read(state_path) if state_path.exists() else {}
controller_sha=ledger.digest(Path(__file__))
if state.get('controller_sha256',controller_sha)!=controller_sha:
    raise RuntimeError('Controllerchanged sincecheckpoint; review andstartanewphase')
state['controller_sha256']=controller_sha
if state.get('complete'):
    print('PHASE2_ALREADY_FINISHED '+json.dumps(state),flush=True)
    raise SystemExit(0)
python=sys.executable
fixture='/home/share/nsls_lwb/.cache/mg-20261102/propagator'
reference='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
extractor='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
reference_prop=fixture+'/propagator.npy'
allocation='mg-opt-20261103-worker1'

def current_best():
    best=ledger.read(ledger_root/'best.json')
    return best['attempt'],ledger.read(ledger_root/'attempts'/best['attempt']/'report.json')

def make_plan(configuration):
    result=dict(context_environment=configuration['context_environment'],cases=[dict(id='full12',
        threads=configuration['threads'],batch=configuration['batch'],environment=configuration['solve_environment'])])
    for key in ['placement_threads','setup_threads']:
        if key in configuration:result[key]=configuration[key]
    return result

def proposal(name,change,mechanism,history=None):
    value=dict(bottleneck='Freshfull12 profile per2cols:R.219/coarse.94/P.20/SAP2.12; measuredfactorial/probe history',
        hypothesis=mechanism,change=change,mechanism=mechanism,
        history_links=['docs/optimization-candidates.md','docs/optimization-framework.md',
            str(ledger_root/'attempts/010a-profile/benchmark-000.log'),str(root/'probes/hbw.log')]+(history or []),
        retry_conditions='Read currentledger beforeproposal; unchanged physics, zero starts, independent12columnprecision; experimentaldefaultsoff')
    ledger.atomic(root/'proposals'/f'{name}.json',value)

def run_trial(name,plan,change,mechanism,source_from=None,reuse=None,against=None):
    path=root/'plans'/f'{name}.json'
    if path.exists() and ledger.read(path)!=plan:raise RuntimeError('Resumedplan differs: '+name)
    existing=ledger_root/'attempts'/name/'attempt.json'
    if existing.exists() and 'report' in ledger.read(existing):
        data,_,_=ledger.checked_attempt(ledger_root,name,ledger.campaign(ledger_root)[1])
        if against and data['status']=='measured':
            try:ledger.promote(ledger_root,name,against=against)
            except ledger.EvidenceError as exc:
                ledger.conclude(ledger_root,name,'inconclusive',str(exc),[str(existing)])
        print('RESUME_VERIFIED '+name,flush=True)
        return
    proposal(name,change,mechanism)
    ledger.atomic(path,plan)
    argv=[python,str(source/'tools/optimization/trial.py'),'--campaign',str(ledger_root),
        '--id',name,'--proposal',str(root/'proposals'/f'{name}.json'),'--plan',str(path),
        '--fixture',fixture,'--reference',reference,'--extractor',extractor,'--reference-propagator',reference_prop,
        '--backend','arm','--allocation',allocation,
        '--test-regex','^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning)$']
    if source_from:argv+=['--source-from',source_from]
    if reuse:argv+=['--reuse-attempt',reuse]
    if against:argv+=['--against',against]
    print('EXECUTE '+json.dumps(argv),flush=True)
    subprocess.run(argv,check=True)

# All older queued experiments must have finished before the working checkout
# advances; their immutable copies and the retained best artifact stay intact.
subprocess.run(['git','-C',str(source),'fetch',str(root/'candidates.bundle'),
                'codex/lingsheng-optimization-framework-20261103'],check=True)
subprocess.run(['git','-C',str(source),'merge','--ff-only','FETCH_HEAD'],check=True)
import importlib
ledger=importlib.reload(ledger)
head=ledger.git(source,'rev-parse','HEAD')
if state.get('source_head',head)!=head:raise RuntimeError('Controller source revision changed; use a newphase')
state['source_head']=head
if not state.get('linux_lifecycle_preflight'):
    subprocess.run([python,'-m','unittest','discover','-s',str(source/'tests'),
                    '-p','test_optimization*.py','-v'],check=True)
    state['linux_lifecycle_preflight']=True
if 'initial_best' not in state:
    initial_id,initial_report=current_best()
    state.update(initial_best=initial_id,initial_configuration=initial_report['configuration'])
ledger.atomic(state_path,state)

best_id=state['initial_best']
run_trial('019-frozen-control',make_plan(state['initial_configuration']),
    'Remeasure actual retained best on this allocation before numerical candidate',
    'Preserve oldsource/archive/binary/config withoutcheckoutrollback; expose drift',source_from=best_id,reuse=best_id)

plan=make_plan(state['initial_configuration'])
plan['context_environment']=dict(plan['context_environment'],LQCD_ARM_SVE_REUSE=1)
run_trial('020-sve-reuse',plan,
    'Reuse neighbor halfspin projection across outputcolors in explicitSVEregisters',
    'SAPdominates; source-level neighborloads36to12 per tile/direction/halfspin whilepreserving j order andmaskcontracts',
    against='019-frozen-control')

if 'overlap_configuration' not in state:
    best_id,best_report=current_best()
    state.update(overlap_configuration=best_report['configuration'],
                 overlap_control=best_id if best_id=='020-sve-reuse' else '019-frozen-control')
    ledger.atomic(state_path,state)
control=state['overlap_control']
plan=make_plan(state['overlap_configuration'])
plan['context_environment']=dict(plan['context_environment'],LQCD_COARSE_SPATIAL_OVERLAP=1)
run_trial('021-coarse-overlap',plan,
    'Compute coarse diagonal/spatial contributions whilemainthread waitsfor temporalhalo',
    'Currentcoarse has nointeriorplanes buthas independent0..6 terms; preserve directionorder andappend7/8 afterbarrier',
    reuse='020-sve-reuse',against=control)

# Work-grain model:32 same-color blocks perrank. Teamprobe found21worker
# recreations when37->16->37. Compare amortizedcoarsecap16 withfixedwhole
# teams32/16, whichavoid repeatedinnerphase transitions andreservehelperCPUs.
# The four cases share one hierarchy and alternateorder on successive rounds.
if 'cap_configuration' not in state:
    best_id,best_report=current_best()
    state.update(cap_configuration=best_report['configuration'],cap_seed_best=best_id)
    ledger.atomic(state_path,state)
best_id=state['cap_seed_best']
configuration=state['cap_configuration']
context=dict(configuration['context_environment'])
cases=[]
names=['022-schedule-control','023-coarse16','024-whole32','025-whole16']
caps=[0,16,0,0]
fine_counts=[configuration['threads'],configuration['threads'],32,16]
for name,cap,fine_threads in zip(names,caps,fine_counts):
    solve=dict(configuration['solve_environment'])
    if cap:solve['LQCD_COARSE_THREADS']=cap
    case=dict(id=name,threads=fine_threads,batch=configuration['batch'],environment=solve)
    cases.append(case)
    proposal(name,'Coarsecap '+str(cap)+'; fixedfineteam '+str(fine_threads),
        'Probeidentifiedworkerturnover; compareamortizedcoarsecapwithstablewholeteams and32activeblockgranularity',
        history=[str(ledger_root/'attempts'/best_id/'report.json')])
    if not (ledger_root/'attempts'/name).exists():
        history=ledger.show_history(ledger_root)
        description=ledger.read(root/'proposals'/f'{name}.json')
        description['history_read_token']=history['history_read_token']
        ledger.propose(ledger_root,name,description)
    snapshot=ledger.snapshot(ledger_root,name)
snapshots=[ledger.read(ledger_root/'attempts'/n/'attempt.json')['snapshot']['source_manifest_sha256'] for n in names]
if len(set(snapshots))!=1:raise RuntimeError('Coarsecap comparison sourcechanged whilepreparing')
parent=ledger.read(ledger_root/'attempts/020-sve-reuse/attempt.json')
ledger.check_snapshot(ledger_root/'attempts/020-sve-reuse',parent)
if parent['snapshot']['source_manifest_sha256']!=snapshots[0]:raise RuntimeError('Candidatebuild source mismatch')
library=ledger_root/'attempts/020-sve-reuse/artifacts/liblqcd_cpu.so'
ledger.check_artifact(ledger_root/'attempts/020-sve-reuse',parent)
attempt=ledger_root/'attempts'/names[0]
plan_path=attempt/'interleaved-plan.json'
ledger.atomic(plan_path,dict(context_environment=context,cases=cases,
                            placement_threads=configuration.get('placement_threads',configuration['threads']),
                            setup_threads=configuration.get('setup_threads',configuration['threads'])))
frozen=attempt/'source'
argv=[python,str(frozen/'tools/run_numa.py'),'--threads',str(configuration.get('placement_threads',configuration['threads'])),'--',
    python,'-u',str(frozen/'tools/optimization/bench_full12.py'),'--fixture',fixture,
    '--plan',str(plan_path),'--library',str(library),'--backend','arm',
    '--output',str(attempt/'measurements'),'--allocation',allocation,
    '--snapshot-sha',snapshots[0],'--reference-propagator',reference_prop]
result=ledger.run_stage(ledger_root,names[0],'interleaved-benchmark',dict(argv=argv,
    cwd=str(attempt/'build'),timeout_seconds=1800))
if result['status']!='passed':raise RuntimeError('Interleavedcap benchmarkfailed; retainpartialevidence')
for name in names:
    run=attempt/'measurements'/name
    result=ledger.run_stage(ledger_root,name,'independent',dict(argv=[python,
        str(frozen/'tools/optimization/bench_full12.py'),'--verify',str(run),
        '--reference',reference,'--extractor',extractor],cwd=str(ledger_root/'attempts'/name/'build'),
        timeout_seconds=1200,env=dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close')))
    if result['status']!='passed':raise RuntimeError('Cap independentverificationfailed')
    ledger.ingest(ledger_root,name,run/'result.json')

best_id,best_report=current_best()
same_library=best_report['library_sha256']==ledger.digest(library)
if not same_library:
    # The current best is still the older binary; bracket the long source/build
    # interval with a fresh frozen control instead of ranking against stale019.
    run_trial('026-cap-frozen-bracket',make_plan(best_report['configuration']),
        'Bracket interleavedcoarsecap phase withretainedcurrentbestbinary',
        'Rejectclock/resource drift across longerbuild+testphase',source_from=best_id,reuse=best_id)
control=names[0] if same_library else '026-cap-frozen-bracket'
ranked=sorted(names,key=lambda n:ledger.read(ledger_root/'attempts'/n/'attempt.json')['report']['median_seconds'])
winner=ranked[0]
try:
    decision=ledger.promote(ledger_root,winner,against=control)
    print('CAP_PROMOTED '+json.dumps(decision),flush=True)
except ledger.EvidenceError as exc:
    print('CAP_NOT_PROMOTED '+str(exc),flush=True)
for name in names:
    if name!=current_best()[0] and ledger.read(ledger_root/'attempts'/name/'attempt.json')['status']!='inconclusive':
        ledger.conclude(ledger_root,name,'inconclusive',
            'Full12correctcap comparison retained; inspectprofile/granularity before retry; noautomaticclaimfromlocalwork',
            [str(attempt/'measurements'/name/'result.json')])
state.update(complete=True,best=current_best()[0])
ledger.atomic(state_path,state)
print('PHASE2_FINISHED '+json.dumps(current_best()[0]),flush=True)
