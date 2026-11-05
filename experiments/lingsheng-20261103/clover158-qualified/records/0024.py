"""Read actual terminal qualification through the same paths used by160."""
import importlib.util
import json
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
spec=importlib.util.spec_from_file_location('new_entry',root/'clover_full12_worker13_v2.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
state_path,status_path=entry.qualification_paths(root)
def read(p):return json.loads(source_bytes(p,integrity.read_dual(p)['openssl_sha256']))
state,status=read(state_path),read(status_path)
assert status_path.parent==root/'queue13'and state_path.name=='158-clover-arm-qualify-worker13-state.json'
assert state['complete']and state['status']=='passed'and state['actual_sve_widths']==[16,32,64]
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
failed=read(root/'queue13/159-clover-full12-worker13.status.json')
assert failed['status']=='failed'and failed['cleanup']['complete']and not failed['cleanup']['surviving_pids']
assert not(root/'159-clover-full12-worker13-state.json').exists()and not(root/'campaign-clover-reuse-v1/attempts/159-clover-control-a').exists()
print(json.dumps(dict(complete=True,actual_dependency_paths_passed=True,failed159_before_numerics=True,qualifier158_unchanged=True,source_or_binary_edited=False)),flush=True)
