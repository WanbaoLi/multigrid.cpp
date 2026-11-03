#!/usr/bin/env python3
"""Audit compiled coarse SVE support or verify per-rank VL after inherited exec.

No new solver mathematics: the MPI mode runs the existing independent12-column
oracle unchanged in the checked process. Invoked by phase6 only on compute nodes.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import shlex
import subprocess
import sys


def compiler_audit(build, source):
    cache=(build/'CMakeCache.txt').read_text()
    compiler=next(line.split('=',1)[1] for line in cache.splitlines()
                  if line.startswith('CMAKE_CXX_COMPILER:FILEPATH='))
    database=json.loads((build/'compile_commands.json').read_text())
    target=(source/'src/solver/native/batched_coarse_operator.cpp').resolve()
    entry=next(row for row in database if Path(row['file']).resolve()==target)
    original=entry.get('arguments') or shlex.split(entry['command'])
    compiler_slot=next(index for index,value in enumerate(original)
                       if Path(value).resolve()==Path(compiler).resolve())
    flags=[]
    skip=False
    for value in original[compiler_slot+1:]:
        if skip:skip=False;continue
        if value in ('-o','-MF','-MT','-MQ'):skip=True;continue
        if value in ('-c','-MD','-MMD') or Path(value).resolve()==target:continue
        flags.append(value)
    header=source/'src/solver/native/kernels.hpp'
    command=[compiler,*flags,'-dM','-E','-x','c++','-']
    result=subprocess.run(command,input='#include '+json.dumps(str(header))+'\n',
                          cwd=entry['directory'],capture_output=True,text=True,check=True,timeout=60)
    macros=[line for line in result.stdout.splitlines() if line.startswith((
        '#define LQCD_NATIVE_SVE_COARSE ','#define __ARM_FEATURE_SVE ','#define __ARM_FEATURE_SVE_BITS '))]
    if not any(line.startswith('#define LQCD_NATIVE_SVE_COARSE ') for line in macros):
        raise RuntimeError('The actual native target flags did not compile the coarse SVE branch')
    record=dict(complete=True,compiler=compiler,command=command,macros=macros,
        compile_entry=entry,compile_entry_sha256=hashlib.sha256(json.dumps(entry,sort_keys=True).encode()).hexdigest(),
        header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),
        meaning='Actual target preprocessing enables the new ghost helper SVE branch; runtime counter and VL checks are separate')
    print('PHASE6_SVE_COMPILED '+json.dumps(record),flush=True)


def rank_test(expected, test):
    from mpi4py import MPI
    comm=MPI.COMM_WORLD
    libc=ctypes.CDLL(None,use_errno=True)
    libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
    libc.prctl.restype=ctypes.c_int
    def query():
        value=libc.prctl(51,0,0,0,0)
        return dict(rank=comm.rank,actual_bytes=value&0xffff if value>=0 else value,
                    inherit_exec=bool(value>=0 and value&(1<<17)))
    before=comm.allgather(query())
    if not all(row['actual_bytes']==expected and row['inherit_exec'] for row in before):
        raise RuntimeError('Per-rank SVE length after exec differs: '+json.dumps(before))
    library=Path(os.environ['LQCD_CPU_LIBRARY']).resolve()
    digest=hashlib.sha256(library.read_bytes()).hexdigest()
    if len(set(comm.allgather(digest)))!=1:raise RuntimeError('MPI ranks loaded different test libraries')
    if comm.rank==0:
        print('PHASE6_SVE_RANKS_BEGIN '+json.dumps(dict(requested_bytes=expected,
            ranks=before,library_sha256=digest,test=str(test))),flush=True)
    # Every OpenMP team is first created after the inherited main-thread length
    # has been checked. This records main-thread VL on every rank; it does not
    # relabel the check as a direct prctl query inside every worker thread.
    sys.argv=[str(test)]
    runpy.run_path(str(test),run_name='__main__')
    after=comm.allgather(query())
    if after!=before:raise RuntimeError('Per-rank SVE length changed during numerical tests')
    if comm.rank==0:
        print('PHASE6_SVE_RANKS_COMPLETE '+json.dumps(dict(complete=True,
            requested_bytes=expected,ranks=after,library_sha256=digest,test=str(test))),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-build',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--expected-bytes',type=int,choices=(16,32,64))
    parser.add_argument('--test',type=Path)
    args=parser.parse_args()
    if platform.system()!='Linux' or platform.machine().lower() not in ('aarch64','arm64'):
        parser.error('Linux Arm compute node required')
    if args.audit_build and args.source:compiler_audit(args.audit_build,args.source)
    elif args.expected_bytes and args.test:rank_test(args.expected_bytes,args.test)
    else:parser.error('Choose compiler audit or per-rank numerical execution')


if __name__=='__main__':main()
