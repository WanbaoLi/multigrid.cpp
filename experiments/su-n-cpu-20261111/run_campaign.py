import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
R=Path('/public2/home/lwb_720/.cache/sun-cpu-20261111-v2')
assert socket.gethostname()=='node5005'
def run(name,argv,timeout=600,env=None):
 record=dict(name=name,argv=argv,started=time.time(),status='running')
 (R/(name+'.status.json')).write_text(json.dumps(record))
 with(R/(name+'.log')).open('x')as log:
  try:
   result=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
   record.update(returncode=result.returncode,status='passed' if result.returncode==0 else 'failed')
  except subprocess.TimeoutExpired:
   record['status']='timeout'
 record['ended']=time.time();(R/(name+'.status.json')).write_text(json.dumps(record,indent=2))
 print(name,record['status'],flush=True)
 assert record['status']=='passed',name
env=dict(os.environ,PATH='/public2/home/lwb_720/miniconda3/envs/pyquda/bin:/public2/home/lwb_720/miniconda3/bin:'+os.environ['PATH'],OMP_PLACES='cores',OMP_PROC_BIND='spread',OPENBLAS_NUM_THREADS='1')
run('configure',['cmake','-S',str(R),'-B',str(R/'build'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=/public2/home/lwb_720/miniconda3/bin/g++'],env=env)
run('build',['cmake','--build',str(R/'build'),'-j8'],env=env)
run('ctest',['ctest','--test-dir',str(R/'build'),'--output-on-failure'],env=env)
run('assemble',[sys.executable,str(R/'assemble_gauge.py'),'/public2/home/lwb_720/.cache/mg-opt-20261103/fixture-ls-canonical',str(R/'gauge-su3.bin')],env=env)
for n in (3,4,6):
 run(f'n{n}-random-operator',['numactl','--interleave=all',str(R/'build/sun_cpu'),str(n),'12','64','3','12','12','12','16','random','operator'],env=env)
 run(f'n{n}-random-solve',['numactl','--interleave=all',str(R/'build/sun_cpu'),str(n),'12','64','2','8','8','8','8','random','solve'],env=env)
run('real-su3-operator',['numactl','--interleave=all',str(R/'build/sun_cpu'),'3','12','256','3','24','24','24','64',str(R/'gauge-su3.bin'),'operator','-.277'],env=env)
run('real-su3-propagator',['numactl','--interleave=all',str(R/'build/sun_cpu'),'3','12','256','2','24','24','24','64',str(R/'gauge-su3.bin'),'propagator','-.277',str(R/'prop')],timeout=1800,env=env)
(R/'complete.json').write_text(json.dumps(dict(complete=True,source_sha256=hashlib.sha256((R/'main.cpp').read_bytes()).hexdigest())))
