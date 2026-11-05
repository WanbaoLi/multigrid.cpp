"""Queue once behind the already active owned qualification task."""
import fcntl
import json
import os
from pathlib import Path
import socket
import sys
import time
root=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105');sys.path.insert(0,str(root))
import file_integrity as integrity
assert socket.gethostname()=='node5005'and len(os.sched_getaffinity(0))==256
launch=json.loads((root/'launch.json').read_text());assert launch['worker_pid']==492870
os.kill(launch['worker_pid'],0)
queue=root/'queue';name='100-delivery-full12'
assert not list(queue.glob(name+'.*'))and not list(queue.glob('*.ready.json'))
with(queue/'worker.lock').open()as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:pass
    else:raise RuntimeError('Owned worker must hold queue lock')
task=dict(argv=[sys.executable,'-u',str(root/'x86_delivery833_full12.py')],cwd=str(root),timeout=3800,environment=dict(OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
private=queue/(name+'.task.json');integrity.write_json_private(private,task);os.link(private,queue/(name+'.ready.json'))
print(json.dumps(dict(enqueued=True,name=name,task_sha256=integrity.read_dual(private)['openssl_sha256'],epoch=time.time())),flush=True)
