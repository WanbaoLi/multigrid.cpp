"""Bind exact new allocation and old diagnostic without importing old timings."""
import json
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-runtime-worker10-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def pin(path,expected=None):return dict(path=str(path),sha256=integrity.read_dual(path,expected)['openssl_sha256'])
def read(path):return json.loads(source_bytes(path,pin(path)['sha256']))
statuspath=root/'queue10/146-old-runtime-capture-smoke-worker10.status.json'
status=read(statuspath);result=read(root/'runtime-capture-old-smoke146/result.json')
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert result['complete']and result['passed']and result['ranks']==16
request=dict(root=str(root),output=str(root/'prepared-runtime147-worker10'),id='147-runtime-only-worker10-v6',prefix='p5w10v6',queue='queue10',
    python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',
    startup=pin(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2'),
    failed_state=pin(root/'141-phase5-worker8-v5-state.json'),failed_status=pin(root/'queue8/141-phase5-worker8-v5.status.json'),
    profile_state=pin(root/'143-best-solve-profile-worker8-state.json'),profile_status=pin(root/'queue8/143-best-solve-profile-worker8.status.json'),
    profile_wrapper=pin(root/'solve-profile-worker8-143/143-best-solve-profile-worker8/wrapper-v7-summary.json'),
    runtime_manifest=pin(root/'runtime-shim-manifest-worker10-v3.json'),
    helper_manifest_sha256='c6fd07bfef0f1328cf5a0c15b4fffaa147aec6673c787edac2cb4147753b0977',
    smoke_status=pin(statuspath),smoke_result=pin(root/'runtime-capture-old-smoke146/result.json'),
    smoke_maps=pin(root/'runtime-capture-old-smoke146/maps.json',result['maps_sha256']),
    historical_profile_scope='hotspot selection only; all five ordinary cases fresh current allocation')
path=root/'runtime147-worker10-request.json';integrity.write_json_private(path,request);print(json.dumps(pin(path)),flush=True)
