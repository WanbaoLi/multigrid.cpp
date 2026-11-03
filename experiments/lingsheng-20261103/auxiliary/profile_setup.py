#!/usr/bin/env python3
"""Unranked Solver.setup perf on ranks0/8, using the existing full12 helpers.

Pass --diagnostic and the explicit cold_full12.py arguments. Constructor/load
walls remain separate in the cold report; perf covers Solver.setup only. No
distributed setup implementation is introduced. Run after review, never beside
an ordinary benchmark. Sampled setup time is not a production cold/steady score.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def memory_cpu():
    import resource  # Linux execution only; keep local --help/AST review portable.
    value=resource.getrusage(resource.RUSAGE_SELF)
    return dict(user_seconds=value.ru_utime,system_seconds=value.ru_stime,
        minor_faults=value.ru_minflt,major_faults=value.ru_majflt,max_rss_kib_linux=value.ru_maxrss)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold-wrapper',type=Path,required=True)
    parser.add_argument('--profile-helper',type=Path,required=True,
                        help='Explicit existing tools/optimization/profile_full12.py, helpers only')
    parser.add_argument('--profile-output',type=Path,required=True)
    parser.add_argument('--perf',default='perf')
    parser.add_argument('--frequency',type=int,default=19,help='Low-rate setup sampling, default19Hz to bound DWARF data')
    args,remaining=parser.parse_known_args(argv)
    if not 1<=args.frequency<=99:
        parser.error('Frequency must be 1..99Hz')
    if '--diagnostic' not in remaining or '--project' not in remaining:
        parser.error('Require explicit --diagnostic and --project cold-wrapper arguments')
    if '--verify' in remaining:
        parser.error('Independent verification is a separate unprofiled command')
    cold=args.cold_wrapper.resolve();helper_path=args.profile_helper.resolve()
    if cold.name!='cold_full12.py' or not cold.is_file() or helper_path.name!='profile_full12.py' or not helper_path.is_file():
        parser.error('Explicit existing cold_full12.py and profile_full12.py required')
    project=Path(remaining[remaining.index('--project')+1]).resolve()
    sys.path.insert(0,str(project/'python'))
    from mpi4py import MPI
    from lqcd_cpu import Solver
    comm=MPI.COMM_WORLD
    helpers=load_module('_setup_perf_helpers',helper_path)
    out=args.profile_output.resolve()
    error=None
    if comm.rank==0:
        try:out.mkdir(parents=True,exist_ok=False)
        except Exception as exc:error=str(exc)
    errors=comm.allgather(error)
    if any(errors):raise RuntimeError('Fresh setup-profile output required: '+repr(errors))
    comm.Barrier()
    original=Solver.setup
    captured=False
    local_errors=[]
    def instrumented(solver,*call_args,**call_kwargs):
        nonlocal captured
        if captured:
            raise RuntimeError('Setup profiler expects exactly one fresh hierarchy per process')
        captured=True
        selected=comm.rank in (0,8)
        prefix=out/f'rank{comm.rank:05d}'
        record=dict(complete=False,passed=False,selected=selected,rank=comm.rank,pid=os.getpid(),
            coverage='Solver.setup only, one fresh hierarchy; all timing scopes explicitly diagnostic/unranked',
            cold_wrapper=str(cold),cold_wrapper_sha256=helpers.sha(cold),
            profile_helper=str(helper_path),profile_helper_sha256=helpers.sha(helper_path),
            class_module=type(solver).__module__,class_name=type(solver).__qualname__,
            method='Solver.setup',event='cycles:u',frequency=args.frequency,call_graph='dwarf,4096',errors=[])
        process=stream=None
        if selected:
            try:
                evidence=helpers.runtime_evidence(MPI,cold)
                evidence['phase']='after context/load, immediately before setup and perf attachment'
                # Existing helper's machine/library evidence is reused. Restrict
                # environment output to documented loader/OpenMP/runtime tuning.
                allowed=('LQCD_MG_SETUP_PASSES','LQCD_MG_SETUP_ITERATIONS','LQCD_MG_SETUP_SMOOTH',
                         'LQCD_HBW_ALLOC','LQCD_HBM','LQCD_SETUP_UPDATE','LQCD_SAP_EO','LQCD_COARSE_EO',
                         'LQCD_ARM_SVE','LQCD_ARM_SVE_REUSE','LQCD_COARSE_SPATIAL_OVERLAP',
                         'OMP_NUM_THREADS','OMP_PLACES','OMP_PROC_BIND','OMP_WAIT_POLICY','GOMP_SPINCOUNT')
                evidence['tuning_environment']={key:os.environ[key] for key in allowed if key in os.environ}
                helpers.atomic(prefix.with_suffix('.runtime.json'),evidence)
            except Exception as exc:local_errors.append('runtime evidence: '+str(exc))
        comm.Barrier()
        if selected:
            try:
                perf=shutil.which(args.perf)
                if not perf:raise RuntimeError('perf executable not found')
                command=[perf,'record','-e','cycles:u','-F',str(args.frequency),'--call-graph','dwarf,4096',
                         '-p',str(os.getpid()),'-o',str(prefix.with_suffix('.perf.data'))]
                record['record_argv']=command
                stream=prefix.with_suffix('.perf-record.log').open('xb')
                process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                time.sleep(.2)
                if process.poll() is not None:raise RuntimeError('perf exited during startup: '+str(process.returncode))
            except Exception as exc:local_errors.append('perf start: '+str(exc))
        comm.Barrier()
        before=memory_cpu()
        begin=time.perf_counter()
        try:
            value=original(solver,*call_args,**call_kwargs)
            record.update(native_return_seconds=value,setup_python_wall_seconds=time.perf_counter()-begin,
                          solver_completed=True)
            return value  # exact original return, no result/stat/numerical change
        except BaseException as exc:
            record.update(solver_completed=False,setup_python_wall_seconds=time.perf_counter()-begin)
            local_errors.append('setup: '+repr(exc))
            raise
        finally:
            record.update(resource_before=before,resource_after=memory_cpu())
            if selected:
                eligible=False
                if process:
                    try:
                        record.update(helpers.stop_perf(process))
                        eligible=helpers.record_exit_eligible(record['record_returncode'],record['stop_requested_sigint'])
                        if not eligible:raise RuntimeError('perf record failed: '+str(record['record_returncode']))
                    except Exception as exc:local_errors.append('perf stop: '+str(exc))
                if stream:stream.close()
                try:
                    data=prefix.with_suffix('.perf.data')
                    if not eligible or not data.is_file() or not data.stat().st_size:
                        raise RuntimeError('No valid nonempty setup perf data')
                    command=[shutil.which(args.perf),'report','--stdio','--no-children','--sort','symbol','--input',str(data)]
                    record['report_argv']=command
                    with prefix.with_suffix('.perf-flat.txt').open('xb') as flat, prefix.with_suffix('.perf-report.log').open('xb') as log:
                        result=subprocess.run(command,stdout=flat,stderr=log,timeout=60)
                    if result.returncode or not prefix.with_suffix('.perf-flat.txt').stat().st_size:
                        raise RuntimeError('Setup perf report failed/empty')
                    record.update(perf_data_sha256=helpers.sha(data),
                                  flat_report_sha256=helpers.sha(prefix.with_suffix('.perf-flat.txt')))
                except Exception as exc:local_errors.append('perf report: '+str(exc))
            record.update(complete=True,passed=not local_errors,errors=list(local_errors))
            helpers.atomic(prefix.with_suffix('.setup-profile.json'),record)
    Solver.setup=instrumented
    saved=sys.argv
    try:
        sys.argv=[str(cold),*remaining]
        runpy.run_path(str(cold),run_name='__main__')
    finally:
        Solver.setup=original
        sys.argv=saved
    if not captured:local_errors.append('Target never reached Solver.setup')
    failures=comm.allgather(dict(rank=comm.rank,errors=local_errors))
    failed=any(row['errors'] for row in failures)
    if comm.rank==0:
        helpers.atomic(out/'setup-profile-summary.json',dict(complete=True,passed=not failed,
            selected_ranks=[rank for rank in (0,8) if rank<comm.size],rank_failures=failures,
            scope='unranked setup diagnosis; constructor/gauge-load walls remain in cold report; never a warm API speed claim'))
    return 2 if failed else 0


if __name__=='__main__':
    sys.exit(main())
