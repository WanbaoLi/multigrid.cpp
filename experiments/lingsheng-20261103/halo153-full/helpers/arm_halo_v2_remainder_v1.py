"""Independent HaloV2 codegen or full small-input correctness. Never performance."""
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

HEAD='760666c8ac459ef062c749ee7ee9964c99e7c3c8'
OLD_LIBRARY='d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82'
CPP='^(core|arm_.*|coarse_kernel|wilson_.*|hbw_buffer|hbm_placement|native_allocator)$'
MPI='^(coarse_batch_reduce_serial|coarse_batch_reduce_mpi2|coarse_batch_halo_mpi4|batch12_coarse_reduce_mpi2|batch12_coarse_halo_mpi[24]|runtime_batch_coarse_reduce|runtime_batch_coarse_halo|mg_tuning|coarse_batch_halo_(blocking|fused|shrunk_team|interior))$'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def check_recovery(args,sha,integrity):
    import ctest_remainder_v1 as coverage
    require=coverage.require
    from raw_scalar_helper import source_bytes
    plan=json.loads(source_bytes(args.recovery_plan,sha(args.recovery_plan,args.recovery_plan_sha)))
    require(plan['complete']and plan['id']==args.state_id=='153-halo-v2-remainder-worker10'and
        plan['numerical_tests_or_limits_changed']is False,'Exact timeout recovery scope required')
    for row in plan['pinned_files']:sha(row['path'],row['sha256'])
    prior=plan['prior_stage'];require(prior['status']=='timeout'and prior['timeout_seconds']==1000 and
        prior['cleanup']['complete']and not prior['cleanup']['surviving_pids'],'Only a cleaned whole-suite timeout can resume')
    actual=json.loads(source_bytes(args.root/'campaign-halo-v2/attempts/000-halo-v2-tests/attempt.json',
        sha(args.root/'campaign-halo-v2/attempts/000-halo-v2-tests/attempt.json')))
    require(actual['stages']['mpi-numerical-ctest']==prior,'Prior failed stage changed')
    catalog=json.loads(source_bytes(plan['catalog_path'],sha(plan['catalog_path'],plan['catalog_sha256'])))
    names=[row['name']for row in catalog['tests']]
    require(names==plan['all_tests']and len(names)==13,'Original complete13-test catalog required')
    text=source_bytes(plan['prior_log'],sha(plan['prior_log'],plan['prior_log_sha256'])).decode()
    passed=coverage.passed_prefix(text,names)
    require(passed==plan['completed_tests']and names[len(passed):]==plan['remaining_tests'],
        'Only actually completed cases can be reused')
    return dict(plan,plan_path=str(args.recovery_plan),plan_sha256=args.recovery_plan_sha,
        complete=False,meaning='11 actually passed original cases plus fresh execution of interrupted12th and unstarted13th; original timeout retained')


def complete_recovery(plan,directory,sha):
    import ctest_remainder_v1 as coverage
    require=coverage.require
    log=directory/'mpi-numerical-ctest-remainder-v1-000.log'
    from raw_scalar_helper import source_bytes
    digest=sha(log);text=source_bytes(log,digest).decode()
    fresh=coverage.completed_remainder(text,plan['remaining_tests'])
    require(plan['completed_tests']+fresh==plan['all_tests']and
        len(set(plan['completed_tests']+fresh))==13,'Full13-case numerical coverage required')
    sha(plan['prior_log'],plan['prior_log_sha256'])
    return dict(plan,complete=True,executed_remaining_tests=fresh,remainder_log=str(log),remainder_log_sha256=digest,
        full_test_coverage=plan['completed_tests']+fresh,numerical_tests_or_limits_changed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--auxiliary',type=Path,required=True)
    p.add_argument('--scope',choices=['codegen','full'],required=True)
    p.add_argument('--state-id',required=True)
    p.add_argument('--test-attempt',default='000-halo-v2-tests')
    p.add_argument('--expected-entry-sha',required=True)
    p.add_argument('--expected-manifest-sha',required=True)
    p.add_argument('--expected-host',required=True)
    p.add_argument('--recovery-plan',type=Path,required=True)
    p.add_argument('--recovery-plan-sha',required=True)
    a=p.parse_args();r=a.root.resolve();aux=a.auxiliary.resolve()
    sys.dont_write_bytecode=True
    integrity=load('_halo_v2_integrity',aux/'file_integrity.py');integrity.known_vectors()
    sha=lambda path,expected=None:integrity.read_dual(Path(path),expected)['openssl_sha256']
    sha(__file__,a.expected_entry_sha);sha(aux/'halo-v2-arm-helpers.json',a.expected_manifest_sha)
    manifest=json.loads((aux/'halo-v2-arm-helpers.json').read_text())
    for name,value in manifest['files'].items():sha(aux/name,value)
    recovery=check_recovery(a,sha,integrity)
    source=r/'source-halo-v2-760';campaign=r/'campaign-halo-v2'
    sys.path.insert(0,str(source/'tools/optimization'))
    import campaign as ledger
    ledger.digest=sha;require=ledger.require
    require(platform.machine().lower() in ('aarch64','arm64') and
        socket.gethostname().split('.')[0]==a.expected_host,'Exact ARM compute host required')
    require(os.environ.get('LQCD_OPT_ALLOCATION') and os.environ.get('LQCD_OPT_TASK_ID'),'Owned worker task required')
    deadline=float(os.environ.get('LQCD_OPT_DEADLINE_EPOCH','0'))
    require(math.isfinite(deadline) and deadline>time.time(),'Finite safe worker deadline required')
    require(ledger.NAME.fullmatch(a.state_id),'Safe distinct scope state ID required')
    require(ledger.NAME.fullmatch(a.test_attempt),'Safe explicit new test attempt required')
    require(ledger.git(source,'rev-parse','HEAD')==HEAD and not ledger.git(source,'status','--short'),
        'Clean independent exact760 source required')
    old=r/'campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so';sha(old,OLD_LIBRARY)
    best_sha=sha(r/'campaign/best.json')
    recipe={key:os.environ.get(key) for key in ['LQCD_MPI_FLAGS','LQCD_EXPERIMENT_KUPL_ROOT','LQCD_EXPERIMENT_CXX_RUNTIME']}
    for key in list(os.environ):
        if key.startswith(('LQCD_','NATIVE_')) and not key.startswith('LQCD_OPT_'):os.environ.pop(key,None)
    for key in ['LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT','OMP_WAIT_POLICY','GOMP_SPINCOUNT']:
        os.environ.pop(key,None)
    state_path=r/(a.state_id+'-state.json')
    require(not state_path.exists(),'A new explicit scope identity is required; never overwrite old state')
    state=dict(complete=False,status='started',scope=a.scope,source_head=HEAD,
        controller_sha256=sha(__file__),helper_manifest_sha256=sha(aux/'halo-v2-arm-helpers.json'),test_attempt=a.test_attempt,
        host=socket.gethostname(),allocation=os.environ['LQCD_OPT_ALLOCATION'],
        full_numerical_complete=False,mpi_status='pending',sve_matrix_status='pending',
        main_best_unchanged_sha256=best_sha,production_full12_verified=False,performance_ranked=False,stages={})
    save=lambda:ledger.atomic(state_path,state)
    state['ctest_recovery']=recovery
    save()
    def unchanged():
        require(sha(r/'campaign/best.json')==best_sha,'Main best changed')
        sha(__file__,state['controller_sha256'])
        sha(aux/'halo-v2-arm-helpers.json',state['helper_manifest_sha256'])
        for name,value in manifest['files'].items():sha(aux/name,value)
    if not campaign.exists():
        ledger.initialize(campaign,source,source/'skills/kunpeng-lqcd-reference',
            '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30',
            '1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c',baseline_commit=HEAD)
    name=a.test_attempt
    if not (campaign/'attempts'/name).exists():
        history=ledger.show_history(campaign)
        ledger.propose(campaign,name,dict(history_read_token=history['history_read_token'],
            bottleneck='711 ARM disabled-halo ELF retains three empty vector lifetimes and a repeated state-base stack load',
            hypothesis='Fixed-mode noinline bodies remove the observed control mechanism without changing independent GCR arithmetic',
            change='760666c constexpr dispatch only; no persistent workspace, tolerance or work changes',
            mechanism='False specialization has empty halo scratch and no halo field/helper access',
            history_links=['docs/coarse-batch-halo-v2.md','docs/coarse-batch-halo-candidate.md'],
            retry_conditions='Existing failure never retried. Passed immutable build/unit checkpoints may be reused by a new full scope task.'))
    snap=ledger.snapshot(campaign,name);src,build=Path(snap['source']),Path(snap['build'])
    state['snapshot']=snap;save()
    def stage(key,argv,timeout,env=None):
        unchanged()
        prior=ledger.read(campaign/'attempts'/name/'attempt.json')['stages'].get(key)
        require(not prior or prior['status']=='passed','Failed/incomplete stage retained; new attempt required')
        if not prior and deadline-time.time()<timeout+60:
            state.update(status='pending',pending_stage=key,required_seconds=timeout+60);save()
            raise PendingTime('Safe stage budget unavailable: '+key)
        result=ledger.run_stage(campaign,name,key,dict(argv=list(map(str,argv)),cwd=str(build),
            timeout_seconds=prior['timeout_seconds'] if prior else timeout,env=env or {}))
        state['stages'][key]=dict(status=result['status'],log=result['log'],reused=bool(prior));save()
        require(result['status']=='passed' and result['cleanup']['complete'],'Stage failed; retain evidence: '+key)
        print('HALO_V2_ARM_STAGE '+json.dumps(dict(scope=a.scope,stage=key,status='passed',reused=bool(prior))),flush=True)
    try:
        command=['cmake','-S',src,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DLQCD_BUILD_RUNTIME=ON',
            '-DMULTIGRID_NATIVE=ON','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
            '-DMPI_C_COMPILER='+str(shutil.which('mpicc')),'-DMPI_CXX_COMPILER='+str(shutil.which('mpicxx')),
            '-DLQCD_TEST_PYTHON='+sys.executable]
        if recipe['LQCD_MPI_FLAGS']:command+=['-DLQCD_MPI_FLAGS='+recipe['LQCD_MPI_FLAGS']]
        if recipe['LQCD_EXPERIMENT_KUPL_ROOT']:
            command+=['-DLQCD_KUPL_HBW=ON','-DLQCD_KUPL_ROOT='+recipe['LQCD_EXPERIMENT_KUPL_ROOT']]
        if recipe['LQCD_EXPERIMENT_CXX_RUNTIME']:
            runtime=Path(recipe['LQCD_EXPERIMENT_CXX_RUNTIME']).resolve()
            require((runtime/'libstdc++.so').is_file(),'Declared SDK runtime required')
            flags='-L'+str(runtime)+' -Wl,-rpath,'+str(runtime)
            command+=['-DCMAKE_EXE_LINKER_FLAGS='+flags,'-DCMAKE_SHARED_LINKER_FLAGS='+flags]
        stage('configure',command,180)
        stage('build',['cmake','--build',build,'-j','16'],600)
        # CMake's SOVERSION symlink is an expected build artifact. Resolve only
        # this declared artifact and prove its real target remains in build;
        # external immutable inputs still use the strict no-symlink reader.
        library=(build/'liblqcd_cpu.so').resolve(strict=True)
        try:library.relative_to(build.resolve(strict=True))
        except ValueError:raise RuntimeError('CMake library target escaped the canonical build directory')
        env=dict(OMP_NUM_THREADS='2',OMP_PLACES='cores',OMP_PROC_BIND='close',OPENBLAS_NUM_THREADS='1',
            MKL_NUM_THREADS='1',LQCD_HBW_ALLOC='off',LQCD_COARSE_BATCH_REDUCE='0',LQCD_COARSE_BATCH_HALO='0',
            LD_PRELOAD='',PERF_COUNTER_ROOT='',CTEST_PARALLEL_LEVEL='1')
        stage('arm-codegen',[sys.executable,aux/'arm_halo_v2_codegen.py','--library',library,
            '--old-library',old,'--output',campaign/'attempts'/name/'codegen'],90)
        state.update(arm_codegen_complete=True,library=str(library),
            library_sha256=sha(library),
            codegen_files={str(path.relative_to(campaign)):sha(path) for path in
                sorted((campaign/'attempts'/name/'codegen').iterdir()) if path.is_file()});save()
        stage('arm-unit-ctest',['ctest','--test-dir',build,'--parallel','1','--stop-on-failure',
            '--output-on-failure','-V','-R',CPP],240,env)
        state['unit_complete']=True;save()
        if a.scope=='codegen':
            state.update(complete=True,status='passed',meaning='Codegen/unit scope only; MPI/SVE matrix and physical full12 remain pending')
            unchanged();save();return
        # This is an explicitly separate scope/task; do not silently downgrade it.
        if deadline-time.time()<=4300:
            state.update(status='pending',pending_stage='full-mpi-sve-matrix',required_seconds=4300);save()
            raise PendingTime('Full scope requires4300s after reusable compile/unit checkpoints')
        stage('mpi-numerical-ctest-remainder-v1',['ctest','--test-dir',build,'--parallel','1','--stop-on-failure',
            '--output-on-failure','-V','-R','^('+ '|'.join(re.escape(v)for v in recovery['remaining_tests'])+')$'],660,env)
        state['ctest_recovery']=complete_recovery(recovery,campaign/'attempts'/name,sha)
        state['mpi_status']='passed';save()
        probe=aux/'phase6_sve_probe.py'
        stage('sve-compiled-coarse',[sys.executable,probe,'--audit-build',build,'--source',src],90)
        flags=[v for v in (recipe['LQCD_MPI_FLAGS'] or '').split(';') if v]
        require(flags,'Explicit native MPI placement required')
        vector_env=dict(env,LQCD_CPU_LIBRARY=str(library),LQCD_ARM_COARSE_SVE='1',
            LQCD_COARSE_FUSED='1',LQCD_HALO_OVERLAP='1',LQCD_COARSE_SPATIAL_OVERLAP='1',LQCD_TEST_COARSE_HALO_SMOKE='0')
        for width in (16,32,64):
            stage('sve-dense-vl'+str(width),[sys.executable,src/'tools/run_sve_vl.py','--bytes',str(width),
                '--',build/'coarse_kernel_test'],90,vector_env)
            stage('sve-ghost-mpi4-vl'+str(width),[shutil.which('mpiexec'),*flags,'-n','4',sys.executable,
                src/'tools/run_sve_vl.py','--bytes',str(width),'--',sys.executable,probe,
                '--expected-bytes',str(width),'--test',src/'tests/runtime/test_coarse_batch_reduce.py'],900,vector_env)
            text=(campaign/'attempts'/name/('sve-ghost-mpi4-vl'+str(width)+'-000.log')).read_text()
            ranks=[json.loads(v) for v in re.findall(r'PHASE6_SVE_RANKS_COMPLETE (\{[^\n]+\})',text)]
            actual=[json.loads(v) for v in re.findall(r'COARSE_BATCH_HALO_DIAGNOSTIC (\{[^\n]+\})',text)]
            require(len(ranks)==1 and ranks[0]['complete'] and ranks[0]['library_sha256']==state['library_sha256'] and
                {v['rank'] for v in ranks[0]['ranks']}==set(range(4)) and all(v['actual_bytes']==width for v in ranks[0]['ranks']) and
                any(v['calls']>0 for v in actual),'Actual4-rank VL, merged calls and independent oracle required')
            state.setdefault('sve_matrix',{})[str(width)]=dict(ranks=ranks[0],actual=actual);save()
        state.update(complete=True,status='passed',full_numerical_complete=True,sve_matrix_status='passed')
        unchanged();save()
    except PendingTime:
        print('HALO_V2_ARM_PENDING '+json.dumps(state),flush=True)
    except BaseException as error:
        state.update(complete=False,status='failed',error=str(error));save();raise


class PendingTime(RuntimeError):pass

if __name__=='__main__':main()
