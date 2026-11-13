#!/usr/bin/env python3
"""Attach perf to the final diagnostic full12 call without changing its results.

Example (inside the existing NUMA/MPI launcher):
  python profile_full12.py --benchmark FROZEN/tools/optimization/bench_full12.py \
    --profile-output NEW_PROFILE_DIR --diagnostic [benchmark arguments...]

Only rank 0 and rank 8 are sampled, once each. Runtime evidence and compiler
queries run after setup, before attaching perf. A profiler failure is preserved
and causes this wrapper to return failure after the diagnostic benchmark ends.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import socket
import subprocess
import sys
import time


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(8 * 1024**2), b''):
            value.update(data)
    return value.hexdigest()


def atomic(path, data):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(data, indent=2, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def command_evidence(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        return dict(argv=argv, returncode=result.returncode,
                    stdout=result.stdout[:12000], stderr=result.stderr[:4000])
    except Exception as exc:
        return dict(argv=argv, error=repr(exc))


def runtime_evidence(MPI, benchmark):
    """Read actual mappings; path search order alone is not dependency identity."""
    maps = Path('/proc/self/maps').read_text()
    libraries = []
    seen = set()
    for line in maps.splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6 or not fields[5].startswith('/'):
            continue
        path = fields[5]
        if '.so' not in Path(path).name or path in seen:
            continue
        seen.add(path)
        resolved = Path(path.removesuffix(' (deleted)'))
        entry = dict(mapped_path=path, resolved_path=str(resolved.resolve()))
        try:
            entry.update(sha256=sha(resolved), bytes=resolved.stat().st_size)
        except Exception as exc:
            entry['error'] = repr(exc)
        libraries.append(entry)
    allowed = sorted(os.sched_getaffinity(0))
    frequency = {}
    for cpu in allowed[:1]:
        directory = Path(f'/sys/devices/system/cpu/cpu{cpu}/cpufreq')
        for name in ['scaling_governor', 'scaling_cur_freq', 'scaling_min_freq', 'scaling_max_freq']:
            target = directory / name
            try:
                frequency[str(target)] = target.read_text().strip()
            except OSError as exc:
                frequency[str(target)] = dict(error=str(exc))
    compiler = os.environ.get('CXX', 'g++')
    # CXX is an executable path here, never shell-evaluated command text.
    compiler_path = shutil.which(compiler)
    sve = {}
    tasks = []
    for directory in sorted(Path('/proc/self/task').iterdir()):
        try:
            status = directory.joinpath('status').read_text()
            fields = {line.split(':',1)[0]:line.split(':',1)[1].strip()
                      for line in status.splitlines()
                      if line.startswith(('Name:','State:','Cpus_allowed_list:','Mems_allowed_list:'))}
            tasks.append(dict(tid=int(directory.name), **fields))
        except OSError:
            pass  # A helper may exit between directory enumeration and read.
    if os.uname().machine == 'aarch64':
        libc = ctypes.CDLL(None, use_errno=True)
        libc.getauxval.restype = ctypes.c_ulong
        hwcap, hwcap2 = int(libc.getauxval(16)), int(libc.getauxval(26))
        sve.update(hwcap=hwcap, hwcap2=hwcap2, sve=bool(hwcap & (1 << 22)))
        if sve['sve']:
            length = libc.prctl(51, 0, 0, 0, 0)  # query PR_SVE_GET_VL only
            sve['vector_bytes'] = length & 0xffff if length >= 0 else None
    return dict(host=socket.gethostname(), pid=os.getpid(), rank=MPI.COMM_WORLD.rank,
        captured_at=time.time(), phase='after setup, before final diagnostic call and perf attachment',
        benchmark=str(benchmark), benchmark_sha256=sha(benchmark),
        allowed_cpus=allowed, affinity_scope='calling thread only; OpenMP team placement is recorded in OMP_PLACES',
        maps=maps, mapped_libraries=libraries, tasks=tasks, task_count=len(tasks),
        loader_environment={k:os.environ.get(k) for k in ['LD_LIBRARY_PATH','LD_PRELOAD']},
        tuning_environment={k:v for k,v in os.environ.items()
                            if k.startswith(('LQCD_','OMP_','GOMP_','OMPI_MCA_'))},
        compiler=(command_evidence([compiler_path,'--version']) if compiler_path else
                  dict(requested=compiler, error='compiler executable not found')),
        mpi_library_version=MPI.Get_library_version(), mpi_thread_support=MPI.Query_thread(),
        lscpu=command_evidence(['lscpu']), sve=sve, cpu_frequency_snapshot=frequency,
        frequency_interpretation='Instantaneous read of the first allowed CPU only; not a measured all-core operating frequency')


def stop_perf(process):
    requested_sigint = False
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        requested_sigint = True
    try:
        return dict(record_returncode=process.wait(timeout=30),
                    stop_requested_sigint=requested_sigint)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise RuntimeError('perf did not flush/exit after SIGINT')


def record_exit_eligible(returncode, requested_sigint):
    """A requested SIGINT can flush valid data; decoding still has to succeed."""
    return returncode == 0 or (requested_sigint and returncode == -signal.SIGINT)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--profile-output', type=Path, required=True)
    parser.add_argument('--perf', default='perf', help='perf executable, without shell arguments')
    args, remaining = parser.parse_known_args(argv)
    if '--diagnostic' not in remaining:
        parser.error('Profiling requires benchmark --diagnostic; ordinary accepted samples must not be profiled')
    if '--verify' in remaining:
        parser.error('This wrapper profiles diagnostic solves, not independent validation')
    benchmark = args.benchmark.resolve()
    if not benchmark.is_file() or benchmark.name != 'bench_full12.py':
        parser.error('--benchmark must identify an existing explicit bench_full12.py')
    project = benchmark.parents[2]
    sys.path.insert(0, str(project / 'bindings'))
    from mpi4py import MPI
    from lqcd_cpu import Solver
    comm = MPI.COMM_WORLD
    out = args.profile_output.resolve()
    error = None
    if comm.rank == 0:
        try:
            out.mkdir(parents=True, exist_ok=False)
        except Exception as exc:
            error = repr(exc)
    errors = comm.allgather(error)
    if any(errors):
        raise RuntimeError(f'Fresh profile output directory required: {errors}')
    comm.Barrier()
    original = Solver.solve_propagator
    captured = False
    local_errors = []
    profile_record = None

    def instrumented(solver, *call_args, **call_kwargs):
        nonlocal captured, profile_record
        # The benchmark sets verbose=0 for its ordinary diagnostic-scope rounds
        # and verbose=1 only for its last, unranked diagnostic full12 call.
        active = os.environ.get('LQCD_VERBOSE') == '1' and not captured
        if not active:
            return original(solver, *call_args, **call_kwargs)
        captured = True
        selected = comm.rank in (0,8)
        prefix = out / f'rank{comm.rank:05d}'
        process = stream = counter = None
        profile_record = dict(complete=False, passed=False, rank=comm.rank,
            host=socket.gethostname(), pid=os.getpid(), selected=selected,
            event='cycles:u', frequency=49, call_graph='dwarf,4096', errors=[],
            coverage='one final diagnostic full12 call; sampled ranks only; not an accepted timing sample')
        if selected:
            try:
                atomic(prefix.with_suffix('.runtime.json'), runtime_evidence(MPI, benchmark))
            except Exception as exc:
                local_errors.append('runtime evidence: '+repr(exc))
        # All ranks finish untimed setup evidence before any process is sampled.
        comm.Barrier()
        if selected:
            try:
                perf = shutil.which(args.perf)
                if not perf:
                    raise RuntimeError('perf executable not found')
                perfdata = prefix.with_suffix('.perf.data')
                record_argv = [perf,'record','-e','cycles:u','-F','49','--call-graph',
                               'dwarf,4096','-p',str(os.getpid()),'-o',str(perfdata)]
                profile_record['record_argv'] = record_argv
                stream = prefix.with_suffix('.perf-record.log').open('xb')
                process = subprocess.Popen(record_argv,stdout=stream,stderr=subprocess.STDOUT,
                                           start_new_session=True)
                # Bounded startup check catches permissions/event failures before
                # calling the solver. This is diagnostic overhead, not a timer.
                time.sleep(.2)
                if process.poll() is not None:
                    raise RuntimeError(f'perf record exited during startup: {process.returncode}')
            except Exception as exc:
                local_errors.append('perf start: '+repr(exc))
        # Attach each selected process before entering this collective solve.
        comm.Barrier()
        if os.environ.get('PERF_COUNTER_ROOT'):
            try:
                counter = ctypes.CDLL(None)
                counter.bench_begin.argtypes = []
                counter.bench_begin.restype = None
                counter.bench_end.argtypes = []
                counter.bench_end.restype = None
                counter.bench_begin()
            except Exception as exc:
                counter = None
                local_errors.append('optional PMPI counter start: '+repr(exc))
        try:
            # Return the original objects without changing solutions or stats.
            value = original(solver, *call_args, **call_kwargs)
            profile_record['solver_completed'] = True
            return value
        except BaseException as exc:
            profile_record['solver_completed'] = False
            local_errors.append('diagnostic solve: '+repr(exc))
            raise
        finally:
            if counter:
                try:
                    counter.bench_end()
                except Exception as exc:
                    local_errors.append('optional PMPI counter end: '+repr(exc))
            if selected:
                record_exit_ok = False
                if process:
                    try:
                        profile_record.update(stop_perf(process))
                        record_exit_ok = record_exit_eligible(
                            profile_record['record_returncode'],
                            profile_record['stop_requested_sigint'])
                        if not record_exit_ok:
                            raise RuntimeError(f"perf record failed: {profile_record['record_returncode']}")
                    except Exception as exc:
                        local_errors.append('perf stop: '+repr(exc))
                if stream:
                    stream.close()
                try:
                    perfdata = prefix.with_suffix('.perf.data')
                    if not process or not record_exit_ok or not perfdata.is_file() or not perfdata.stat().st_size:
                        raise RuntimeError('No successful nonempty perf recording')
                    report_argv = [shutil.which(args.perf),'report','--stdio','--no-children',
                                   '--sort','symbol','--input',str(perfdata)]
                    profile_record['report_argv'] = report_argv
                    with prefix.with_suffix('.perf-flat.txt').open('xb') as flat, \
                            prefix.with_suffix('.perf-report.log').open('xb') as report_log:
                        result = subprocess.run(report_argv,stdout=flat,stderr=report_log,timeout=60)
                    profile_record['report_returncode'] = result.returncode
                    if result.returncode:
                        raise RuntimeError(f'perf report failed: {result.returncode}')
                    if not prefix.with_suffix('.perf-flat.txt').stat().st_size:
                        raise RuntimeError('perf report produced an empty flat report')
                    profile_record['perf_data_sha256'] = sha(perfdata)
                    profile_record['flat_report_sha256'] = sha(prefix.with_suffix('.perf-flat.txt'))
                except Exception as exc:
                    local_errors.append('perf report: '+repr(exc))
            profile_record.update(complete=True,passed=not local_errors,errors=list(local_errors))
            atomic(prefix.with_suffix('.profile.json'),profile_record)

    Solver.solve_propagator = instrumented
    saved_argv = sys.argv
    try:
        sys.argv = [str(benchmark),*remaining]
        runpy.run_path(str(benchmark),run_name='__main__')
    finally:
        Solver.solve_propagator = original
        sys.argv = saved_argv
    if not captured:
        local_errors.append('Benchmark never reached a final verbose diagnostic solve')
    failures = comm.allgather(dict(rank=comm.rank,errors=local_errors))
    failed = any(item['errors'] for item in failures)
    if comm.rank == 0:
        atomic(out/'profile-summary.json',dict(complete=True,passed=not failed,
            benchmark=str(benchmark),benchmark_sha256=sha(benchmark),
            selected_ranks=[rank for rank in (0,8) if rank < comm.size],
            actual_ranks=comm.size,rank_failures=failures,
            scope='auxiliary diagnostic evidence; never a performance acceptance sample'))
    return 2 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
