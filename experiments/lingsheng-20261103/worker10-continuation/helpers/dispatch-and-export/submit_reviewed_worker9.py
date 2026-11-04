"""Pin concrete prepared argv then invoke the verified successor submitter."""
import json
from pathlib import Path
import subprocess
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root))
import file_integrity as integrity
def sha(path):return integrity.read_dual(path)['openssl_sha256']
plan=root/'worker9-reviewed-submit-plan.json';manifest=root/'worker9-launch-manifest.json';proof=root/'worker8-natural-exit-proof-for-worker9.json'
argv=['python3',str(root/'submit_worker9_terminal_v2.py'),'--root',str(root),'--plan',str(plan),'--plan-sha',sha(plan),
    '--wrapper-manifest',str(manifest),'--wrapper-manifest-sha',sha(manifest),'--stop-proof',str(proof),'--stop-proof-sha',sha(proof)]
if '--execute'in sys.argv:argv+=['--execute','--expected-entry-sha',sha(root/'submit_worker9_terminal_v2.py')]
subprocess.run(argv,check=True)
