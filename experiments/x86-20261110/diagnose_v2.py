import json, os, socket, subprocess
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/mg-x86-20261110')
S=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/source')
P='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
assert socket.gethostname()=='node5005' and len(os.sched_getaffinity(0))==256
plan=json.loads((S/'profiles/optimization/node5005-833-full12.json').read_text()) if (S/'profiles/optimization/node5005-833-full12.json').exists() else json.loads((R/'plan.json').read_text())
(R/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
lib='/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/campaign/attempts/000-delivery-tests/build/liblqcd_cpu.so'
env=dict(os.environ,PATH=str(Path(P).parent)+':'+os.environ['PATH'],OPENBLAS_NUM_THREADS='1',OMP_PROC_BIND='close')
for k in list(env):
 if k.startswith('NATIVE_') or (k.startswith('LQCD_') and not k.startswith('LQCD_OPT_')):env.pop(k)
argv=[P,str(S/'tools/run_numa.py'),'--ranks-per-numa','2','--threads','16','--',P,'-u',str(S/'tools/optimization/profile_full12.py'),
 '--benchmark',str(S/'tools/optimization/bench_full12.py'),'--profile-output',str(R/'perf-v2'),'--diagnostic',
 '--fixture','/public2/home/lwb_720/.cache/mg-opt-20261103/fixture-ls-canonical','--plan',str(R/'plan.json'),
 '--library',lib,'--backend','x86','--output',str(R/'diagnostic-v2'),'--allocation','node5005-20261110',
 '--snapshot-sha','833f8732f6b06e370074efbb610fc7a85fe11a46','--repeats','3']
with (R/'diagnostic-v2.log').open('x') as f:
 r=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=650)
assert r.returncode==0,r.returncode
