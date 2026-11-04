"""Bounded environment-only reproduction; retain failed measurement untouched."""
import fcntl
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).parent/'aux-phase5-worker8-v5'))
import file_integrity as integrity

root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');q=root/'queue8'
name='142-old-runtime-environment-probe'
start=json.loads((root/'worker8-startup.json').read_text())
status=json.loads((q/'141-phase5-worker8-v5.status.json').read_text())
assert status['status']=='failed'and status['cleanup']['complete']and status['cleanup']['surviving_pids']==[]
assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))and not list(q.glob(name+'.*'))
assert start['safe_deadline_epoch']-time.time()>300
assert time.time()-(q/'heartbeat.json').stat().st_mtime<15
with (q/'worker.lock').open()as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:pass
    else:raise RuntimeError('Worker lock is not held')
stage=json.loads((root/'campaign/attempts/p5w8v5-old-default/attempt.json').read_text())['stages']['benchmark']
argv=stage['argv'];index=next(i for i,v in enumerate(argv)if Path(v).name=='runtime_benchmark_capture_v5.py')
task=dict(argv=[*argv[:index],str(root/'runtime_environment_probe142.py')],cwd=stage['cwd'],
    environment=stage['env_overrides'],timeout=120)
integrity.write_json_private(root/'runtime-environment-probe142-plan.json',dict(task=task,
    source_stage_sha256=integrity.read_dual(root/'campaign/attempts/p5w8v5-old-default/attempt.json')['openssl_sha256'],
    probe_sha256=integrity.read_dual(root/'runtime_environment_probe142.py')['openssl_sha256'],
    scope='Exact failed launcher prefix and stage environment; no solver or timing'))
private=q/(name+'.task.json');integrity.write_json_private(private,task)
os.link(private,q/(name+'.ready.json'))
print(json.dumps(dict(enqueued=True,id=name)))
