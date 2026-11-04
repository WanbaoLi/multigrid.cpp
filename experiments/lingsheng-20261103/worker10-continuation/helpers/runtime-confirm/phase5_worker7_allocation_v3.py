#!/usr/bin/env python3
"""Dispatch only a reviewed prepared c5 task in its exact current allocation.

No queue publication, numerical source change or result acceptance occurs here.
All scientific work/8-case gates remain in the frozen c5 controller and raw v4.
"""
import argparse
import json
import math
import os
from pathlib import Path
import runpy
import socket
import sys
import time

import file_integrity as integrity
import raw_cold_adapter as cold


def validate(contract,actual_host,actual_allocation,now,environment,parent_cpus,parallel_runtime_loaded):
    require=integrity.require
    require(contract.get('schema')=='portable-phase5-preparation-v3'and contract.get('complete')is True,
            'Complete reviewed preparation contract required')
    require(contract['host']==actual_host and contract['allocation']==actual_allocation,
            'Actual worker differs from explicit startup host/allocation')
    deadline=contract['safe_deadline_epoch'];raw=environment.get('LQCD_OPT_DEADLINE_EPOCH','')
    try:actual_deadline=float(raw)
    except(ValueError,TypeError):raise RuntimeError('Finite actual worker deadline required')
    require(math.isfinite(deadline)and math.isfinite(actual_deadline)and actual_deadline<=deadline and
            min(deadline,actual_deadline)-now-90>=4700,'Pending: complete8-trial budget no longer fits at dispatch')
    require(environment.get('LQCD_OPT_TASK_ID'),'Bounded worker ownership tag required')
    require(environment.get('LD_LIBRARY_PATH')==contract['startup_ld_library_path'],
            'Actual SDK search path differs from explicit runtime manifest')
    require(not any(environment.get(key)for key in('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT')),
            'Unexpected preload/debug/profiling startup environment')
    require(sorted(parent_cpus)==sorted(contract['expected_parent_cpus'])and not parallel_runtime_loaded,
            'Parent mask changed or parallel runtime loaded before NUMA launcher')


def sanitize(environment,numerical_keys,startup_keys):
    removed=[]
    for key in set(numerical_keys)|set(startup_keys):
        if key.startswith('LQCD_OPT_')or key in('LQCD_NUMA_NODE','LQCD_CPU_THREADS'):continue
        if key in environment:removed.append(key);environment.pop(key)
    return sorted(removed)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',type=Path,required=True);parser.add_argument('--contract-sha',required=True)
    args=parser.parse_args()
    integrity.read_dual(integrity.__file__,'34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427')
    integrity.read_dual(cold.__file__,'c65c2da816c9a68f992a6db4cdbbef98e02954a17015abf8405ea474d780cc69')
    payload,_=cold.read_source(args.contract,args.contract_sha);contract=json.loads(payload)
    for row in contract['pinned_files']:integrity.read_dual(Path(row['path']),row['sha256'])
    loaded=any('libgomp.so'in line or'libkupl.so'in line for line in Path('/proc/self/maps').read_text().splitlines())
    validate(contract,socket.gethostname().split('.')[0],os.environ.get('LQCD_OPT_ALLOCATION'),time.time(),
             os.environ,os.sched_getaffinity(0),loaded)
    # The worker's own running/status claim is expected; every scientific case,
    # plan/proposal/log/audit/state must still be new when this task starts.
    root=Path(contract['root']);state=Path(contract['state']);audit=Path(contract['runtime_audit_dir'])
    targets=[state,audit]
    for name in contract['case_ids']:
        targets.extend([root/'campaign/attempts'/name,root/'plans'/(name+'.json'),root/'proposals'/(name+'.json')])
        targets.extend((root/'phase5-shim-logs').glob(name+'-*.log'))
    targets.extend((root/'phase5-shim-logs').glob(contract['prefix']+'-loader-*.log'))
    integrity.require(not any(path.exists()or path.is_symlink()for path in targets),'Fresh phase5 case/state/audit identity already used; explicit recovery required')
    queue=Path(contract['queue'])
    claims=list(queue.glob('*.running.json'))
    integrity.require(len(claims)==1 and claims[0].name==contract['task_id']+'.running.json',
                      'Exact owned worker queue claim required; no concurrent task')
    status=json.loads(cold.read_source(queue/(contract['task_id']+'.status.json'))[0])
    integrity.require(status.get('status')=='running'and status.get('task_tag')==os.environ['LQCD_OPT_TASK_ID'],
                      'Queue claim ownership differs from executing task')
    removed=sanitize(os.environ,contract['numerical_environment_keys'],contract['startup_clear_keys'])
    controller=contract['controller'];integrity.read_dual(controller['path'],controller['sha256'])
    print('PHASE5_PORTABLE_DISPATCH '+json.dumps(dict(contract=str(args.contract),contract_sha256=args.contract_sha,
        host=contract['host'],allocation=contract['allocation'],cleared_environment_keys=removed,
        scope='Fresh8 c5 processes, no automatic retry or changed numerical plan')),flush=True)
    sys.argv=[controller['path'],*controller['argv']]
    runpy.run_path(controller['path'],run_name='__main__')


if __name__=='__main__':main()
