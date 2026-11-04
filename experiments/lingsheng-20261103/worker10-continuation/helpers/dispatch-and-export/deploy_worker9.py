"""Deploy reviewed fresh wrappers and authenticate actual predecessor exit."""
import fcntl
import importlib.util
import json
from pathlib import Path
import shutil
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path):return json.loads(source_bytes(path,sha(path)))
aux=root/'worker9-helpers';manifest=read(aux/'worker9-launch-manifest.json')
sha(aux/'worker9-launch-manifest.json','51719841afa802e24fbff722d4f98fb7790680232811caeb4989ce05dd702519')
for name,row in manifest['files'].items():
    source=aux/name;sha(source,row['sha256'])
    integrity.write_private_new(root/name,[source_bytes(source,row['sha256'])])
integrity.write_private_new(root/'worker9-launch-manifest.json',[source_bytes(aux/'worker9-launch-manifest.json',sha(aux/'worker9-launch-manifest.json'))])
q=root/'queue8';assert not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))
with(q/'worker.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
statuses={str(p):sha(p)for p in sorted(q.glob('*.status.json'))}
for path in statuses:
    status=read(Path(path))
    assert status['status']in('passed','failed','timeout')and status['task_tag']and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
spec=importlib.util.spec_from_file_location('actual_old_worker',root/'worker8_login_record.py')
login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
job,query=login.query(shutil.which('djob'),'2023152')
assert job['state']=='SUCCEEDED'and job['exitCode']==0 and job['jobExitCode']==0 and job['user']=='nsls_lwb'
assert(root/'worker8.log').read_text().strip().splitlines()[-1]=='Bounded worker finished; no active task'
proof=dict(complete=True,previous_job='2023152',worker_stopped=True,all_owned_tasks_cleaned=True,
    exit_kind='natural-idle',scheduler_end_time=job['endTime'],worker_log_sha256=sha(root/'worker8.log'),
    task_status_sha256=statuses,lock_unheld=True,scheduler_query=query)
integrity.write_json_private(root/'worker8-natural-exit-proof-for-worker9.json',proof)
print(json.dumps(dict(deployed=True,files=len(manifest['files']),stop_proof_sha256=sha(root/'worker8-natural-exit-proof-for-worker9.json'))),flush=True)
