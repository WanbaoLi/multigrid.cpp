#!/usr/bin/env python3
"""Compare dynamic solve options on one frozen hierarchy and retained binary.

Plan case IDs are ledger attempt IDs. The first case must reproduce the current
best configuration. Each case needs a proposal in --proposals/CASE.json.
"""
import argparse
import json
from pathlib import Path
import sys

import campaign as ledger


def configuration(plan,case,reference):
    result=dict(reference,context_environment=plan.get('context_environment',{}),
                solve_environment=case.get('environment',{}),
                threads=case['threads'],batch=case['batch'])
    for key in ['placement_threads','setup_threads']:
        value=plan.get(key,max(c['threads'] for c in plan['cases']))
        if value!=case['threads']:result[key]=value
        else:result.pop(key,None)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',type=Path,required=True)
    p.add_argument('--reuse-attempt',required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--proposals',type=Path,required=True)
    p.add_argument('--fixture',required=True)
    p.add_argument('--reference',required=True)
    p.add_argument('--extractor',required=True)
    p.add_argument('--reference-propagator',required=True)
    p.add_argument('--backend',choices=['arm','x86'],required=True)
    p.add_argument('--allocation',required=True)
    p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args()
    root,config=ledger.campaign(args.campaign)
    parent,reference,_=ledger.checked_attempt(root,args.reuse_attempt,config)
    best=ledger.read(root/'best.json')
    # A new group cannot start against a version which has already been replaced.
    plan=ledger.read(args.plan)
    names=[case['id'] for case in plan['cases']]
    ledger.require(len(names)>1 and len(set(names))==len(names),'Need at least two unique cases')
    group=root/'attempts'/names[0]
    if not group.exists():
        ledger.require(best['attempt']==args.reuse_attempt,'New group must use current best')
    ledger.require(plan.get('context_environment',{})==reference['configuration']['context_environment'],
                   'Cached context flags require separate processes, not this driver')
    ledger.require(configuration(plan,plan['cases'][0],reference['configuration'])==reference['configuration'],
                   'First case must reproduce the complete retained-best configuration')
    ledger.require(args.repeats>=3,'Need at least three steady repeats')
    snapshots=[]
    for name in names:
        if not (root/'attempts'/name).exists():
            history=ledger.show_history(root)
            description=ledger.read(args.proposals/(name+'.json'))
            description['history_read_token']=history['history_read_token']
            ledger.propose(root,name,description)
        snapshots.append(ledger.snapshot_from(root,name,args.reuse_attempt))
    fingerprints={s['source_manifest_sha256'] for s in snapshots}
    ledger.require(fingerprints=={parent['snapshot']['source_manifest_sha256']},'Source fingerprint mismatch')
    saved_plan=group/'interleaved-plan.json'
    if saved_plan.exists():
        ledger.require(ledger.read(saved_plan)==plan,'Cannot alter a resumed group plan')
    else:ledger.atomic(saved_plan,plan)
    source=Path(snapshots[0]['source'])
    library=root/'attempts'/args.reuse_attempt/'artifacts/liblqcd_cpu.so'
    maximum=plan.get('placement_threads',max(c['threads'] for c in plan['cases']))
    command=[sys.executable,str(source/'tools/run_numa.py')]
    if args.backend=='x86':command+=['--ranks-per-numa','2']
    command+=['--threads',str(maximum),'--',sys.executable,'-u',
        str(source/'tools/optimization/bench_full12.py'),'--fixture',args.fixture,
        '--plan',str(saved_plan),'--library',str(library),'--backend',args.backend,
        '--output',str(group/'measurements'),'--allocation',args.allocation,
        '--snapshot-sha',snapshots[0]['source_manifest_sha256'],
        '--reference-propagator',args.reference_propagator,'--repeats',str(args.repeats)]
    def stage(name,label,argv,timeout,env=None):
        result=ledger.run_stage(root,name,label,dict(argv=argv,
            cwd=str(root/'attempts'/name/'build'),timeout_seconds=timeout,env=env or {}))
        ledger.require(result['status']=='passed',label+' failed; explicit attributed retry required')
    stage(names[0],'interleaved-benchmark',command,1800)
    for name in names:
        target=group/'measurements'/name
        stage(name,'independent',[sys.executable,str(source/'tools/optimization/bench_full12.py'),
            '--verify',str(target),'--reference',args.reference,'--extractor',args.extractor],1200,
            dict(OMP_NUM_THREADS='4',OMP_PLACES='cores',OMP_PROC_BIND='close'))
        ledger.ingest(root,name,target/'result.json')
    # Existing promotions are idempotent. Otherwise choose one candidate using
    # the exact same precision/noise/current-best gates as the single trial.
    data=[ledger.checked_attempt(root,name,config) for name in names]
    ranked=sorted(range(1,len(names)),key=lambda i:data[i][2]['median_seconds'])
    reasons={}
    for candidate in ranked:
        winner=names[candidate]
        try:
            decision=ledger.promote(root,winner,against=names[0])
            print('PROMOTED '+json.dumps(decision),flush=True)
            break
        except ledger.EvidenceError as exc:
            reasons[winner]=str(exc)
            print('INCONCLUSIVE '+winner+' '+str(exc),flush=True)
    for name in names:
        if ledger.read(root/'best.json')['attempt']!=name:
            record=ledger.read(root/'attempts'/name/'attempt.json')
            if record['status']!='inconclusive':
                ledger.conclude(root,name,'inconclusive',
                    reasons.get(name,'Paired full12 group complete; retained as control or superseded by a faster eligible candidate'),
                    [str(group/'measurements'/name/'result.json')])


if __name__=='__main__':main()
