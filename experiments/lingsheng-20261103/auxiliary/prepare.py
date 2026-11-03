"""Site experiment seed; records all runnable command arguments and hypotheses."""
import json
from pathlib import Path
import sys
root = Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
source = root/'source'
sys.path.insert(0,str(source/'tools/optimization'))
import campaign
campaign_root = root/'campaign'
if not campaign_root.exists():
    campaign.initialize(campaign_root,source,source/'skills/kunpeng-lqcd-reference',
        '47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30',
        '1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c',
        baseline_commit='a8803fd')
baseline=json.loads((source/'tools/optimization/plans/baseline.json').read_text())
specs=[
 ('000-baseline',0,0,'Create a repeatable current default full12 baseline',
  'Historical normal full12 about22.6s; earlier103s and nodevariation are not reliable ranking controls'),
 ('001-fused',1,0,'Reuse coarse Schur buffers and fuse inverse/extended-vector construction',
  'Coarse~0.6s per column; repeated small teams and temporary allocations consume time'),
 ('002-sve',0,1,'Use existing SVE coarse column packing without Schur fusion',
  'Output-row SVE removes horizontal reductions in repeated48x48 complexmatvec'),
 ('003-fused-sve',1,1,'Combine existing coarse SIMD layout with Schur workspace fusion',
  'Arithmetic throughput and fewer intermediate traversals can address different portions of coarse cost'),
 ('004-baseline-bracket',0,0,'Repeat unchanged baseline at end of factorial block',
  'Bracketing reveals node drift/cache/resource changes before choosing a winning configuration'),
]
for name,fused,sve,change,mechanism in specs:
    plan=json.loads(json.dumps(baseline))
    plan['context_environment'].update(LQCD_COARSE_FUSED=fused,LQCD_ARM_COARSE_SVE=sve)
    (root/'plans'/f'{name}.json').write_text(json.dumps(plan,indent=2)+'\n')
    proposal=dict(bottleneck='Coarse stage0.60–0.65s/column and SAP0.94s under16MPIx37; batch-stage profile newly observable',
        hypothesis=mechanism,change=change,mechanism=mechanism,
        history_links=['docs/kunpeng-hpc-optimization.md','docs/kupl-hbw-optimization.md',
                       'docs/optimization-candidates.md','outputs/performance-20261103/summary.json'],
        retry_conditions='This is16MPI/592core full12 with separated ordinary/profile runs; Oct26 combined8MPI results did not isolate these two switches')
    (root/'proposals'/f'{name}.json').write_text(json.dumps(proposal,indent=2)+'\n')
    argv=[sys.executable,str(source/'tools/optimization/trial.py'),'--campaign',str(campaign_root),
          '--id',name,'--proposal',str(root/'proposals'/f'{name}.json'),
          '--plan',str(root/'plans'/f'{name}.json'),'--fixture','/home/share/nsls_lwb/.cache/mg-20261102/propagator',
          '--reference','/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid',
          '--extractor','/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/extract_columns',
          '--backend','arm','--allocation','mg-opt-20261103-worker1']
    if name=='000-baseline':argv+=['--baseline']
    else:argv+=['--reuse-attempt','000-baseline']
    task=dict(argv=argv,cwd=str(source),timeout=3600,
        environment=dict(LD_LIBRARY_PATH='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64:'+
        '/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release/lib:'+__import__('os').environ.get('LD_LIBRARY_PATH',''),
        LIBRARY_PATH='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64:'+__import__('os').environ.get('LIBRARY_PATH',''),
        LQCD_EXPERIMENT_KUPL_ROOT='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release'))
    # create files atomically so a running worker cannot claim an unfinished task
    path=root/'queue'/f'{name}.ready.json'
    if not any((root/'queue').glob(name+'.*')):
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(task,indent=2)+'\n');tmp.replace(path)
print(campaign_root)
