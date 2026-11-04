"""Attest the actual allocated worker parent before original scope execution."""
import argparse
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-runtime-confirm-v7';sys.path.insert(0,str(aux))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def validate(startup,heartbeat,status,host,ppid,parent_uid,uid,command,allocation,parent_cpus,self_cpus,loaded,task_tag,deadline,now):
    require=integrity.require
    require(host==startup['host']=='cn19486'and startup['allocation']==allocation=='mg-opt-20261103-worker10','Actual node/allocation differs')
    expected=startup['before_worker_exec_parent_state']['cpus']
    require(ppid==heartbeat['pid']and parent_uid==uid and sorted(parent_cpus)==expected==sorted(self_cpus)and len(expected)==592,'Live exact full-affinity worker parent required')
    worker=startup['source_root']+'/tools/optimization/worker.py'
    require(worker in command and '--queue'in command and command[command.index('--queue')+1]==str(root/'queue10'),'Actual parent command/queue differs')
    require(not loaded and deadline<=startup['safe_deadline_epoch']and deadline-now>=3090,'Parent runtime or live allocation budget differs')
    require(status['status']=='running'and status['task_tag']==task_tag and bool(task_tag),'Actual task ownership differs')
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--contract-sha',required=True)
    p.add_argument('--original-entry-sha',required=True);args=p.parse_args()
    contract=read(args.contract,args.contract_sha);name=contract['id'];assert name=='151-runtime-confirm-worker10-v7'
    startup=read(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
    heartbeat=read(root/'queue10/heartbeat.json');status=read(root/'queue10'/(name+'.status.json'))
    ppid=os.getppid();proc=Path('/proc')/str(ppid)
    command=[os.fsdecode(value)for value in(proc/'cmdline').read_bytes().split(b'\0')if value]
    allocations=[os.fsdecode(row.split(b'=',1)[1])for row in(proc/'environ').read_bytes().split(b'\0')if row.startswith(b'LQCD_OPT_ALLOCATION=')]
    integrity.require(allocations==[startup['allocation']],'Actual parent allocation tag differs')
    loaded=any('libgomp.so'in row or'libomp.so'in row or'libkupl.so'in row for row in(proc/'maps').read_text().splitlines())
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH'])
    validate(startup,heartbeat,status,socket.gethostname(),ppid,proc.stat().st_uid,os.getuid(),command,allocations[0],
        os.sched_getaffinity(ppid),os.sched_getaffinity(0),loaded,os.environ.get('LQCD_OPT_TASK_ID'),deadline,time.time())
    ticks=int((proc/'stat').read_text().rpartition(') ')[2].split()[19])
    integrity.write_json_private(root/'runtime151-actual-parent-guard.json',dict(complete=True,host=socket.gethostname(),
        parent_pid=ppid,parent_starttime_ticks=ticks,parent_uid=proc.stat().st_uid,parent_command=command,
        parent_cpus=sorted(os.sched_getaffinity(ppid)),parallel_runtime_loaded=False,task_tag=status['task_tag'],
        allocation=startup['allocation'],safe_deadline_epoch=deadline,guard_sha256=sha(__file__),
        scope='Live actual worker proof; original scope, numerical trials and acceptance gates unchanged'))
    entry=aux/'runtime_confirm_scope_v7.py';sha(entry,args.original_entry_sha)
    sys.argv=[str(entry),'--contract',str(args.contract),'--contract-sha',args.contract_sha]
    runpy.run_path(entry,run_name='__main__')
if __name__=='__main__':main()
