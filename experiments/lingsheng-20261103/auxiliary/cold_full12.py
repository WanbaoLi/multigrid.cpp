#!/usr/bin/env python3
"""Fresh hierarchy through first full12, with a single continuous wall clock.

Run under the selected project's tools/run_numa.py. This is neither a steady
benchmark nor a claim about a cold OS/storage cache. Python/MPI startup, source
checks, output writing and independent verification are outside the cold clock.
Input hashing, parsing/reading, optional stout, canonical-field validation,
context construction, gauge/clover load, setup and first full12 are inside it.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import sys
import time

RAW_SHA = '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30'
PREPARED_SHA = '126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834'
PHYSICS = dict(mass=-.277,csw=1.160920226,lattice_xyzt=[24,24,24,64],
    normalization='mass',source_xyzt=[0,0,0,0],source_scale=1.,gamma_basis='DeGrand-Rossi',
    fermion_t_boundary=-1,gauge_t_boundary=1,gauge_reunitarized=False,
    stout=dict(steps=1,rho=.125,dir_ignore=4))

# Audited getenv/setting literals in native setup, fine/coarse/transfer kernels,
# allocator and Python RHS dispatch. Per-rank NUMA and task ownership are not
# numerical defaults and are deliberately excluded from clearing/rejection.
KNOWN_NUMERICAL_ENV = set('LQCD_ADAPTIVE_CORRECTION LQCD_ARM_COARSE_SVE LQCD_ARM_SVE_PLANNED '
    'LQCD_ARM_SVE_REUSE LQCD_ARM_SVE_TRANSFER LQCD_ARM_SVE LQCD_COARSE_BATCH_REDUCE '
    'LQCD_COARSE_CGS2 LQCD_COARSE_EMPTY_INTERIOR LQCD_COARSE_EO LQCD_COARSE_FUSED '
    'LQCD_COARSE_SPATIAL_OVERLAP LQCD_COARSE_THREADS LQCD_CORRECTION_BASE_TOL '
    'LQCD_CPU_LIBRARY LQCD_FINE_SCHEDULE LQCD_FINE_TEAM_FUSED LQCD_FLOAT_CORRECTION_VERIFY '
    'LQCD_GCR_FUSED LQCD_HALO_OVERLAP LQCD_HALO_PROFILE LQCD_HBM LQCD_HBW_ALLOC '
    'LQCD_LOCAL_CONTIGUOUS LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL LQCD_MG_SAP_CYCLES '
    'LQCD_MG_SAP_STEPS LQCD_MG_SETUP_ITERATIONS LQCD_MG_SETUP_PASSES LQCD_MG_SETUP_SMOOTH '
    'LQCD_RESTRICT_FLOAT LQCD_RHS_BATCH LQCD_SAP_EO LQCD_SETUP_UPDATE LQCD_TRANSFER_TILE '
    'LQCD_VERBOSE LQCD_WILSON_PACKED LQCD_WILSON_SIMD NATIVE_COARSE_IT NATIVE_OUTER_FLOAT '
    'NATIVE_SAP_CYCLES NATIVE_SAP_STEPS'.split())


def numerical_environment_keys(project):
    result=set(KNOWN_NUMERICAL_ENV)
    for directory in (Path(project)/'src',Path(project)/'core',Path(project)/'python/lqcd_cpu'):
        if not directory.is_dir():
            continue
        for path in directory.rglob('*'):
            if path.suffix in {'.cpp','.hpp','.h','.c','.cc','.py'} and path.is_file():
                result.update(re.findall(r'''["']((?:LQCD|NATIVE)_[A-Z0-9_]+)["']''',path.read_text(encoding='utf-8')))
    return {name for name in result if name not in {'LQCD_NUMA_NODE','LQCD_CPU_THREADS'}
            and not name.startswith('LQCD_OPT_') and not name.endswith('_')}


def validate_launcher_resources(environment,placement_threads):
    raw=environment.get('LQCD_CPU_THREADS','')
    if not re.fullmatch('[0-9]+',raw) or int(raw)!=placement_threads:
        raise ValueError('Launcher LQCD_CPU_THREADS must equal placement_threads')
    node=environment.get('LQCD_NUMA_NODE')
    if node is not None and not re.fullmatch('[0-9]+',node):
        raise ValueError('Launcher LQCD_NUMA_NODE must be a nonnegative decimal node ID')
    return dict(cpu_threads=int(raw),numa_node=int(node) if node is not None else None)


def audit_numerical_environment(project,context,environment):
    keys=numerical_environment_keys(project)
    unexpected=sorted(key for key in keys if key in environment and key not in context
        and not (key in {'LQCD_VERBOSE','LQCD_HALO_PROFILE'} and environment[key]=='0'))
    if unexpected:
        raise ValueError('Unexpected unrecorded numerical/setup environment: '+', '.join(unexpected))
    return dict(known_keys=sorted(keys),explicit_context_values={key:value for key,value in context.items() if key in keys},
                unrequested_policy='unset; use the defaults in the exact frozen source/library',
                preserved_resources='LQCD_CPU_THREADS (validated against placement), LQCD_NUMA_NODE, LQCD_OPT_* ownership, launcher placement')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024**2),b''):
            h.update(chunk)
    return h.hexdigest()


def atomic(path,value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp-'+str(os.getpid()))
    with temporary.open('w',encoding='utf-8') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,path)


def source_check(project,manifest_path,expected):
    if sha(manifest_path)!=expected:
        raise ValueError('Frozen source manifest identity changed')
    manifest = json.loads(manifest_path.read_text())
    for row in manifest['files']:
        relative = Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe frozen source path')
        path = project/relative
        if row.get('deleted'):
            if path.exists():
                raise ValueError('Deleted source file reappeared')
        elif path.is_symlink() or not path.is_file() or sha(path)!=row['sha256']:
            raise ValueError('Frozen source file changed: '+str(relative))


def require_plan(plan,solve_keys):
    cases = plan.get('cases',[])
    if len(cases)!=1 or not isinstance(plan.get('context_environment',{}),dict):
        raise ValueError('One case/context per fresh process required')
    case = cases[0]
    managed={'OMP_NUM_THREADS','OMP_PLACES','OMP_PROC_BIND','GOMP_CPU_AFFINITY',
             'LQCD_CPU_THREADS','LQCD_NUMA_NODE','LQCD_CPU_LIBRARY','LQCD_RHS_BATCH','LQCD_VERBOSE','LQCD_HALO_PROFILE'}
    if managed & set(plan['context_environment']):
        raise ValueError('Context conflicts with launcher/worker-managed settings')
    for key in ('threads','batch'):
        if type(case.get(key)) is not int or case[key]<1:
            raise ValueError('Positive solve threads/batch required')
    if case['batch']>12 or set(case.get('environment',{}))-set(solve_keys):
        raise ValueError('Invalid solve-only tuning/batch')
    setup = plan.get('setup_threads',case['threads'])
    placement = plan.get('placement_threads',case['threads'])
    if type(setup) is not int or type(placement) is not int or not 1<=setup<=placement or case['threads']>placement:
        raise ValueError('Setup/fine teams must fit fixed placement')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
           for v in case.get('environment',{}).values()):
        raise ValueError('Finite numeric solve tuning required')
    return case,setup,placement


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path,required=True)
    p.add_argument('--snapshot-sha',required=True)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--expected-library-sha',required=True)
    p.add_argument('--plan',type=Path,required=True)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--fixture',type=Path)
    source.add_argument('--gauge',type=Path)
    p.add_argument('--expected-input-sha',default=RAW_SHA)
    p.add_argument('--expected-prepared-sha',default=PREPARED_SHA)
    p.add_argument('--reference-propagator',type=Path,required=True)
    p.add_argument('--backend',choices=['arm','x86'],required=True)
    p.add_argument('--allocation',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--diagnostic',action='store_true',help='Explicitly unranked setup/profile run')
    args = p.parse_args(argv)
    project = args.project.resolve()
    plan = json.loads(args.plan.read_text())
    numerical_policy=audit_numerical_environment(project,plan.get('context_environment',{}),os.environ)
    # Context variables must already be present at process startup, particularly
    # loader/OpenMP variables; changing LD_PRELOAD after importing is ineffective.
    for key,value in plan.get('context_environment',{}).items():
        if os.environ.get(key,'')!=str(value):
            raise ValueError('Launch context environment before Python/MPI startup: '+key)
    if os.environ.get('PERF_COUNTER_ROOT') or os.environ.get('LD_DEBUG'):
        raise ValueError('Ordinary cold timing excludes profiler/loader tracing')
    source_check(project,args.source_manifest,args.snapshot_sha)
    library = args.library.resolve()
    if sha(library)!=args.expected_library_sha:
        raise ValueError('Measured library differs from frozen selection')
    sys.path.insert(0,str(project/'python'))
    import numpy as np
    from mpi4py import MPI
    from lqcd_cpu import Solver
    from lqcd_cpu.io import read_lime_gauge,read_lime_metadata
    from lqcd_cpu.smearing import stout_smear
    from lqcd_cpu.propagator import SOLVE_TUNING_KEYS,_solve_options
    from lqcd_cpu.propagator_io import write_propagator
    comm = MPI.COMM_WORLD
    rank,ranks = comm.rank,comm.size
    if not MPI.Is_thread_main():
        raise RuntimeError('Collective cold workflow must run on MPI main thread')
    case,setup_threads,placement_threads = require_plan(plan,SOLVE_TUNING_KEYS)
    launcher_resources=validate_launcher_resources(os.environ,placement_threads)
    if ranks>16 or 64%ranks or (64//ranks)%4:
        raise ValueError('Ranks must leave complete 4-time-site aggregates')
    agreements = comm.allgather((vars(args),plan))
    if any(row!=agreements[0] for row in agreements):
        raise ValueError('Arguments and plan must agree across ranks')
    def guard(function):
        value,error = None,None
        try:
            value = function()
        except Exception as exc:
            error = str(exc)
        errors = comm.allgather(error)
        if any(errors):
            raise RuntimeError('Collective cold workflow: '+repr(errors))
        return value
    def root(function):
        return comm.bcast(guard(lambda:function() if rank==0 else None),root=0)
    output = args.output.resolve()
    root(lambda:output.mkdir(parents=True,exist_ok=False))
    os.environ['LQCD_VERBOSE']='0'
    os.environ['LQCD_HALO_PROFILE']='0'
    for key in SOLVE_TUNING_KEYS:
        if key not in plan['context_environment']:
            os.environ.pop(key,None)
    resources = comm.allgather(dict(rank=rank,cpus=sorted(os.sched_getaffinity(0)),
        **launcher_resources,
        omp_places=os.environ.get('OMP_PLACES'),omp_proc_bind=os.environ.get('OMP_PROC_BIND')))
    guard(lambda:None if len(os.sched_getaffinity(0))==placement_threads else
          (_ for _ in ()).throw(ValueError('Actual rank placement differs from plan')))
    mode = 'lime' if args.gauge else 'canonical_fixture'
    scope = ('profile_' if args.diagnostic else '')+'cold_'+mode+'_to_first12'
    configuration = dict(context_environment=plan['context_environment'],solve_environment=case.get('environment',{}),
        threads=case['threads'],batch=case['batch'],ranks=ranks,block=[6,6,6,4],seed=1024)
    for key,value in [('setup_threads',setup_threads),('placement_threads',placement_threads)]:
        if value!=case['threads']:
            configuration[key]=value
    report = dict(PHYSICS,complete=False,measurements_complete=False,timing_scope=scope,
        backend=args.backend,source_manifest_sha256=args.snapshot_sha,library_sha256=args.expected_library_sha,
        library_path=str(library),library=str(library),input_sha256=args.expected_input_sha,
        gauge_sha256=args.expected_input_sha,grid_xyzt=[1,1,1,ranks],configuration=configuration,
        zero_initial_guess=True,initial_guess='zero for all12, first solve on fresh hierarchy; no warmup',
        samples=[],verification=dict(complete=False,passed=False),resources=resources,phases={},
        numerical_environment_policy=numerical_policy,
        diagnostic=args.diagnostic,rank_eligible=False if args.diagnostic else None,
        reference_propagator=str(args.reference_propagator.resolve()),wrapper_sha256=root(lambda:sha(__file__)),
        cache_state='OS/storage caches uncontrolled; cold means fresh process/hierarchy, never drop_caches',
        clock_includes='Input hashing/metadata/read, optional stout, canonical field check, context/load/setup and first12',
        clock_excludes='Python/MPI startup, source/library checks, output arrays, context destruction and independent verification',
        stage_sum_warning='Stage rank maxima do not sum to the continuous rank-maximum cold wall time')
    root(lambda:atomic(output/'result.json',report))
    def timed(name,function):
        comm.Barrier()
        begin = time.perf_counter()
        value = guard(function)
        report['phases'][name] = comm.allreduce(time.perf_counter()-begin,op=MPI.MAX)
        return value
    comm.Barrier()
    cold_begin = time.perf_counter()
    solver = None
    try:
        if args.gauge:
            metadata = timed('lime_metadata_seconds',lambda:read_lime_metadata(str(args.gauge)))
            guard(lambda:None if tuple(metadata['lattice_xyzt'])==tuple(PHYSICS['lattice_xyzt']) else
                  (_ for _ in ()).throw(ValueError('Original LIME lattice differs from frozen problem')))
            actual_input = timed('input_sha_seconds',lambda:root(lambda:sha(args.gauge)))
            if actual_input!=args.expected_input_sha:
                raise ValueError('Original LIME SHA differs from frozen input')
            gauge = timed('gauge_read_seconds',lambda:read_lime_gauge(str(args.gauge),
                (1,1,1,ranks),(0,0,0,rank),comm=comm,checksum=True))
            gauge = timed('stout_seconds',lambda:stout_smear(gauge,steps=1,rho=.125,dir_ignore=4,comm=comm))
        else:
            fixture = args.fixture.resolve()
            previous = timed('fixture_metadata_seconds',lambda:json.loads((fixture/'result.json').read_text()))
            guard(lambda:None if not any(previous.get(key)!=value for key,value in PHYSICS.items())
                and previous.get('gauge_sha256')==args.expected_input_sha else
                (_ for _ in ()).throw(ValueError('Frozen fixture physics/input provenance differs')))
            oldranks = previous['grid_xyzt'][3]
            if previous['grid_xyzt'][:3]!=[1,1,1] or 64%oldranks:
                raise ValueError('Unsupported frozen fixture decomposition')
            def load_fixture():
                nt,oldnt = 64//ranks,64//oldranks
                parts=[]
                for owner in range(oldranks):
                    lo,hi=max(rank*nt,owner*oldnt),min((rank+1)*nt,(owner+1)*oldnt)
                    if lo<hi:
                        value=np.load(fixture/f'gauge_rank{owner:05d}.npy',mmap_mode='r',allow_pickle=False)
                        if value.shape!=(oldnt,24,24,24,4,3,3) or value.dtype!=np.dtype('<c16') or not value.flags.c_contiguous:
                            raise ValueError('Unexpected canonical gauge layout/dtype')
                        parts.append(np.array(value[lo-owner*oldnt:hi-owner*oldnt],copy=True))
                return np.concatenate(parts,axis=0)
            gauge = timed('gauge_read_seconds',load_fixture)
            report['phases']['stout_seconds']=0.0
            report['input_hash_evidence']='Frozen original-LIME provenance declaration; actual prepared gauge bytes rehashed below'
        # Same global lexical raw-byte hash regardless of rank decomposition.
        # The validation communication/checksum cost is explicitly inside clock.
        def prepared_hash():
            valid = gauge.dtype==np.dtype('<c16') and gauge.flags.c_contiguous and gauge.shape==(64//ranks,24,24,24,4,3,3)
            guard(lambda:None if valid else (_ for _ in ()).throw(ValueError('Invalid prepared field')))
            local = gauge.view(np.uint8)
            value = hashlib.sha256() if rank==0 else None
            buffer = np.empty(local.nbytes,dtype=np.uint8) if rank==0 else None
            for owner in range(ranks):
                if owner==0 and rank==0:
                    value.update(local)
                elif rank==owner:
                    comm.Send([local,MPI.BYTE],dest=0,tag=8212)
                elif rank==0:
                    comm.Recv([buffer,MPI.BYTE],source=owner,tag=8212)
                    value.update(buffer)
            return comm.bcast(value.hexdigest() if rank==0 else None,root=0)
        actual_prepared = timed('canonical_gauge_check_seconds',prepared_hash)
        report['prepared_gauge_sha256']=actual_prepared
        if actual_prepared!=args.expected_prepared_sha:
            raise ValueError('Prepared gauge differs from canonical bytes: expected '+args.expected_prepared_sha+' actual '+actual_prepared)
        report['comparison_key']=dict(host=socket.gethostname(),allocation=args.allocation,
            input_sha256=args.expected_input_sha,prepared_gauge_manifest_sha256=actual_prepared,scope=scope)
        solver = timed('context_create_seconds',lambda:Solver([24,24,24,64],[1,1,1,ranks],
            mass=-.277,csw=1.160920226,block=[6,6,6,4],seed=1024,threads=setup_threads,
            normalization='mass',backend=args.backend,library=library,comm=comm))
        capabilities = guard(lambda:dict(solver.capabilities))
        guard(lambda:None if capabilities.get('backend')==args.backend and capabilities.get('device')=='cpu' else
              (_ for _ in ()).throw(ValueError('Actually loaded solver capabilities differ from selected CPU backend')))
        report['capabilities']=capabilities
        timed('gauge_load_clover_seconds',lambda:solver.load_gauge(gauge,'lex'))
        report['native_setup_seconds']=timed('setup_wall_seconds',solver.setup)
        timed('set_solve_threads_seconds',lambda:solver.set_threads(case['threads']))
        os.environ['LQCD_RHS_BATCH']=str(case['batch'])
        with _solve_options(case.get('environment',{})):
            comm.Barrier()
            api_begin=time.perf_counter()
            propagator,stats=solver.solve_propagator((0,0,0,0),1e-8,source_scale=1.,layout='lex')
            returned=time.perf_counter()  # stop BOTH clocks before validation, reductions, output or close
        cold_wall=comm.allreduce(returned-cold_begin,op=MPI.MAX)
        api_wall=comm.allreduce(returned-api_begin,op=MPI.MAX)
        guard(lambda:None if len(stats)==12 and all(s['converged'] and np.isfinite(s['true_residual'])
            and 0<=s['true_residual']<=1e-8 for s in stats) else
            (_ for _ in ()).throw(ValueError('Full12 residual/statistics failure')))
        report.update(cold_wall_seconds=cold_wall,first12_api_seconds=api_wall,
            samples=[dict(repeat=0,warmup=False,wall_seconds=cold_wall,first12_api_seconds=api_wall,stats=stats)])
    except Exception as error:
        report.update(error=str(error),partial_elapsed_seconds=comm.allreduce(time.perf_counter()-cold_begin,op=MPI.MAX))
        root(lambda:atomic(output/'result.json',report))
        raise
    finally:
        if solver is not None:
            timed('context_destroy_seconds_outside_cold',solver.close)
    # Independent verifier requires saved gauges and propagator; every byte of
    # this I/O and every independent scalar/solution check is outside cold wall.
    guard(lambda:np.save(output/f'gauge_rank{rank:05d}.npy',gauge,allow_pickle=False))
    write_propagator(output/'propagator.npy',propagator,[24,24,24,64],[1,1,1,ranks],[0,0,0,rank],comm)
    root(lambda:fsync_file(output/'propagator.npy'))
    report['propagator_sha256']=root(lambda:sha(output/'propagator.npy'))
    report['output_gauge_files']=comm.allgather((rank,guard(lambda:sha(output/f'gauge_rank{rank:05d}.npy'))))
    guard(lambda:None if sha(library)==args.expected_library_sha else
          (_ for _ in ()).throw(ValueError('Measured library changed during run')))
    report.update(complete=True,measurements_complete=True)
    root(lambda:atomic(output/'result.json',report))
    if rank==0:
        print(json.dumps(dict(timing_scope=scope,cold_wall_seconds=cold_wall,first12_api_seconds=api_wall,
            prepared_gauge_sha256=actual_prepared,verification_complete=False)),flush=True)


def fsync_file(path):
    with Path(path).open('r+b') as stream:
        os.fsync(stream.fileno())


if __name__=='__main__':
    main()
