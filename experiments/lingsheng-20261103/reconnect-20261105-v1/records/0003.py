"""Deploy new immutable wrappers and record actual closed predecessor; no submit."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(p,e=None):return integrity.read_dual(p,e)['openssl_sha256']
def read(p):return json.loads(source_bytes(p,sha(p)))
spec=importlib.util.spec_from_file_location('actual_login',root/'worker11_login_record.py')
login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
previous,query=login.query(shutil.which('djob'),'2026153')
assert previous['state']=='SUCCEEDED'and previous['exitCode']==previous['jobExitCode']==0
assert previous['jobName']=='mg-opt-worker11'and previous['user']=='nsls_lwb'and previous['taskExecNodes']=='cn19486'
assert (root/'worker11.log').read_text().strip().splitlines()[-1]=='Bounded worker finished; no active task'
queue=root/'queue11';assert not list(queue.glob('*.ready.json'))and not list(queue.glob('*.running.json'))
statuses={str(p):sha(p)for p in sorted(queue.glob('*.status.json'))};assert statuses
for p in statuses:
    s=read(Path(p));assert s['status']in('passed','failed','timeout')and s['cleanup']['complete']and not s['cleanup']['surviving_pids']
with (queue/'worker.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
archive=root/'worker12-prepared-v1.tar.gz';sha(archive,'7b84a42fa71d4e952a479134b3d23bffb7612cff15d9558de0ef49a277ff3776')
out=root/'worker12-prepared-v1';out.mkdir(exist_ok=False)
with tarfile.open(archive,'r:gz')as tar:
    for m in tar.getmembers():
        assert m.isfile()and Path(m.name).name==m.name and m.size<1024**2
        integrity.write_private_new(out/m.name,[tar.extractfile(m).read()])
mp=out/'worker12-launch-manifest-v1.json';sha(mp,'ea028eed16df96444752113597189c0501add92e500841b2b1b65e6acb17baef');manifest=read(mp)
for n,h in manifest['existing_reader_sha256'].items():sha(root/n,h)
for n,r in manifest['files'].items():
    assert Path(n).name==n and n.startswith(('worker12','prepare_worker12','submit_worker12'))
    integrity.write_private_new(root/n,[source_bytes(out/n,sha(out/n,r['sha256']))])
integrity.write_private_new(root/mp.name,[source_bytes(mp,sha(mp))])
proof=dict(complete=True,previous_job='2026153',worker_stopped=True,all_owned_tasks_cleaned=True,exit_kind='natural-idle',
    scheduler_end_time=previous['endTime'],scheduler_query=query,task_status_sha256=statuses,
    worker_log_sha256=sha(root/'worker11.log'),lock_unheld=True,epoch=time.time())
proofpath=root/'worker11-exit-proof-for-worker12.json';integrity.write_json_private(proofpath,proof)
spec=importlib.util.spec_from_file_location('new_plan',root/'prepare_worker12.py')
planner=importlib.util.module_from_spec(spec);spec.loader.exec_module(planner)
plan=planner.plan(str(root/'source-setup-owned-f94'),'f94f27d2a07ff3363bea43c1a3b2ca45277de674',str(root))
plan['wrapper_sha256']={n:sha(root/n)for n in planner.WRAPPERS}
planpath=root/'worker12-plan-v1.json';integrity.write_json_private(planpath,plan)
print(json.dumps(dict(complete=True,submitted=False,queue=plan['queue'],argv=plan['argv'],plan_sha=sha(planpath),
    proof_sha=sha(proofpath),manifest_sha=sha(root/mp.name),submit_entry_sha=sha(root/'submit_worker12_terminal_v2.py'))),flush=True)
