"""Cancel only our exact never-started resource request before changing node."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root));import file_integrity as integrity
spec=importlib.util.spec_from_file_location('scheduler_query',root/'worker8_login_record.py')
login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
job,query=login.query(shutil.which('djob'),'2024986')
assert job['state']=='PENDING'and job['jobName']=='mg-opt-worker9'and job['user']=='nsls_lwb'and job['startTime']=='-'
assert not(root/'worker9-startup.json').exists()and not(root/'worker9-allocation.json').exists()
path=root/'worker9-pending-cancel-intent.json';integrity.write_json_private(path,dict(job=job,query=query,reason='Requested host occupied; move fresh experiment to equivalent idle cn19486',epoch=time.time()))
result=subprocess.run(['dkill','2024986'],capture_output=True,text=True,timeout=25)
integrity.write_json_private(root/'worker9-pending-cancel-result.json',dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,epoch=time.time()))
result.check_returncode();print(result.stdout,flush=True)
