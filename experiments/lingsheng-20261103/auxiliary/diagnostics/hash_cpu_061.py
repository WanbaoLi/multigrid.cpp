#!/usr/bin/env python3
"""Separate061 continuation after060 passes: same snapshot on two actual CPUs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
HELPER_SHA='643201d131c155b9025740c9ce4e83324e8e219afc150c60216ea62f2a41ea79'


def main():
    helper=ROOT/'hash_visibility_060.py'
    if hashlib.sha256(helper.read_bytes()).hexdigest()!=HELPER_SHA:raise RuntimeError('Frozen060 helper changed')
    previous=ROOT/'hash-diagnostic060-057';old=json.loads((previous/'result.json').read_text())
    if not old.get('passed') or not old.get('original_unchanged_metadata') or old.get('original_rounds')!=2:
        raise RuntimeError('060 must pass both original rounds, exact snapshot and metadata before061')
    status=json.loads((ROOT/'queue5/060-hash-057-visibility.status.json').read_text())
    if status['status']!='passed' or not status['cleanup']['complete']:raise RuntimeError('060 queue cleanup not complete')
    spec=importlib.util.spec_from_file_location('immutable_hash060',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original=Path(old['original']);original_before=module.status(original.stat())
    snapshot=previous/'first-read-snapshot.npy';snapshot_before=module.status(snapshot.stat())
    allowed=sorted(os.sched_getaffinity(0))
    if 0 not in allowed or len(allowed)!=592:raise RuntimeError('ExpectedCPU0 andfull592CPUworker placement')
    topology={cpu:int(Path(f'/sys/devices/system/cpu/cpu{cpu}/topology/physical_package_id').read_text()) for cpu in allowed}
    sockets=sorted(set(topology.values()))
    if len(sockets)!=2:raise RuntimeError('Need actualtwo-socket topology')
    socket1=next(cpu for cpu in allowed if topology[cpu]==sockets[1])
    cpus=[0,socket1]
    if topology[0]==topology[socket1]:raise RuntimeError('SelectedCPUs are not on differentactualsockets')
    output=ROOT/'hash-diagnostic061-057';output.mkdir(exist_ok=False)
    summary=dict(complete=False,passed=False,started=time.time(),scope='Snapshot-only crossCPU diagnosis, no numerical acceptance',
        cpus=cpus,sockets={str(cpu):topology[cpu] for cpu in cpus},original_path=str(original),snapshot_path=str(snapshot),
        original_before=original_before,snapshot_before=snapshot_before,armcap_environment_modified=False,
        openssl_armcap_environment=os.environ.get('OPENSSL_armcap'),rows=[])
    module.dump(output/'attempt.json',summary)
    try:
        for cpu in cpus:
            os.sched_setaffinity(0,{cpu})
            if os.sched_getaffinity(0)!={cpu} or module.cpu()!=cpu:raise RuntimeError('RequestedCPUpinningdidnotapply')
            row=module.check(snapshot,f'snapshot-cpu{cpu}',output)
            summary['rows'].append(f'snapshot-cpu{cpu}.json')
            if not module.good(row) or any(c['before_read_cpu']!=cpu or c['after_hash_cpu']!=cpu for c in row['chunks']):
                raise RuntimeError('CrossCPU hash,metadata orCPUmismatch; strictstop')
        summary.update(passed=True,complete=True,interpretation='BothpinnedCPUreadssameexpected; thisdoesnotidentifypriorfailurecause')
    except BaseException as error:
        summary.update(complete=True,passed=False,error=repr(error),traceback=traceback.format_exc());raise
    finally:
        os.sched_setaffinity(0,allowed)
        summary.update(seconds=time.time()-summary['started'],restored_task_affinity=sorted(os.sched_getaffinity(0)),
            original_after=module.status(original.stat()),snapshot_after=module.status(snapshot.stat()))
        if summary['original_after']!=original_before or summary['snapshot_after']!=snapshot_before:summary['passed']=False
        module.dump(output/'result.json',summary)
        print(json.dumps(summary),flush=True)
    if not summary['passed']:raise RuntimeError('Filemetadatachanged; strictstop')


if __name__=='__main__':main()
