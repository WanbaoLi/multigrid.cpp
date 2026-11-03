"""Targeted work-balance and batching experiments, using retained correct code."""
import json
import subprocess
import sys
from pathlib import Path

root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0,str(root/'reporter'))
import campaign as ledger
campaign=root/'campaign'
state_file=root/'phase3-state.json'
state=ledger.read(state_file) if state_file.exists() else {}
controller_sha=ledger.digest(Path(__file__))
if state.get('controller_sha256',controller_sha)!=controller_sha:
    raise RuntimeError('Phase3 controller changed after checkpoint')
state['controller_sha256']=controller_sha
fixture='/home/share/nsls_lwb/.cache/mg-20261102/propagator'
reference='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
extractor='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'

def best():
    name=ledger.read(campaign/'best.json')['attempt']
    return name,ledger.read(campaign/'attempts'/name/'report.json')

def group(key,variants,reason):
    if state.get(key,{}).get('complete'):return state[key]
    if key not in state:
        name,report=best()
        state[key]=dict(parent=name,configuration=report['configuration'])
        ledger.atomic(state_file,state)
    item=state[key]
    configuration=item['configuration']
    cases=[]
    for name,delta,batch,mechanism in variants:
        environment=dict(configuration['solve_environment'],**delta)
        cases.append(dict(id=name,threads=configuration['threads'],
                          batch=batch or configuration['batch'],environment=environment))
        description=dict(bottleneck=reason,hypothesis=name+': '+mechanism,
            change=dict(solve_delta=delta,batch=batch),mechanism=mechanism,
            history_links=[str(campaign/'attempts'/item['parent']/'report.json'),
                str(root/'reports'),str(root/'profile-hbw'),str(root/'probes/team.json')],
            retry_conditions='One frozen hierarchy/currentbestlibrary; full12 precision unchanged; read ledger history before proposal')
        ledger.atomic(root/'proposals'/(name+'.json'),description)
    plan=dict(context_environment=configuration['context_environment'],cases=cases,
        placement_threads=configuration.get('placement_threads',configuration['threads']),
        setup_threads=configuration.get('setup_threads',configuration['threads']))
    path=root/'plans'/(key+'.json')
    if path.exists() and ledger.read(path)!=plan:raise RuntimeError('Resumed group plan changed')
    ledger.atomic(path,plan)
    argv=[sys.executable,str(root/'reporter/interleaved.py'),'--campaign',str(campaign),
        '--reuse-attempt',item['parent'],'--plan',str(path),'--proposals',str(root/'proposals'),
        '--fixture',fixture,'--reference',reference,'--extractor',extractor,
        '--reference-propagator',fixture+'/propagator.npy','--backend','arm',
        '--allocation','mg-opt-20261103-worker1','--repeats','3']
    print('PHASE3_GROUP '+json.dumps(dict(key=key,parent=item['parent'],variants=variants)),flush=True)
    subprocess.run(argv,check=True)
    item.update(complete=True,attempts=[v[0] for v in variants],best_after=best()[0])
    ledger.atomic(state_file,state)
    return item

work=group('work-balance',[
    ('030-work-control',{},None,'Reproduce retained current best before changing preconditioner work'),
    ('031-sap5',{'LQCD_MG_SAP_STEPS':5},None,
     'SAP dominates and 24-25 Vcycles are used per column: 25% more local steps may reduce costly full Vcycles; compare actual iteration counts and total time'),
    ('032-coarse005',{'LQCD_MG_COARSE_TOL':.05},None,
     'Stronger coarse approximation may reduce SAP/outer work enough to pay additional coarse iterations; known9755 profile supplies a bounded prior'),
    ('033-coarse02',{'LQCD_MG_COARSE_TOL':.2},None,
     'Weaker coarse approximation may cut synchronization; profile contains many small Allreduces; any extra outer work and final precision remain measured'),
    ('034-correction003',{'LQCD_CORRECTION_BASE_TOL':.003},None,
     'Earlier single-precision correction stop may avoid oversolving between double-precision reliable updates; final all12 double residual unchanged')],
    'HBW profile SAP/local and fine kernels dominate; normal full12 stats use24-25 outer Vcycles; coarse solve has many small reductions')

# Retry the same work-balance direction with evidence: combine only independently
# beneficial mechanisms; if extra SAP work did not pay, test less work once.
if 'work-refinement' not in state:
    reports={n:ledger.read(campaign/'attempts'/n/'report.json') for n in work['attempts']}
    summaries={n:ledger.validate_report(r,ledger.campaign(campaign)[1],r['source_manifest_sha256']) for n,r in reports.items()}
    control=summaries['030-work-control']['median_seconds']
    beneficial=[]
    for name in work['attempts'][1:]:
        if summaries[name]['median_seconds']<.99*control and summaries[name]['relative_spread']<=.1:
            beneficial.append(name)
    name,current=best()
    deltas={}
    for candidate in sorted(beneficial,key=lambda n:summaries[n]['median_seconds'],reverse=True):
        for key,value in reports[candidate]['configuration']['solve_environment'].items():
            if work['configuration']['solve_environment'].get(key)!=value:
                deltas[key]=value
    fresh={k:v for k,v in deltas.items() if current['configuration']['solve_environment'].get(k)!=v}
    variants=[('035-refine-control',{},None,'Retain current best while refining work balance')]
    if fresh:
        variants.append(('036-work-combined',fresh,None,
            'Combine only independently >=1% faster stable work-balance changes; verify interactions and actual iterations rather than adding speedups'))
    if summaries['031-sap5']['median_seconds']>=control:
        variants.append(('037-sap3',{'LQCD_MG_SAP_STEPS':3},None,
            'Extra SAP work failed to pay in031; test opposite work allocation: cheaper local solves against measured extra outer Vcycles'))
    state['work-refinement']=dict(variants=variants)
    ledger.atomic(state_file,state)
refinement=state['work-refinement']['variants']
if len(refinement)>1:
    group('work-refinement-run',refinement,'Actual030-034 full12 timings/iteration counts justify this next balance experiment')

group('batch-reuse',[
    ('040-batch-control',{},None,'Reproduce current retained best before increasing active source columns'),
    ('041-batch4',{},4,'Reuse fine coefficient/halo data across4 columns; test cache/workspace costs on HBW and new scheduling'),
    ('042-batch12',{},12,'One full-source batch reduces repeated halo launches; coarse RHS remain independent, so do not assume its reductions disappear')],
    'Current fine MPI halo remains significant; changedverifiedHBW+schedule conditions justify prior296corebatch retry; coarse solver is still perRHS')
state.update(complete=True,best=best()[0])
ledger.atomic(state_file,state)
print('PHASE3_FINISHED '+json.dumps(state),flush=True)
