"""After ordinary160 only: diagnose source reuse/cache/codegen without ranking."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(p):return integrity.read_dual(p)['openssl_sha256']
def read(p):return json.loads(source_bytes(p,sha(p)))
assert socket.gethostname()=='cn19480'and os.environ.get('LQCD_OPT_ALLOCATION')=='mg-opt-20261103-worker13'and os.environ.get('LQCD_OPT_TASK_ID')
assert len(os.sched_getaffinity(0))==592
prior=read(root/'queue13/160-clover-full12-worker13.status.json');assert prior['status']=='passed'and prior['cleanup']['complete']and not prior['cleanup']['surviving_pids']
qualified=read(root/'163-clover-pair-qualify-worker13-state.json');source=Path(qualified['snapshot']['source']);build=Path(qualified['snapshot']['build'])
assert qualified['complete']and qualified['status']=='passed'and qualified['source_head']=='067b28bd787a6428400e23d683596cd2120c5f6a'
assert qualified['actual_sve_widths']==[16,32,64]
out=root/'clover-micro-164-v2';out.mkdir(exist_ok=False)
database=json.loads((build/'compile_commands.json').read_text());target=(source/'src/solver/native/fine_operator.cpp').resolve()
row=next(v for v in database if Path(v['file']).resolve()==target)
import shlex
argv=row.get('arguments')or shlex.split(row['command']);cache=(build/'CMakeCache.txt').read_text()
compiler=next(l.split('=',1)[1]for l in cache.splitlines()if l.startswith('CMAKE_CXX_COMPILER:FILEPATH='));slot=next(i for i,v in enumerate(argv)if Path(v).resolve()==Path(compiler).resolve())
flags=[];skip=False
for v in argv[slot+1:]:
    if skip:skip=False;continue
    if v in('-o','-MF','-MT','-MQ'):skip=True;continue
    if v in('-c','-MD','-MMD')or Path(v).resolve()==target:continue
    flags.append(v)
command=[compiler,*flags,'-I'+str(source/'src/backends/arm'),str(root/'clover_reuse_micro.cpp'),'-o',str(out/'micro')]
compile_argv=list(command)
with(out/'compile.log').open('xb')as log:r=subprocess.run(command,cwd=build,stdout=log,stderr=subprocess.STDOUT,timeout=90)
assert r.returncode==0
cpu=read(root/'worker13-startup.json')['before_worker_exec_parent_state']['cpus'][0]
rows=[]
for sites in(432,864):
    for label,mode in(('off-a',0),('on',1),('off-b',0)):
        env=dict(os.environ,LQCD_ARM_SVE='1',LQCD_ARM_SVE_CLOVER_REUSE=str(mode),OMP_NUM_THREADS='1')
        command=['taskset','-c',str(cpu),str(out/'micro'),str(sites),'30000']
        r=subprocess.run(command,capture_output=True,text=True,env=env,timeout=90);(out/(str(sites)+'-'+label+'.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==0
        actual=[json.loads(v)for v in re.findall(r'CLOVER_MICRO (\{[^\n]+\})',r.stdout)]
        assert len(actual)==5 and all(v['vector_bytes']==64 and v['full12_metric']is False and v['max_abs_oracle_error']<=2e-5 for v in actual)
        rows.append(dict(sites=sites,mode=mode,label=label,results=actual,argv=command))
integrity.write_json_private(out/'result.json',dict(complete=True,status='passed',host=socket.gethostname(),allocation=os.environ['LQCD_OPT_ALLOCATION'],performance_ranked=False,full12_metric=False,
    purpose='Attribute actual whole-solve Clover result to local reuse/cache behavior; same native compilation flags, one pinned core, off/on/off controls',
    source_manifest_sha256=qualified['snapshot']['source_manifest_sha256'],prior160_state_sha256=sha(root/'160-clover-full12-worker13-state.json'),
    cpu=cpu,rows=rows,compile_argv=compile_argv))
print(json.dumps(dict(complete=True,results=str(out/'result.json'),full12_metric=False)),flush=True)
