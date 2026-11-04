"""Publish only this bounded actual16-rank small smoke after idle-worker checks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time
import uuid
import file_integrity as integrity

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ID='139d-capture-v5-sdk-worker8'


def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']


def main():
    p=argparse.ArgumentParser();p.add_argument('--enqueue',action='store_true');args=p.parse_args()
    q=ROOT/'queue8';startup=ROOT/'worker8-startup.json'
    sha(startup,'c54fd907920ddd836941f9b475df1171ac60243c47c53541d2bb4f04b600f826')
    start=json.loads(startup.read_text());heartbeat=json.loads((q/'heartbeat.json').read_text())
    assert start['complete']and start['allocation']=='mg-opt-20261103-worker8'
    assert len(heartbeat['allowed_cpus'])==592 and heartbeat['host']=='cn19483'
    assert time.time()-(q/'heartbeat.json').stat().st_mtime<15
    assert start['safe_deadline_epoch']-time.time()>5000
    assert not list(q.glob('*.ready.json'))and not list(q.glob('*.running.json'))and not list(q.glob(ID+'.*'))
    assert not (q/'STOP').exists()and 'Bounded worker finished'not in(ROOT/'worker8.log').read_text()
    with (q/'worker.lock').open()as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:raise RuntimeError('Idle worker lock is not held')
    aux=ROOT/'aux-phase5-worker8-v5'
    manifest=json.loads((aux/'capture-v5-package-manifest.json').read_text())
    sha(aux/'capture-v5-package-manifest.json','2de5df16026d4d7371cbd6498ba2ab3916944aababf3b02edadb7c2f49be518a')
    for name,row in manifest['files'].items():sha(aux/name,row['sha256'])
    best=json.loads((ROOT/'campaign/best.json').read_text());assert best['attempt']=='052-reduce-on'
    source=ROOT/'campaign/attempts/052-reduce-on/source'
    script=ROOT/'runtime_capture_v5_sdk_smoke_worker8.py'
    env={key:str(value)for key,value in json.loads((ROOT/'campaign/attempts/052-reduce-on/report.json').read_text())['configuration']['context_environment'].items()}
    plan=ROOT/'runtime-capture-v5-sdk-smoke-worker8-plan.json'
    output=ROOT/'runtime-capture-v5-sdk-smoke-worker8'
    assert not plan.exists()and not output.exists()
    env.update(LQCD_OPT_CAPTURE_BASE_LD=start['loader_environment']['LD_LIBRARY_PATH'],
        LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LQCD_OPT_STAGE_ID=uuid.uuid4().hex,
        LD_PRELOAD='',LD_DEBUG='',PERF_COUNTER_ROOT='',OPENBLAS_NUM_THREADS='1')
    task=dict(argv=['/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',str(source/'tools/run_numa.py'),
        '--threads','2','--lattice','8','8','8','32','--block','2','2','2','2','--',
        '/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',str(script)],
        cwd=str(aux),environment=env,timeout=240)
    receipt=dict(task=task,smoke_script_sha256=sha(script),scope='Small actual16-rank capture/constructor/setup smoke; no production timing or full12 precision claim')
    if not args.enqueue:
        print(json.dumps(receipt,indent=2));return
    integrity.write_json_private(plan,dict(context_environment={key:value for key,value in env.items()if not key.startswith('LQCD_OPT_')}))
    integrity.write_json_private(ROOT/'runtime-capture-v5-sdk-smoke-worker8-launch.json',receipt)
    private=q/(ID+'.task.json');integrity.write_json_private(private,task)
    os.link(private,q/(ID+'.ready.json'))
    print(json.dumps(dict(enqueued=True,id=ID,task_sha256=sha(private))),flush=True)


if __name__=='__main__':main()
