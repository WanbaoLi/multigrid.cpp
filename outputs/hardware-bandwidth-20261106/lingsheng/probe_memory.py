#!/usr/bin/env python3
"""Record NUMA/allowed topology and independently verify KUPL HBW locations."""
import ctypes
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

output = Path(sys.argv[1])
sdk = sys.argv[2] if len(sys.argv)>2 else None
output.mkdir(parents=True,exist_ok=True)

def cpus(text):
    result=[]
    for s in text.strip().split(','):
        if s:
            e=list(map(int,s.split('-')))
            result.extend(range(e[0],e[-1]+1))
    return result

def command(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    return dict(command=args,returncode=p.returncode,output=p.stdout)

nodes=[]
for path in sorted(Path('/sys/devices/system/node').glob('node[0-9]*'),key=lambda p:int(p.name[4:])):
    meminfo=(path/'meminfo').read_text()
    total=int(re.search(r'MemTotal:\s+(\d+)',meminfo).group(1))*1024
    free=int(re.search(r'MemFree:\s+(\d+)',meminfo).group(1))*1024
    nodes.append(dict(node=int(path.name[4:]),cpus=cpus((path/'cpulist').read_text()),
                      distances=list(map(int,(path/'distance').read_text().split())),
                      memory_total_bytes=total,memory_free_bytes=free,meminfo=meminfo))
allowed=sorted(os.sched_getaffinity(0))
status=Path('/proc/self/status').read_text()
mems=cpus(re.search(r'Mems_allowed_list:\s*(.*)',status).group(1))
data=dict(hostname=platform.node(),allowed_cpus=allowed,allowed_mems=mems,nodes=nodes,
          lscpu=command(['lscpu','-J']),numactl=command(['numactl','-H']),
          dmi=command(['dmidecode','--type','17']),load=list(os.getloadavg()),
          cpuinfo=Path('/proc/cpuinfo').read_text().split('\n\n')[0],
          proc_meminfo=Path('/proc/meminfo').read_text(),kupl=None)
if sdk:
    lib=ctypes.CDLL(sdk,mode=ctypes.RTLD_GLOBAL)
    lib.kupl_hbw_check_available.restype=ctypes.c_int
    lib.kupl_hbw_malloc.argtypes=[ctypes.c_size_t]
    lib.kupl_hbw_malloc.restype=ctypes.c_void_p
    lib.kupl_hbw_verify.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
    lib.kupl_hbw_verify.restype=ctypes.c_int
    lib.kupl_hbw_free.argtypes=[ctypes.c_void_p]
    libc=ctypes.CDLL('libnuma.so.1',use_errno=True)
    libc.numa_move_pages.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.c_int]
    oldaff=set(allowed)
    samples=[]
    for node in nodes:
        local=sorted(oldaff.intersection(node['cpus']))
        if not local:
            continue
        os.sched_setaffinity(0,{local[0]})
        count=8<<20
        pointer=lib.kupl_hbw_malloc(count)
        r=dict(cpu_node=node['node'],cpu=local[0],allocated=bool(pointer))
        if pointer:
            ctypes.memset(pointer,7,count)
            r['sdk_verify']=lib.kupl_hbw_verify(pointer,count,0)
            page=os.sysconf('SC_PAGE_SIZE')
            base=pointer//page*page
            addresses=(ctypes.c_void_p*32)(*[base+i*(count//32//page)*page for i in range(32)])
            residence=(ctypes.c_int*32)(*([-999]*32))
            ctypes.set_errno(0)
            rc=libc.numa_move_pages(0,32,addresses,None,residence,0)
            r.update(move_pages_rc=rc,move_pages_errno=ctypes.get_errno(),sampled_nodes=list(residence))
            r['numa_maps_candidates']=[s for s in Path('/proc/self/numa_maps').read_text().splitlines()
                                       if s.startswith(f'{base:x} ')]
            lib.kupl_hbw_free(pointer)
        samples.append(r)
    os.sched_setaffinity(0,oldaff)
    data['kupl']=dict(library=sdk,available=lib.kupl_hbw_check_available(),samples=samples)
(output/'memory-topology.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(hostname=data['hostname'],cpus=len(allowed),mems=mems,
                     memory_nodes=[(n['node'],len(n['cpus']),n['memory_total_bytes']) for n in nodes],
                     kupl=data['kupl']),indent=2))
