import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).parent))
import raw_controller_v4 as adapter


class DispatchContract(unittest.TestCase):
    def setUp(self):
        self.options=SimpleNamespace(wrapper=Path('/aux/raw_benchmark.py'),benchmark_sha='b'*64,
            wrapper_sha='w'*64,reader_sha='r'*64,gold_sha='g'*64,framework_tools=Path('/repo/tools/optimization'),
            audit_root=Path('/aux/audits'),adapter_sha='a'*64,helper_sha='h'*64,helper_wrapper=Path('/aux/raw_scalar_helper.py'),helper_wrapper_sha='s'*64)

    def test_numa_benchmark_preserves_placement_command_and_environment(self):
        command=dict(argv=['python','/source/tools/run_numa.py','--threads','37','--','python','-u',
            '/frozen/tools/optimization/bench_full12.py','--output','/attempt/measurements','--diagnostic'],
            env={'OMP_NUM_THREADS':'37'},cwd='/attempt/build',timeout_seconds=600)
        result=adapter.transform_stage(self.options,'/campaign','090-worker6','benchmark',command)
        self.assertEqual(result['argv'][:7],command['argv'][:7])
        self.assertIn(str(Path('/aux/raw_benchmark.py')),result['argv']);self.assertIn('--diagnostic',result['argv'])
        self.assertEqual(result['env'],command['env']);self.assertEqual(result['cwd'],command['cwd'])
        self.assertEqual(result['timeout_seconds'],600)
        self.assertNotIn('--verification-output',result['argv'])
        self.assertEqual(command['argv'][7],'/frozen/tools/optimization/bench_full12.py')

    def test_verification_uses_new_raw_protocol_explicit_gold_and_default_name(self):
        result=adapter.transform_stage(self.options,'/campaign','090-worker6','independent',
            dict(argv=['python','/frozen/tools/optimization/bench_full12.py','--verify','/measurements/full12']))
        argv=result['argv'];self.assertEqual(argv[argv.index('--expected-gold-sha')+1],'g'*64)
        self.assertEqual(argv[argv.index('--verification-output')+1],'independent')
        self.assertEqual(argv[argv.index('--audit-output')+1],str(Path('/campaign/attempts/090-worker6/checksum-audit/independent')))

    def test_non_benchmark_build_and_tests_are_unchanged(self):
        command=dict(argv=['ctest','--parallel','1'],env={},timeout_seconds=300)
        self.assertEqual(adapter.transform_stage(self.options,'/c','id','ctest',command),command)

    def test_child_trial_keeps_python_flags_and_arguments(self):
        command=['python','-u','/frozen/tools/optimization/trial.py','--id','090-worker6','--diagnostic']
        with mock.patch.object(adapter.integrity,'read_dual',return_value={'openssl_sha256':'e'*64}):
            result=adapter.child_trial_command(self.options,command)
        self.assertEqual(result[:2],command[:2]);self.assertIn('--entry',result)
        self.assertEqual(result[-3:],['--id','090-worker6','--diagnostic'])
        self.assertIn('--adapter-sha',result)


if __name__=='__main__':unittest.main()
