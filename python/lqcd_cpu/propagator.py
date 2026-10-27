"""CPU-only LIME -> optional stout -> Wilson-Clover point propagator workflow."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time

import numpy as np
from mpi4py import MPI

from . import Solver
from .io import read_lime_gauge, read_lime_metadata
from .smearing import stout_smear
from .propagator_io import write_propagator

SOLVE_TUNING_KEYS = {
    'LQCD_MG_SAP_STEPS', 'LQCD_MG_SAP_CYCLES', 'LQCD_MG_COARSE_IT',
    'LQCD_MG_COARSE_TOL', 'LQCD_CORRECTION_BASE_TOL',
    'LQCD_FLOAT_CORRECTION_VERIFY', 'LQCD_FINE_TEAM_FUSED',
    'LQCD_COARSE_CGS2', 'LQCD_RESTRICT_FLOAT', 'LQCD_GCR_FUSED'}


@contextmanager
def _solve_options(settings):
    """Apply solve-only tuning after setup, then restore caller environment."""
    previous = {key: os.environ.get(key) for key in settings}
    os.environ.update({key: str(value) for key, value in settings.items()})
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _guard(comm, function):
    """Finish rank-local work everywhere before reporting any local exception."""
    error = None
    value = None
    try:
        value = function()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    errors = comm.allgather(error)
    for rank, message in enumerate(errors):
        if message is not None:
            raise RuntimeError(f"rank {rank}: {message}")
    return value


def _root(comm, function):
    value = _guard(comm, lambda: function() if comm.rank == 0 else None)
    return comm.bcast(value, root=0)


def _hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _measure(comm, function):
    comm.Barrier()
    start = time.perf_counter()
    value = function()
    return value, comm.allreduce(time.perf_counter() - start, op=MPI.MAX)


def solve_lime_propagator(gauge_path, output, *, mass=None, csw=None,
                          block=(6, 6, 6, 4), point=(0, 0, 0, 0),
                          stout_steps=0, stout_rho=0.125, stout_dir_ignore=4,
                          tol=1e-8, repeats=2, threads=None, seed=1024,
                          normalization='mass', source_scale=1., checksum=True,
                          save_gauge=False, library=None, solve_tuning=None, backend=None, comm=MPI.COMM_WORLD):
    """Write propagator.npy (PyQUDA-loadable) and result.json into a fresh directory.

    Gauge I/O and stout execute on CPU, without importing QUDA/CUDA/PyTorch.
    Current production geometry is one equal t slab per MPI rank, two levels,
    isotropic Wilson-Clover and antiperiodic fermion time. Gauge is periodic.
    mass/csw default to unambiguous LIME metadata; missing values require an
    explicit argument. Stout is opt-in and always recorded. All output sources
    have the stated amplitude (default unit delta), independent of normalization.
    Repeats reuse setup and always start every column from zero. I/O, stout,
    setup and complete 12-column API wall times are recorded separately.
    """
    if not MPI.Is_thread_main():
        raise RuntimeError('propagator workflow must run on the MPI main thread')
    solve_tuning = {} if solve_tuning is None else solve_tuning
    gauge_path = str(Path(gauge_path).expanduser().resolve())
    output = Path(output).expanduser().resolve()
    options = dict(gauge=gauge_path, output=str(output), mass=mass, csw=csw, backend=backend,
                   block=list(block), point=list(point), stout_steps=stout_steps,
                   stout_rho=stout_rho, stout_dir_ignore=stout_dir_ignore,
                   tol=tol, repeats=repeats, seed=seed, normalization=normalization,
                   source_scale=source_scale, checksum=checksum, save_gauge=save_gauge,
                   library=str(library) if library is not None else None,
                   solve_tuning=solve_tuning)
    options['tuning_environment'] = {
        key: value for key, value in sorted(os.environ.items())
        if key.startswith(('LQCD_MG_', 'LQCD_CORRECTION_')) or key in (
            'LQCD_FLOAT_CORRECTION_VERIFY', 'LQCD_FINE_TEAM_FUSED',
            'LQCD_LOCAL_CONTIGUOUS', 'LQCD_RESTRICT_FLOAT', 'LQCD_GCR_FUSED',
            'LQCD_ARM_SVE', 'LQCD_ARM_SVE_PLANNED', 'LQCD_ARM_SVE_TRANSFER', 'LQCD_HBM',
            'LQCD_COARSE_FUSED', 'LQCD_ARM_COARSE_SVE', 'LQCD_HBW_ALLOC',
            'LQCD_SAP_EO', 'LQCD_COARSE_EO', 'LQCD_COARSE_CGS2', 'LQCD_SETUP_UPDATE',
            'LQCD_ADAPTIVE_CORRECTION', 'LQCD_HALO_OVERLAP', 'LQCD_RHS_BATCH')}
    configs = comm.allgather(options)
    if any(c != configs[0] for c in configs):
        raise ValueError('workflow numerical and output settings must agree across ranks')
    metadata = _guard(comm, lambda: read_lime_metadata(gauge_path))
    if any(m != metadata for m in comm.allgather(metadata)):
        raise ValueError('LIME metadata differs across ranks')
    lattice = tuple(metadata['lattice_xyzt'])
    grid = (1, 1, 1, comm.size)
    coords = (0, 0, 0, comm.rank)

    def validate():
        if not isinstance(solve_tuning, dict) or set(solve_tuning) - SOLVE_TUNING_KEYS:
            raise ValueError('unknown solve-only tuning parameter')
        for key, value in solve_tuning.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'{key} must be a finite JSON number')
            bounds = {'LQCD_MG_SAP_STEPS': (1, 32), 'LQCD_MG_SAP_CYCLES': (1, 8),
                      'LQCD_MG_COARSE_IT': (1, 200), 'LQCD_MG_COARSE_TOL': (1e-4, .9),
                      'LQCD_CORRECTION_BASE_TOL': (1e-6, .1)}
            low, high = bounds.get(key, (0, 1))
            if not low <= value <= high or (key not in (
                    'LQCD_MG_COARSE_TOL', 'LQCD_CORRECTION_BASE_TOL') and value != int(value)):
                raise ValueError(f'{key} outside supported range')
        resolved_mass = metadata.get('mass') if mass is None else float(mass)
        resolved_csw = metadata.get('csw') if csw is None else float(csw)
        if resolved_mass is None or resolved_csw is None:
            raise ValueError('LIME lacks unambiguous mass/csw; supply --mass and --csw explicitly')
        if not math.isfinite(resolved_mass) or resolved_mass <= -4 or not math.isfinite(resolved_csw):
            raise ValueError('mass must be finite and > -4; csw must be finite')
        if len(block) != 4 or any(type(b) is not int or b <= 0 for b in block):
            raise ValueError('block requires four positive integers')
        if any(n % b or n // b < 4 or (n // b) % 2 for n, b in zip(lattice, block)):
            raise ValueError('native MG requires even coarse extents >=4')
        if lattice[3] % comm.size or (lattice[3] // comm.size) % block[3]:
            raise ValueError('MPI ranks must leave complete t-slab aggregates')
        if block[0] % 2 or any(n % 2 for n in lattice):
            raise ValueError('EO needs even x block and even lattice extents')
        if (lattice[3] // comm.size) % 2:
            raise ValueError('local time extent must be even')
        if len(point) != 4 or any(type(p) is not int or not 0 <= p < n for p, n in zip(point, lattice)):
            raise ValueError('source must be a global XYZT coordinate inside the lattice')
        if type(repeats) is not int or repeats < 1 or not 0 < tol < 1:
            raise ValueError('repeats >=1 and 0<tol<1 required')
        if type(stout_steps) is not int or stout_steps < 0 or not 0 <= stout_dir_ignore <= 4:
            raise ValueError('invalid stout steps/direction')
        if not math.isfinite(stout_rho) or not math.isfinite(source_scale) or source_scale == 0:
            raise ValueError('stout rho/source amplitude must be finite, amplitude nonzero')
        if normalization not in ('mass', 'kappa'):
            raise ValueError('normalization must be mass or kappa')
        return resolved_mass, resolved_csw

    mass, csw = _guard(comm, validate)
    _root(comm, lambda: output.mkdir(parents=True, exist_ok=False))
    input_hash = _root(comm, lambda: _hash(gauge_path))
    total_begin = time.perf_counter()
    gauge, io_seconds = _measure(comm, lambda: read_lime_gauge(
        gauge_path, grid, coords, comm=comm, checksum=checksum))
    gauge, smear_seconds = _measure(comm, lambda: stout_smear(
        gauge, steps=stout_steps, rho=stout_rho,
        dir_ignore=stout_dir_ignore, comm=comm))
    # Raw F links are preserved as stored, unlike some readers that silently
    # project single precision to SU(3). This policy is part of the manifest.
    if save_gauge:
        _guard(comm, lambda: np.save(output / f'gauge_rank{comm.rank:05d}.npy', gauge,
                                    allow_pickle=False))
    samples = []
    with Solver(lattice, grid, mass=mass, csw=csw, block=block,
                threads=threads, seed=seed, normalization=normalization,
                library=library, backend=backend, comm=comm) as solver:
        resources = comm.allgather(dict(rank=comm.rank, threads=solver.config.threads,
                                       omp_places=os.environ.get('OMP_PLACES'),
                                       cpu_affinity=sorted(os.sched_getaffinity(0)),
                                       cpu_affinity_scope='calling thread; OpenMP team places above'))
        _, load_seconds = _measure(comm, lambda: solver.load_gauge(gauge, layout='lex'))
        setup_seconds = solver.setup()
        with _solve_options(solve_tuning):
            for run in range(repeats):
                if run:
                    del propagator
                (propagator, stats), elapsed = _measure(comm, lambda: solver.solve_propagator(
                    point, tol, source_scale=source_scale, layout='lex'))
                if len(stats) != 12 or any(not s['converged'] or s['true_residual'] > tol for s in stats):
                    raise RuntimeError('one or more propagator columns failed the full residual gate')
                samples.append(dict(wall_seconds=elapsed, stats=stats))
                if comm.rank == 0:
                    print(f'propagator round {run+1}: {elapsed:.6f} s, '
                          f'max residual {max(s["true_residual"] for s in stats):.6e}', flush=True)
        capabilities = solver.capabilities
        actual_backend = solver._backend_name
        loaded_library = str(Path(solver.lib._name).resolve())
    _, output_seconds = _measure(comm, lambda: write_propagator(
        output / 'propagator.npy', propagator, lattice, grid, coords, comm=comm))
    report = dict(format_version=1, complete=True, input=options, lime=metadata, backend=actual_backend,
                  library=loaded_library, library_sha256=_root(comm, lambda: _hash(loaded_library)),
                  gauge_sha256=input_hash, lattice_xyzt=lattice, grid_xyzt=grid,
                  mass=mass, csw=csw,
                  mass_source='lime' if options['mass'] is None else 'explicit',
                  csw_source='lime' if options['csw'] is None else 'explicit',
                  normalization=normalization, source_xyzt=list(point), source_scale=source_scale,
                  equation='Mx=b' if normalization == 'mass' else '(2*kappa*M)x=b',
                  gamma_basis='DeGrand-Rossi', fermion_t_boundary=-1, gauge_t_boundary=1,
                  gauge_reunitarized=False,
                  stout=dict(steps=stout_steps, rho=stout_rho, dir_ignore=stout_dir_ignore),
                  block_xyzt=list(block), seed=seed, resources=resources, capabilities=capabilities,
                  initial_guess='zero_for_every_column_every_round',
                  columns='source_spin*3+source_color', output_file='propagator.npy',
                  output_layout='global [t,z,y,x,sink_spin,source_spin,sink_color,source_color]',
                  setup_seconds=setup_seconds, lime_read_seconds=io_seconds,
                  stout_seconds=smear_seconds, gauge_load_clover_seconds=load_seconds,
                  output_seconds=output_seconds, samples=samples,
                  first_seconds=samples[0]['wall_seconds'],
                  max_true_residual=max(s['true_residual'] for r in samples for s in r['stats']))
    if repeats >= 2:
        report['second_seconds'] = samples[1]['wall_seconds']
        report['steady_median_seconds'] = statistics.median(s['wall_seconds'] for s in samples[1:])
    report['total_wall_seconds'] = comm.allreduce(time.perf_counter() - total_begin, op=MPI.MAX)
    _root(comm, lambda: (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n'))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gauge', required=True, help='single-file SciDAC/ILDG LIME gauge')
    parser.add_argument('--output', type=Path, required=True, help='new output directory (never overwritten)')
    parser.add_argument('--backend', choices=['x86', 'arm'], help='hardware backend; default selects executing CPU architecture')
    parser.add_argument('--mass', type=float, help='override LIME valence mass')
    parser.add_argument('--csw', type=float, help='override LIME Clover coefficient')
    parser.add_argument('--block', nargs=4, type=int, default=(6, 6, 6, 4), metavar=('X','Y','Z','T'))
    parser.add_argument('--source', nargs=4, type=int, default=(0, 0, 0, 0), metavar=('X','Y','Z','T'))
    parser.add_argument('--source-scale', type=float, default=1., help='point amplitude, default unit delta')
    parser.add_argument('--normalization', choices=['mass', 'kappa'], default='mass')
    parser.add_argument('--stout-steps', type=int, default=0, help='opt-in stout steps, default 0')
    parser.add_argument('--stout-rho', type=float, default=.125)
    parser.add_argument('--stout-dir-ignore', type=int, choices=range(5), default=4,
                        help='4: all four directions; 3: spatial-only')
    parser.add_argument('--tol', type=float, default=1e-8)
    parser.add_argument('--repeats', type=int, default=2, help='complete zero-start propagator rounds')
    parser.add_argument('--threads', type=int, help='rank-local OpenMP count, otherwise OMP/affinity')
    parser.add_argument('--seed', type=int, default=1024)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--solver-options', type=Path,
                        help='JSON numeric tuning applied after setup (physics unchanged)')
    parser.add_argument('--skip-checksum', action='store_true', help='explicitly disable SciDAC checksum')
    parser.add_argument('--save-gauge', action='store_true', help='save preprocessed local gauges for audit')
    args = parser.parse_args(argv)
    option_paths = MPI.COMM_WORLD.allgather(
        str(args.solver_options.resolve()) if args.solver_options else None)
    if any(path != option_paths[0] for path in option_paths):
        raise ValueError('--solver-options must agree on every rank')
    solve_tuning = (_root(MPI.COMM_WORLD, lambda: json.loads(args.solver_options.read_text()))
                    if args.solver_options else None)
    report = solve_lime_propagator(
        args.gauge, args.output, mass=args.mass, csw=args.csw, block=tuple(args.block),
        point=tuple(args.source), source_scale=args.source_scale,
        normalization=args.normalization, stout_steps=args.stout_steps,
        stout_rho=args.stout_rho, stout_dir_ignore=args.stout_dir_ignore,
        tol=args.tol, repeats=args.repeats, threads=args.threads, seed=args.seed,
        library=args.library, checksum=not args.skip_checksum, save_gauge=args.save_gauge,
        solve_tuning=solve_tuning, backend=args.backend)
    if MPI.COMM_WORLD.rank == 0:
        print(json.dumps({key: report[key] for key in ('output_file', 'mass', 'csw',
              'setup_seconds', 'first_seconds', 'max_true_residual')}
              | {k: report[k] for k in ('second_seconds', 'steady_median_seconds') if k in report}, indent=2))
