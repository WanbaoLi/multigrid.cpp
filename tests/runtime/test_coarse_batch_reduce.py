"""Independent-RHS coarse reduction/halo batching: CPU-only public MPI gate.

Uses a small lattice and a separate NumPy Wilson stencil. Different sources,
zero/dependent columns, changing widths, fallback modes and collective tuning
errors all run on a live context. No PyQUDA, GPU or real gauge is required.
"""
import ctypes as C
import json
import os
from pathlib import Path
import sys
import tempfile

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from lqcd_cpu import Solver
from lqcd_cpu.propagator import SOLVE_TUNING_KEYS

comm = MPI.COMM_WORLD
assert comm.size in (1, 2, 4)
assert 'LQCD_COARSE_BATCH_REDUCE' in SOLVE_TUNING_KEYS
assert 'LQCD_COARSE_BATCH_HALO' in SOLVE_TUNING_KEYS
extent, mass, tolerance = 8, .25, 1e-10
temporal_extent = int(os.environ.get('LQCD_TEST_COARSE_TEMPORAL_EXTENT', str(extent)))
assert temporal_extent >= 2 * comm.size and temporal_extent % (2 * comm.size) == 0
smoke = os.environ.get('LQCD_TEST_COARSE_HALO_SMOKE', '0') == '1'
local_t = temporal_extent // comm.size
slab = slice(comm.rank * local_t, (comm.rank + 1) * local_t)
shape = (temporal_extent,) + (extent,) * 3 + (4, 3)
lattice = [extent] * 3 + [temporal_extent]
gamma = np.array([
    [[0,0,0,1j],[0,0,1j,0],[0,-1j,0,0],[-1j,0,0,0]],
    [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
    [[0,0,1j,0],[0,0,0,-1j],[-1j,0,0,0],[0,1j,0,0]],
    [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]],
], dtype=np.complex128)


def independent_apply(field):
    result = (4 + mass) * field.copy()
    for direction in range(4):
        plus = np.roll(field, -1, axis=3-direction)
        minus = np.roll(field, 1, axis=3-direction)
        if direction == 3:
            plus[-1] *= -1
            minus[0] *= -1
        result -= .5 * (
            np.einsum('ij,...jc->...ic', np.eye(4)-gamma[direction], plus)
            + np.einsum('ij,...jc->...ic', np.eye(4)+gamma[direction], minus))
    return result


rng = np.random.default_rng(8127)
known = rng.normal(size=(12,) + shape) + 1j * rng.normal(size=(12,) + shape)
# Smooth, localized, zero, dependent and oscillating exact solutions have
# distinct coarse/outer convergence histories; scaling alone would not do so.
time = np.arange(temporal_extent)
known[1] = np.broadcast_to(np.exp(1j*np.pi*time[:,None,None,None,None,None]/temporal_extent), shape)
known[2] = 0
known[2, 0, 0, 0, 0, 1, 2] = 1
known[3] = 0
known[4] = known[0]
known[5] = known[1] * (-1.)**np.arange(extent)[None,None,None,:,None,None]
for column in range(6, 12):
    known[column] *= 10.**(column % 5 - 2)
whole_sources = np.stack([independent_apply(field) for field in known])
sources = np.ascontiguousarray(whole_sources[:, slab])
gauge = np.broadcast_to(np.eye(3, dtype=np.complex128),
                       (local_t, extent, extent, extent, 4, 3, 3)).copy()
maximum_residual = 0.


def relative(actual, expected):
    difference = comm.allreduce(float(np.vdot(actual-expected, actual-expected).real))
    norm = comm.allreduce(float(np.vdot(expected, expected).real))
    return (difference / norm)**.5 if norm else difference**.5


def verify(solver, indices, grouping, flag, halo=0):
    global maximum_residual
    os.environ['LQCD_RHS_BATCH'] = str(grouping)
    os.environ['LQCD_COARSE_BATCH_REDUCE'] = str(flag)
    os.environ['LQCD_COARSE_BATCH_HALO'] = str(halo)
    rhs = np.ascontiguousarray(sources[indices])
    before = rhs.copy()
    result, stats = solver.solve_many(rhs, tol=tolerance, layout='lex')
    assert np.array_equal(rhs, before)
    assert len(stats) == len(indices)
    for slot, column in enumerate(indices):
        assert stats[slot]['converged'] and stats[slot]['true_residual'] <= tolerance
        global_result = np.concatenate(comm.allgather(result[slot]), axis=0)
        norm = np.linalg.norm(whole_sources[column].ravel())
        if norm == 0:
            assert np.count_nonzero(result[slot]) == 0 and stats[slot]['iterations'] == 0
        else:
            residual = np.linalg.norm((independent_apply(global_result)-whole_sources[column]).ravel()) / norm
            assert residual <= tolerance, (grouping, flag, halo, column, residual)
            maximum_residual = max(maximum_residual, residual)
            assert relative(result[slot], known[column, slab]) < 1e-8
    maximum_threads = solver.lib.omp_get_max_threads
    maximum_threads.argtypes, maximum_threads.restype = [], C.c_int
    assert maximum_threads() == solver.config.threads, 'coarse team cap leaked into caller'
    return result, stats


def captured_verify(solver, indices, grouping, flag, halo=0):
    """Retain native execution counters without interpreting wall timings."""
    previous_verbose = os.environ.get('LQCD_VERBOSE')
    previous_stderr = os.dup(2)
    os.environ['LQCD_VERBOSE'] = '1'
    try:
        with tempfile.TemporaryFile(mode='w+b') as capture:
            try:
                os.dup2(capture.fileno(), 2)
                result, stats = verify(solver, indices, grouping, flag, halo)
            finally:
                os.dup2(previous_stderr, 2)
            capture.seek(0)
            lines = capture.read().decode('utf-8', errors='replace').splitlines()
    finally:
        os.close(previous_stderr)
        if previous_verbose is None:
            os.environ.pop('LQCD_VERBOSE', None)
        else:
            os.environ['LQCD_VERBOSE'] = previous_verbose
    return result, stats, lines


def halo_diagnostic(solver, indices, grouping, flag, halo, supported=True, label=''):
    result, stats, lines = captured_verify(solver, indices, grouping, flag, halo)
    prefix = 'native coarse batch halo '
    records = [json.loads(line[len(prefix):]) for line in lines if line.startswith(prefix)]
    expected = comm.size > 1 and grouping > 1 and flag and halo and supported
    error, summary = None, None
    if comm.rank == 0:
        try:
            summary = dict(label=label, ranks=comm.size, grouping=grouping,
                           reduce=flag, halo=halo, records=len(records),
                           calls=sum(r['calls'] for r in records),
                           send_bytes=sum(r['send_bytes'] for r in records),
                           rhs_slots=sum(r['rhs_slots'] for r in records),
                           max_width=max((r['max_width'] for r in records), default=0))
            for record in records:
                assert all(record[key] >= 0 for key in ('calls', 'send_bytes', 'rhs_slots', 'max_width'))
                assert record['max_width'] <= grouping
                if record['calls']:
                    assert 2 * record['calls'] <= record['rhs_slots'] <= grouping * record['calls']
                    # Two temporal faces, 48 complex components per spatial
                    # coarse site, interleaved real/imaginary float32 values.
                    bytes_per_rhs = 2 * (extent // 2)**3 * 48 * 2 * 4
                    assert record['send_bytes'] == record['rhs_slots'] * bytes_per_rhs
            if expected:
                assert summary['calls'] > 0, 'enabled halo batch produced no actual communication'
                assert summary['send_bytes'] > 0 and summary['rhs_slots'] > 0
                assert 2 <= summary['max_width'] <= grouping
            else:
                assert summary['calls'] == summary['send_bytes'] == summary['rhs_slots'] == 0
        except (AssertionError, KeyError, TypeError) as failure:
            error = repr(failure)
    error = comm.bcast(error)
    if error:
        raise AssertionError(error)
    summary = comm.bcast(summary)
    if comm.rank == 0:
        print('COARSE_BATCH_HALO_DIAGNOSTIC ' + json.dumps(summary, sort_keys=True), flush=True)
    return result, stats, summary


def rejected_then_recover(solver, name, invalid):
    previous = os.environ.get(name)
    os.environ[name] = invalid if comm.rank == 0 else (previous or '0')
    caught = False
    try:
        solver.solve_many(sources[:2], tol=tolerance, layout='lex')
    except RuntimeError as error:
        caught = 'tuning' in str(error)
    assert comm.allreduce(int(caught)) == comm.size, (name, invalid)
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous
    verify(solver, [1, 0], 2, 1)


def diagnostic(solver, cap):
    """Capture only the native verbose records; no timings enter a ranking."""
    previous = {key: os.environ.get(key) for key in (
        'LQCD_VERBOSE', 'LQCD_MG_COARSE_TOL', 'LQCD_MG_COARSE_IT')}
    os.environ.update(LQCD_VERBOSE='1', LQCD_MG_COARSE_TOL='1e-4',
                      LQCD_MG_COARSE_IT=str(cap))
    _, _, lines = captured_verify(solver, [1, 0, 2, 5], 4, 1, halo=1)
    prefix = 'native coarse batch reduce '
    records = [json.loads(line[len(prefix):]) for line in lines if line.startswith(prefix)]
    error, summary = None, None
    if comm.rank == 0:
        try:
            assert records, 'enabled coarse batch produced no verbose evidence'
            for record in records:
                assert record['coarse_it_limit'] == cap
                assert record['coarse_tolerance'] == 1e-4
                assert all(0 <= count <= cap for count in record['iterations'])
                assert record['reduction_rounds'] > 0
                assert record['allreduce_calls'] == (record['reduction_rounds'] if comm.size > 1 else 0)
            summary = dict(cap=cap, calls=len(records),
                           capped=sum(sum(r['capped']) for r in records),
                           restarts=sum(sum(r['restarts']) for r in records),
                           differing_iterations=any(len(set(r['iterations'])) > 1 for r in records),
                           differing_refreshes=any(len(set(r['refreshes'])) > 1 for r in records),
                           allreduce_calls=sum(r['allreduce_calls'] for r in records))
        except (AssertionError, KeyError, TypeError) as failure:
            error = repr(failure)
    error = comm.bcast(error)
    if error:
        raise AssertionError(error)
    summary = comm.bcast(summary)
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    if comm.rank == 0:
        print('COARSE_BATCH_DIAGNOSTIC ' + json.dumps(summary, sort_keys=True), flush=True)
    return summary


os.environ.update(LQCD_COARSE_EO='1', LQCD_COARSE_CGS2='0',
                 LQCD_GCR_FUSED='1', LQCD_COARSE_BATCH_REDUCE='0',
                 LQCD_COARSE_BATCH_HALO='0')


def exercise(solver):
    if smoke:
        # Context-time mode variants share this short probe. The full serial,
        # MPI2 and MPI4 suites below cover all widths and tuning errors.
        indices = [1, 0, 3, 2, 5]  # a zero middle slot and a partial width-one tail
        normal, _ = verify(solver, indices, 4, 1, halo=0)
        merged, _, _ = halo_diagnostic(solver, indices, 4, 1, 1, label='mode-partial-tail')
        assert relative(merged, normal) < 1e-8
        halo_diagnostic(solver, [1, 0], 1, 1, 1, label='mode-single-rhs')
        return
    scalar, _ = verify(solver, list(range(12)), 1, 0)
    # Keep one hierarchy while the active width and history storage grow/shrink.
    for indices, grouping in [([0],1), ([1,0],2), ([0,1,2,3],4),
                              (list(range(12)),12), ([11,2],2),
                              ([3,3,3,3],4), ([3,3,2,3],4)]:
        normal, _ = verify(solver, indices, grouping, 0)
        reduced, _ = verify(solver, indices, grouping, 1, halo=0)
        merged, _ = verify(solver, indices, grouping, 1, halo=1)
        assert relative(merged, normal) < 1e-8
        assert relative(merged, reduced) < 1e-8
        assert relative(merged, scalar[indices]) < 1e-8
    # Flags alone are not execution evidence. Inspect real packed-MPI calls,
    # bytes and active widths, including an inactive middle slot and tail.
    halo_diagnostic(solver, [1,0,3,2], 4, 1, 1, label='active-zero')
    halo_diagnostic(solver, [1,0,3,2,5], 4, 1, 1, label='partial-tail')
    halo_diagnostic(solver, [1,0], 2, 1, 0, label='halo-off')
    halo_diagnostic(solver, [1,0], 2, 0, 1, label='reduce-off')
    halo_diagnostic(solver, [1,0], 1, 1, 1, label='single-rhs')
    halo_diagnostic(solver, [3,3,3,3], 4, 1, 1, supported=False, label='all-zero')
    # Observe actual internal cap/restart behavior rather than inferring it
    # from an outer source shape. The small free-field case may converge before
    # a restart even at the tightest allowed coarse tolerance; report that gap.
    assert diagnostic(solver, 1)['capped'] > 0
    restart_case = diagnostic(solver, 40)
    if not restart_case['restarts']:
        restart_case = diagnostic(solver, 200)
    if comm.rank == 0:
        print('COARSE_BATCH_COVERAGE ' + json.dumps({
            'restart_observed': bool(restart_case['restarts']),
            'different_stops_observed': restart_case['differing_iterations'],
            'different_refreshes_observed': restart_case['differing_refreshes']},
            sort_keys=True), flush=True)
    # A cap applies once around the whole supported coarse batch and restores
    # the calling task's ICV. The cap is not a performance assertion.
    os.environ['LQCD_COARSE_THREADS'] = '1'
    halo_diagnostic(solver, [1,0], 2, 1, 1, label='one-coarse-thread')
    os.environ['LQCD_COARSE_THREADS'] = '0'
    # Unsupported orthogonalization/update modes take the old scalar path.
    for name in ['LQCD_COARSE_CGS2', 'LQCD_GCR_FUSED']:
        original = os.environ[name]
        os.environ[name] = '1' if name.endswith('CGS2') else '0'
        normal, normal_stats = verify(solver, [1,0], 2, 0, halo=1)
        fallback, fallback_stats, _ = halo_diagnostic(
            solver, [1,0], 2, 1, 1, supported=False, label=name+'-fallback')
        assert relative(fallback, normal) < 1e-12
        assert [s['iterations'] for s in normal_stats] == [s['iterations'] for s in fallback_stats]
        os.environ[name] = original
    for name in ['LQCD_COARSE_BATCH_REDUCE', 'LQCD_COARSE_BATCH_HALO']:
        for invalid in ['2', '-1', '.5', 'nan', 'bad', '']:
            rejected_then_recover(solver, name, invalid)
    # strtod rounds both ranks to zero here, while the existing setting()->atoi
    # would select fused=1 on rank 0. Reject before either solver branch runs.
    os.environ['LQCD_GCR_FUSED'] = '0'
    rejected_then_recover(solver, 'LQCD_GCR_FUSED', '1e-400')
    os.environ['LQCD_GCR_FUSED'] = '1'
    rejected_then_recover(solver, 'LQCD_GCR_FUSED', '.999999999999999999')
    if comm.size > 1:
        # Legal local values with an illegal collective disagreement.
        for name in ['LQCD_COARSE_BATCH_REDUCE', 'LQCD_COARSE_BATCH_HALO']:
            os.environ[name] = '0' if comm.rank == 0 else '1'
            caught = False
            try: solver.solve_many(sources[:2], tol=tolerance, layout='lex')
            except RuntimeError as error: caught = 'tuning' in str(error)
            assert comm.allreduce(int(caught)) == comm.size, name
            os.environ[name] = '1'
        os.environ['LQCD_GCR_FUSED'] = '0' if comm.rank == 0 else '1'
        caught = False
        try: solver.solve_many(sources[:2], tol=tolerance, layout='lex')
        except RuntimeError as error: caught = 'tuning' in str(error)
        assert comm.allreduce(int(caught)) == comm.size
        os.environ['LQCD_GCR_FUSED'] = '1'
    verify(solver, [1,0], 2, 1, halo=1)


with Solver(lattice, [1,1,1,comm.size], mass=mass, csw=1.160920226,
            block=[2]*4, threads=1+comm.rank%2) as solver:
    solver.load_gauge(gauge, layout='lex')
    solver.setup()
    exercise(solver)

# Legacy non-EO coarse mode is a separate context-time configuration. Both flag
# values must retain the scalar implementation and the same numerical result.
if not smoke:
    os.environ['LQCD_COARSE_EO'] = '0'
    with Solver(lattice, [1,1,1,comm.size], mass=mass, block=[2]*4,
                threads=1+comm.rank%2) as solver:
        solver.load_gauge(gauge, layout='lex')
        solver.setup()
        normal, _ = verify(solver, [1,0], 2, 0, halo=1)
        fallback, _, _ = halo_diagnostic(solver, [1,0], 2, 1, 1,
                                         supported=False, label='non-EO-fallback')
        assert relative(fallback, normal) < 1e-12

if comm.rank == 0:
    print(f'PASS coarse independent-RHS reduction/halo batching ranks={comm.size} '
          f'local_coarse_t={local_t//2} smoke={smoke} '
          f'max_independent_residual={maximum_residual:.9e}', flush=True)
