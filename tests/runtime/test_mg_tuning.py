"""Collective tuning validation and zero-start numerical invariance on one setup."""
from pathlib import Path
import ctypes as C
import os
import sys
import numpy as np
from mpi4py import MPI
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'python'))
from lqcd_cpu import Solver
comm=MPI.COMM_WORLD
lat=(8,8,8,8);grid=(1,1,1,comm.size)
lt=8//comm.size;shape=(lt,8,8,8,4,3)
gauge=np.broadcast_to(np.eye(3),(*shape[:4],4,3,3)).astype(np.complex128).copy()
# A temporal antiperiodic plane wave gives an independent exact eigenvector.
t=np.arange(lt)+comm.rank*lt;p=np.pi/8
x=np.broadcast_to(np.exp(1j*p*t[:,None,None,None,None,None]),shape).copy()
gamma_x=np.concatenate((x[...,2:4,:],x[...,:2,:]),axis=-2)
rhs=(4+.05-3-np.cos(p))*x+1j*np.sin(p)*gamma_x
original=rhs.copy()
with Solver(lat,grid,mass=.05,csw=1.160920226,block=(2,2,2,2),threads=2+comm.rank%2) as solver:
 solver.load_gauge(gauge,'lex');solver.setup()
 max_threads=solver.lib.omp_get_max_threads
 max_threads.argtypes=[];max_threads.restype=C.c_int
 def check():
  got=solver.solve(rhs,tol=1e-10,layout='lex')
  error=comm.allreduce(float(np.linalg.norm(got-x)**2))/comm.allreduce(float(np.linalg.norm(x)**2))
  assert np.sqrt(error)<2e-9 and np.array_equal(rhs,original)
  assert max_threads()==solver.config.threads, 'coarse phase leaked its thread cap'
  return got
 baseline=check()
 # Switch outer precision collectively on the same ready hierarchy. Both the
 # scalar entry and batch fallback must reproduce this independent eigenmode.
 for outer,fused in (('0','0'),('0','1'),('1','0'),('1','1')):
  os.environ.update(LQCD_OUTER_FLOAT=outer,LQCD_RELIABLE_FUSED=fused)
  check()
  os.environ['LQCD_RHS_BATCH']='2'
  batched,stats=solver.solve_many(np.stack([rhs,2*rhs]),tol=1e-10,layout='lex')
  for got,expected,st in zip(batched,(x,2*x),stats):
   error=comm.allreduce(float(np.linalg.norm(got-expected)**2))/comm.allreduce(float(np.linalg.norm(expected)**2))
   assert np.sqrt(error)<2e-9 and st['true_residual']<=1e-10
 os.environ['LQCD_RHS_BATCH']='1'
 for schedule in ('0','1','2'):
  os.environ['LQCD_SAP_SCHEDULE']=schedule
  check()
  os.environ['LQCD_RHS_BATCH']='2'
  batched,stats=solver.solve_many(np.stack([rhs,2*rhs]),tol=1e-10,layout='lex')
  for got,expected,st in zip(batched,(x,2*x),stats):
   error=comm.allreduce(float(np.linalg.norm(got-expected)**2))/comm.allreduce(float(np.linalg.norm(expected)**2))
   assert np.sqrt(error)<2e-9 and st['true_residual']<=1e-10
 os.environ['LQCD_RHS_BATCH']='1'
 os.environ['LQCD_SAP_SCHEDULE']='0'
 # Change only the coarse phase after setup. A request above the fine team
 # is clamped, and the caller's ICV must be restored after every solve.
 for cap in ('1','2','608','0'):
  os.environ['LQCD_COARSE_THREADS']=cap
  got=check()
  difference=comm.allreduce(float(np.linalg.norm(got-baseline)**2))
  reference=comm.allreduce(float(np.linalg.norm(baseline)**2))
  assert np.sqrt(difference/reference)<2e-9
 settings=dict(LQCD_MG_SAP_STEPS='2',LQCD_MG_SAP_CYCLES='1',LQCD_MG_COARSE_IT='20',
               LQCD_MG_COARSE_TOL='.3',LQCD_CORRECTION_BASE_TOL='.01',
               LQCD_FLOAT_CORRECTION_VERIFY='0',LQCD_FINE_TEAM_FUSED='1',LQCD_COARSE_THREADS='0',
               LQCD_COARSE_BATCH_REDUCE='0',LQCD_GCR_FUSED='1',LQCD_OUTER_FLOAT='1',LQCD_RELIABLE_FUSED='0',LQCD_SAP_SCHEDULE='0')
 os.environ.update(settings);check()
 for verify in ('0','1'):
  for team in ('0','1'):
   os.environ.update(LQCD_FLOAT_CORRECTION_VERIFY=verify,LQCD_FINE_TEAM_FUSED=team);check()
 for key,bad in [('LQCD_MG_SAP_STEPS','2.5'),('LQCD_MG_COARSE_TOL','nan'),
                 ('LQCD_CORRECTION_BASE_TOL','0'),('LQCD_FINE_TEAM_FUSED','2'),
                 ('LQCD_COARSE_THREADS','-1'),('LQCD_COARSE_THREADS','1.5'),
                 ('LQCD_COARSE_THREADS','609'),('LQCD_COARSE_BATCH_REDUCE','2'),
                 ('LQCD_COARSE_BATCH_REDUCE','nan'),('LQCD_GCR_FUSED','2'),
                 ('LQCD_OUTER_FLOAT','2'),('LQCD_OUTER_FLOAT','nan'),('LQCD_OUTER_FLOAT','.5'),
                 ('LQCD_RELIABLE_FUSED','2'),('LQCD_RELIABLE_FUSED','nan'),
                 ('LQCD_SAP_SCHEDULE','3'),('LQCD_SAP_SCHEDULE','1.5')]:
  good=os.environ.get(key)
  os.environ[key]=bad if comm.rank==0 else settings[key]
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('invalid collective setting accepted')
  if good is None:os.environ.pop(key,None)
  else:os.environ[key]=good
 if comm.size>1:
  os.environ['LQCD_SAP_SCHEDULE']='0' if comm.rank==0 else '2'
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('rank-inconsistent SAP schedule accepted')
  os.environ['LQCD_SAP_SCHEDULE']='0'
  os.environ['LQCD_RELIABLE_FUSED']='0' if comm.rank==0 else '1'
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('rank-inconsistent reliable fusion accepted')
  os.environ['LQCD_RELIABLE_FUSED']='0'
  os.environ['LQCD_OUTER_FLOAT']='0' if comm.rank==0 else '1'
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('rank-inconsistent outer precision accepted')
  os.environ['LQCD_OUTER_FLOAT']='1'
  os.environ['LQCD_MG_COARSE_TOL']='.1' if comm.rank==0 else '.2'
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('rank mismatch accepted')
  os.environ['LQCD_MG_COARSE_TOL']='.3'
  os.environ['LQCD_COARSE_THREADS']='1' if comm.rank==0 else '2'
  try:solver.solve(rhs,layout='lex')
  except RuntimeError as exc:assert 'tuning' in str(exc)
  else:raise AssertionError('rank-inconsistent coarse thread cap accepted')
  os.environ['LQCD_COARSE_THREADS']='0'
 check()
if comm.rank==0:print('PASS MG tuning: one hierarchy, coarse thread cap/restoration, verify/team modes, plane-wave residual, invalid/mismatched settings and recovery')
