"""ARM build, assembly and small-input qualification; no performance promotion."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import sys
import time
ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
HEAD='861613c703117c6b5b671e245a7142e217b09501'
TESTS='^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning|coarse_batch_reduce_.*|batch12_coarse_reduce_mpi2|runtime_batch_coarse_reduce)$'

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha',required=True);args=p.parse_args()
    aux=Path(__file__).parent;sys.path.insert(0,str(aux));import file_integrity as integrity
    from raw_scalar_helper import source_bytes
    def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
    def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
    plan=read(args.plan,args.plan_sha)
    for row in plan['pinned_files']:sha(row['path'],row['sha256'])
    startup=read(plan['startup']['path'],plan['startup']['sha256']);status=read(plan['dependency_status'])
    require=integrity.require
    require(plan['source_head']==HEAD and plan['scope']=='arm-clover-full-qualification-v1','Exact reviewed Clover test plan required')
    require(status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids'],'Prior ordinary bracket must finish and clean before ARM compilation')
    require(platform.machine()=='aarch64'and socket.gethostname()==startup['host']and os.environ.get('LQCD_OPT_ALLOCATION')==startup['allocation']and os.environ.get('LQCD_OPT_TASK_ID'),'Exact owned ARM worker required')
    require(sorted(os.sched_getaffinity(0))==startup['before_worker_exec_parent_state']['cpus']and len(os.sched_getaffinity(0))==592,'Full unpinned parent required')
    require(not any('libgomp.so'in s or'libkupl.so'in s for s in Path('/proc/self/maps').read_text().splitlines()),'No runtime in parent')
    deadline=float(os.environ['LQCD_OPT_DEADLINE_EPOCH']);require(math.isfinite(deadline)and deadline-time.time()>=3690,'Whole qualification budget3600 plus90 reserve required')
    recipe={k:os.environ.get(k)for k in('LQCD_MPI_FLAGS','LQCD_EXPERIMENT_KUPL_ROOT','LQCD_EXPERIMENT_CXX_RUNTIME')}
    for key in list(os.environ):
        if(key.startswith(('LQCD_','NATIVE_'))and not key.startswith('LQCD_OPT_'))or key in('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):
            os.environ.pop(key,None)
    source=Path(plan['source']);tools=source/'tools/optimization';sys.path.insert(0,str(tools));import campaign as ledger
    ledger.digest=sha;require(ledger.git(source,'rev-parse','HEAD')==HEAD and not ledger.git(source,'status','--porcelain'),'Clean exact Clover source required')
    campaign=ROOT/'campaign-clover-reuse-v1';owner='000-arm-clover-tests'
    if not campaign.exists():ledger.initialize(campaign,source,source/'skills/kunpeng-lqcd-reference',
        '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30','1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c',baseline_commit=HEAD)
    require(not(campaign/'attempts'/owner).exists(),'Fresh qualification attempt required; failed stages are preserved')
    proposal=dict(bottleneck='Verified143: fine/local/Clover source loads and repeated input rows; native annotation supports a cache/register reuse experiment',
        hypothesis='Site-outer Clover input reuse reduces source reloads; default-off dispatch must avoid the earlier halo frame regression',
        change='Exact052-base opt-in out-of-line input reuse with unchanged j-order and precision',
        mechanism='Qualify ARM codegen, dense/tail/VL16/32/64 plus native MPI/runtime before physical full12 ordinary trials',
        history_links=['docs/arm-clover-reuse-candidate.md',str(ROOT/'143-best-solve-profile-worker8-state.json')],
        retry_conditions='First Clover variant, no old test or timing inheritance',history_read_token=ledger.show_history(campaign)['history_read_token'])
    ledger.propose(campaign,owner,proposal);snap=ledger.snapshot(campaign,owner)
    src,build=Path(snap['source']),Path(snap['build']);directory=campaign/'attempts'/owner
    state=dict(complete=False,status='running',scope=plan['scope'],source_head=HEAD,snapshot=snap,
        host=startup['host'],allocation=startup['allocation'],performance_ranked=False,physical_full12=False,stages={})
    statepath=ROOT/(plan['id']+'-state.json');require(not statepath.exists(),'Fresh state ID required')
    bestsha=sha(ROOT/'campaign/best.json');ledger.atomic(statepath,state)
    def save():ledger.atomic(statepath,state)
    def stage(name,argv,timeout,env=None):
        require(sha(ROOT/'campaign/best.json')==bestsha,'Ordinary main best changed during qualification')
        require(deadline-time.time()>timeout+45,'Whole next stage and cleanup no longer fit')
        result=ledger.run_stage(campaign,owner,name,dict(argv=list(map(str,argv)),cwd=str(build),timeout_seconds=timeout,env=env or {}))
        state['stages'][name]=dict(status=result['status'],log=result['log']);save()
        require(result['status']=='passed'and result['cleanup']['complete'],'Qualification stage failed; retain source and evidence: '+name)
        print('ARM_CLOVER_STAGE '+json.dumps(dict(stage=name,status='passed')),flush=True);return result
    try:
        runtime=recipe['LQCD_EXPERIMENT_CXX_RUNTIME'];kupl=recipe['LQCD_EXPERIMENT_KUPL_ROOT']
        require(runtime and kupl and recipe['LQCD_MPI_FLAGS'],'Explicit validated SDK/MPI build recipe required')
        flags='-L'+runtime+' -Wl,-rpath,'+runtime
        stage('configure',['cmake','-S',src,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DLQCD_BUILD_RUNTIME=ON','-DMULTIGRID_NATIVE=ON',
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DLQCD_KUPL_HBW=ON','-DLQCD_KUPL_ROOT='+kupl,
            '-DCMAKE_EXE_LINKER_FLAGS='+flags,'-DCMAKE_SHARED_LINKER_FLAGS='+flags,
            '-DMPI_C_COMPILER='+str(shutil.which('mpicc')),'-DMPI_CXX_COMPILER='+str(shutil.which('mpicxx')),
            '-DLQCD_TEST_PYTHON='+sys.executable,'-DLQCD_MPI_FLAGS='+recipe['LQCD_MPI_FLAGS']],180)
        stage('build',['cmake','--build',build,'-j','16'],600)
        library=(build/'liblqcd_cpu.so').resolve(strict=True);require(library.is_relative_to(build.resolve()),'Library alias escaped build')
        state.update(library=str(library),library_sha256=sha(library));save()
        stage('codegen',[sys.executable,aux/'clover_codegen_audit.py','--library',library,'--old-library',ROOT/'campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so','--output',directory/'codegen'],90)
        env=dict(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
            LQCD_HBW_ALLOC='off',LQCD_ARM_SVE='1',LQCD_ARM_SVE_REUSE='1',LQCD_ARM_SVE_CLOVER_REUSE='1')
        dense_env=dict(env,LQCD_ARM_SVE_CLOVER_REUSE='0')
        for width in(16,32,64):
            stage('dense-vl'+str(width),[sys.executable,src/'tools/run_sve_vl.py','--bytes',str(width),'--',build/'arm_sve_test'],90,dense_env)
        catalog=stage('catalog',['ctest','--test-dir',build,'--show-only=json-v1','-R',TESTS],30)
        count=len(json.loads((directory/catalog['log']).read_text())['tests']);require(count>20,'Incomplete CTest catalog')
        tests=stage('ctest',['ctest','--test-dir',build,'--parallel','1','--output-on-failure','-V','-R',TESTS],1400,env)
        text=(directory/tests['log']).read_text();require(re.search(r'100% tests passed, 0 tests failed out of '+str(count)+r'\b',text),'Missing full CTest terminal summary')
        mpi_flags=[s for s in recipe['LQCD_MPI_FLAGS'].split(';')if s]
        vector_env=dict(env,LQCD_CPU_LIBRARY=str(library))
        for width in(16,32,64):
            stage('native-mpi2-vl'+str(width),[shutil.which('mpiexec'),*mpi_flags,'-n','2',sys.executable,src/'tools/run_sve_vl.py',
                '--bytes',str(width),'--',sys.executable,aux/'phase6_sve_probe.py','--expected-bytes',str(width),
                '--test',src/'tests/runtime/test_cpu_backend.py'],240,vector_env)
            log=(directory/('native-mpi2-vl'+str(width)+'-000.log')).read_text()
            rows=[json.loads(v)for v in re.findall(r'PHASE6_SVE_RANKS_COMPLETE (\{[^\n]+\})',log)]
            require(len(rows)==1 and rows[0]['complete']and rows[0]['library_sha256']==state['library_sha256']and
                {r['rank']for r in rows[0]['ranks']}=={0,1}and all(r['actual_bytes']==width for r in rows[0]['ranks']),'Actual MPI2 SVE length/identity/oracle proof missing')
        state.update(complete=True,status='passed',selected_tests=count,actual_sve_widths=[16,32,64],main_best_unchanged=True);save()
    except BaseException as error:state.update(complete=False,status='failed',error=str(error));save();raise
if __name__=='__main__':main()
