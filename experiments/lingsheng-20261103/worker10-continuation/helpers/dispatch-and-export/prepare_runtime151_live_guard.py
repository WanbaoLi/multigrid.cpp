"""New task revision adds live-parent proof; original prepared files untouched."""
import json
from pathlib import Path
import subprocess
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-runtime-confirm-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
name='151-runtime-confirm-worker10-v7';q=root/'queue10'
assert not list(q.glob(name+'.*'))and not list(q.glob('*.running.json'))and not list(q.glob('*.ready.json'))
task=read(root/'prepared-runtime151-worker10/task.json','566d8386dcb41869b03dfce7986813c9515fd5e2074b437a360a311e28d2611d')
argv=task['argv'];entry_at=argv.index('--entry')+1;old=Path(argv[entry_at]);oldsha=argv[argv.index('--entry-sha')+1]
assert old.name=='runtime_confirm_scope_v7.py';sha(old,oldsha)
guard=root/'worker10_live_parent_guard_v1.py';argv[entry_at]=str(guard);argv[argv.index('--entry-sha')+1]=sha(guard)
at=argv.index('--contract');argv.extend(['--original-entry-sha',oldsha])
path=root/'prepared-runtime151-worker10/task-live-guard-v2.json';integrity.write_json_private(path,task)
failure=dict(complete=True,read_only=True,argv=['djob','-J','-l','2025061'],epoch=time.time())
try:
    result=subprocess.run(failure['argv'],capture_output=True,text=True,timeout=6)
    failure.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
except subprocess.TimeoutExpired as exc:
    failure.update(timeout_seconds=6,error='TimeoutExpired',stdout=(exc.stdout or b'').decode()if isinstance(exc.stdout,bytes)else exc.stdout,
        stderr=(exc.stderr or b'').decode()if isinstance(exc.stderr,bytes)else exc.stderr)
integrity.write_json_private(root/'runtime151-control-plane-query-evidence.json',failure)
print(json.dumps(dict(prepared_not_queued=True,new_task_sha256=sha(path),original_task_unchanged=True,
    guard_sha256=sha(guard),scheduler_query_evidence_sha256=sha(root/'runtime151-control-plane-query-evidence.json'))),flush=True)
