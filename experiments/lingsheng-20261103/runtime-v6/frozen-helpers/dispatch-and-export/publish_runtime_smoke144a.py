"""Publish exact bounded old-runtime smoke only after profile task is terminal."""
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import uuid
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-runtime-only-v6';q=root/'queue8'
sys.path.insert(0,str(aux));import file_integrity as integrity
import phase5_validation_shim as policy
def read(path):return json.loads(path.read_text())
status=read(q/'143-best-solve-profile-worker8.status.json')
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert read(root/'143-best-solve-profile-worker8-state.json')['complete']
name='144a-old-runtime-capture-smoke'
assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(name+'.*'))
assert not(q/'STOP').exists()and time.time()-(q/'heartbeat.json').stat().st_mtime<15
assert read(root/'worker8-startup.json')['safe_deadline_epoch']-time.time()>5200
with(q/'worker.lock').open()as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:pass
    else:raise RuntimeError('Worker lock not held')
manifest=read(aux/'runtime-only-v6-files.json')
integrity.read_dual(aux/'runtime-only-v6-files.json','35dbef1def6d2b8aef669ed149a4640de4077763616e245acac9d422844b8cd8')
for path,expected in manifest['files'].items():integrity.read_dual(aux/path,expected)
shim=read(root/'aux-phase5-worker8-v5/runtime-shim-manifest-worker8-v3.json')
context=dict(read(root/'campaign/attempts/052-reduce-on/report.json')['configuration']['context_environment'],LD_LIBRARY_PATH=policy.old_search_path(shim))
plan=root/'runtime-capture-old-smoke144a-plan.json';output=root/'runtime-capture-old-smoke144a'
assert not plan.exists()and not output.exists()
env={k:str(v)for k,v in context.items()};env.update(LD_PRELOAD='',LD_DEBUG='',PERF_COUNTER_ROOT='',OPENBLAS_NUM_THREADS='1',
    LQCD_OPT_STAGE_ID=uuid.uuid4().hex,LQCD_OPT_CAPTURE_BASE_LD=shim['base_ld_library_path'])
script=root/'runtime_capture_old_smoke144a.py';python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
task=dict(argv=[python,str(root/'campaign/attempts/052-reduce-on/source/tools/run_numa.py'),'--threads','2',
    '--lattice','8','8','8','32','--block','2','2','2','2','--',python,str(script)],cwd=str(aux),environment=env,timeout=240)
integrity.write_json_private(plan,dict(context_environment=context))
integrity.write_json_private(root/'runtime-capture-old-smoke144a-launch.json',dict(task=task,
    script_sha256=integrity.read_dual(script)['openssl_sha256'],scope='Actual old-GOMP maps and small setup only'))
private=q/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,q/(name+'.ready.json'))
print(json.dumps(dict(enqueued=True,id=name)),flush=True)
