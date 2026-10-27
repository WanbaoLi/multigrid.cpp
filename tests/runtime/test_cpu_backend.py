"""CPU-only public runtime gate: numpy/mpi4py, no PyQUDA or Torch imports."""
import os
from pathlib import Path
import sys
import numpy as np
from mpi4py import MPI
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'python'))
from lqcd_cpu import Solver, _resolve_backend

comm=MPI.COMM_WORLD
assert comm.size in (1,2)
lat=(8,8,8,8);grid=(1,1,1,comm.size);lt=8//comm.size
mass=.05;kappa=1/(2*(4+mass));tol=1e-10
rng=np.random.default_rng(3291)
full=(rng.standard_normal((2,8,8,8,8,4,3))+1j*rng.standard_normal((2,8,8,8,8,4,3))).astype(np.complex128)
sl=slice(comm.rank*lt,(comm.rank+1)*lt)
rhs=full[:,sl].copy()
gammas=np.array([
 [[0,0,0,1j],[0,0,1j,0],[0,-1j,0,0],[-1j,0,0,0]],
 [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]],
 [[0,0,1j,0],[0,0,0,-1j],[-1j,0,0,0],[0,1j,0,0]],
 [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]]],np.complex128)
def apply(field):
    result=(4+mass)*field.copy()
    for mu in range(4):
        plus=np.roll(field,-1,axis=3-mu);minus=np.roll(field,1,axis=3-mu)
        if mu==3:plus[-1]*=-1;minus[0]*=-1
        result-=.5*(np.einsum('ij,...jc->...ic',np.eye(4)-gammas[mu],plus)+np.einsum('ij,...jc->...ic',np.eye(4)+gammas[mu],minus))
    return result
# Explicit x-checkerboard map independent of PyQUDA's conversion helpers.
def eo(field):
    out=np.empty((2,lt,8,8,4,*field.shape[4:]),dtype=np.complex128)
    for t in range(lt):
        for z in range(8):
            for y in range(8):
                for parity in (0,1):
                    offset=(parity-t-z-y)%2
                    out[parity,t,z,y]=field[t,z,y,offset::2]
    return out

def lex(field):
    out=np.empty((lt,8,8,8,*field.shape[5:]),dtype=np.complex128)
    for t in range(lt):
        for z in range(8):
            for y in range(8):
                for parity in (0,1):out[t,z,y,(parity-t-z-y)%2::2]=field[parity,t,z,y]
    return out

def relative(a,b):
    return np.sqrt(comm.allreduce(float(np.vdot((a-b).ravel(),(a-b).ravel()).real))/comm.allreduce(float(np.vdot(b.ravel(),b.ravel()).real)))

def failure(fn):
    caught=False
    try:fn()
    except (ValueError,RuntimeError):caught=True
    assert comm.allreduce(int(caught))==comm.size

# Rejected unavailable target must leave lifecycle reusable.
missing='arm' if _resolve_backend()=='x86' else 'x86'
failure(lambda:Solver(lat,grid,mass=mass,block=[2]*4,threads=2,backend=missing))
gauge=np.broadcast_to(np.eye(3,dtype=np.complex128),(lt,8,8,8,4,3,3)).copy()
for normalization in ('mass','kappa'):
    scale=1 if normalization=='mass' else 2*kappa
    with Solver(lat,grid,mass=mass,csw=1.160920226,block=[2]*4,threads=2,normalization=normalization) as s:
        s.load_gauge(gauge,layout='lex');s.setup()
        expected=(apply(full[0])*scale)[sl].copy()
        assert relative(s.apply(rhs[0],layout='lex'),expected)<2e-12
        assert relative(s.apply(eo(rhs[0])),eo(expected))<2e-12
        solutions=[]
        for batch,layout in ((1,'lex'),(2,'pyquda')):
            os.environ['LQCD_RHS_BATCH']=str(batch)
            source=rhs.copy() if layout=='lex' else np.stack([eo(b) for b in rhs])
            original=source.copy()
            x,stats=s.solve_many(source,tol,layout=layout)
            assert np.array_equal(original,source)
            assert all(q['converged'] and q['true_residual']<=tol for q in stats)
            xlex=x if layout=='lex' else np.stack([lex(b) for b in x])
            for col in range(2):
                globalx=np.concatenate(comm.allgather(xlex[col]),axis=0)
                residual=np.linalg.norm((scale*apply(globalx)-full[col]).ravel())/np.linalg.norm(full[col].ravel())
                assert residual<=tol,residual
            solutions.append(xlex)
        assert relative(solutions[0],solutions[1])<1e-8
        zeros,stats=s.solve_many(np.zeros_like(rhs),tol,layout='lex')
        assert np.count_nonzero(zeros)==0 and all(q['iterations']==0 for q in stats)
if comm.rank==0:print('PASS: CPU backend independent full operator/residual, mass/kappa, two random RHS scalar/batch, zero, EO/lex, source preservation and unavailable backend recovery',flush=True)
