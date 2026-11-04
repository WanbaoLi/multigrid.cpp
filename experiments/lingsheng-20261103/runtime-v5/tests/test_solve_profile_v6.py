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

import profile_benchmark_publication_v6 as wrapper
import raw_controller_solve_profile_v6 as adapter


class Contracts(unittest.TestCase):
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
            summary=json.loads((output/'wrapper-v6-summary.json').read_text())
            self.assertTrue(summary['unranked']);self.assertTrue(summary['actual_profiled_stats_checked'])


if __name__=='__main__':unittest.main(verbosity=2)
