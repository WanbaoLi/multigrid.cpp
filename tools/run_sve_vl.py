"""Run one standalone SVE numerical test with an explicitly inherited Linux VL."""
import argparse
import ctypes
import json
import os
import platform

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bytes',type=int,choices=[16,32,64],required=True)
parser.add_argument('command',nargs=argparse.REMAINDER)
args=parser.parse_args()
command=args.command[1:] if args.command[:1]==['--'] else args.command
if platform.system()!='Linux' or platform.machine().lower() not in ['aarch64','arm64'] or not command:
    parser.error('Linux AArch64 and an explicit command are required')
# Constants verified against both site /usr/include/linux/prctl.h copies.
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
libc.prctl.restype=ctypes.c_int
result=libc.prctl(50,ctypes.c_ulong(args.bytes|(1<<17)),0,0,0)
if result<0:
    error=ctypes.get_errno()
    raise OSError(error,os.strerror(error))
actual=libc.prctl(51,0,0,0,0)
if actual<0 or actual&0xffff!=args.bytes or not actual&(1<<17):
    raise RuntimeError('Kernel did not establish the exact inherited SVE vector length')
print(json.dumps(dict(requested_bytes=args.bytes,actual_bytes=actual&0xffff,
                      inherit_exec=bool(actual&(1<<17)),command=command)),flush=True)
os.execvpe(command[0],command,os.environ)
