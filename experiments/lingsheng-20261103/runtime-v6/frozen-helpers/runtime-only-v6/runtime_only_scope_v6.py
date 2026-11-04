"""Exact current allocation and fresh five-case runtime task scope."""
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

def read(path,expected=None):return json.loads(source_bytes(path,integrity.read_dual(path,expected)['openssl_sha256']))

def validate(contract,host,allocation,now,deadline,cpus,loaded,loader):
    require=integrity.require
    require(contract['schema']=='runtime-only-scope-v6'and contract['complete'],'Explicit runtime preparation required')
    require(host==contract['host']and allocation==contract['allocation'],'Actual runtime worker differs')
    require(math.isfinite(deadline)and deadline-now>=4890,'Need4800s whole runtime bracket plus90s reserve')
    require(sorted(cpus)==contract['expected_parent_cpus']and not loaded,'Parent mask/runtime changed before NUMA launcher')
    require(loader==contract['startup_ld_library_path'],'Startup loader path differs')

def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--contract-sha',required=True)
    args=p.parse_args();contract=read(args.contract,args.contract_sha)
    root=Path(contract['root']);queue=root/contract['queue'];name=contract['id']
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
    loaded=any('libgomp.so'in row or'libomp.so'in row or'libkupl.so'in row for row in Path('/proc/self/maps').read_text().splitlines())
    validate(contract,socket.gethostname(),os.environ.get('LQCD_OPT_ALLOCATION'),time.time(),deadline,
        os.sched_getaffinity(0),loaded,os.environ.get('LD_LIBRARY_PATH'))
    claims=list(queue.glob('*.running.json'));integrity.require(len(claims)==1 and claims[0].name==name+'.running.json','Exact one owned queue claim required')
    status=read(queue/(name+'.status.json'))
    integrity.require(status.get('status')=='running'and status.get('task_tag')==os.environ.get('LQCD_OPT_TASK_ID'),'Task owner differs')
    for row in contract['pinned_files']:integrity.read_dual(row['path'],row['sha256'])
    integrity.require(read(root/'campaign/best.json')['attempt']==contract['expected_best'],'Best changed before dispatch')
    future=[Path(contract['state']),Path(contract['runtime_audit_dir'])]
    for case in contract['case_ids']:
        future.extend([root/'campaign/attempts'/case,root/'plans'/(case+'.json'),root/'proposals'/(case+'.json')])
        future.extend((root/'phase5-shim-logs').glob(case+'-*.log'))
    integrity.require(not any(path.exists()or path.is_symlink()for path in future),'Used state or case namespace; no implicit retries')
    path=Path(__file__).with_name('phase5_worker7_allocation_v3.py')
    integrity.read_dual(path,'ad253df6ea118b16380d8a39b78f1fcba4df48c4e3c44929b4f581aa11490295')
    spec=importlib.util.spec_from_file_location('_existing_numerical_env_sanitizer',path)
    sanitizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(sanitizer)
    removed=sanitizer.sanitize(os.environ,contract['numerical_environment_keys'],contract['startup_clear_keys'])
    os.environ['LQCD_OPT_DEADLINE_EPOCH']=str(min(deadline,time.time()+contract['task_timeout_seconds']-60))
    entry=contract['controller'];integrity.read_dual(entry['path'],entry['sha256'])
    print('RUNTIME_ONLY_V6_SCOPE '+json.dumps(dict(contract_sha256=args.contract_sha,host=contract['host'],
        allocation=contract['allocation'],removed_environment_keys=removed,case_ids=contract['case_ids'])),flush=True)
    sys.argv=[entry['path'],*entry['argv']];runpy.run_path(entry['path'],run_name='__main__')

if __name__=='__main__':main()
