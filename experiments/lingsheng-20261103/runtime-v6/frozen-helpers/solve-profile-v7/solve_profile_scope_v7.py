"""Exact allocated diagnostic scope, reusing the existing environment sanitizer."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import socket
import sys
import time

import file_integrity as integrity
from raw_scalar_helper import source_bytes


def read(path,expected=None):
    value=integrity.read_dual(path,expected)['openssl_sha256']
    return json.loads(source_bytes(path,value))


def validate(contract,host,allocation,now,deadline,cpus,loaded,loader):
    require=integrity.require
    require(contract['schema']=='solve-profile-scope-v7'and contract['complete'],'Explicit completed preparation required')
    require(host==contract['host']and allocation==contract['allocation'],'Actual profile worker epoch differs')
    require(math.isfinite(deadline)and deadline-now>=3690,'Whole diagnostic task budget no longer fits')
    require(sorted(cpus)==contract['expected_parent_cpus']and not loaded,
            'Parent affinity or runtime isolation changed before NUMA launcher')
    require(loader==contract['startup_ld_library_path'],'Actual startup loader path differs')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha',required=True);args=p.parse_args()
    contract=read(args.contract,args.contract_sha)
    root=Path(contract['root']);queue=root/contract['queue'];name=contract['id']
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
    loaded=any('libgomp.so'in row or'libomp.so'in row or'libkupl.so'in row for row in Path('/proc/self/maps').read_text().splitlines())
    validate(contract,socket.gethostname(),os.environ.get('LQCD_OPT_ALLOCATION'),time.time(),deadline,
             os.sched_getaffinity(0),loaded,os.environ.get('LD_LIBRARY_PATH'))
    claims=list(queue.glob('*.running.json'))
    integrity.require(len(claims)==1 and claims[0].name==name+'.running.json','Exact one owned queue claim required')
    status=read(queue/(name+'.status.json'))
    integrity.require(status.get('status')=='running'and status.get('task_tag')==os.environ.get('LQCD_OPT_TASK_ID'),
        'Profile task ownership differs')
    for row in contract['helper_pins']:integrity.read_dual(row['path'],row['sha256'])
    future=[root/(name+'-state.json'),root/'campaign/attempts'/name,Path(contract['profile_output'])]
    integrity.require(not any(path.exists()or path.is_symlink()for path in future),'Used profile output; no automatic retry')
    path=Path(__file__).with_name('phase5_worker7_allocation_v3.py')
    integrity.read_dual(path,'ad253df6ea118b16380d8a39b78f1fcba4df48c4e3c44929b4f581aa11490295')
    spec=importlib.util.spec_from_file_location('_existing_environment_sanitizer',path)
    sanitizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(sanitizer)
    removed=sanitizer.sanitize(os.environ,contract['numerical_environment_keys'],contract['startup_clear_keys'])
    os.environ['LQCD_OPT_DEADLINE_EPOCH']=str(min(deadline,time.time()+contract['task_timeout_seconds']-60))
    controller=contract['controller'];integrity.read_dual(controller['path'],controller['sha256'])
    print('SOLVE_PROFILE_V7_SCOPE '+json.dumps(dict(contract_sha256=args.contract_sha,host=contract['host'],
        allocation=contract['allocation'],removed_environment_keys=removed,unranked=True)),flush=True)
    sys.argv=[controller['path'],*controller['argv']]
    runpy.run_path(controller['path'],run_name='__main__')


if __name__=='__main__':main()
