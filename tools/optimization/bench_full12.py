#!/usr/bin/env python3
"""Frozen-fixture full12 API benchmark. Run under tools/run_numa.py.

One context, balanced alternating solve configurations, no reused solutions.
Run independent validation afterwards with --verify RUN --reference EXE
--extractor EXE. No partial run is eligible for campaign promotion.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
VERIFICATION_OUTPUT_NAME = r'[a-z0-9][a-z0-9_-]{0,79}'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def sync_completed_output(path):
    # The collective mmap writer has joined all slab writes. Commit the file
    # once more after that join, before a fresh verifier process opens it.
    # This is outside every accepted timing interval; digest mismatches still
    # fail strictly and are never repaired by changing the expected digest.
    with Path(path).open('r+b') as stream:
        os.fsync(stream.fileno())


def validate_fixture(previous):
    expected = dict(complete=True, mass=-.277, csw=1.160920226,
        lattice_xyzt=[24,24,24,64], normalization='mass', source_xyzt=[0,0,0,0],
        source_scale=1., gamma_basis='DeGrand-Rossi', fermion_t_boundary=-1,
        gauge_t_boundary=1, gauge_reunitarized=False,
        stout=dict(steps=1, rho=.125, dir_ignore=4))
    for key, value in expected.items():
        if previous.get(key) != value:
            raise RuntimeError(f'Frozen fixture contract differs: {key}')
    grid = previous.get('grid_xyzt', [])
    if len(grid) != 4 or grid[:3] != [1,1,1] or type(grid[3]) is not int or grid[3] < 1 or 64 % grid[3]:
        raise RuntimeError('Invalid frozen fixture decomposition')
    if not re.fullmatch('[0-9a-f]{64}', str(previous.get('gauge_sha256', ''))):
        raise RuntimeError('Frozen fixture input SHA256 missing')


def fixture_metadata(previous):
    """Carry physical provenance only; fixture creation timings are not samples."""
    keys = ['mass','csw','lattice_xyzt','grid_xyzt','normalization','source_xyzt',
            'source_scale','gamma_basis','fermion_t_boundary','gauge_t_boundary',
            'gauge_reunitarized','stout','gauge_sha256']
    return {key:previous[key] for key in keys}


def validate_plan(plan, solve_keys):
    cases = plan.get('cases', [])
    if not cases or not isinstance(plan.get('context_environment', {}), dict):
        raise RuntimeError('Plan needs nonempty cases and context_environment object')
    managed={'OMP_NUM_THREADS','OMP_PLACES','OMP_PROC_BIND','GOMP_CPU_AFFINITY',
             'LQCD_CPU_LIBRARY','LQCD_RHS_BATCH','LQCD_VERBOSE','LQCD_HALO_PROFILE'}
    for key,value in plan.get('context_environment',{}).items():
        if key in managed:
            raise RuntimeError('Context environment conflicts with benchmark-owned '+key)
        if not isinstance(key,str) or isinstance(value,bool) or not isinstance(value,(str,int,float)):
            raise RuntimeError('Context environment needs string keys and string/finite-number values')
        if isinstance(value,(int,float)) and not math.isfinite(value):
            raise RuntimeError('Context environment needs finite values')
    names = []
    for case in cases:
        name = case.get('id', '')
        if not isinstance(name, str) or not re.fullmatch('[a-z0-9][a-z0-9_-]{0,79}', name):
            raise RuntimeError('Unique safe case IDs required')
        names.append(name)
        if type(case.get('threads')) is not int or case['threads'] < 1:
            raise RuntimeError('Positive case thread count required')
        if type(case.get('batch')) is not int or not 1 <= case['batch'] <= 12:
            raise RuntimeError('Case batch must be 1 through 12')
        environment = case.get('environment', {})
        if not isinstance(environment, dict) or set(environment) - set(solve_keys):
            raise RuntimeError('Case environment accepts only dynamic SOLVE_TUNING_KEYS; cached/setup flags need a separate context plan')
        if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) for v in environment.values()):
            raise RuntimeError('Solve-only environment values must be finite numbers')
    if len(set(names)) != len(names):
        raise RuntimeError('Unique safe case IDs required')
    maximum=max(case['threads'] for case in cases)
    for key in ['placement_threads','setup_threads']:
        if key in plan and (type(plan[key]) is not int or plan[key] < 1):
            raise RuntimeError(key+' must be a positive integer')
    placement=plan.get('placement_threads',maximum)
    if placement < maximum or plan.get('setup_threads',maximum) > placement:
        raise RuntimeError('Fine/setup teams must fit the declared rank CPU placement')


def collective(comm, function, root_only=False):
    result = error = None
    try:
        if not root_only or comm.rank == 0:
            result = function()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    errors = comm.allgather(error)
    if any(errors):
        raise RuntimeError(f'Collective benchmark operation failed: {errors}')
    return comm.bcast(result, root=0) if root_only else result


def apply_case_environment(base, case, diagnostic=False):
    os.environ.clear()
    os.environ.update(base)
    os.environ.update({k:str(v) for k,v in case.get('environment', {}).items()})
    os.environ['LQCD_RHS_BATCH'] = str(case['batch'])
    if diagnostic:
        os.environ['LQCD_VERBOSE'] = '1'


def apply_context_environment(context,solve_keys):
    # An inherited tuning variable must not silently change setup or a case
    # whose recorded solve environment requests the default.
    for key in solve_keys:
        if key not in context:os.environ.pop(key,None)
    os.environ.update({key:str(value) for key,value in context.items()})


def shared_process_thread_teams(plan):
    """Distinct fine/coarse teams switched between cases, excluding setup.

    CoarseThreadScope caps a positive request at the case's fine team. A
    constant setup-to-solve transition is covered by full12 warmup; alternating
    different solve teams in one process needs independent-process confirmation.
    """
    teams=set()
    for case in plan['cases']:
        fine=case['threads']
        cap=case.get('environment',{}).get('LQCD_COARSE_THREADS',
            plan.get('context_environment',{}).get('LQCD_COARSE_THREADS',0))
        cap=int(cap)
        teams.add((fine,min(fine,cap) if cap>0 else fine))
    return [dict(fine_threads=fine,coarse_threads=coarse) for fine,coarse in sorted(teams)]


def check_saved_artifacts(run, report):
    actual=sha(run / 'propagator.npy')
    if actual != report['propagator_sha256']:
        raise RuntimeError('Saved propagator digest mismatch: expected '+
                           report['propagator_sha256']+' actual '+actual)
    for rank, expected in report['output_gauge_files']:
        actual=sha(run / f'gauge_rank{rank:05d}.npy')
        if actual != expected:
            raise RuntimeError(f'Saved gauge rank {rank} digest mismatch: expected {expected} actual {actual}')


def verification_output_name(value):
    if not isinstance(value, str) or not re.fullmatch(VERIFICATION_OUTPUT_NAME, value):
        raise argparse.ArgumentTypeError('Verification output must be a single safe name: lowercase letters, digits, _ or -')
    return value


def verification_evidence_path(run, relative):
    # A verifier directory is one named child, never an arbitrary report path.
    # Reject links even when their target happens to remain inside this run.
    if not isinstance(relative, str) or not re.fullmatch(VERIFICATION_OUTPUT_NAME + r'/verification\.json', relative):
        raise RuntimeError('Independent verification evidence needs a safe NAME/verification.json path')
    root = Path(run).resolve()
    evidence = root / relative
    output = evidence.parent
    if (output.is_symlink() or evidence.is_symlink() or
            output.resolve() != output or evidence.resolve() != evidence):
        raise RuntimeError('Independent verification evidence must not use symlinks or escape its run')
    return evidence


def check_cached_verification(run, report, reference, extractor):
    validation = report['verification']
    if validation.get('passed') is not True or validation.get('columns') != 12:
        raise RuntimeError('Cached independent verification is not a full12 pass')
    if not math.isfinite(validation['max_true_residual']) or validation['max_true_residual'] > 1e-8:
        raise RuntimeError('Cached independent residual failed')
    evidence = verification_evidence_path(run, validation.get('evidence_relative_path', 'independent/verification.json'))
    if ('verification_driver_sha256' in validation and
            not re.fullmatch('[0-9a-f]{64}', str(validation['verification_driver_sha256']))):
        raise RuntimeError('Cached verification driver provenance needs a SHA256')
    check_saved_artifacts(run, report)
    checks = [(reference, validation['reference_sha256']),
              (extractor, validation['extractor_sha256']),
              (evidence, validation['evidence_sha256']),
              (run / 'propagator.npy', validation['propagator_sha256'])]
    if report.get('reference_propagator'):
        checks.append((report['reference_propagator'], validation['reference_propagator_sha256']))
    for path, expected in checks:
        if sha(path) != expected:
            raise RuntimeError(f'Independent verification artifact changed: {path}')


def verify(args):
    run = Path(args.verify).resolve()
    name = verification_output_name(getattr(args, 'verification_output', 'independent'))
    report = json.loads((run / 'result.json').read_text())
    if not report['measurements_complete']:
        raise RuntimeError('Incomplete benchmark cannot be independently validated')
    if report.get('verification', {}).get('complete'):
        check_cached_verification(run, report, args.reference, args.extractor)
        print(json.dumps(report['verification']))
        return
    evidence = verification_evidence_path(run, name + '/verification.json')
    output = evidence.parent
    if output.exists():
        raise RuntimeError('Interrupted validation retained; inspect and retry with --verification-output NEW_NAME')
    check_saved_artifacts(run, report)
    driver = Path(__file__).resolve()
    driver_sha = sha(driver)
    reference_sha, extractor_sha = sha(args.reference), sha(args.extractor)
    baseline_sha = sha(report['reference_propagator']) if report.get('reference_propagator') else None
    env = dict(os.environ, OMP_NUM_THREADS='4', OMP_PLACES='cores', OMP_PROC_BIND='close')
    subprocess.run([sys.executable, str(PROJECT / 'benchmarks/runtime/verify_fixture_propagator.py'),
                    str(run), str(Path(args.reference).resolve()),
                    str(Path(args.extractor).resolve()), str(output)], env=env, check=True)
    evidence = verification_evidence_path(run, name + '/verification.json')
    independent = json.loads(evidence.read_text())
    residuals = [r['residual'] for r in independent['columns']]
    if not independent['complete'] or len(residuals) != 12 or not all(math.isfinite(r) and 0 <= r <= 1e-8 for r in residuals):
        raise RuntimeError('Independent full12 verification failed')
    validation = dict(complete=True, passed=True, columns=12,
        max_true_residual=max(residuals), reference_sha256=independent['reference_sha256'],
        method=independent['method'], evidence_sha256=sha(evidence),
        evidence_relative_path=evidence.relative_to(run).as_posix(),
        verification_driver_sha256=driver_sha,
        propagator_sha256=independent['propagator_sha256'], extractor_sha256=extractor_sha)
    if report.get('reference_propagator'):
        import numpy as np
        baseline = np.load(report['reference_propagator'], mmap_mode='r')
        measured = np.load(run / 'propagator.npy', mmap_mode='r')
        if baseline.shape != measured.shape:
            raise RuntimeError('Baseline solution shape mismatch')
        differences, norms = [0.] * 12, [0.] * 12
        for t in range(64):
            for spin in range(4):
                for color in range(3):
                    col = spin * 3 + color
                    x = np.asarray(measured[t, ..., :, spin, :, color])
                    y = np.asarray(baseline[t, ..., :, spin, :, color])
                    differences[col] += float(np.vdot(x-y, x-y).real)
                    norms[col] += float(np.vdot(y, y).real)
        errors = [(a / b)**.5 if b > 0 else float('inf') for a, b in zip(differences, norms)]
        if not all(__import__('math').isfinite(e) and e <= 1e-6 for e in errors):
            raise RuntimeError('Solution difference against frozen output exceeds 1e-6')
        validation.update(solution_relative_error=max(errors), solution_relative_errors=errors,
                          reference_propagator_sha256=baseline_sha)
    check_saved_artifacts(run, report)
    if sha(args.reference) != reference_sha or sha(args.extractor) != extractor_sha or independent['reference_sha256'] != reference_sha:
        raise RuntimeError('Independent executable changed during validation')
    if baseline_sha and sha(report['reference_propagator']) != baseline_sha:
        raise RuntimeError('Baseline propagator changed during validation')
    if sha(driver) != driver_sha:
        raise RuntimeError('Verification driver changed during validation')
    report['verification'] = validation
    report['complete'] = True
    atomic(run / 'result.json', report)
    print(json.dumps(validation), flush=True)


def benchmark(args):
    import numpy as np
    from mpi4py import MPI
    sys.path.insert(0, str(PROJECT / 'python'))
    sys.path.insert(0, str(PROJECT / 'tools'))
    from lqcd_cpu import Solver
    from lqcd_cpu.propagator_io import write_propagator
    from lqcd_cpu.propagator import SOLVE_TUNING_KEYS
    from probe_host import probe
    comm = MPI.COMM_WORLD
    rank, ranks = comm.rank, comm.size
    plan = collective(comm, lambda: json.loads(Path(args.plan).read_text()))
    collective(comm, lambda: validate_plan(plan, SOLVE_TUNING_KEYS))
    plans = comm.allgather(plan)
    if any(p != plans[0] for p in plans):
        raise RuntimeError('Plan differs across MPI ranks')
    fixture = Path(args.fixture).resolve()
    previous = collective(comm, lambda: json.loads((fixture / 'result.json').read_text()))
    collective(comm, lambda: validate_fixture(previous))
    if ranks > 16 or 64 % ranks:
        raise RuntimeError('Invalid t-slab decomposition')
    out = Path(args.output).resolve()
    collective(comm, lambda: out.mkdir(parents=True, exist_ok=False), root_only=True)
    apply_context_environment(plan.get('context_environment', {}),SOLVE_TUNING_KEYS)
    library = Path(args.library).resolve()
    library_sha = collective(comm, lambda: sha(library))
    if len(set(comm.allgather(library_sha))) != 1:
        raise RuntimeError('Library differs across MPI ranks')
    os.environ['LQCD_CPU_LIBRARY'] = str(library)
    # Diagnostics are additional full12 solves, never included in accepted samples.
    os.environ['LQCD_VERBOSE'] = '0'
    os.environ['LQCD_HALO_PROFILE'] = '1' if args.diagnostic else '0'
    nt, oldnt = 64 // ranks, 64 // previous['grid_xyzt'][3]
    parts = []
    fixture_hashes = []
    for oldrank in range(previous['grid_xyzt'][3]):
        begin, end = max(rank*nt, oldrank*oldnt), min((rank+1)*nt, (oldrank+1)*oldnt)
        if begin < end:
            path = fixture / f'gauge_rank{oldrank:05d}.npy'
            values = np.load(path, mmap_mode='r')
            parts.append(np.array(values[begin-oldrank*oldnt:end-oldrank*oldnt], copy=True))
            fixture_hashes.append((oldrank, sha(path)))
    gauge = np.concatenate(parts, axis=0)
    del parts
    # Hash the ordered global raw gauge bytes; unlike hashes of rank-local
    # slices, this fingerprint is invariant under the candidate MPI rank count.
    def global_gauge_sha():
        value = hashlib.sha256()
        for oldrank in range(previous['grid_xyzt'][3]):
            array = np.load(fixture / f'gauge_rank{oldrank:05d}.npy', mmap_mode='r', allow_pickle=False)
            if array.shape != (oldnt,24,24,24,4,3,3) or array.dtype != np.dtype('<c16') or not array.flags.c_contiguous:
                raise RuntimeError('Invalid frozen gauge array')
            value.update(array.view(np.uint8))
        return value.hexdigest()
    prepared_sha = collective(comm, global_gauge_sha, root_only=True)
    resources = comm.allgather(dict(rank=rank, cpus=sorted(os.sched_getaffinity(0)),
        omp_places=os.environ.get('OMP_PLACES'), omp_proc_bind=os.environ.get('OMP_PROC_BIND')))
    all_hashes = comm.allgather(fixture_hashes)
    metadata = fixture_metadata(previous)
    metadata.update(complete=False, measurements_complete=False, backend=args.backend,
        propagator_output_protocol='collective slab writer, final joined fsync, SHA256, independent reopen',
        library=str(library), library_path=str(library), library_sha256=library_sha,
        source_manifest_sha256=args.snapshot_sha, input_sha256=previous['gauge_sha256'],
        gauge_sha256=previous['gauge_sha256'], grid_xyzt=[1, 1, 1, ranks],
        lattice_xyzt=[24, 24, 24, 64], source_xyzt=[0, 0, 0, 0], source_scale=1.,
        normalization='mass', fermion_t_boundary=-1, gauge_t_boundary=1,
        timing_scope='profile_full12_api' if args.diagnostic else 'full12_api', zero_initial_guess=True, samples=[], resources=resources,
        shared_process_thread_teams=shared_process_thread_teams(plan),
        fixture_files=sorted(set(pair for values in all_hashes for pair in values)),
        fixture_report_sha256=collective(comm,lambda:sha(fixture/'result.json')),
        comparison_key=dict(host=socket.gethostname(), allocation=args.allocation,
                            problem='24x24x24x64-m-.277-csw1.160920226-stout1-rho.125-point0000',
                            input_sha256=previous['gauge_sha256'], prepared_gauge_manifest_sha256=prepared_sha,
                            scope='profile_full12_api' if args.diagnostic else 'full12_api'),
        environment={k:v for k,v in os.environ.items() if k.startswith(('LQCD_', 'OMP_', 'OMPI_MCA_', 'GOMP_', 'LD_'))},
        reference_propagator=str(Path(args.reference_propagator).resolve()) if args.reference_propagator else None,
        verification=dict(complete=False, passed=False))
    if rank == 0:
        atomic(out / 'host.json', probe())
        atomic(out / 'plan.json', plan)
    cases = plan['cases']
    setup_threads=plan.get('setup_threads',max(c['threads'] for c in cases))
    placement_widths=[len(r['cpus']) for r in resources]
    if len(set(placement_widths))!=1 or min(placement_widths)<max(c['threads'] for c in cases):
        raise RuntimeError('This driver requires equal, sufficient per-rank CPU placement widths')
    placement_threads=placement_widths[0]
    if plan.get('placement_threads',placement_threads)!=placement_threads:
        raise RuntimeError('Declared placement differs from actual rank CPU mask')
    names = [c['id'] for c in cases]
    reports = {}
    for case in cases:
        report = dict(metadata)
        report['samples'] = []
        report['configuration'] = dict(context_environment=plan.get('context_environment', {}),
            solve_environment=case.get('environment', {}), threads=case['threads'], batch=case['batch'],
            ranks=ranks, block=[6, 6, 6, 4], seed=1024)
        if placement_threads!=case['threads']:
            report['configuration']['placement_threads']=placement_threads
        if setup_threads!=case['threads']:
            report['configuration']['setup_threads']=setup_threads
        reports[case['id']] = report
        if rank == 0:
            (out / case['id']).mkdir()
            atomic(out / case['id'] / 'result.json', report)
    comm.Barrier()
    final_propagators = {}
    with Solver([24,24,24,64], [1,1,1,ranks], mass=-.277, csw=1.160920226,
                block=[6,6,6,4], seed=1024, threads=setup_threads,
                normalization='mass', backend=args.backend, library=library) as solver:
        capabilities=collective(comm,lambda:solver.capabilities)
        if capabilities.get('backend')!=args.backend or capabilities.get('device')!='cpu':
            raise RuntimeError('Loaded solver capabilities differ from the requested CPU backend')
        for report in reports.values():report['capabilities']=dict(capabilities)
        solver.load_gauge(gauge, 'lex')
        setup = solver.setup()
        base_environment = dict(os.environ)
        for repeat in range(args.repeats + 1):
            order = cases if repeat % 2 == 0 else list(reversed(cases))
            for case in order:
                apply_case_environment(base_environment, case)
                solver.set_threads(case['threads'])
                comm.Barrier()
                start = time.perf_counter()
                propagator, stats = solver.solve_propagator((0,0,0,0), 1e-8, layout='lex')
                elapsed = comm.allreduce(time.perf_counter()-start, op=MPI.MAX)
                if len(stats) != 12 or not all(s['converged'] and np.isfinite(s['true_residual']) and s['true_residual'] <= 1e-8 for s in stats):
                    raise RuntimeError('Full12 true residual failure')
                row = dict(repeat=repeat, warmup=(repeat==0), wall_seconds=elapsed, stats=stats,
                           order_in_round=[c['id'] for c in order].index(case['id']))
                report = reports[case['id']]
                report['setup_seconds'] = setup
                report['samples'].append(row)
                if rank == 0:
                    print('FULL12 '+json.dumps(dict(case=case['id'], **row)), flush=True)
                    atomic(out / case['id'] / 'result.json', report)
                if repeat == args.repeats:
                    final_propagators[case['id']] = propagator
                del propagator
        if args.diagnostic:
            for case in cases:
                apply_case_environment(base_environment, case, diagnostic=True)
                solver.set_threads(case['threads'])
                if rank == 0:
                    print('DIAGNOSTIC_BEGIN '+case['id'], flush=True)
                propagator, stats = solver.solve_propagator((0,0,0,0), 1e-8, layout='lex')
                del propagator
                if rank == 0:
                    print('DIAGNOSTIC_END '+case['id'], flush=True)
    if collective(comm, lambda: sha(library)) != library_sha:
        raise RuntimeError('Measured library changed during benchmark')
    # All timed rounds finish before any large gauge/propagator output I/O.
    for name in names:
        target = out / name
        collective(comm, lambda: np.save(target / f'gauge_rank{rank:05d}.npy', gauge, allow_pickle=False))
        write_propagator(target / 'propagator.npy', final_propagators.pop(name), [24,24,24,64],
                         [1,1,1,ranks], [0,0,0,rank], comm)
        collective(comm,lambda:sync_completed_output(target/'propagator.npy'),root_only=True)
        reports[name]['propagator_sha256'] = collective(comm, lambda: sha(target / 'propagator.npy'), root_only=True)
        gauge_hash = collective(comm, lambda: sha(target / f'gauge_rank{rank:05d}.npy'))
        reports[name]['output_gauge_files'] = comm.allgather((rank, gauge_hash))
    for name, report in reports.items():
        report['measurements_complete'] = True
        # Existing scalar verifier requires complete measurement output.
        report['complete'] = True
        if rank == 0:
            atomic(out / name / 'result.json', report)
    if rank == 0:
        atomic(out / 'measurements.json', dict(complete=True, cases=names))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verify')
    p.add_argument('--reference')
    p.add_argument('--extractor')
    p.add_argument('--verification-output', type=verification_output_name, default='independent',
                   help='new single-level evidence directory for --verify (default: independent)')
    p.add_argument('--fixture')
    p.add_argument('--plan')
    p.add_argument('--library')
    p.add_argument('--backend', choices=['arm', 'x86'])
    p.add_argument('--output')
    p.add_argument('--allocation')
    p.add_argument('--snapshot-sha')
    p.add_argument('--reference-propagator')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--diagnostic', action='store_true')
    args = p.parse_args()
    if args.verify:
        if not args.reference or not args.extractor:
            p.error('--verify requires --reference and --extractor')
        verify(args)
    else:
        if any(not getattr(args, k) for k in ['fixture','plan','library','backend','output','allocation','snapshot_sha']) or args.repeats < 3:
            p.error('Benchmark requires fixture, plan, library, backend, output, allocation, snapshot-sha, and >=3 steady repeats')
        benchmark(args)


if __name__ == '__main__':
    main()
