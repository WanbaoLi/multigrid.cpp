"""Frozen solve profiler around the unchanged strict publication benchmark.

Diagnostic only. Original49Hz recording and clocks stay intact. Independently
verified saved output is the last light diagnostic sample; the actual sampled
call additionally must return12 converged, finite true-residual statistics.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import file_integrity as integrity

PROFILE_SHA='0f8f91305635ae7085d6bb9dcaa96b4c0607b3dfbeb4b83cc3b34526f714bc98'
RAW_SHA='f55aae8c4f460c93d5f913682e3f526e5f66d4109f84646a9c2a7198f8023f60'
BENCH_SHA='711df30c341f31aa8770b371b5d8ec32fb90cbbe8dff0a173e5e1532d977f5a1'


def option(argv,flag):
    integrity.require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Exactly one '+flag+' required')
    return argv[argv.index(flag)+1]


def load(path,name,expected):
    integrity.read_dual(path,expected)
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def check_stats(value):
    _,stats=value
    integrity.require(len(stats)==12 and all(row.get('converged')in(1,True)and
        math.isfinite(row.get('true_residual',float('nan')))and 0<=row['true_residual']<=1e-8 for row in stats),
        'Actual profiled full12 call failed true-residual/convergence checks')
    return stats


def main():
    argv=sys.argv[1:];integrity.require('--'in argv,'Explicit frozen publication argv required')
    at=argv.index('--');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-self-sha',required=True);parser.add_argument('--profile-output',type=Path,required=True)
    args=parser.parse_args(argv[:at]);remaining=argv[at+1:]
    integrity.read_dual(__file__,args.expected_self_sha)
    integrity.require('--diagnostic'in remaining and '--verify'not in remaining,'Only explicitly unranked diagnostic solves may be profiled')
    benchmark=Path(option(remaining,'--benchmark')).resolve(strict=True);integrity.read_dual(benchmark,BENCH_SHA)
    plan=json.loads(Path(option(remaining,'--plan')).read_text());integrity.require(len(plan['cases'])==1,'One exact retained-best diagnostic case required')
    root=Path(__file__).resolve().parent
    profile=load(root/'profile_full12.py','_frozen_solve_profile_v7',PROFILE_SHA)
    raw=load(root/'raw_benchmark_publication_v2.py','_frozen_profile_publication_v7',RAW_SHA)
    profile.sha=lambda path:integrity.read_dual(Path(path).resolve(strict=True))['openssl_sha256']
    sys.path.insert(0,str(benchmark.parents[2]/'python'))
    from mpi4py import MPI
    from lqcd_cpu import Solver
    import os
    comm=MPI.COMM_WORLD;original_solve=Solver.solve_propagator
    calls=[];profiled=[];saved=sys.argv;execute=runpy.run_path
    def checked(solver,*positional,**kwargs):
        result=original_solve(solver,*positional,**kwargs)
        if os.environ.get('LQCD_VERBOSE')=='1':profiled.append(check_stats(result))
        return result
    def entry(path,*positional,**kwargs):
        if Path(path).resolve()!=benchmark:return execute(path,*positional,**kwargs)
        integrity.require(not calls and kwargs.get('run_name')=='__main__','Exactly one frozen benchmark entry required')
        calls.append(True);current=sys.argv
        try:
            sys.argv=[str(root/'raw_benchmark_publication_v2.py'),*remaining]
            return raw.main()
        finally:sys.argv=current
    try:
        Solver.solve_propagator=checked;runpy.run_path=entry
        result=profile.main(['--benchmark',str(benchmark),'--profile-output',str(args.profile_output),*remaining])
        integrity.require(result==0 and len(calls)==1 and len(profiled)==1,'Frozen profile or actual sampled-call checks failed')
    finally:
        runpy.run_path=execute;Solver.solve_propagator=original_solve;sys.argv=saved
    error=None;record=dict(rank=comm.rank,complete=False,wrapper_sha256=args.expected_self_sha,
        frozen_profile_sha256=PROFILE_SHA,frozen_publication_sha256=RAW_SHA,
        actual_profiled_stats=profiled[0],actual_profiled_stats_checked=True,
        independently_verified_saved_output_scope='Last light diagnostic sample; final verbose sampled output is not saved',
        timing_scope='Auxiliary diagnostic only; no ordinary performance acceptance')
    try:
        if comm.rank in (0,8):
            prefix=args.profile_output/('rank%05d'%comm.rank)
            command=[shutil.which('perf'),'report','--stdio','--no-children','--call-graph','none',
                '--sort','comm,pid,dso,symbol','--percent-limit','0','--input',str(prefix.with_suffix('.perf.data'))]
            target=prefix.with_suffix('.leaf-by-thread.txt')
            with target.open('xb')as output,prefix.with_suffix('.leaf-by-thread.log').open('xb')as log:
                decoded=subprocess.run(command,stdout=output,stderr=log,timeout=90)
            integrity.require(decoded.returncode==0 and target.stat().st_size>0,'Leaf/thread perf decoding failed')
            record.update(decode_argv=command,decode_returncode=decoded.returncode,
                          leaf_report_sha256=integrity.read_dual(target)['openssl_sha256'])
        record['complete']=True
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    record['error']=error
    integrity.write_json_private(args.profile_output/('rank%05d.wrapper-v7.json'%comm.rank),record)
    failures=comm.allgather(error);integrity.require(not any(failures),'Final diagnostic decode failed: '+repr(failures))
    if comm.rank==0:
        integrity.write_json_private(args.profile_output/'wrapper-v7-summary.json',dict(complete=True,passed=True,
            selected_ranks=[0,8],rank_count=comm.size,actual_profiled_stats_checked=True,
            wrapper_sha256=args.expected_self_sha,frozen_profile_sha256=PROFILE_SHA,
            unranked=True,recording_frequency_hz=49,call_graph='dwarf,4096',flat_decode_call_graph='none',
            thread_key='pid (perf5.10 command and task TID; not a tid sort key)',
            thread_key_primary_source='https://raw.githubusercontent.com/torvalds/linux/v5.10/tools/perf/Documentation/perf-report.txt'))


if __name__=='__main__':main()
