"""Validate and compare packed independent-RHS coarse reductions."""
import importlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
source=root/'source'; campaign=root/'campaign'
sys.path.insert(0,str(source/'tools/optimization'))
import campaign as ledger
ledger.require(ledger.read(root/'phase3-state.json').get('complete'),'Phase3 not complete')
state_file=root/'phase4-state.json'
state=ledger.read(state_file) if state_file.exists() else {}
controller_sha=ledger.digest(Path(__file__))
ledger.require(state.get('controller_sha256',controller_sha)==controller_sha,'Controller changed since checkpoint')
state['controller_sha256']=controller_sha
if state.get('complete'):
    print('PHASE4_ALREADY_FINISHED',flush=True);raise SystemExit(0)
allocation=os.environ.get('LQCD_OPT_ALLOCATION','mg-opt-20261103-worker1')
deadline=float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH',
    datetime.fromisoformat('2026-11-04T01:48:00+08:00').timestamp()))
ledger.require(deadline-time.time()>=2500,
    'Insufficient bounded allocation time for build/tests/full12verification; continue in the next allocation before registering new evidence')
ledger.require(state.get('allocation',allocation)==allocation,
    'Incomplete phase belongs to another allocation; inspect checkpoints and create a fresh matched-control phase')
state['allocation']=allocation
subprocess.run(['git','-C',str(source),'fetch',str(root/'phase4.bundle'),
                'codex/lingsheng-optimization-framework-20261103'],check=True)
subprocess.run(['git','-C',str(source),'merge','--ff-only','FETCH_HEAD'],check=True)
ledger=importlib.reload(ledger)
head=ledger.git(source,'rev-parse','HEAD')
ledger.require(state.get('source_head',head)==head,'Phase4 source revision changed')
state['source_head']=head
if not state.get('linux_framework_preflight'):
    subprocess.run([sys.executable,'-m','unittest','discover','-s',str(source/'tests'),
                    '-p','test_optimization*.py','-q'],check=True)
    state['linux_framework_preflight']=True

def best():
    name=ledger.read(campaign/'best.json')['attempt']
    return name,ledger.read(campaign/'attempts'/name/'report.json')

if 'initial_best' not in state:
    name,report=best()
    state.update(initial_best=name,initial_configuration=report['configuration'])
ledger.atomic(state_file,state)

def plan(configuration):
    return dict(context_environment=configuration['context_environment'],
        placement_threads=configuration.get('placement_threads',configuration['threads']),
        setup_threads=configuration.get('setup_threads',configuration['threads']),
        cases=[dict(id='full12',threads=configuration['threads'],batch=configuration['batch'],
                    environment=configuration['solve_environment'])])

def trial(name,configuration,change,mechanism,source_from=None,reuse=None,against=None):
    attempt=campaign/'attempts'/name
    if (attempt/'report.json').exists():
        ledger.checked_attempt(campaign,name,ledger.campaign(campaign)[1])
        print('RESUME_VERIFIED '+name,flush=True);return
    proposal=dict(bottleneck='018diagnostic40652smallAllreduces/full12; currentbesthasfasterSAP/HBW; independentcoarseRHSstillserial',
        hypothesis=name+': '+mechanism,change=change,mechanism=mechanism,
        history_links=['docs/coarse-batch-reduce.md',str(root/'profile-hbw'),
                       str(root/'phase3-state.json'),str(campaign/'attempts'/state['initial_best']/'report.json')],
        retry_conditions='New source candidate merges independent RHS reductions only; scalar math unchanged; test flag1 and fallback; never weaken full12reference precision')
    proposal_path=root/'proposals'/(name+'.json')
    plan_path=root/'plans'/(name+'.json')
    ledger.atomic(proposal_path,proposal)
    value=plan(configuration)
    if plan_path.exists():ledger.require(ledger.read(plan_path)==value,'Resumed plan changed')
    ledger.atomic(plan_path,value)
    argv=[sys.executable,str(source/'tools/optimization/trial.py'),'--campaign',str(campaign),
        '--id',name,'--proposal',str(proposal_path),'--plan',str(plan_path),
        '--fixture','/home/share/nsls_lwb/.cache/mg-20261102/propagator',
        '--reference','/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid',
        '--extractor','/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns',
        '--reference-propagator','/home/share/nsls_lwb/.cache/mg-20261102/propagator/propagator.npy',
        '--backend','arm','--allocation',allocation,
        '--test-regex','^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning|coarse_batch_reduce_.*|batch12_coarse_reduce_mpi2|runtime_batch_coarse_reduce)$']
    if source_from:argv+=['--source-from',source_from]
    if reuse:argv+=['--reuse-attempt',reuse]
    if against:argv+=['--against',against]
    print('PHASE4_TRIAL '+json.dumps(dict(name=name,configuration=configuration,mechanism=mechanism)),flush=True)
    subprocess.run(argv,check=True)

trial('050-reduce-frozen-control',state['initial_configuration'],
      'Fresh retained-best source/library control before compiling new algorithm',
      'Expose allocation/time drift; preserve original artifact and zero starts',
      source_from=state['initial_best'],reuse=state['initial_best'])
trial('051-reduce-off',state['initial_configuration'],
      'Build new source with packed reduction defaultoff; run all candidate-enabled tests',
      'Separate new binary/code layout/validation payload effects from enabling merged RHS collectives',
      against='050-reduce-frozen-control')
if 'on_configuration' not in state:
    _,report=best()
    configuration=json.loads(json.dumps(report['configuration']))
    configuration['solve_environment']['LQCD_COARSE_BATCH_REDUCE']=1
    state.update(on_configuration=configuration,
                 on_control='051-reduce-off' if best()[0]=='051-reduce-off' else '050-reduce-frozen-control')
    ledger.atomic(state_file,state)
trial('052-reduce-on',state['on_configuration'],
      'Pack per-RHS MGS beta/norm/fused update/residual norm into sharedAllreduce calls',
      'Remove repeated collective startups while preserving independent histories, convergence, 16restart and40cap; keepmatvec/halo sequential',
      reuse='051-reduce-off',against=state['on_control'])
state.update(complete=True,best=best()[0])
ledger.atomic(state_file,state)
print('PHASE4_FINISHED '+json.dumps(state),flush=True)
