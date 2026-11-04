"""Prepare full ARM HaloV2 tests; queue publication deliberately separate."""
import json
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root));import file_integrity as integrity
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
start=json.loads((root/'worker10-startup.json').read_text());assert start['complete']and start['host']=='cn19486'
aux=root/'aux-halo-v2-760';entry=aux/'arm_halo_v2_qualify.py'
entrysha='d0d910ff0501d6fdb752d1a64ed1aafb934e27aa1d74b5781f8a3071805bfa7d'
manifestsha='8923c17bdd89a9be489e131e5f0cad51eb8372cc0d1a6cda7efb79415ce59c27'
sha(entry,entrysha);sha(aux/'halo-v2-arm-helpers.json',manifestsha)
old=json.loads((root/'campaign-halo-v2/attempts/000-halo-v2-tests/attempt.json').read_text())
assert all(v['status']=='passed'and v['cleanup']['complete']for v in old['stages'].values())
name='148-halo-v2-full-worker10';python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
task=dict(argv=[python,'-u',str(entry),'--root',str(root),'--auxiliary',str(aux),'--scope','full','--state-id',name,
    '--expected-host','cn19486','--expected-entry-sha',entrysha,'--expected-manifest-sha',manifestsha,'--test-attempt','000-halo-v2-tests'],
    cwd=str(root),timeout=4500,environment=dict(LD_LIBRARY_PATH=start['loader_environment']['LD_LIBRARY_PATH'],
        LD_PRELOAD='',LD_DEBUG='',LD_DEBUG_OUTPUT='',PERF_COUNTER_ROOT='',OMP_WAIT_POLICY='',GOMP_SPINCOUNT='',
        LQCD_EXPERIMENT_KUPL_ROOT='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release',
        LQCD_EXPERIMENT_CXX_RUNTIME='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64',
        LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'))
out=root/'prepared-halo148-worker10';out.mkdir(exist_ok=False)
integrity.write_json_private(out/'task.json',task)
integrity.write_json_private(out/'preparation.json',dict(complete=True,prepared_not_queued=True,
    task_sha256=sha(out/'task.json'),source_head='760666c8ac459ef062c749ee7ee9964c99e7c3c8',
    reused_passed_stage_names=list(old['stages']),prior_library_sha256=sha((Path(old['snapshot']['build'])/'liblqcd_cpu.so').resolve()),
    startup_sha256=sha(root/'worker10-startup.json'),minimum_dispatch_remaining_seconds=4590,
    gate='147 terminal and cleaned; same actual parent592/SVE/HBW; unchanged main best; no concurrent numerical task'))
print(json.dumps(dict(prepared=True,task_sha256=sha(out/'task.json'))),flush=True)
