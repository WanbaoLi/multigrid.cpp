"""Pin concrete prepared argv then invoke the verified successor submitter."""
import json
from pathlib import Path
import subprocess
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root))
import file_integrity as integrity
def sha(path):return integrity.read_dual(path)['openssl_sha256']
plan=root/'worker10-reviewed-submit-plan.json';manifest=root/'worker10-launch-manifest.json';proof=root/'worker8-natural-exit-proof-for-worker10.json'
import importlib.util,shutil
spec=importlib.util.spec_from_file_location('pending_query',root/'worker8_login_record.py');login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
old,_=login.query(shutil.which('djob'),'2024986')
assert old['state']=='FAILED' and old['user']=='nsls_lwb' and old['jobName']=='mg-opt-worker9' and old['startTime']=='-'
argv=['python3',str(root/'submit_worker10_terminal_v2.py'),'--root',str(root),'--plan',str(plan),'--plan-sha',sha(plan),
    '--wrapper-manifest',str(manifest),'--wrapper-manifest-sha',sha(manifest),'--stop-proof',str(proof),'--stop-proof-sha',sha(proof)]
if '--execute'in sys.argv:argv+=['--execute','--expected-entry-sha',sha(root/'submit_worker10_terminal_v2.py')]
subprocess.run(argv,check=True)
