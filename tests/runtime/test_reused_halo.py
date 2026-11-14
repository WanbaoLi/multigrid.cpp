"""Exercise mmap-sized spinors, reused halos, scalar/batch transitions and an analytic oracle."""
import os
import numpy as np
from mpi4py import MPI
from lqcd_cpu import Solver

comm=MPI.COMM_WORLD
assert comm.size==2
lat=(8,8,8,32)
local_t=lat[3]//comm.size
part=slice(comm.rank*local_t,(comm.rank+1)*local_t)
mass=1.0
gamma=np.array([
 [[0,0,0,1j],[0,0,1j,0],[0,-1j,0,0],[-1j,0,0,0]],
 [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
 [[0,0,1j,0],[0,0,0,-1j],[-1j,0,0,0],[0,1j,0,0]],
 [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]],
],dtype=np.complex128)

def independent(field):
    result=(4+mass)*field
    for direction in range(4):
        plus=np.roll(field,-1,axis=3-direction)
        minus=np.roll(field,1,axis=3-direction)
        if direction==3:
            plus[-1]*=-1
            minus[0]*=-1
        result-=.5*(np.einsum('ij,...jc->...ic',np.eye(4)-gamma[direction],plus)
                    +np.einsum('ij,...jc->...ic',np.eye(4)+gamma[direction],minus))
    return result

rng=np.random.default_rng(91847)
exact=[rng.standard_normal((32,8,8,8,4,3))+1j*rng.standard_normal((32,8,8,8,4,3))
       for _ in range(2)]
rhs=[independent(field) for field in exact]
sources=np.ascontiguousarray([field[part] for field in rhs])
original=sources.copy()
gauge=np.broadcast_to(np.eye(3,dtype=np.complex128),(local_t,8,8,8,4,3,3)).copy()
os.environ.update(LQCD_MG_SETUP_PASSES='0',LQCD_MG_SETUP_SMOOTH='2',LQCD_RHS_BATCH='2')

def verify(solution,column):
    whole=np.concatenate(comm.allgather(solution),axis=0)
    residual=np.linalg.norm(independent(whole)-rhs[column])/np.linalg.norm(rhs[column])
    assert residual<=1e-8,residual
    return residual

baseline=None
for mode in ('0','1'):
    os.environ['LQCD_REUSE_HALO_PAGES']=mode
    with Solver(lat,(1,1,1,2),mass=mass,csw=1.,block=(2,2,2,2),threads=2) as solver:
        solver.load_gauge(gauge,layout='lex')
        solver.setup()
        outputs,stats=solver.solve_many(sources,1e-8,layout='lex')
        assert all(row['converged'] and row['true_residual']<=1e-8 for row in stats)
        residuals=[verify(outputs[column],column) for column in range(2)]
        scalar=solver.solve(sources[1],1e-8,layout='lex')
        residuals.append(verify(scalar,1))
        repeated,stats=solver.solve_many(sources,1e-8,layout='lex')
        residuals.extend(verify(repeated[column],column) for column in range(2))
        assert np.array_equal(sources,original)
        if baseline is None: baseline=outputs.copy()
        else:
            difference=comm.allreduce(float(np.linalg.norm(outputs-baseline)**2))
            norm=comm.allreduce(float(np.linalg.norm(baseline)**2))
            assert (difference/norm)**.5<=5e-9
        if comm.rank==0:
            print('REUSED_HALO mode='+mode+' max_independent_residual='+str(max(residuals)),flush=True)
if comm.rank==0: print('PASS mmap-sized halos, independent operator, repeat/batch/scalar and owned preservation',flush=True)
