import ctypes
import json
import mmap
import os
from pathlib import Path
import sys

old=ctypes.CDLL(sys.argv[1],mode=ctypes.RTLD_LOCAL)
new=ctypes.CDLL(sys.argv[2],mode=ctypes.RTLD_LOCAL)
for lib in (old,new):
    lib.kupl_hbw_verify.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
    lib.kupl_hbw_verify.restype=ctypes.c_int
numa=ctypes.CDLL('libnuma.so.1',use_errno=True)
numa.mbind.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.POINTER(ctypes.c_ulong),ctypes.c_ulong,ctypes.c_uint]
numa.mbind.restype=ctypes.c_long
numa.numa_move_pages.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.c_int]
data=[]
for target in (0,16,28,30,31):
    buf=mmap.mmap(-1,4<<20,flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS)
    pointer=ctypes.addressof(ctypes.c_char.from_buffer(buf))
    mask=(ctypes.c_ulong*1)(1<<target)
    ctypes.set_errno(0)
    rc=numa.mbind(pointer,len(buf),2,mask,64,0)
    assert rc==0,(target,ctypes.get_errno())
    ctypes.memset(pointer,1,len(buf))
    addresses=(ctypes.c_void_p*2)(pointer,pointer+len(buf)-4096)
    residence=(ctypes.c_int*2)(-1,-1)
    query=numa.numa_move_pages(0,2,addresses,None,residence,0)
    data.append(dict(target=target,old_verify=old.kupl_hbw_verify(pointer,len(buf),0),
                     new_verify=new.kupl_hbw_verify(pointer,len(buf),0),move_pages=query,nodes=list(residence)))
    buf.close()
Path(sys.argv[3]).write_text(json.dumps(dict(hostname=os.uname().nodename,classes=data),indent=2)+'\n')
print(json.dumps(data),flush=True)
