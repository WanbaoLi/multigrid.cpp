"""Reuse verified parent checks before an exact pinned serial successor task."""
import argparse
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root))
import worker10_live_parent_guard_v1 as previous
integrity=previous.integrity
def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha',required=True);a=p.parse_args()
    plan=previous.read(a.plan,a.plan_sha);previous.sha(__file__,plan['guard_sha256'])
    previous.sha(previous.__file__,'63d2cd54b0246e8ffee9e0e524fd300fe25059e2e25b4e25cbce7747394c00f6')
    name=plan['id'];integrity.require(name in('150-best-solve-profile-worker10','148-halo-v2-full-worker10','149-clover-arm-qualify-worker10','152-halo-v2-ordinary-worker10'),'Explicit reviewed successor ID required')
    task=previous.read(plan['original_task']['path'],plan['original_task']['sha256'])
    startup=previous.read(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
    heartbeat=previous.read(root/'queue10/heartbeat.json');status=previous.read(root/'queue10'/(name+'.status.json'))
    pid=os.getppid();proc=Path('/proc')/str(pid)
    command=[os.fsdecode(v)for v in(proc/'cmdline').read_bytes().split(b'\0')if v]
    allocations=[os.fsdecode(v.split(b'=',1)[1])for v in(proc/'environ').read_bytes().split(b'\0')if v.startswith(b'LQCD_OPT_ALLOCATION=')]
    integrity.require(allocations==[startup['allocation']],'Actual parent allocation differs')
    loaded=any('libgomp.so'in row or'libomp.so'in row or'libkupl.so'in row for row in(proc/'maps').read_text().splitlines())
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH']);now=time.time()
    previous.validate(startup,heartbeat,status,socket.gethostname(),pid,proc.stat().st_uid,os.getuid(),command,allocations[0],
        os.sched_getaffinity(pid),os.sched_getaffinity(0),loaded,os.environ.get('LQCD_OPT_TASK_ID'),deadline,now)
    integrity.require(deadline-now>=task['timeout']+90 and task['timeout']==plan['task_timeout_seconds'],'Entire original task budget no longer fits')
    integrity.require(task['argv'][0]==sys.executable and task['argv'][1]=='-u','Original task must use exact inherited Python')
    entry=Path(task['argv'][2]);previous.sha(entry,plan['original_entry_sha256'])
    integrity.write_json_private(root/(name+'-actual-parent-guard-v3.json'),dict(complete=True,parent_pid=pid,
        parent_starttime_ticks=int((proc/'stat').read_text().rpartition(') ')[2].split()[19]),host=socket.gethostname(),
        allocation=allocations[0],parent_cpus=sorted(os.sched_getaffinity(pid)),task_tag=status['task_tag'],
        original_task_sha256=plan['original_task']['sha256'],guard_plan_sha256=a.plan_sha,parallel_runtime_loaded=False,
        original_argv_and_scientific_scope_preserved=True))
    sys.argv=task['argv'][2:];runpy.run_path(str(entry),run_name='__main__')
if __name__=='__main__':main()
