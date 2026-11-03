#!/usr/bin/env python3
"""Prepare queue110 only after closed phase100 and enough complete-group time.

Default is read-only and prints pending or exact argv/task. --enqueue is for
the root operator after review; it never retries an old task identity.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import time

R=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ID='110-phase5-shim-worker6'
ENTRY_SHA='c5a8a8b3c14d697c9062bf04172e2eb616ffebda66298a99aa123ca80419d9fe'
MANIFEST_SHA='c3f5fbca582920302010b5c742e4e59d78eb5f24a1a99861520e2464df5dae98'
TASK_BUDGET=8*550+300
DISPATCH_CLEANUP_RESERVE=90


def dependency_gate(status,state,best,startup,now):
    """Pure closed-predecessor/best/allocation/resource gate; never relabel."""
    reasons=[]
    if not (status.get('status')=='passed' and status.get('returncode')==0 and status.get('cleanup',{}).get('complete') is True):
        reasons.append('Phase100 queue task is not passed with complete cleanup')
    if not (state.get('complete') is True and state.get('status')=='complete'):
        reasons.append('Phase100 state is not complete')
    if state.get('best')!=best.get('attempt'):
        reasons.append('Phase100 final best differs from current best pointer')
    if not (startup.get('complete') is True and startup.get('allocation')=='mg-opt-20261103-worker6' and startup.get('host')=='cn19483'):
        reasons.append('Reviewed worker6 startup identity is missing/incomplete')
    if state.get('allocation')!=startup.get('allocation') or state.get('host')!=startup.get('host'):
        reasons.append('Phase100 belongs to another host/allocation')
    deadline=startup.get('safe_deadline_epoch',0)
    remaining=deadline-now if isinstance(deadline,(int,float)) and math.isfinite(deadline) else 0
    if remaining-DISPATCH_CLEANUP_RESERVE<TASK_BUDGET:
        reasons.append(f'Need {TASK_BUDGET}s complete8-trial budget plus90s dispatch/cleanup; {remaining:.0f}s remain')
    return dict(passed=not reasons,status='ready' if not reasons else 'pending',reasons=reasons,
                remaining_seconds=remaining,task_timeout_seconds=min(6500,max(1,int(remaining)-DISPATCH_CLEANUP_RESERVE)),
                task_budget_seconds=TASK_BUDGET)


def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enqueue',action='store_true')
    args=parser.parse_args()
    import file_integrity as integrity
    import raw_protocol_v4 as protocol
    q=R/'queue6'
    status=read(q/'100-phase6-halo-worker6.status.json')
    state=read(R/'100-halo-state.json')
    best=read(R/'campaign/best.json')
    startup=read(R/'worker6-startup.json')
    gate=dependency_gate(status,state,best,startup,time.time())
    if not gate['passed']:
        print('PHASE5_SHIM_PENDING '+json.dumps(gate),flush=True)
        if args.enqueue:raise RuntimeError('Dependencies/resource gate incomplete; no task published')
        return
    manifest_path=R/'runtime-shim-manifest-v2.json'
    integrity.read_dual(manifest_path,MANIFEST_SHA)
    manifest=read(manifest_path)
    seed=deepcopy(read(q/'090-best-profile-worker6.finished.json'))
    environment={key:value for key,value in seed.get('environment',{}).items()if not key.startswith('LQCD_OPT_')}
    for key in ('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):
        environment.pop(key,None)
    integrity.require(environment.get('LD_LIBRARY_PATH')==manifest['base_ld_library_path'],
                      'Seed must preserve exact original SDK search path for both controls')
    arguments=['--root',str(R),'--prefix','110','--state',str(R/'110-phase5-shim-state.json'),
        '--runtime-shim-manifest',str(manifest_path),'--runtime-shim-manifest-sha',MANIFEST_SHA,
        '--runtime-audit-dir',str(R/'110-phase5-shim-runtime-audit')]
    command=protocol.command(R,R/'phase5_validation_shim.py',ENTRY_SHA,ID,seed['argv'][0],arguments)
    seed.update(argv=command,cwd=str(R),timeout=gate['task_timeout_seconds'],environment=environment)
    print(json.dumps(dict(gate=gate,task=seed),indent=2),flush=True)
    if not args.enqueue:return
    integrity.require(not list(q.glob('*.running.json')) and not list(q.glob('*.ready.json')) and
        not list(q.glob(ID+'.*')) and not (R/'110-phase5-shim-state.json').exists(),
        'No concurrent/pending/reused task or state permitted; recover explicitly rather than auto retry')
    integrity.require('Bounded worker finished'not in (R/'worker6.log').read_text(),'Worker6 already exited')
    # Refresh state/best/deadline immediately before publication. No promotion or
    # ledger write occurs in this publisher; every trial has its own precision.
    current_best=read(R/'campaign/best.json')
    integrity.require(current_best==best and dependency_gate(read(q/'100-phase6-halo-worker6.status.json'),
        read(R/'100-halo-state.json'),current_best,read(R/'worker6-startup.json'),time.time())['passed'],
        'Dependencies/best/time changed during preparation; retain evidence and rerun check')
    dependency_paths=[q/'100-phase6-halo-worker6.status.json',R/'100-halo-state.json',
        R/'campaign/best.json',R/'worker6-startup.json',manifest_path]
    launch=dict(complete=True,kind='Prepared finite phase5 shim experiment; no numerical result yet',
        task=seed,gate=gate,dependencies={str(path):integrity.read_dual(path)['openssl_sha256']for path in dependency_paths},
        controller_sha256=ENTRY_SHA,shim_manifest_sha256=MANIFEST_SHA,
        publisher_sha256=integrity.read_dual(Path(__file__))['openssl_sha256'],
        original_phase5_and_v4_and_frozen_source_changed=False)
    integrity.write_json_private(R/(ID+'-launch.json'),launch)
    path=q/(ID+'.ready.json');temporary=q/(ID+'.tmp')
    with temporary.open('x')as stream:json.dump(seed,stream,indent=2);stream.write('\n')
    temporary.replace(path)
    print('QUEUED '+str(path),flush=True)


if __name__=='__main__':main()
