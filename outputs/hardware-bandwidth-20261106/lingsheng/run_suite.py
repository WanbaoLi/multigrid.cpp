#!/usr/bin/env python3
"""Compare verified local NUMA memory with identical logical stream kernels."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess

def capture(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)

def ids(text):
    result=[]
    for p in text.strip().split(','):
        if p:
            a=list(map(int,p.split('-'))); result.extend(range(a[0],a[-1]+1))
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--compiler',required=True)
    ap.add_argument('--kupl-lib')
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    allowed=set(os.sched_getaffinity(0))
    mems=ids(re.search(r'Mems_allowed_list:\s*(.*)',Path('/proc/self/status').read_text()).group(1))
    nodes=[]
    for path in sorted(Path('/sys/devices/system/node').glob('node[0-9]*'),key=lambda p:int(p.name[4:])):
        cpus=sorted(allowed.intersection(ids((path/'cpulist').read_text())))
        physical=[]; seen=set()
        for cpu in cpus:
            identity=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list').read_text()
            if identity not in seen: physical.append(cpu); seen.add(identity)
        info=(path/'meminfo').read_text()
        nodes.append(dict(node=int(path.name[4:]),cpus=physical,
                          distance=list(map(int,(path/'distance').read_text().split())),meminfo=info))
    groups=[n for n in nodes if n['cpus'] and n['node'] in mems]
    candidates=[n for n in nodes if not n['cpus'] and n['node'] in mems
                and not (Path('/sys/devices/system/node')/f"node{n['node']}"/'cpulist').read_text().strip()]
    assert len(groups) in (8,16),len(groups)
    mib=8192//len(groups)
    assert mib*len(groups)==8192
    mapping={n['node']:n['node'] for n in groups}
    mappings={'ddr':mapping}
    if args.kupl_lib:
        assert len(candidates)==len(groups)
        available={n['node'] for n in candidates}; mapping={}
        for n in groups:
            target=min(available,key=lambda v:(n['distance'][v],v))
            mapping[n['node']]=target; available.remove(target)
        mappings['hbw']=mapping
    source=Path(__file__).with_name('bandwidth_bench.cpp')
    binary=args.output/'bandwidth_bench'
    meta=dict(hostname=platform.node(),allowed_cpus=sorted(allowed),allowed_mems=mems,nodes=nodes,
              mappings=mappings,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              load_before=list(os.getloadavg()),lscpu=capture(['lscpu','-J']),
              compiler=capture([args.compiler,'--version']),
              proc_meminfo=Path('/proc/meminfo').read_text())
    if args.kupl_lib:
        meta['kupl']=dict(path=args.kupl_lib,sha256=hashlib.sha256(Path(args.kupl_lib).read_bytes()).hexdigest())
    meta['compile']=capture([args.compiler,'-O3','-std=c++17','-pthread','-march=native',
                             str(source),'-ldl','-o',str(binary)])
    def save_meta(): (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    save_meta()
    if meta['compile']['returncode']: raise RuntimeError(meta['compile'])
    meta['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    meta['ldd']=capture(['ldd',str(binary)])
    dis=capture(['/usr/bin/objdump','-d','-C',str(binary)])
    (args.output/'disassembly.txt').write_text(dis['stdout'])
    meta['objdump_returncode']=dis['returncode']; save_meta()
    results=[]
    def case(kind,threads,per_array_mib,label):
        plan=args.output/f'{label}.plan'
        rows=[]
        for n in groups:
            cpus=n['cpus'][:threads] if threads else n['cpus']
            rows.extend(f"{n['node']} {cpu} {mappings[kind][n['node']]}" for cpu in cpus)
        plan.write_text('\n'.join(rows)+'\n')
        cmd=[str(binary),'--plan',str(plan),'--mib-per-array-per-group',str(per_array_mib),
             '--passes','16','--repeats','5']
        if args.kupl_lib: cmd+=['--kupl-lib',args.kupl_lib]
        before=list(os.getloadavg())
        run=capture(cmd)
        (args.output/f'{label}.stdout').write_text(run['stdout'])
        (args.output/f'{label}.stderr').write_text(run['stderr'])
        if run['returncode']: raise RuntimeError(f'{label}: {run}')
        d=json.loads(run['stdout'])
        assert d['status']=='PASS'
        if args.kupl_lib:
            expected=1 if kind=='hbw' else 0
            assert all(a['sdk_verify_before']==expected and a['sdk_verify_after']==expected
                       for g in d['placement'] for a in g['arrays']),f'{label}: SDK class mismatch'
        result=dict(label=label,memory_kind=kind,threads_per_group=threads or len(groups[0]['cpus']),
                    array_mib=per_array_mib,load_before=before,load_after=list(os.getloadavg()),benchmark=d)
        results.append(result)
        (args.output/f'{label}.json').write_text(json.dumps(d,indent=2)+'\n')
        (args.output/'suite.json').write_text(json.dumps(results,indent=2)+'\n')
        print('CASE_PASS',label,d['threads'],[(k['kernel'],round(k['median_gb_per_second'],3)) for k in d['kernels']],flush=True)
        return result
    for kind in mappings:
        candidates=[]
        for threads in (8,16,0):
            candidates.append(case(kind,threads,mib,f'{kind}-threads{threads or "all"}-size{mib}'))
        best=max(candidates,key=lambda r:next(k['median_gb_per_second'] for k in r['benchmark']['kernels'] if k['kernel']=='triad'))
        case(kind,best['threads_per_group'],2*mib,f'{kind}-threads{best["threads_per_group"]}-size{2*mib}')
    meta.update(status='PASS',load_after=list(os.getloadavg()))
    save_meta()
    print('SUITE_PASS',flush=True)

if __name__=='__main__':main()
