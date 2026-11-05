"""Isolated Clover-reuse x86 regression correctness only; no production full12 timing or promotion."""
from pathlib import Path
import hashlib
import json
import os
import re
import socket
import subprocess
import sys

ROOT=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105')
HEAD='833f8732f6b06e370074efbb610fc7a85fe11a46'
DEFAULT_TESTS='^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning|coarse_batch_reduce_.*|coarse_batch_halo_.*|batch12_coarse_(reduce|halo)_mpi[24]|runtime_batch_coarse_reduce)$'
OWNED_TESTS='^(setup_source_owned_.*|cpu_backend_source_owned_mpi2)$'


def main():
    if socket.gethostname().split('.')[0]!='node5005'or not os.environ.get('LQCD_OPT_TASK_ID'):
        raise RuntimeError('Owned node5005 bounded task required')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
    import file_integrity as integrity
    integrity.read_dual(integrity.__file__,'34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427')
    digest=lambda path:integrity.read_dual(Path(path))['openssl_sha256']
    source=ROOT/'source'
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=HEAD or subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip():
        raise RuntimeError('Source HEAD/cleanliness differs from exact Clover experiment')
    sys.path.insert(0,str(source/'tools/optimization'));import campaign as ledger
    ledger.digest=digest
    campaign=ROOT/'campaign';owner='000-delivery-tests'
    reference=Path('/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid')
    if not campaign.exists():ledger.initialize(campaign,source,source/'skills/kunpeng-lqcd-reference',
        '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30',digest(reference),baseline_commit=HEAD)
    if not(campaign/'attempts'/owner).exists():
        proposal=dict(bottleneck='Final delivery source must match the retained measured052 numerical implementation',
            hypothesis='Restored052 arithmetic/build/runtime files retain correctness with accumulated framework and evidence changes',
            change='Fresh exact833 source; numerical files equal5fe accepted source; independent build and configured native/MPI tests',
            mechanism='No performance attribution to the source restoration; qualify the actual deliverable before fresh full12 comparison',
            history_links=['docs/optimization-progress-20261104.md'],retry_conditions='New coherent delivery source after unadoptedHalo rollback')
        proposal['history_read_token']=ledger.show_history(campaign)['history_read_token'];ledger.propose(campaign,owner,proposal)
    snapshot=ledger.snapshot(campaign,owner);s=Path(snapshot['source']);build=Path(snapshot['build']);path=campaign/'attempts'/owner
    if snapshot['git_head']!=HEAD:raise RuntimeError('Frozen source snapshot differs')
    for key in list(os.environ):
        if(key.startswith('LQCD_')and not key.startswith('LQCD_OPT_'))or key in('LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT','OMP_WAIT_POLICY','GOMP_SPINCOUNT'):
            os.environ.pop(key,None)
    ledger.atomic(path/'controller.json',dict(controller_sha256=digest(__file__),
        head=HEAD,source_manifest_sha256=snapshot['source_manifest_sha256'],ordinary_performance=False,
        limitation='Direct SSH correctness task; scheduler nodeDOWN*, no scheduler exclusivity; no physical fixture/performance claim'))
    def stage(key,argv,timeout,env=None):
        previous=ledger.read(path/'attempt.json')['stages'].get(key)
        if previous and previous['status']!='passed':raise RuntimeError('Retain failed stage; fresh explicit identity required')
        result=ledger.run_stage(campaign,owner,key,dict(argv=list(map(str,argv)),cwd=str(build),timeout_seconds=timeout,env=env or {}))
        print('BESTBASE_STAGE '+json.dumps(dict(stage=key,status=result['status'],log=result['log'])),flush=True)
        if result['status']!='passed'or not result['cleanup']['complete']:raise RuntimeError('Stage failed or cleanup incomplete: '+key)
        return result
    stage('configure',['cmake','-S',s,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DLQCD_BUILD_RUNTIME=ON','-DMULTIGRID_NATIVE=ON',
        '-DCMAKE_C_COMPILER=/public2/home/lwb_720/miniconda3/bin/gcc','-DCMAKE_CXX_COMPILER=/public2/home/lwb_720/miniconda3/bin/g++',
        '-DMPI_C_COMPILER=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/mpicc','-DMPI_CXX_COMPILER=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/mpicxx',
        '-DLQCD_TEST_PYTHON='+sys.executable,'-DCMAKE_CXX_COMPILER_LAUNCHER='+sys.executable+';'+str(s/'tools/pin_build.py'),
        '-DCMAKE_C_COMPILER_LAUNCHER='+sys.executable+';'+str(s/'tools/pin_build.py'),
        '-DLQCD_MPI_FLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'],180)
    stage('build',['cmake','--build',build,'-j','16'],600)
    catalog={}
    for label,pattern in [('default',DEFAULT_TESTS)]:
        row=stage('catalog-'+label,['ctest','--test-dir',build,'--show-only=json-v1','-R',pattern],30)
        catalog[label]=json.loads((path/row['log']).read_text())
        if not catalog[label]['tests']:raise RuntimeError('Empty actual CTest selection '+label)
    env=dict(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        LQCD_COARSE_BATCH_REDUCE='0',LQCD_ARM_SVE_CLOVER_REUSE='1',LQCD_HBW_ALLOC='off')
    summaries={}
    for label,pattern,timeout in [('default',DEFAULT_TESTS,2400)]:
        row=stage(label+'-ctest',['ctest','--test-dir',build,'--parallel','1','--output-on-failure','-V','-R',pattern],timeout,env)
        text=(path/row['log']).read_text();match=re.search(r'(\d+)% tests passed, (\d+) tests failed out of (\d+)',text)
        if not match or int(match[1])!=100 or int(match[2])or int(match[3])!=len(catalog[label]['tests']):
            raise RuntimeError('Actual selected count or terminal CTest summary differs: '+label)
        summaries[label]=dict(selected_count=len(catalog[label]['tests']),names=[t['name']for t in catalog[label]['tests']],
            reported_count=int(match[3]),failed=0,explicit_skip_lines=[line.strip()for line in text.splitlines()if 'SKIP'in line or'***Skipped'in line],log_sha256=digest(path/row['log']))
    library=(build/'liblqcd_cpu.so').resolve(strict=True)
    if not library.is_relative_to(build.resolve(strict=True)):raise RuntimeError('Known CMake library alias escaped build')
    result=dict(complete=True,status='passed',source_commit=HEAD,source_manifest_sha256=snapshot['source_manifest_sha256'],snapshot=snapshot,
        library=str(library),library_sha256=digest(library),tests=summaries,stages=ledger.read(path/'attempt.json')['stages'],performance_ranked=False,
        precision_scope='Existing native, dense oracle and MPI/runtime tests on x86; ARM SVE skips are not target qualification',
        arm_backend_execution=False,accepted_source_base='5fe1b5fd2702f799488a2b8119002c450de5b4cd')
    ledger.atomic(ROOT/'000-summary.json',result)
    ledger.conclude(campaign,owner,'inconclusive','Existing x86 native/MPI correctness passed; no ARM SVE or physical-performance claim',
        [str(ROOT/'000-summary.json'),str(path/'default-ctest-000.log')])
    print('BESTBASE_CORRECTNESS_PASSED '+json.dumps(dict(summary=str(ROOT/'000-summary.json'))),flush=True)


if __name__=='__main__':main()
