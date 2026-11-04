"""Bind current terminal comparison to a new, unranked retained-best profile."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'aux-solve-profile-v7'))
import file_integrity as integrity
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
def pin(path,expected=None):return dict(path=str(path),sha256=integrity.read_dual(path,expected)['openssl_sha256'])
request=dict(root=str(root),output=str(root/'prepared-solve-profile-v7-143'),
    profile_output=str(root/'solve-profile-worker8-143'),id='143-best-solve-profile-worker8',queue='queue8',
    python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python',
    startup=pin(root/'worker8-startup.json','c54fd907920ddd836941f9b475df1171ac60243c47c53541d2bb4f04b600f826'),
    phase5_state=pin(root/'141-phase5-worker8-v5-state.json'),
    phase5_status=pin(root/'queue8/141-phase5-worker8-v5.status.json'),
    helper_manifest_sha256=pin(root/'aux-solve-profile-v7/solve-profile-v7-files.json',
        '0b8516f8dbcabb3d6e676d8755e6f68908223b05f221e7ba0058659e15f47286')['sha256'])
path=root/'solve-profile-v7-143-request.json'
integrity.write_json_private(path,request)
print(json.dumps(pin(path),indent=2))
