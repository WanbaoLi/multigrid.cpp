"""Refresh component evidence on current exact833 source; no full12 ranking."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
root=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105');sys.path.insert(0,str(root))
import file_integrity as integrity
sha=lambda p:integrity.read_dual(p)['openssl_sha256']
assert socket.gethostname()=='node5005'and os.environ.get('LQCD_OPT_TASK_ID')and len(os.sched_getaffinity(0))==256
source=root/'source';out=root/'component-probe-current-v1';out.mkdir(exist_ok=False)
assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()=='833f8732f6b06e370074efbb610fc7a85fe11a46'
compiler='/public2/home/lwb_720/miniconda3/bin/g++'
command=[compiler,'-O3','-std=c++17','-march=native','-mtune=native','-fopenmp','-I'+str(source),str(root/'cpu_bench_current.cpp'),'-o',str(out/'probe')]
with(out/'compile.log').open('xb')as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120)
assert r.returncode==0
sys.path.insert(0,str(source/'tools'));from run_numa import discover_nodes
nodes=discover_nodes();assert len(nodes)==8 and all(len(c)==32 for c in nodes.values())
rows=[]
for count in(1,32,128,256):
    cpus=nodes[min(nodes)][:count]if count<=32 else [c for n in sorted(nodes)for c in nodes[n][:count//8]]
    assert len(cpus)==count
    env=dict(os.environ,OMP_NUM_THREADS=str(count),OMP_DYNAMIC='FALSE',OMP_PROC_BIND='close',OMP_PLACES=','.join('{%d}'%c for c in cpus),LQCD_ARM_SVE_REUSE='1')
    command=['taskset','-c',','.join(map(str,cpus)),str(out/'probe'),str(count)]
    with(out/(str(count)+'.json')).open('xb')as log:r=subprocess.run(command,env=env,stdout=log,stderr=subprocess.PIPE,timeout=120)
    (out/(str(count)+'.stderr')).write_bytes(r.stderr);assert r.returncode==0
    row=json.loads((out/(str(count)+'.json')).read_text());row['cpus']=cpus;row['load_average_after']=list(os.getloadavg());rows.append(row)
result=dict(complete=True,performance_ranked=False,full12_metric=False,source_head='833f8732f6b06e370074efbb610fc7a85fe11a46',source_sha256=sha(root/'cpu_bench_current.cpp'),
    compile_argv=command,compiler=compiler,host=socket.gethostname(),rows=rows,direct_ssh_not_scheduler_exclusive=True,
    limitation='Unpacked component entry, current source, logical triad traffic only. No attribution to theoretical peak or physical memory-controller bandwidth; no single-core complete propagator claim.')
integrity.write_json_private(out/'result.json',result);print(json.dumps(dict(complete=True,full12_metric=False,rows=rows)),flush=True)
