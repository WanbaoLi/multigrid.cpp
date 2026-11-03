"""Resume verified measurements across an allocation change without relabeling timings."""
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
source=root/'source'; campaign=root/'campaign'
sys.path.insert(0,str(source/'tools/optimization'))
import campaign as ledger
allocation=os.environ['LQCD_OPT_ALLOCATION']
preflight=ledger.read(root/'worker2-preflight/result.json')
ledger.require(preflight['complete'] and preflight['host']==platform.node(),'Current node preflight missing')
for task in ['000a-hash-visibility','000b-node-preflight']:
    ledger.require(ledger.read(root/'queue2'/(task+'.status.json'))['status']=='passed','Required diagnostic failed')
probe=[json.loads(line) for line in (root/'queue2/000a-hash-visibility.log').read_text().splitlines()
       if line.startswith('{')]
hashes=[row for row in probe if 'label' in row]
ledger.require(len(hashes)==4 and all(row['python']==row['same_bytes_portable']==row['sha256sum']==row['expected']
    and row['before']==row['after'] and row['read_bytes']==2038431872 for row in hashes),
    'Output integrity diagnostic reproduced an unresolved mismatch; stop before accepting old measurements')

subprocess.run(['git','-C',str(source),'fetch',str(root/'phase4.bundle'),
                'codex/lingsheng-optimization-framework-20261103'],check=True)
subprocess.run(['git','-C',str(source),'merge','--ff-only','FETCH_HEAD'],check=True)
ledger=importlib.reload(ledger)
state_path=root/'phase3-state.json'
state=ledger.read(state_path)
continuation_sha=ledger.digest(Path(__file__))
ledger.require(state.get('continuation_sha256',continuation_sha)==continuation_sha,'Continuation changed since checkpoint')
state['continuation_sha256']=continuation_sha
state['continuation_allocation']=allocation
ledger.atomic(state_path,state)
driver=source/'tools/optimization/bench_full12.py'
reference='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid'
extractor='/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns'
fixture='/home/share/nsls_lwb/.cache/mg-20261102/propagator'

def best():
    name=ledger.read(campaign/'best.json')['attempt']
    return name,ledger.read(campaign/'attempts'/name/'report.json')

names=['030-work-control','031-sap5','032-coarse005','033-coarse02','034-correction003']
if not state['work-balance'].get('complete'):
    for name in names:
        attempt=campaign/'attempts'/name
        if (attempt/'report.json').exists():
            ledger.checked_attempt(campaign,name,ledger.campaign(campaign)[1]);continue
        run=campaign/'attempts/030-work-control/measurements'/name
        report=ledger.read(run/'result.json')
        record=ledger.read(attempt/'attempt.json')
        previous=record['stages'].get('independent')
        output='independent-retry1' if (run/'independent').exists() else 'independent'
        ledger.require(ledger.digest(run/'propagator.npy')==report['propagator_sha256'],
                       'Original saved propagator does not match its unchanged measured digest')
        audit=attempt/'recovery-worker2.json'
        if not audit.exists():
            ledger.atomic(audit,dict(allocation=allocation,host=platform.node(),
                action='Fresh full12 verification; preserve all old validation outputs and measured timing identity',
                previous_attempt_record_sha256=ledger.digest(attempt/'attempt.json'),
                probe_log_sha256=ledger.digest(root/'queue2/000a-hash-visibility.log'),
                original_expected_sha256=report['propagator_sha256'],
                old_validation_path=str(run/'independent'),new_validation_output=output,
                new_driver_path=str(driver),new_driver_sha256=ledger.digest(driver),
                limitation='Mismatch root cause unknown; four later passing read rounds demonstrate only non-reproduction'))
        command=dict(argv=[sys.executable,str(driver),'--verify',str(run),'--reference',reference,
            '--extractor',extractor,'--verification-output',output],cwd=str(attempt/'build'),
            timeout_seconds=1200,env=dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close'))
        result=ledger.run_stage(campaign,name,'independent',command,retry_failed=bool(previous),
            reason=('Old full12 scalar verification passed then posthash failed; new allocated node four-round '
                    'same-bytes Python/builtin/GNU checks agree with ORIGINAL expectedSHA. Recheck all12 '
                    'in a new directory without changing payload, expectedSHA, goldreference or tolerances.') if previous else None)
        ledger.require(result['status']=='passed','Full12 independent verification failed again; retain evidence and stop')
        ledger.ingest(campaign,name,run/'result.json')
    config=ledger.campaign(campaign)[1]
    ranked=sorted(names[1:],key=lambda n:ledger.checked_attempt(campaign,n,config)[2]['median_seconds'])
    reasons={}
    for name in ranked:
        try:
            ledger.promote(campaign,name,against=names[0]);break
        except ledger.EvidenceError as error:reasons[name]=str(error)
    for name in names:
        if name!=best()[0] and ledger.read(campaign/'attempts'/name/'attempt.json')['status']!='inconclusive':
            ledger.conclude(campaign,name,'inconclusive',reasons.get(name,'Verified matched work-balance control; no optimization adoption'),
                [str(campaign/'attempts'/name/'report.json')])
    state['work-balance'].update(complete=True,attempts=names,best_after=best()[0])
    ledger.atomic(state_path,state)

def group(key,variants,reason):
    if state.get(key,{}).get('complete'):return
    if key not in state:
        name,report=best()
        state[key]=dict(parent=name,configuration=report['configuration'],allocation=allocation)
        ledger.atomic(state_path,state)
    item=state[key]
    ledger.require(item['allocation']==allocation,'New timing group belongs to a different allocation')
    configuration=item['configuration']
    cases=[]
    for name,delta,batch,mechanism in variants:
        cases.append(dict(id=name,threads=configuration['threads'],batch=batch or configuration['batch'],
                          environment=dict(configuration['solve_environment'],**delta)))
        ledger.atomic(root/'proposals'/(name+'.json'),dict(bottleneck=reason,
            hypothesis=name+': '+mechanism,change=dict(solve_delta=delta,batch=batch),mechanism=mechanism,
            history_links=[str(campaign/'attempts'/item['parent']/'report.json'),
                str(campaign/'attempts/030-work-control/report.json'),str(root/'phase3-state.json'),
                str(root/'worker2-preflight/result.json')],
            retry_conditions='New matched controls oncn19483/allocationworker2. Never mix old cn22801 times into new timing comparison; all12zero-start independent precision unchanged.'))
    plan=dict(context_environment=configuration['context_environment'],cases=cases,
        placement_threads=configuration.get('placement_threads',configuration['threads']),
        setup_threads=configuration.get('setup_threads',configuration['threads']))
    path=root/'plans'/(key+'-worker2.json')
    if path.exists():ledger.require(ledger.read(path)==plan,'Resumed plan changed')
    ledger.atomic(path,plan)
    print('CONTINUATION_GROUP '+json.dumps(dict(key=key,parent=item['parent'],allocation=allocation,variants=variants)),flush=True)
    subprocess.run([sys.executable,str(source/'tools/optimization/interleaved.py'),'--campaign',str(campaign),
        '--reuse-attempt',item['parent'],'--plan',str(path),'--proposals',str(root/'proposals'),
        '--fixture',fixture,'--reference',reference,'--extractor',extractor,
        '--reference-propagator',fixture+'/propagator.npy','--backend','arm','--allocation',allocation],check=True)
    item.update(complete=True,attempts=[v[0] for v in variants],best_after=best()[0])
    ledger.atomic(state_path,state)

group('work-refinement-run',[
    ('035-refine-control',{},None,'Fresh production-style fixed32 control on the new allocation'),
    ('036-correction-confirm',{'LQCD_CORRECTION_BASE_TOL':.003},None,
     '034 gave about2.25% gain belowadoption; isolate and repeat on new context/node with freshcontrol, not claim a new combined optimization'),
    ('037-sap3',{'LQCD_MG_SAP_STEPS':3},None,
     '031 extra25%localsteps saved onlyoneouteriteration and<1%walltime; test cheaperlocalwork against explicitly measured added outer/coarse work'),
    ('038-known-profile',{'LQCD_MG_SAP_CYCLES':2,'LQCD_MG_SAP_STEPS':5,'LQCD_MG_COARSE_IT':40,
        'LQCD_MG_COARSE_TOL':.05,'LQCD_CORRECTION_BASE_TOL':.003,'LQCD_COARSE_CGS2':0,'LQCD_RESTRICT_FLOAT':0},None,
     'Samecanonicalgauge node5005 validated this repositoryprofile; test interactions of stronger preconditioning and shorter corrections onARM, without adding individual gains')],
    'Initial isolated workchanges didnotpass3%gate; retainactualiterations and validate a bounded weaker-work/interaction followup')
group('batch-reuse',[
    ('040-batch-control',{},None,'Fresh currentbest control before changing active source width'),
    ('041-batch4',{},4,'HBW plusreusedprojections andstableteam change balance: reusefine coefficient/halo data across4RHS'),
    ('042-batch12',{},12,'Fullsourcebatch reduces repeated finehalo launches; coarseRHS stillindependent, so no claim of reducedcoarsecollectives')],
    'Measuredfinehalo remains; changedHBW/SVEreuse/scheduleconditions justify bounded2/4/12comparison')
state.update(complete=True,best=best()[0])
ledger.atomic(state_path,state)
print('PHASE3_CONTINUATION_FINISHED '+best()[0],flush=True)
subprocess.run([sys.executable,str(root/'phase4.py')],check=True)
