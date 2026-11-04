"""Actual rank0/8 runtime maps immediately before the original setup call.

Outer wrapper only. Frozen benchmark, publication, solver and clocks are intact.
All ranks join capture before setup; nothing observes ordinary timed solves.
"""
import argparse
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time

import file_integrity as integrity
import phase5_validation_shim as policy

HMPI_LIB='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/hmpi/bisheng/release/hmpi/lib'
MPI_PREFIX=HMPI_LIB+':'+HMPI_LIB+':'

RAW_SHA='f55aae8c4f460c93d5f913682e3f526e5f66d4109f84646a9c2a7198f8023f60'
BENCH_SHA='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'
SOLVER_SHA='0b87424381da035ab27ae3bf9022aebf277b052cad502e09284f469e8f34716c'
POLICY_SHA='c5a8a8b3c14d697c9062bf04172e2eb616ffebda66298a99aa123ca80419d9fe'


def option(argv,flag):
    integrity.require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Exactly one '+flag+' required')
    return argv[argv.index(flag)+1]


def mapped_libraries(maps=None, clock=time.monotonic, deadline=None):
    deadline=clock()+30 if deadline is None else deadline
    paths=set()
    for line in (maps if maps is not None else Path('/proc/self/maps').read_text()).splitlines():
        fields=line.split(None,5)
        if len(fields)!=6 or not fields[5].startswith('/'):continue
        raw=fields[5]
        if '.so'not in Path(raw).name and policy.library_family(Path(raw).name)is None:continue
        integrity.require(not raw.endswith(' (deleted)'),'Deleted mapped shared object cannot be qualified')
        paths.add(Path(raw).resolve(strict=True))
    rows=[]
    for path in sorted(paths):
        integrity.require(clock()<=deadline,'Pre-setup runtime capture exceeded30s')
        value=integrity.read_dual(path)
        rows.append(dict(path=str(path),sha256=value['openssl_sha256'],bytes=path.stat().st_size))
    integrity.require(clock()<=deadline,'Pre-setup runtime hash exceeded30s')
    for family in ('gomp','stdcpp','gcc','libc','mpi','solver'):
        integrity.require(sum(policy.library_family(Path(row['path']).name)==family for row in rows)==1,
                          'Expected exactly one actual runtime mapping: '+family)
    return rows


def capture(solver,args,remaining):
    comm=solver.comm
    integrity.require(comm.size==16,'This explicit runtime comparison requires16MPI ranks')
    rank=comm.rank;row=None;error=None
    try:
        if rank in (0,8):
            libraries=mapped_libraries()
            library=Path(option(remaining,'--library')).resolve(strict=True)
            expected=integrity.read_dual(library)['openssl_sha256']
            actual=[r for r in libraries if policy.library_family(Path(r['path']).name)=='solver']
            integrity.require(actual==[dict(path=str(library),sha256=expected,bytes=library.stat().st_size)],
                              'Actual mapped solver differs from explicitly measured library')
            context=json.loads(Path(option(remaining,'--plan')).read_text())['context_environment']
            environment=policy.runtime_environment_snapshot(
                [(key+'='+value).encode()for key,value in os.environ.items()],
                dict(context,LD_LIBRARY_PATH=MPI_PREFIX+str(context.get('LD_LIBRARY_PATH',os.environ['LQCD_OPT_CAPTURE_BASE_LD']))),
                MPI_PREFIX+os.environ['LQCD_OPT_CAPTURE_BASE_LD'])
            if context.get('LQCD_HBW_ALLOC')=='require':
                integrity.require(any(Path(r['path']).name.startswith('libkupl.so')for r in libraries),
                                  'HBW require has no actual KUPL map')
            stat=Path('/proc/self/stat').read_text().rpartition(') ')[2].split()
            row=dict(rank=rank,pid=os.getpid(),pid_starttime=int(stat[19]),captured_epoch=time.time(),
                host=socket.gethostname(),libraries=libraries,runtime_environment=environment,
                thread_affinity=policy.thread_affinity_snapshot(os.getpid()),
                capture_point='after gauge load, immediately before original Solver.setup call')
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    errors=comm.allgather(error)
    integrity.require(not any(errors),'Collective runtime capture failed: '+repr(errors))
    rows=comm.allgather(row);error=None
    if rank==0:
        try:
            rows=[r for r in rows if r is not None]
            integrity.require({r['rank']for r in rows}=={0,8}and len(rows)==2,'Both representative ranks required')
            output=args.capture_output
            integrity.require(output.is_absolute()and output==output.resolve(strict=False),'Canonical capture output required')
            output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            integrity.write_json_private(output,dict(complete=True,completed_before_steady=True,attempt=args.attempt,
                host=socket.gethostname(),allocation=os.environ['LQCD_OPT_ALLOCATION'],
                library_sha256=rows[0]['libraries'][next(i for i,r in enumerate(rows[0]['libraries'])if policy.library_family(Path(r['path']).name)=='solver')]['sha256'],
                benchmark_stage_tag=os.environ['LQCD_OPT_STAGE_ID'],task_tag=os.environ['LQCD_OPT_TASK_ID'],
                ranks=rows,capture_point='after gauge load, immediately before original setup',
                captured_during_setup=False,setup_launch_window_used=False,
                observed_fixed_mpi_prefix=MPI_PREFIX,actual_runtime_environment_not_normalized=True,
                wrapper_sha256=args.expected_self_sha,solver_python_sha256=SOLVER_SHA,
                benchmark_sha256=BENCH_SHA,frozen_publication_wrapper_sha256=RAW_SHA,
                ordinary_solve_observer_running=False))
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
    errors=comm.allgather(error)
    integrity.require(not any(errors),'Collective runtime receipt failed: '+repr(errors))
    comm.Barrier()


def main():
    argv=sys.argv[1:];integrity.require('--'in argv,'Explicit unchanged frozen argv boundary required')
    at=argv.index('--');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-self-sha',required=True)
    parser.add_argument('--capture-output',type=Path,required=True)
    parser.add_argument('--attempt',required=True)
    args=parser.parse_args(argv[:at]);remaining=argv[at+1:]
    integrity.read_dual(__file__,args.expected_self_sha)
    integrity.read_dual(policy.__file__,POLICY_SHA)
    integrity.require('--verify'not in remaining,'Only ordinary producer processes may capture runtime')
    raw=Path(__file__).with_name('raw_benchmark_publication_v2.py');integrity.read_dual(raw,RAW_SHA)
    target=Path(option(remaining,'--benchmark')).resolve(strict=True);integrity.read_dual(target,BENCH_SHA)
    execute=importlib.machinery.SourceFileLoader.exec_module
    installed=[];calls=[];saved=sys.argv
    def load(loader,module):
        selected=Path(getattr(loader,'path','')).resolve()==target
        execute(loader,module)
        if not selected:return
        integrity.require(not installed,'Frozen benchmark must load once')
        sys.path.insert(0,str(target.parents[2]/'python'))
        import lqcd_cpu
        integrity.require(Path(lqcd_cpu.__file__).resolve()==target.parents[2]/'python/lqcd_cpu/__init__.py',
                          'Solver module belongs to a different source snapshot')
        integrity.read_dual(lqcd_cpu.__file__,SOLVER_SHA)
        original=lqcd_cpu.Solver.setup
        def setup(solver,*positional,**kwargs):
            integrity.require(not calls,'Exactly one original setup call required')
            calls.append(True)
            capture(solver,args,remaining)
            return original(solver,*positional,**kwargs)
        installed.append((lqcd_cpu.Solver,original));lqcd_cpu.Solver.setup=setup
    try:
        importlib.machinery.SourceFileLoader.exec_module=load
        spec=importlib.util.spec_from_file_location('_unchanged_warm_capture_target',raw)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        sys.argv=[str(raw),*remaining];module.main()
        integrity.require(len(installed)==1 and len(calls)==1,'Actual pre-setup capture hook did not execute once')
    finally:
        importlib.machinery.SourceFileLoader.exec_module=execute;sys.argv=saved
        for cls,original in installed:cls.setup=original


if __name__=='__main__':main()
