#!/usr/bin/env python3
"""Freeze current ledger selection and write ordinary build/run recipes.

Preparation is read-only on the campaign; no source checkout, build, benchmark,
verification or promotion is executed. Generated scripts use argv-safe quoting,
the recorded configuration, and the exact selected binary by default. Rebuilds
are separate artifacts and require their own full12 numerical/performance check.
"""
import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(8*1024**2),b''):
            value.update(part)
    return value.hexdigest()


def shell(argv):
    return shlex.join([str(value) for value in argv])


def solve_keys(project):
    tree=ast.parse((project/'python/lqcd_cpu/propagator.py').read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='SOLVE_TUNING_KEYS' for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Frozen project has no documented SOLVE_TUNING_KEYS')


def write_script(path,lines):
    path.write_text('#!/bin/bash\nset -eo pipefail\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    path.chmod(0o700)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools-project',type=Path,required=True,help='Current bookkeeping API/verification project')
    parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--attempt',default='best')
    parser.add_argument('--fixture',type=Path,required=True,help='Canonical prepared field, not the original x86 fixture')
    parser.add_argument('--gauge',type=Path,required=True,help='Original LIME, used only by raw cold script')
    parser.add_argument('--backend',choices=['arm','x86'],required=True)
    parser.add_argument('--allocation',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--python',default=sys.executable)
    parser.add_argument('--steady-repeats',type=int,default=3)
    parser.add_argument('--cold-wrapper',type=Path,default=Path(__file__).with_name('cold_full12.py'))
    parser.add_argument('--reference',type=Path)
    parser.add_argument('--extractor',type=Path)
    parser.add_argument('--reference-propagator',type=Path)
    args=parser.parse_args(argv)
    if args.steady_repeats<3:
        parser.error('At least three complete12 steady samples required')
    tools=args.tools_project.resolve()
    sys.path.insert(0,str(tools/'tools/optimization'))
    ledger=importlib.import_module('campaign')
    campaign=args.campaign.resolve()
    config=ledger.campaign(campaign)[1]
    best_before=sha(campaign/'best.json')
    selected=ledger.read(campaign/'best.json')['attempt'] if args.attempt=='best' else args.attempt
    data,report,performance=ledger.checked_attempt(campaign,selected,config)
    path=campaign/'attempts'/selected
    project=path/'source'
    library=path/'artifacts/liblqcd_cpu.so'
    if report.get('backend')!=args.backend:
        raise ValueError('Selected report backend differs from recipe target')
    if args.attempt=='best' and sha(campaign/'best.json')!=best_before:
        raise ValueError('Best changed during preparation; regenerate into a fresh directory')
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(campaign) or output.is_relative_to(tools) or output.is_relative_to(project):
        raise ValueError('Choose a new output directory outside ledger/source')
    cfg=report['configuration']
    context=cfg['context_environment']
    if context.get('PERF_COUNTER_ROOT') or context.get('LD_DEBUG'):
        raise ValueError('Selected configuration includes diagnostic instrumentation')
    if any('REDACTED' in str(value) for value in context.values()):
        raise ValueError('A redacted export cannot substitute for original runtime settings')
    setup=cfg.get('setup_threads',cfg['threads'])
    placement=cfg.get('placement_threads',cfg['threads'])
    plan=dict(context_environment=context,setup_threads=setup,placement_threads=placement,
        cases=[dict(id='full12',threads=cfg['threads'],batch=cfg['batch'],environment=cfg['solve_environment'])])
    reference_root=(Path('/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation') if args.backend=='arm'
                    else Path('/public2/home/lwb_720/.cache/mg-20261102/source/build/validation'))
    reference=(args.reference or reference_root/'multigrid').resolve()
    extractor=(args.extractor or reference_root/'extract_columns').resolve()
    baseline=(args.reference_propagator or Path(report['reference_propagator'])).resolve()
    if sha(reference)!=config['reference_sha256']:
        raise ValueError('Independent scalar reference differs from campaign contract')
    extractor_sha=sha(extractor)
    if extractor_sha!=report['verification']['extractor_sha256']:
        raise ValueError('Independent extractor differs from validated measurement')
    baseline_sha=sha(baseline)
    if baseline_sha!=report['verification']['reference_propagator_sha256']:
        raise ValueError('Baseline must match the recorded independently validated reference SHA, including overrides')
    cold=args.cold_wrapper.resolve()
    if not cold.is_file():
        raise ValueError('Cold wrapper missing')
    spec=importlib.util.spec_from_file_location('_cold_replay_policy',cold)
    policy_module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy_module)
    numerical_keys=policy_module.numerical_environment_keys(project)
    output.mkdir(parents=True)
    ledger.atomic(output/'plan.json',plan)
    verifier=tools/'tools/optimization/bench_full12.py'
    provenance=dict(complete=True,created=ledger.now(),selected_attempt=selected,campaign=str(campaign),
        source=str(project),source_manifest=str(path/'source-manifest.json'),
        source_manifest_sha256=data['snapshot']['source_manifest_sha256'],library=str(library),
        library_sha256=report['library_sha256'],configuration=cfg,prior_steady_samples=performance,
        fixture=str(args.fixture.resolve()),gauge=str(args.gauge.resolve()),allocation=args.allocation,
        reference=str(reference),reference_sha256=sha(reference),extractor=str(extractor),extractor_sha256=extractor_sha,
        reference_propagator=str(baseline),reference_propagator_sha256=baseline_sha,
        cold_wrapper=str(cold),cold_wrapper_sha256=sha(cold),verification_driver=str(verifier),verification_driver_sha256=sha(verifier),
        numerical_environment_policy=dict(known_keys=sorted(numerical_keys),explicit_context_values=context,
            unrequested_policy='clear before startup, then restore only recorded context; source defaults otherwise',
            preserved_resources=['LQCD_NUMA_NODE','LQCD_OPT_*','launcher placement']),
        note='No computation performed by preparation. Cold scopes are separate and never imported as steady full12_api scores.')
    ledger.atomic(output/'selection.json',provenance)
    remove=sorted(numerical_keys|set(solve_keys(project))|{'LD_PRELOAD','PERF_COUNTER_ROOT','LD_DEBUG','LD_DEBUG_OUTPUT',
        'OMP_WAIT_POLICY','GOMP_SPINCOUNT','NATIVE_SAP_STEPS','NATIVE_SAP_CYCLES','NATIVE_COARSE_IT','NATIVE_OUTER_FLOAT'})
    env=['env']
    for key in remove:
        env+=['-u',key]
    env += [str(key)+'='+str(value) for key,value in sorted(context.items())]
    env += ['LQCD_VERBOSE=0','LQCD_HALO_PROFILE=0','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1']
    launcher=[args.python,str(project/'tools/run_numa.py')]
    if args.backend=='x86':
        launcher+=['--ranks-per-numa','2']
    launcher+=['--threads',str(placement),'--',args.python,'-u']
    common=['--fixture',str(args.fixture.resolve()),'--plan',str(output/'plan.json'),
        '--library',str(library),'--backend',args.backend,'--allocation',args.allocation,
        '--snapshot-sha',data['snapshot']['source_manifest_sha256'],'--reference-propagator',str(baseline)]
    steady=env+launcher+[str(project/'tools/optimization/bench_full12.py')]+common+[
        '--output',str(output/'steady'),'--repeats',str(args.steady_repeats)]
    # Verification executes without the candidate libgomp preload or profiler.
    verify_env=['env','-u','LD_PRELOAD','-u','PERF_COUNTER_ROOT','-u','LD_DEBUG',
        'OMP_NUM_THREADS=4','OMP_PLACES=cores','OMP_PROC_BIND=close','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1']
    for key in ('LD_LIBRARY_PATH',):
        if key in context:
            verify_env.append(key+'='+str(context[key]))
    def verification(run):
        return verify_env+[args.python,str(verifier),'--verify',str(run),'--reference',str(reference),'--extractor',str(extractor)]
    def canonical_report_guard(run):
        code="import json,sys; d=json.load(open(sys.argv[1])); assert d['comparison_key']['prepared_gauge_manifest_sha256']=='126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834', 'Prepared field differs from canonical bytes'"
        return shell([args.python,'-c',code,str(run/'result.json')])
    write_script(output/'run-steady.sh',[shell(steady),canonical_report_guard(output/'steady/full12'),
                                        shell(verification(output/'steady/full12'))])
    cold_commands={}
    for mode,input_flag,input_path in [('fixture','--fixture',args.fixture),('lime','--gauge',args.gauge)]:
        run=output/('cold-'+mode)
        command=env+launcher+[str(cold),'--project',str(project),'--source-manifest',str(path/'source-manifest.json'),
            '--snapshot-sha',data['snapshot']['source_manifest_sha256'],'--library',str(library),
            '--expected-library-sha',report['library_sha256'],'--plan',str(output/'plan.json'),
            input_flag,str(input_path.resolve()),'--backend',args.backend,'--allocation',args.allocation,
            '--reference-propagator',str(baseline),'--output',str(run)]
        cold_commands[mode]=command
        write_script(output/f'run-cold-{mode}.sh',[shell(command),shell(verification(run))])
    # Existing runbook toolchains, with the source selected from the ledger.
    # Compilation remains on the compute node; generated scripts never modify
    # the measured binary or source. New build SHA is a new measured artifact.
    build=output/'build'
    cmake=['cmake','-S',str(project),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release',
        '-DMULTIGRID_NATIVE=ON','-DLQCD_BUILD_RUNTIME=ON','-DLQCD_DD_REFERENCE=OFF',
        '-DLQCD_TEST_PYTHON='+args.python,
        '-DCMAKE_C_COMPILER_LAUNCHER='+args.python+';'+str(project/'tools/pin_build.py'),
        '-DCMAKE_CXX_COMPILER_LAUNCHER='+args.python+';'+str(project/'tools/pin_build.py')]
    lines=['export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close',
        'unset LD_PRELOAD PERF_COUNTER_ROOT LD_DEBUG LD_DEBUG_OUTPUT']
    if args.backend=='arm':
        sdk='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001'
        gcc='/work_ssd/system/os_jasmine_v01/vroot/usr/bin'
        runtime=sdk+'/compiler/gcc/lib64'
        kupl=sdk+'/kupl/gcc/release'
        lines += ['source '+shlex.quote(sdk+'/setvars.sh')+' --use-bisheng --force',
            'export CC='+shlex.quote(gcc+'/gcc')+' CXX='+shlex.quote(gcc+'/g++'),
            'export OMPI_CC="$CC" OMPI_CXX="$CXX"',
            'export CPATH=/work_ssd/system/os_jasmine_v01/vroot/usr/include:/work_ssd/system/os_jasmine_v01/vroot/usr/local/include',
            'export LIBRARY_PATH='+shlex.quote(runtime)+':${LIBRARY_PATH:-}:/work_ssd/system/os_jasmine_v01/vroot/usr/lib64:/work_ssd/system/os_jasmine_v01/vroot/usr/lib',
            'export LD_LIBRARY_PATH='+shlex.quote(runtime+':'+kupl+'/lib')+':${LD_LIBRARY_PATH:-}',
            'export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp']
        cmake += ['-DCMAKE_C_COMPILER='+gcc+'/gcc','-DCMAKE_CXX_COMPILER='+gcc+'/g++',
            '-DLQCD_KUPL_HBW=ON','-DLQCD_KUPL_ROOT='+kupl,
            '-DCMAKE_EXE_LINKER_FLAGS=-L'+runtime+' -Wl,-rpath,'+runtime,
            '-DCMAKE_SHARED_LINKER_FLAGS=-L'+runtime+' -Wl,-rpath,'+runtime]
        probe_check="import json,sys; d=json.load(open(sys.argv[1])); assert d['machine']=='aarch64' and d.get('sve_vector_bytes')==64"
    else:
        gcc='/public2/home/lwb_720/miniconda3/bin'
        lines += ['export CC='+shlex.quote(gcc+'/gcc')+' CXX='+shlex.quote(gcc+'/g++')]
        cmake += ['-DCMAKE_C_COMPILER='+gcc+'/gcc','-DCMAKE_CXX_COMPILER='+gcc+'/g++','-DLQCD_KUPL_HBW=OFF']
        probe_check="import json,sys; d=json.load(open(sys.argv[1])); assert d['machine']=='x86_64'"
    lines += ['export PATH='+shlex.quote(str(Path(args.python).parent))+':$PATH']
    bootstrap=list(lines)
    lines += [shell([args.python,str(project/'tools/probe_host.py')])+' > '+shlex.quote(str(output/'build-host.json')),
        shell([args.python,'-c',probe_check,str(output/'build-host.json')]),
        shell(cmake)+' -DMPI_C_COMPILER="$(command -v mpicc)" -DMPI_CXX_COMPILER="$(command -v mpicxx)" '+
            shlex.quote('-DLQCD_MPI_FLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'),
        shell(['cmake','--build',str(build),'-j16']),
        shell(['env','OMP_NUM_THREADS=2','OMP_PLACES=cores','ctest','--test-dir',str(build),'--output-on-failure']),
        shell(['sha256sum',str(build/'liblqcd_cpu.so')])]
    write_script(output/'build-source.sh',lines)
    # Build and run are separate shell processes. Give every recipe the same
    # self-contained site bootstrap; a previous build shell cannot export into
    # its caller. Context env assignments are then applied before Python starts.
    write_script(output/'site-environment.sh',bootstrap)
    rebuilt_library=build/'liblqcd_cpu.so'
    rebuilt_cold=list(cold_commands['fixture'])
    rebuilt_cold[rebuilt_cold.index('--library')+1]=str(rebuilt_library)
    rebuilt_cold[rebuilt_cold.index('--expected-library-sha')+1]='__REBUILT_SHA__'
    rebuilt_cold[rebuilt_cold.index('--output')+1]=str(output/'cold-rebuilt-fixture')
    rebuilt_sha_command=shell([args.python,'-c',
        "import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],'rb'); [h.update(x) for x in iter(lambda:f.read(8*1024**2),b'')]; print(h.hexdigest())",str(rebuilt_library)])
    rebuilt_command=' '.join('"$rebuilt_sha"' if value=='__REBUILT_SHA__' else shlex.quote(str(value)) for value in rebuilt_cold)
    write_script(output/'run-rebuilt-cold-fixture.sh',['test -f '+shlex.quote(str(rebuilt_library)),
        'rebuilt_sha=$('+rebuilt_sha_command+')',rebuilt_command,
        shell(verification(output/'cold-rebuilt-fixture'))])
    for name in ('run-steady.sh','run-cold-fixture.sh','run-cold-lime.sh','run-rebuilt-cold-fixture.sh'):
        recipe=output/name
        text=recipe.read_text(encoding='utf-8')
        recipe.write_text(text.replace('set -eo pipefail\n','set -eo pipefail\nsource '+
            shlex.quote(str(output/'site-environment.sh'))+'\n',1),encoding='utf-8')
    (output/'README.md').write_text('Selected '+selected+'; frozen exact-binary replay scripts and independent verification.\n\n'
        'Run build-source.sh only on the actual target compute node in its MPI/Python environment. '
        'It creates a separate build and tests it. Ordinary run scripts use the measured frozen library; '
        'run-rebuilt-cold-fixture.sh explicitly tests the newly built library with its actual SHA and full12 independent checks. '
        'A rebuilt library needs a fresh framework attempt, recorded source/build flags/SHA and matched performance evidence before adoption.\n\n'
        'run-steady.sh performs one warmup and >=3 complete12 steady solves. run-cold-fixture.sh performs one fresh-hierarchy canonical-field read/load/setup/first12. '
        'run-cold-lime.sh also parses/hashes original LIME and computes stout; canonical hash mismatch is a preserved failure, never a silent field replacement. '
        'Cold outputs are separate scopes; no OS page-cache cold claim. Output writing and all independent scalar/solution checks follow the cold timer. '
        'Each script needs a new output location; regenerate recipes into a new directory for every repeat.\n',encoding='utf-8')
    print(json.dumps(dict(selection=str(output/'selection.json'),selected_attempt=selected,source=str(project),
        frozen_library=str(library),scripts=['build-source.sh','run-steady.sh','run-cold-fixture.sh','run-cold-lime.sh','run-rebuilt-cold-fixture.sh'],
        computation_executed=False),ensure_ascii=False))


if __name__=='__main__':
    main()
