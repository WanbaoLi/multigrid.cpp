"""Prepare current-best profile only after the new runtime bracket closes."""
import json
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def pin(path,expected=None):return dict(path=str(path),sha256=integrity.read_dual(path,expected)['openssl_sha256'])
def read(path):return json.loads(source_bytes(path,pin(path)['sha256']))
state=root/'151-runtime-confirm-worker10-v7-state.json';status=root/'queue10/151-runtime-confirm-worker10-v7.status.json'
phase=read(state);task=read(status)
assert phase['complete']and phase['status']=='complete'and task['status']=='passed'and task['cleanup']['complete']and not task['cleanup']['surviving_pids']
request=dict(root=str(root),output=str(root/'prepared-profile150-worker10'),profile_output=str(root/'solve-profile-worker10-150'),
    id='150-best-solve-profile-worker10',queue='queue10',python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',
    startup=pin(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2'),
    phase5_state=pin(state),phase5_status=pin(status),helper_manifest_sha256='0b8516f8dbcabb3d6e676d8755e6f68908223b05f221e7ba0058659e15f47286')
path=root/'profile150-worker10-request.json';integrity.write_json_private(path,request);print(json.dumps(pin(path)),flush=True)
