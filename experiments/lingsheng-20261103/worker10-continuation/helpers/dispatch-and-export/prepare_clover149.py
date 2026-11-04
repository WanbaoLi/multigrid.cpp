"""Prepare but never queue the new ARM Clover source qualification."""
import json
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-arm-clover-v1';sys.path.insert(0,str(aux))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
manifest=read(aux/'arm-clover-v1-files.json','1836042fc66ce0be549713432d4a007af4e5a148d1c07dd2894ca1eb7d360e47')
pins=[dict(path=str(aux/name),sha256=sha(aux/name,expected))for name,expected in manifest['files'].items()]
startup=root/'worker10-startup.json';start=read(startup,'f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2')
name='149-clover-arm-qualify-worker10';out=root/'prepared-clover149-worker10';out.mkdir(exist_ok=False)
plan=dict(complete=True,prepared_not_queued=True,id=name,scope='arm-clover-full-qualification-v1',
    source_head='861613c703117c6b5b671e245a7142e217b09501',source=str(root/'source-clover-reuse-861'),
    startup=dict(path=str(startup),sha256=sha(startup)),dependency_status=str(root/'queue10/147-runtime-only-worker10-v6.status.json'),
    pinned_files=pins,performance_ranked=False,physical_full12=False)
integrity.write_json_private(out/'plan.json',plan)
task=dict(argv=['/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python','-u',str(aux/'arm_clover_qualify_v1.py'),
    '--plan',str(out/'plan.json'),'--plan-sha',sha(out/'plan.json')],cwd=str(aux),timeout=3600,
    environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',
        PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT=''))
integrity.write_json_private(out/'task.json',task)
print(json.dumps(dict(prepared=True,plan_sha256=sha(out/'plan.json'),task_sha256=sha(out/'task.json'),not_queued=True)),flush=True)
