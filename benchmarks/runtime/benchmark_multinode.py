"""One reused hierarchy: zero-start single/full12 API and native solver timings."""
import argparse
import faulthandler
import json
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bindings'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_lime_solver import atomic, native_timing, phase_summary, _measure, digest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gauge',required=True)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--scratch',required=True,type=Path)
    p.add_argument('--library',required=True)
    p.add_argument('--lattice',nargs=4,type=int,default=[64,64,64,128])
    p.add_argument('--block',nargs=4,type=int,default=[8,8,8,4])
    p.add_argument('--mass',type=float,default=-.2334)
    p.add_argument('--csw',type=float,default=1.140825606017)
    p.add_argument('--tol',type=float,default=1e-8)
    a=p.parse_args()
    import numpy as np
    from mpi4py import MPI
    from lqcd_cpu import Solver
    from lqcd_cpu.io import read_lime_gauge,read_lime_metadata
    from lqcd_cpu.smearing import stout_smear
    comm=MPI.COMM_WORLD; rank=comm.rank
    faulthandler.dump_traceback_later(180,repeat=True)
    def stage(name):
        if rank==0: print('STAGE',name,flush=True)
    stage('mpi_ready')
    lat=tuple(a.lattice); grid=(1,1,1,comm.size); coords=(0,0,0,rank)
    assert lat[3]%comm.size==0 and lat[3]//comm.size%a.block[3]==0
    assert int(os.environ['OMP_NUM_THREADS'])==32
    if rank==0: a.output.mkdir(parents=True,exist_ok=False)
    local=comm.Split_type(MPI.COMM_TYPE_SHARED)
    if local.rank==0: a.scratch.mkdir(parents=True,exist_ok=False)
    comm.Barrier()
    if int(os.environ.get('LQCD_TEST_SMALL','0'))!=1:
        assert local.size==16
    placement=comm.allgather(dict(rank=rank,host=socket.gethostname(),
        cpus=sorted(os.sched_getaffinity(0)),numa=os.environ.get('LQCD_NUMA_NODE')))
    stage('placement_ready')
    report=dict(complete=False,measurements_complete=False,source_commit=subprocess.check_output(
        ['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        source_branch=subprocess.check_output(['git','-C',str(ROOT),'branch','--show-current'],text=True).strip(),
        ranks=comm.size,ranks_per_node=local.size,threads=32,batch=2,outer_restart=16,
        lattice_xyzt=lat,grid_xyzt=grid,block_xyzt=a.block,mass=a.mass,csw=a.csw,tol=a.tol,
        zero_initial_guesses=True,stout=dict(steps=1,rho=.125,dir_ignore=4),
        source_xyzt=[0,0,0,0],seed=1024,placement=placement,
        mpi_library=MPI.Get_library_version(),
        mpi_environment={k:v for k,v in os.environ.items() if k.startswith('OMPI_MCA_')},
        context_environment={k:v for k,v in os.environ.items() if k.startswith('LQCD_')},
        library_sha256=digest(a.library),single_samples=[],twelve_samples=[])
    def memory():
        data={}
        for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
            if ':' in line and line.split(':')[0] in ('Rss','Pss','Private_Dirty','Shared_Dirty'):
                k,v=line.split(':',1); data[k+'_KiB']=int(v.split()[0])
        data['rank']=rank; data['host']=socket.gethostname()
        return comm.allgather(data)
    def checkpoint(phase):
        report['phase']=phase;report['memory_'+phase]=memory()
        if rank==0:
            atomic(a.output/'checkpoint.json',report)
            print('CHECKPOINT',phase,json.dumps({k:report[k] for k in report if k.endswith('_seconds')}),flush=True)
    checkpoint('created')
    meta=read_lime_metadata(a.gauge); assert tuple(meta['lattice_xyzt'])==lat
    stage('sha256_start')
    report['input_sha256']=comm.bcast(digest(a.gauge) if rank==0 else None)
    stage('read_start')
    gauge,report['read_seconds']=_measure(comm,lambda:read_lime_gauge(a.gauge,grid,coords,comm))
    stage('stout_start')
    gauge,report['stout_seconds']=_measure(comm,lambda:stout_smear(gauge,steps=1,rho=.125,dir_ignore=4,comm=comm))
    gauge.astype('<c16',copy=False).tofile(a.scratch/f'gauge-{rank}.bin')
    checkpoint('preprocessed')
    with Solver(lat,grid,mass=a.mass,csw=a.csw,block=a.block,threads=32,seed=1024,
                backend='arm',normalization='mass',library=a.library,comm=comm) as solver:
        _,report['gauge_clover_seconds']=_measure(comm,lambda:solver.load_gauge(gauge,layout='lex'))
        del gauge
        checkpoint('loaded')
        _,report['setup_seconds']=_measure(comm,solver.setup)
        checkpoint('setup')
        faulthandler.cancel_dump_traceback_later()
        shape=(lat[3]//comm.size,lat[2],lat[1],lat[0],4,3)
        src=np.zeros(shape,dtype=np.complex128)
        if rank==0: src[0,0,0,0,0,0]=1
        for i in range(3):
            os.environ['LQCD_RHS_BATCH']='1'
            single,wall=_measure(comm,lambda:solver.solve(src,a.tol,layout='lex'))
            stats=[dict(solver.last_result)]
            assert all(s['converged'] and s['true_residual']<=a.tol for s in stats)
            report['single_samples'].append(dict(run=i+1,wall_seconds=wall,stats=stats,**native_timing(stats)))
        single.astype('<c16',copy=False).tofile(a.scratch/f'solution-{rank}-0.bin')
        checkpoint('single')
        for i in range(3):
            os.environ['LQCD_RHS_BATCH']='2'
            (prop,stats),wall=_measure(comm,lambda:solver.solve_propagator((0,0,0,0),a.tol,layout='lex'))
            assert len(stats)==12 and all(s['converged'] and s['true_residual']<=a.tol for s in stats)
            report['twelve_samples'].append(dict(run=i+1,wall_seconds=wall,stats=stats,**native_timing(stats)))
            if i<2: del prop
        first=prop[..., :,0,:,0]
        num=comm.allreduce(float(np.linalg.norm(single-first)**2))
        den=comm.allreduce(float(np.linalg.norm(first)**2))
        report['single_full12_relative_error']=(num/den)**.5
        assert report['single_full12_relative_error']<=1e-6
        for col in range(12):
            spin,color=divmod(col,3)
            np.asarray(prop[..., :,spin,:,color],dtype='<c16',order='C').tofile(
                a.scratch/f'solution-{rank}-{col+1}.bin')
        for key in ('single','twelve'):
            samples=report[key+'_samples']
            report[key+'_api_summary']=phase_summary(samples)
            report[key+'_pure_summary']={
                'first_seconds':samples[0]['native_solver_seconds'],
                'second_seconds':samples[1]['native_solver_seconds'],
                'steady_median_seconds':statistics.median(s['native_solver_seconds'] for s in samples[1:]),
                'best_seconds':min(s['native_solver_seconds'] for s in samples),
            }
        checkpoint('measured')
    report['measurements_complete']=True
    report['timing_excludes']='read, stout, gauge/clover, setup, output and independent scalar verification'
    if rank==0: atomic(a.output/'result.json',report)
    comm.Barrier();local.Free()

if __name__=='__main__':
    from mpi4py import MPI
    try: main()
    except Exception:
        import traceback
        traceback.print_exc(); MPI.COMM_WORLD.Abort(1)
