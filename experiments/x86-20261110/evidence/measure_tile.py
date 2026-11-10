import json, os, socket, subprocess, sys
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/mg-x86-20261110');OLD=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/source')
P='/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python'
mode=sys.argv[1];assert socket.gethostname()=='node5005'
assert (R/'tile-build-passed').exists()
source=OLD if mode.startswith('old') else R/'source-tile'
lib=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/campaign/attempts/000-delivery-tests/build/liblqcd_cpu.so') if mode.startswith('old') else R/'build-tile/liblqcd_cpu.so'
plan=json.loads((R/'plan.json').read_text());plan['context_environment']['LQCD_X86_CLOVER_REGISTERS']=mode[-1] if mode.startswith('new') else '0'
plan['context_environment']['LQCD_X86_SIGNED_PROJECTORS']=mode[-1] if mode.startswith('proj') else '0'
plan['context_environment']['LQCD_X86_RHS_SITE_TILE']=mode[4:] if mode.startswith('tile') else '0'
pl=R/(mode+'-plan.json');pl.write_text(json.dumps(plan,indent=2)+'\n')
env=dict(os.environ,PATH=str(Path(P).parent)+':'+os.environ['PATH'],OPENBLAS_NUM_THREADS='1',OMP_PROC_BIND='close')
for k in list(env):
 if k.startswith('NATIVE_') or (k.startswith('LQCD_') and not k.startswith('LQCD_OPT_')):env.pop(k)
argv=[P,str(source/'tools/run_numa.py'),'--ranks-per-numa','2','--threads','16','--',P,'-u',str(source/'tools/optimization/bench_full12.py'),
 '--fixture','/public2/home/lwb_720/.cache/mg-opt-20261103/fixture-ls-canonical','--plan',str(pl),'--library',str(lib),'--backend','x86',
 '--output',str(R/mode),'--allocation','node5005-20261110','--snapshot-sha',subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),'--repeats','3',
 '--reference-propagator','/public2/home/lwb_720/.cache/mg-opt-20261103/campaign-canonical/attempts/001-canonical-profile-t12/measurements/full12/propagator.npy']
# Use the exact established reference path rather than assuming its directory.
parent=json.loads(Path('/public2/home/lwb_720/.cache/mg-opt-20261103/campaign-canonical/attempts/001-canonical-profile-t12/report.json').read_text())
argv[-1]=parent['reference_propagator']
with(R/(mode+'.log')).open('x')as f:subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=650,check=True)
ref='/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid'
with(R/(mode+'-verify.log')).open('x')as f:
 subprocess.run([P,str(source/'tools/optimization/bench_full12.py'),'--verify',str(R/mode/'full12'),'--reference',ref,'--extractor',str(Path(ref).with_name('extract_columns'))],env=dict(env,OMP_NUM_THREADS='4'),stdout=f,stderr=subprocess.STDOUT,timeout=400,check=True)
