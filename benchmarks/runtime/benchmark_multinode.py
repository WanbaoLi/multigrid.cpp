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


def numa_memory():
    pools=[]
    for path in sorted(Path('/sys/devices/system/node').glob('node[0-9]*')):
        cpus=(path/'cpulist').read_text().strip()
        values={}
        for line in (path/'meminfo').read_text().splitlines():
            fields=line.split()
            if fields[2] in ('MemTotal:','MemFree:'):
                values[fields[2][:-1]+'_KiB']=int(fields[3])
        pools.append(dict(numa_node=int(path.name[4:]),cpu_list=cpus,**values))
    return pools


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gauge',required=True)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--scratch',required=True,type=Path)
    p.add_argument('--library',required=True)
    p.add_argument('--backend',choices=('arm','x86'),default='arm')
    p.add_argument('--threads',type=int,help='Expected OpenMP threads per rank')
    p.add_argument('--lattice',nargs=4,type=int,default=[64,64,64,128])
    p.add_argument('--block',nargs=4,type=int,default=[8,8,8,4])
    p.add_argument('--mass',type=float,default=-.2334)
    p.add_argument('--csw',type=float,default=1.140825606017)
    p.add_argument('--tol',type=float,default=1e-8)
    p.add_argument('--source',choices=['point','wall'],default='point')
    p.add_argument('--single-only',action='store_true')
    p.add_argument('--ranks-per-node',type=int,choices=(4,8,16,32),default=16)
    p.add_argument('--time-replicas',type=int,default=1,
                   help='Tile the input and a single wall RHS along time; --lattice gives the global dimensions')
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
    repeats=a.time_replicas
    if repeats<1 or comm.size%repeats or lat[3]%repeats:
        raise ValueError('Time replicas must divide the rank count and global time extent')
    if repeats>1 and (a.source!='wall' or not a.single_only):
        raise ValueError('Replicated time benchmarks require a single wall RHS')
    tile_ranks=comm.size//repeats
    tile_time=lat[3]//repeats
    threads=a.threads if a.threads is not None else 512//a.ranks_per_node
    assert int(os.environ['OMP_NUM_THREADS'])==threads
    if rank==0: a.output.mkdir(parents=True,exist_ok=False)
    local=comm.Split_type(MPI.COMM_TYPE_SHARED)
    if local.rank==0: a.scratch.mkdir(parents=True,exist_ok=False)
    comm.Barrier()
    if int(os.environ.get('LQCD_TEST_SMALL','0'))!=1:
        assert local.size==a.ranks_per_node
    placement=comm.allgather(dict(rank=rank,host=socket.gethostname(),
        cpus=sorted(os.sched_getaffinity(0)),numa=os.environ.get('LQCD_NUMA_NODE'),
        numa_domains=os.environ.get('LQCD_NUMA_NODES')))
    for host in {row['host'] for row in placement}:
        masks=[set(row['cpus']) for row in placement if row['host']==host]
        assert all(len(mask)==threads for mask in masks)
        assert len(set.union(*masks))==len(masks)*threads
    if repeats>1:
        assert tile_ranks==local.size
        for start in range(0,comm.size,tile_ranks):
            assert len({row['host'] for row in placement[start:start+tile_ranks]})==1
    memory_pools={host:pools for host,pools in
                  comm.allgather((socket.gethostname(),numa_memory() if local.rank==0 else [])) if pools}
    stage('placement_ready')
    report=dict(complete=False,measurements_complete=False,source_commit=subprocess.check_output(
        ['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        source_branch=subprocess.check_output(['git','-C',str(ROOT),'branch','--show-current'],text=True).strip(),
        ranks=comm.size,ranks_per_node=local.size,threads=threads,batch=1 if a.single_only else 2,
        outer_restart=16,
        lattice_xyzt=lat,input_lattice_xyzt=(*lat[:3],tile_time),time_replicas=repeats,
        grid_xyzt=grid,block_xyzt=a.block,mass=a.mass,csw=a.csw,tol=a.tol,
        zero_initial_guesses=True,stout=dict(steps=1,rho=.125,dir_ignore=4),
        source=a.source,source_xyzt=[0,0,0,0],wall_period=tile_time if a.source=='wall' else None,
        seed=1024,placement=placement,numa_memory_at_start=memory_pools,
        mpi_library=MPI.Get_library_version(),
        mpi_environment={k:v for k,v in os.environ.items() if k.startswith('OMPI_MCA_')},
        context_environment={k:v for k,v in os.environ.items() if k.startswith('LQCD_')},
        library_sha256=digest(a.library),single_samples=[],twelve_samples=[])
    def memory():
        data={}
        for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
            if ':' in line and line.split(':')[0] in ('Rss','Pss','Private_Dirty','Shared_Dirty'):
                k,v=line.split(':',1); data[k+'_KiB']=int(v.split()[0])
        groups={}
        for line in Path('/proc/self/cgroup').read_text().splitlines():
            _,controllers,relative=line.split(':',2)
            if controllers=='':
                base=Path('/sys/fs/cgroup')/relative.lstrip('/')
                names=('memory.max','memory.current','memory.peak','memory.events','cpu.max')
            elif 'memory' in controllers.split(','):
                base=Path('/sys/fs/cgroup/memory')/relative.lstrip('/')
                names=('memory.limit_in_bytes','memory.usage_in_bytes',
                       'memory.max_usage_in_bytes','memory.failcnt')
            else: continue
            values={}
            for name in names:
                try:
                    values[name]=(base/name).read_text().strip()
                except (FileNotFoundError,PermissionError):
                    # Donau can hide per-job cgroup counters from job users.
                    continue
            groups[str(base)]=values
        data['cgroup']=groups
        data['rank']=rank; data['host']=socket.gethostname()
        return comm.allgather(data)
    def checkpoint(phase):
        report['phase']=phase;report['memory_'+phase]=memory()
        if rank==0:
            atomic(a.output/'checkpoint.json',report)
            print('CHECKPOINT',phase,json.dumps({k:report[k] for k in report if k.endswith('_seconds')}),flush=True)
    checkpoint('created')
    meta=read_lime_metadata(a.gauge); assert tuple(meta['lattice_xyzt'])==(*lat[:3],tile_time)
    stage('sha256_start')
    report['input_sha256']=comm.bcast(digest(a.gauge) if rank==0 else None)
    stage('read_start')
    if repeats==1:
        gauge,report['read_seconds']=_measure(comm,lambda:read_lime_gauge(a.gauge,grid,coords,comm))
    else:
        tile=comm.Split(rank//tile_ranks,rank)
        try:
            tile_grid=(1,1,1,tile_ranks)
            tile_coords=(0,0,0,tile.rank)
            gauge,report['read_seconds']=_measure(
                comm,lambda:read_lime_gauge(a.gauge,tile_grid,tile_coords,tile))
        finally:
            tile.Free()
    stage('stout_start')
    gauge,report['stout_seconds']=_measure(comm,lambda:stout_smear(gauge,steps=1,rho=.125,dir_ignore=4,comm=comm))
    gauge.astype('<c16',copy=False).tofile(a.scratch/f'gauge-{rank}.bin')
    checkpoint('preprocessed')
    with Solver(lat,grid,mass=a.mass,csw=a.csw,block=a.block,threads=threads,seed=1024,
                backend=a.backend,normalization='mass',library=a.library,comm=comm) as solver:
        _,report['gauge_clover_seconds']=_measure(comm,lambda:solver.load_gauge(gauge,layout='lex'))
        del gauge
        checkpoint('loaded')
        _,report['setup_seconds']=_measure(comm,solver.setup)
        checkpoint('setup')
        faulthandler.cancel_dump_traceback_later()
        shape=(lat[3]//comm.size,lat[2],lat[1],lat[0],4,3)
        src=np.zeros(shape,dtype=np.complex128)
        if rank%tile_ranks==0:
            if a.source=='wall':
                src[0,:,:,:,0,0]=1
            else:
                src[0,0,0,0,0,0]=1
        wall_sources=None
        if a.source=='wall' and not a.single_only:
            wall_sources=np.zeros((12,*shape),dtype=np.complex128)
            if rank==0:
                for col in range(12):
                    spin,color=divmod(col,3)
                    wall_sources[col,0,:,:,:,spin,color]=1
        for i in range(3):
            os.environ['LQCD_RHS_BATCH']='1'
            single,wall=_measure(comm,lambda:solver.solve(src,a.tol,layout='lex'))
            stats=[dict(solver.last_result)]
            assert all(s['converged'] and s['true_residual']<=a.tol for s in stats)
            report['single_samples'].append(dict(run=i+1,wall_seconds=wall,stats=stats,**native_timing(stats)))
            if rank==0: print('SAMPLE single',i+1,json.dumps(report['single_samples'][-1]),flush=True)
            checkpoint(f'single_{i+1}')
            if i==1:
                single.astype('<c16',copy=False).tofile(a.scratch/f'solution-{rank}-0.bin')
        checkpoint('single')
        for i in range(0 if a.single_only else 3):
            os.environ['LQCD_RHS_BATCH']='2'
            if wall_sources is not None:
                (prop,stats),wall=_measure(comm,lambda:solver.solve_many(wall_sources,a.tol,layout='lex'))
            else:
                (prop,stats),wall=_measure(comm,lambda:solver.solve_propagator((0,0,0,0),a.tol,layout='lex'))
            assert len(stats)==12 and all(s['converged'] and s['true_residual']<=a.tol for s in stats)
            report['twelve_samples'].append(dict(run=i+1,wall_seconds=wall,stats=stats,**native_timing(stats)))
            if rank==0: print('SAMPLE twelve',i+1,json.dumps(report['twelve_samples'][-1]),flush=True)
            checkpoint(f'twelve_{i+1}')
            if i==1:
                for col in range(12):
                    spin,color=divmod(col,3)
                    field=prop[col] if wall_sources is not None else prop[..., :,spin,:,color]
                    np.asarray(field,dtype='<c16',order='C').tofile(
                        a.scratch/f'solution-{rank}-{col+1}.bin')
            if i<2: del prop
        if not a.single_only:
            first=prop[0] if wall_sources is not None else prop[..., :,0,:,0]
            num=comm.allreduce(float(np.linalg.norm(single-first)**2))
            den=comm.allreduce(float(np.linalg.norm(first)**2))
            report['single_full12_relative_error']=(num/den)**.5
            assert report['single_full12_relative_error']<=1e-6
        for key in ('single','twelve'):
            samples=report[key+'_samples']
            if not samples:
                continue
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
