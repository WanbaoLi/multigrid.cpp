import json,sys
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
sha=lambda p,e=None:integrity.read_dual(p,e)['openssl_sha256']
pin=lambda p,e=None:dict(path=str(p),sha256=sha(p,e))
startup=root/'worker11-startup.json';s=json.loads(source_bytes(startup,sha(startup,'d1682f573747fcdc12003b369a83b64c3a935e7683ae45038e536954a979c859')))
assert s['complete']and s['host']=='cn19486'and s['allocation']=='mg-opt-20261103-worker11'
request=dict(root=str(root),output=str(root/'prepared-profile155-worker11'),profile_output=str(root/'solve-profile-worker11-155'),id='155-best-solve-profile-worker11',queue='queue11',python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',
 startup=pin(startup),predecessor_state=pin(root/'v2-w10v5-state.json'),predecessor_status=pin(root/'queue10/154-halo-v2-ordinary-remainder-worker10.status.json','7d908161fd40c5444297bf5cddd7da66dba2a340c1e606f6e9934e81ff740546'),
 predecessor_startup=pin(root/'worker10-startup.json','f3a40ea0e1185e51c0e7e63750ea18c9b0dae9c489003f280ebef739f59a84c2'),helper_manifest_sha256='0b8516f8dbcabb3d6e676d8755e6f68908223b05f221e7ba0058659e15f47286',retry_of='150-best-solve-profile-worker10')
path=root/'profile155-worker11-request.json';integrity.write_json_private(path,request);print(json.dumps(pin(path)),flush=True)
