import argparse,hashlib,json,os,socket,sys,time
from pathlib import Path
import numpy as np
from mpi4py import MPI
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4')
source=root/'source-reliable';sys.path.insert(0,str(source/'python'))
from lqcd_cpu import Solver
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--library',required=True);p.add_argument('--threads',type=int,required=True);p.add_argument('--setup-threads',type=int);p.add_argument('--pilot',action='store_true');a=p.parse_args()
comm=MPI.COMM_WORLD;rank=comm.rank;ranks=comm.size;nt=64//ranks
out=Path(a.out)
if rank==0:out.mkdir(parents=True,exist_ok=False)
comm.Barrier()
g=np.array(np.load(root/'input/gauge-untwisted.npy',mmap_mode='r')[rank*nt:(rank+1)*nt])
resources=comm.allgather(dict(rank=rank,cpus=sorted(os.sched_getaffinity(0)),places=os.environ.get('OMP_PLACES')))
rows=[]
with Solver([24,24,24,64],[1,1,1,ranks],mass=-.277,csw=1.160920226,block=[6,6,6,4],threads=a.setup_threads or a.threads,seed=1024,normalization='mass',backend='arm',library=a.library)as solver:
    solver.load_gauge(g,'lex');setup=solver.setup()
    os.environ['LQCD_COARSE_BATCH_REDUCE']='1';solver.set_threads(a.threads)
    for repeat in range(1 if a.pilot else 1):
        comm.Barrier();start=time.perf_counter()
        prop,stats=solver.solve_propagator((0,0,0,0),1e-8,layout='lex')
        wall=comm.allreduce(time.perf_counter()-start,op=MPI.MAX)
        assert len(stats)==12 and all(s['converged']and s['true_residual']<=1e-8 for s in stats)
        # Batch statistics repeat the shared timer on each member; count once.
        internal=0.;native_api=0.;i=0
        while i<12:
            n=stats[i].get('batch_size',1);internal+=stats[i]['solver_seconds'];native_api+=stats[i]['api_seconds'];i+=n
        internal=comm.allreduce(internal,op=MPI.MAX)
        native_api=comm.allreduce(native_api,op=MPI.MAX)
        rows.append(dict(repeat=repeat,warmup=False,internal_seconds=internal,native_api_seconds=native_api,api_seconds=wall,stats=stats))
        if rank==0:
            (out/'result.json').write_text(json.dumps(dict(complete=False,host=socket.gethostname(),resources=resources,setup_seconds=setup,samples=rows),indent=2)+'\n')
            print('OURS_FULL12',repeat,internal,wall,flush=True)
    # One normalized source column sufficient for a cross-library solution check;
    # internal true residuals above cover all12 columns of every timed call.
    np.save(out/f'propagator-rank{rank:05d}.npy',prop)
    if rank==0:
        (out/'result.json').write_text(json.dumps(dict(complete=True,host=socket.gethostname(),resources=resources,setup_seconds=setup,
            library_sha256=hashlib.sha256(Path(a.library).read_bytes()).hexdigest(),outer_float=os.environ.get('LQCD_OUTER_FLOAT','1'),rhs_batch=os.environ.get('LQCD_RHS_BATCH'),reliable_fused=os.environ.get('LQCD_RELIABLE_FUSED','0'),tol=1e-8,samples=rows),indent=2)+'\n')
