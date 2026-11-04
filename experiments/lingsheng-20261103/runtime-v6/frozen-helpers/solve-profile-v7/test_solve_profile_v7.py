import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import profile_benchmark_publication_v7 as wrapper
import raw_controller_solve_profile_v7 as adapter
import prepare_solve_profile_v7 as prepare
import solve_profile_scope_v7 as scope


class Contracts(unittest.TestCase):
    def test_preparation_rejects_incomplete_old_epoch_failed_cleanup_and_changed_best(self):
        state=dict(complete=True,status='complete',expected_best='best',contract=dict(host='cn',allocation='new'))
        status=dict(status='passed',returncode=0,task_tag='owned',host='cn',cleanup=dict(complete=True,surviving_pids=[]))
        startup=dict(complete=True,host='cn',allocation='new',safe_deadline_epoch=5000)
        best=dict(attempt='best')
        self.assertTrue(prepare.readiness(state,status,startup,best,1000)['passed'])
        for changed in (dict(state,complete=False),dict(state,status='pending'),
                        dict(state,contract=dict(host='cn',allocation='old')),dict(state,expected_best='other')):
            self.assertFalse(prepare.readiness(changed,status,startup,best,1000)['passed'])
        for changed in (dict(status,returncode=False),dict(status,task_tag=''),
                        dict(status,cleanup=dict(complete=True,surviving_pids=[99]))):
            self.assertFalse(prepare.readiness(state,changed,startup,best,1000)['passed'])
        self.assertFalse(prepare.readiness(state,status,startup,best,1311)['passed'])

    def test_failed_phase_is_retained_but_clean_terminal_task_allows_unranked_best_profile(self):
        state=dict(complete=False,status='failed',expected_best='best',contract=dict(host='cn',allocation='new'))
        status=dict(status='failed',returncode=1,task_tag='owned',host='cn',cleanup=dict(complete=True,surviving_pids=[]))
        startup=dict(complete=True,host='cn',allocation='new',safe_deadline_epoch=5000)
        gate=prepare.readiness(state,status,startup,dict(attempt='best'),1000)
        self.assertTrue(gate['passed']);self.assertTrue(gate['prior_failure_not_reclassified'])
        self.assertEqual(state['status'],'failed');self.assertFalse(state['complete'])
        for changed in (dict(status,status='running'),dict(status,returncode=0),dict(status,returncode=True),
                        dict(status,cleanup=dict(complete=True,surviving_pids=[42]))):
            self.assertFalse(prepare.readiness(state,changed,startup,dict(attempt='best'),1000)['passed'])

    def test_dispatch_rechecks_full_parent_runtime_host_and_deadline(self):
        contract=dict(schema='solve-profile-scope-v7',complete=True,host='cn',allocation='new',
                      expected_parent_cpus=[1,2],startup_ld_library_path='SDK')
        args=[contract,'cn','new',1000,5000,[1,2],False,'SDK']
        scope.validate(*args)
        for index,value in [(1,'other'),(2,'old'),(4,4689),(5,[1]),(6,True),(7,'unrequested')]:
            changed=list(args);changed[index]=value
            with self.assertRaises(RuntimeError):scope.validate(*changed)

    def test_profiler_refuses_ordinary_timing_but_preserves_diagnostic_argv(self):
        original=dict(argv=['python','/aux/raw_benchmark_publication_v2.py','--benchmark','/bench_full12.py'])
        with self.assertRaisesRegex(RuntimeError,'never wrap ordinary'):
            adapter.extend_stage(original,'case',Path('/aux/profile.py'),'a'*64,Path('/profile'))
        command=dict(argv=[*original['argv'],'--diagnostic'])
        result=adapter.extend_stage(command,'case',Path('/aux/profile.py'),'a'*64,Path('/profile'))
        boundary=result['argv'].index('--')
        self.assertEqual(result['argv'][boundary+1:],command['argv'][2:])
        self.assertIn('/profile/case',result['argv'])

    def test_actual_profiled_stats_reject_partial_nan_and_nonconvergence(self):
        rows=[dict(converged=1,true_residual=4e-9)for _ in range(12)]
        value=(object(),rows)
        self.assertIs(wrapper.check_stats(value),rows)
        for bad in (rows[:11],[*rows[:11],dict(converged=0,true_residual=4e-9)],
                    [*rows[:11],dict(converged=1,true_residual=float('nan'))],
                    [*rows[:11],dict(converged=1,true_residual=1e-7)]):
            with self.assertRaises(RuntimeError):wrapper.check_stats((object(),bad))

    def test_real_outer_control_flow_routes_once_preserves_result_and_restores_hooks(self):
        # Synthetic module/solver/perf stand-ins; real files and strict readers.
        # No native solver, MPI launcher or perf process is invoked by this test.
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);benchmark=root/'project/tools/optimization/bench_full12.py'
            benchmark.parent.mkdir(parents=True);benchmark.write_text('# synthetic benchmark\n')
            plan=root/'plan.json';plan.write_text('{"cases":[{"id":"full12"}]}')
            output=root/'profile';remaining=['--benchmark',str(benchmark),'--plan',str(plan),'--diagnostic']
            value=(object(),[dict(converged=1,true_residual=4e-9)for _ in range(12)])
            class Solver:
                def solve_propagator(self,*args,**kwargs):return value
            original=Solver.solve_propagator;actual=[]
            def raw_main():
                actual.append(list(sys.argv[1:]));self.assertIs(Solver().solve_propagator(),value)
            def profile_main(args):
                output.mkdir()
                runpy.run_path(str(benchmark),run_name='__main__')
                return 0
            profile=SimpleNamespace(main=profile_main);raw=SimpleNamespace(main=raw_main)
            def load(path,name,expected):return profile if 'frozen_solve_profile'in name else raw
            def decode(argv,stdout,stderr,timeout):
                self.assertIn('--no-children',argv);self.assertIn('none',argv)
                self.assertIn('comm,pid,dso,symbol',argv);self.assertNotIn('comm,pid,tid,dso,symbol',argv)
                stdout.write(b'# synthetic nonempty leaf/thread report\n')
                return subprocess.CompletedProcess(argv,0)
            comm=SimpleNamespace(rank=0,size=16,allgather=lambda value:[value]*16)
            argv=['profile.py','--expected-self-sha',hashlib.sha256(Path(wrapper.__file__).read_bytes()).hexdigest(),
                  '--profile-output',str(output),'--',*remaining]
            execute=runpy.run_path
            with patch.object(wrapper,'BENCH_SHA',hashlib.sha256(benchmark.read_bytes()).hexdigest()), \
                 patch.object(wrapper,'load',side_effect=load),patch.object(sys,'argv',argv), \
                 patch.dict(sys.modules,{'mpi4py':SimpleNamespace(MPI=SimpleNamespace(COMM_WORLD=comm)),
                                        'lqcd_cpu':SimpleNamespace(Solver=Solver)}), \
                 patch.dict(os.environ,{'LQCD_VERBOSE':'1'}),patch.object(wrapper.shutil,'which',return_value='/synthetic/perf'), \
                 patch.object(wrapper.subprocess,'run',side_effect=decode):
                wrapper.main()
            self.assertEqual(actual,[remaining]);self.assertIs(runpy.run_path,execute)
            self.assertIs(Solver.solve_propagator,original)
            summary=json.loads((output/'wrapper-v7-summary.json').read_text())
            self.assertTrue(summary['unranked']);self.assertTrue(summary['actual_profiled_stats_checked'])


if __name__=='__main__':unittest.main(verbosity=2)
