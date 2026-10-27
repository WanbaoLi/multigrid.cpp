"""CPU-only MPI batch 1..12 contract and independent unit-gauge Wilson oracle.

Needs NumPy/mpi4py and LQCD_CPU_LIBRARY; no PyQUDA import or GPU.
"""
import os
from pathlib import Path
import sys
import numpy as np
from mpi4py import MPI
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from lqcd_cpu import Solver
comm = MPI.COMM_WORLD
assert comm.size in (1, 2, 4)
lt = 8 // comm.size
slab = slice(comm.rank * lt, (comm.rank + 1) * lt)
gamma = np.array([
 [[0,0,0,1j],[0,0,1j,0],[0,-1j,0,0],[-1j,0,0,0]],
 [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
 [[0,0,1j,0],[0,0,0,-1j],[-1j,0,0,0],[0,1j,0,0]],
 [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]]], np.complex128)
mass = .05

def apply(field):
    result = (4 + mass) * field.copy()
    for mu in range(4):
        plus = np.roll(field, -1, axis=3-mu)
        minus = np.roll(field, 1, axis=3-mu)
        if mu == 3:
            plus[-1] *= -1
            minus[0] *= -1
        result -= .5 * (np.einsum('ij,...jc->...ic', np.eye(4)-gamma[mu], plus)
                        + np.einsum('ij,...jc->...ic', np.eye(4)+gamma[mu], minus))
    return result

rng = np.random.default_rng(91824)
whole = rng.normal(size=(12,8,8,8,8,4,3)) + 1j*rng.normal(size=(12,8,8,8,8,4,3))
# Differently conditioned components retain independent histories and stopping.
for k in range(12):
    whole[k] *= 10. ** ((k % 5)-2)
rhs = np.ascontiguousarray(whole[:, slab])
gauge = np.broadcast_to(np.eye(3, dtype=np.complex128), (lt,8,8,8,4,3,3)).copy()
maximum = 0.

def verify(actual, sources, stats, grouping):
    global maximum
    assert len(stats) == len(sources)
    for k, (x, b, st) in enumerate(zip(actual, sources, stats)):
        gx = np.concatenate(comm.allgather(x), axis=0)
        gb = np.concatenate(comm.allgather(b), axis=0)
        norm = np.linalg.norm(gb.ravel())
        if norm == 0:
            assert np.count_nonzero(x) == 0 and st['iterations'] == 0
        else:
            residual = np.linalg.norm((apply(gx)-gb).ravel()) / norm
            assert residual <= 1e-8, (k, residual)
            maximum = max(maximum, residual)
        group_size = min(grouping, len(sources) - (k // grouping)*grouping)
        if group_size > 1:
            assert st['batch_size'] == group_size and st['timing_scope'] == 'shared_batch'
            assert st['solver_seconds'] == stats[(k//grouping)*grouping]['solver_seconds']

with Solver([8]*4, [1,1,1,comm.size], mass=mass, block=[2]*4, threads=1+comm.rank%2) as solver:
    solver.load_gauge(gauge, layout='lex')
    solver.setup()
    # Full 12 independent nonzero sources, then partial tail 3, then mixed
    # zeros with active subsets 3/1/0; finally 12 again checks cached state reset.
    for grouping, sources in [(12,rhs), (4,rhs[:7]),
                              (12,np.concatenate([rhs[:3],np.zeros_like(rhs[3:])])),
                              (12,np.concatenate([np.zeros_like(rhs[:11]),rhs[11:]])),
                              (12,np.zeros_like(rhs)), (12,rhs)]:
        os.environ['LQCD_RHS_BATCH'] = str(grouping)
        original = sources.copy()
        x, stats = solver.solve_many(sources, layout='lex', tol=1e-8)
        verify(x, sources, stats, grouping)
        assert np.array_equal(original, sources)
    os.environ['LQCD_RHS_BATCH'] = '1'
    scalar = solver.solve(rhs[0], layout='lex', tol=1e-8)
    difference = np.linalg.norm((scalar-x[0]).ravel())
    reference = np.linalg.norm(scalar.ravel())
    assert np.sqrt(comm.allreduce(difference**2)/comm.allreduce(reference**2)) < 1e-7
    for invalid in ('0','13','2.0','-1',''):
        os.environ['LQCD_RHS_BATCH'] = invalid
        try: solver.solve_many(rhs[:1],layout='lex')
        except (RuntimeError, ValueError): pass
        else: raise AssertionError('invalid Python batch accepted')
    if comm.size > 1:
        os.environ['LQCD_RHS_BATCH'] = '4' if comm.rank==0 else '12'
        try: solver.solve_many(rhs[:1],layout='lex')
        except (RuntimeError, ValueError): pass
        else: raise AssertionError('rank-inconsistent batch accepted')
    for invalid in (0,13):
        # Invalid count must be rejected before any null field array access.
        status=solver.lib.lqcd_solve_batch(solver._handle,None,None,invalid,1e-8,None)
        assert status != 0
if comm.rank == 0:
    print(f'BATCH12 PASS ranks={comm.size} max_independent_residual={maximum:.9e}')
