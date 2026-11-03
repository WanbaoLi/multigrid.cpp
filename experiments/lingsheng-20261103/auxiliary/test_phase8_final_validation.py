"""Final protocol contracts only; no remote call, solver or task submission."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('phase8_final',Path(__file__).with_name('phase8_final_validation.py'))
phase=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(phase)


class FinalContracts(unittest.TestCase):
    def test_repeat_adapter_changes_only_benchmark_request_and_restores_api(self):
        calls=[]
        def original(root,name,key,command,*args,**kwargs):calls.append((key,command));return dict(status='passed')
        ledger=SimpleNamespace(run_stage=original)
        with tempfile.TemporaryDirectory() as value:
            trial=Path(value)/'trial.py'
            trial.write_text("import campaign\n"
                "campaign.run_stage('root','id','benchmark',{'argv':['python','/frozen/bench_full12.py'],'timeout_seconds':1800})\n"
                "campaign.run_stage('root','id','independent',{'argv':['python','verify.py'],'timeout_seconds':1200})\n")
            with mock.patch.dict(phase.sys.modules,{'campaign':ledger}):
                phase.run_trial_adapter(['--trial',str(trial),'--repeats','5','--campaign','example'])
        self.assertIs(ledger.run_stage,original)
        self.assertEqual(calls[0][1]['argv'][-2:],['--repeats','5'])
        self.assertEqual(calls[1][1]['argv'],['python','verify.py'])

    def test_repeated_commands_are_immutable_and_diagnostic_or_conflicting_counts_fail(self):
        request=dict(argv=['python','/frozen/bench_full12.py'],env={'LQCD_HBW_ALLOC':'off'},timeout_seconds=1800)
        repeated=phase.repeat_command(request,7)
        self.assertNotIn('--repeats',request['argv'])
        self.assertEqual(repeated['argv'][-2:],['--repeats','7'])
        self.assertEqual(repeated['env'],request['env'])
        with self.assertRaisesRegex(ValueError,'ordinary'):
            phase.repeat_command(dict(argv=['python','/frozen/bench_full12.py','--diagnostic']),5)
        with self.assertRaisesRegex(ValueError,'conflicts'):
            phase.repeat_command(dict(argv=['python','/frozen/bench_full12.py','--repeats','3']),5)

    def test_overall_gain_needs_both_fresh_controls_and_noise_range_drift_gates(self):
        limits=dict(minimum_gain=.03,maximum_relative_spread=.10)
        def row(median,low,high):return dict(median_seconds=median,minimum_seconds=low,maximum_seconds=high,
            relative_spread=(high-low)/median,steady_repeats=[1,2,3,4,5])
        best=row(15,14.9,15.1);first=row(26,25.9,26.1);last=row(26.5,26.4,26.6)
        accepted=phase.overall_gate(best,first,last,limits)
        self.assertTrue(accepted['passed'])
        self.assertIsNotNone(accepted['qualified_overall_gain'])
        for bad in [row(30,29.9,30.1),row(26.5,23,30)]:
            rejected=phase.overall_gate(best,first,bad,limits)
            self.assertFalse(rejected['passed'])
            self.assertIsNone(rejected['qualified_overall_gain'])
        overlap=phase.overall_gate(row(25,24.9,26),first,last,limits)
        self.assertFalse(overlap['passed'])
        self.assertIsNone(overlap['qualified_overall_gain'])

    def test_startup_poison_removed_but_worker_and_numa_resources_preserved(self):
        initial=dict(LQCD_MG_SETUP_PASSES='0',LQCD_SETUP_UPDATE='paper',LD_PRELOAD='diagnostic.so',
            OMP_WAIT_POLICY='PASSIVE',LQCD_OPT_TASK_ID='owned',LQCD_NUMA_NODE='7',LQCD_CPU_THREADS='37',OMP_PLACES='cores')
        result=phase.sanitized_environment(initial,{'LQCD_MG_SETUP_PASSES','LQCD_SETUP_UPDATE',
            'LQCD_CPU_THREADS','LQCD_NUMA_NODE','LQCD_OPT_TASK_ID'})
        self.assertNotIn('LQCD_MG_SETUP_PASSES',result)
        self.assertNotIn('LD_PRELOAD',result)
        self.assertNotIn('OMP_WAIT_POLICY',result)
        for key in ('LQCD_OPT_TASK_ID','LQCD_NUMA_NODE','LQCD_CPU_THREADS','OMP_PLACES'):
            self.assertEqual(result[key],initial[key])
        self.assertEqual(initial['LQCD_MG_SETUP_PASSES'],'0')


if __name__=='__main__':unittest.main()
