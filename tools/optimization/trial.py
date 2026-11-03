#!/usr/bin/env python3
"""Execute one evidence-led proposal on an allocated node; resumable stages."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

import campaign as ledger


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--id', required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--fixture', required=True)
    p.add_argument('--reference', required=True)
    p.add_argument('--extractor', required=True)
    p.add_argument('--backend', choices=['arm','x86'], required=True)
    p.add_argument('--allocation', required=True)
    p.add_argument('--reuse-attempt')
    p.add_argument('--against')
    p.add_argument('--baseline', action='store_true')
    p.add_argument('--diagnostic', action='store_true')
    p.add_argument('--reference-propagator')
    p.add_argument('--test-regex', default='^(core|arm_.*|coarse_kernel|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2)$')
    args = p.parse_args()
    root = args.campaign.resolve()
    attempt = root / 'attempts' / args.id
    if not attempt.exists():
        history = ledger.show_history(root)
        proposal = ledger.read(args.proposal)
        proposal['history_read_token'] = history['history_read_token']
        ledger.propose(root, args.id, proposal)
    snapshot = ledger.snapshot(root, args.id)
    source, build = Path(snapshot['source']), Path(snapshot['build'])
    plan = ledger.read(args.plan)
    if len(plan['cases']) != 1:
        p.error('one report per ledger attempt required; use bench_full12 directly for dynamic interleaving')
    plan_path = attempt / 'plan.json'
    if plan_path.exists():
        if ledger.read(plan_path) != plan:
            raise RuntimeError('Cannot change plan while resuming an attempt')
    else:
        ledger.atomic(plan_path, plan)
    def stage(name, argv, timeout, env=None):
        result = ledger.run_stage(root, args.id, name, dict(argv=list(map(str,argv)),
            cwd=str(build), env=env or {}, timeout_seconds=timeout))
        print(json.dumps(dict(stage=name, **result)), flush=True)
        if result['status'] != 'passed':
            raise RuntimeError(f'{name}: {result["status"]}; evidence retained, explicit retry needed')
    if args.reuse_attempt:
        other = ledger.read(root/'attempts'/args.reuse_attempt/'attempt.json')
        ledger.check_snapshot(root/'attempts'/args.reuse_attempt, other)
        if other['snapshot']['source_manifest_sha256'] != snapshot['source_manifest_sha256']:
            raise RuntimeError('Cannot reuse binary compiled from different source snapshot')
        library = root/'attempts'/args.reuse_attempt/'build'/'liblqcd_cpu.so'
        if not library.is_file():
            raise RuntimeError('Reusable build missing')
        reuse = dict(attempt=args.reuse_attempt, source_manifest_sha256=snapshot['source_manifest_sha256'],
                     library_sha256=ledger.digest(library), library_path=str(library))
        reuse_path = attempt/'reused-build.json'
        if reuse_path.exists() and ledger.read(reuse_path) != reuse:
            raise RuntimeError('Reused build changed since checkpoint')
        ledger.atomic(reuse_path,reuse)
    else:
        configure = ['cmake','-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release',
            '-DLQCD_BUILD_RUNTIME=ON','-DMULTIGRID_NATIVE=ON',
            '-DMPI_C_COMPILER='+str(shutil.which('mpicc')),
            '-DMPI_CXX_COMPILER='+str(shutil.which('mpicxx')),
            '-DLQCD_TEST_PYTHON='+sys.executable]
        if os.environ.get('LQCD_MPI_FLAGS'):
            configure.append('-DLQCD_MPI_FLAGS='+os.environ['LQCD_MPI_FLAGS'])
        if os.environ.get('LQCD_EXPERIMENT_KUPL_ROOT'):
            configure += ['-DLQCD_KUPL_HBW=ON','-DLQCD_KUPL_ROOT='+os.environ['LQCD_EXPERIMENT_KUPL_ROOT']]
        stage('configure',configure,180)
        stage('build',['cmake','--build',build,'-j','16'],480)
        stage('ctest',['ctest','--test-dir',build,'--output-on-failure','-R',args.test_regex],1800,
              {'OMP_NUM_THREADS':'2','OMP_PLACES':'cores','OMP_PROC_BIND':'close'})
        library = build/'liblqcd_cpu.so'
    maximum = max(case['threads'] for case in plan['cases'])
    command = [sys.executable,source/'tools/run_numa.py']
    if args.backend == 'x86':
        command += ['--ranks-per-numa','2']
    command += ['--threads',str(maximum),'--',sys.executable,'-u',source/'tools/optimization/bench_full12.py',
        '--fixture',args.fixture,'--plan',plan_path,'--library',library,'--backend',args.backend,
        '--output',attempt/'measurements','--allocation',args.allocation,
        '--snapshot-sha',snapshot['source_manifest_sha256']]
    if args.reference_propagator:
        command += ['--reference-propagator',args.reference_propagator]
    if args.diagnostic:
        command += ['--diagnostic']
    stage('benchmark',command,1800)
    case = attempt/'measurements'/plan['cases'][0]['id']
    stage('independent',[sys.executable,source/'tools/optimization/bench_full12.py','--verify',case,
          '--reference',args.reference,'--extractor',args.extractor],1200,
          {'OMP_NUM_THREADS':'4','OMP_PLACES':'cores','OMP_PROC_BIND':'close'})
    if args.diagnostic:
        ledger.conclude(root,args.id,'inconclusive','Diagnostic-only run; profile timings are not ranked',
                        [str(case/'result.json')])
        return
    ledger.ingest(root,args.id,case/'result.json')
    if args.baseline or args.against:
        try:
            result = ledger.promote(root,args.id,args.against,args.baseline)
            print('PROMOTED '+json.dumps(result),flush=True)
        except ledger.EvidenceError as exc:
            ledger.conclude(root,args.id,'inconclusive',str(exc),[str(case/'result.json')])
            print('INCONCLUSIVE '+str(exc),flush=True)
    else:
        print('CONTROL_READY '+args.id,flush=True)


if __name__ == '__main__':
    main()
