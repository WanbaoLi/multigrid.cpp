"""Fairness checks for solve/placement/setup metadata in paired experiments."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/optimization'))
spec=importlib.util.spec_from_file_location('paired_driver',ROOT/'tools/optimization/interleaved.py')
paired=importlib.util.module_from_spec(spec)
spec.loader.exec_module(paired)


class PairedConfigurationTest(unittest.TestCase):
    def test_reject_team_switches_before_any_ledger_mutation(self):
        for cases in [
            [dict(threads=32),dict(threads=37)],
            [dict(threads=32),dict(threads=32,environment={'LQCD_COARSE_THREADS':16})],
        ]:
            with self.subTest(cases=cases):
                with self.assertRaisesRegex(paired.ledger.EvidenceError,'independent processes'):
                    paired.require_comparable_teams(dict(cases=cases))

    def test_allow_same_effective_teams_with_different_algorithm_or_batch(self):
        plan=dict(setup_threads=37,context_environment={'LQCD_COARSE_THREADS':64},
            cases=[dict(threads=32,batch=2),dict(threads=32,batch=4,
                environment={'LQCD_COARSE_THREADS':32,'LQCD_MG_SAP_STEPS':5})])
        paired.require_comparable_teams(plan)
        self.assertEqual(paired.shared_process_thread_teams(plan),
                         [dict(fine_threads=32,coarse_threads=32)])

    def test_reduced_team_control_preserves_original_setup_and_placement(self):
        reference=dict(context_environment={'LQCD_HBW_ALLOC':'require'},solve_environment={},
            threads=32,batch=2,ranks=16,block=[6,6,6,4],seed=1024,
            placement_threads=37,setup_threads=37)
        cases=[dict(id='control',threads=32,batch=2,environment={}),
               dict(id='smaller',threads=16,batch=4,environment={'LQCD_COARSE_THREADS':8})]
        plan=dict(context_environment=reference['context_environment'],placement_threads=37,
                  setup_threads=37,cases=cases)
        self.assertEqual(paired.configuration(plan,cases[0],reference),reference)
        altered=paired.configuration(plan,cases[1],reference)
        self.assertEqual((altered['threads'],altered['batch'],altered['placement_threads'],
                          altered['setup_threads']),(16,4,37,37))
        self.assertEqual(reference['threads'],32)
        self.assertEqual(reference['solve_environment'],{})

    def test_implicit_identical_teams_do_not_invent_metadata_difference(self):
        reference=dict(context_environment={},solve_environment={},threads=37,batch=2,ranks=16)
        case=dict(id='control',threads=37,batch=2)
        self.assertEqual(paired.configuration(dict(cases=[case]),case,reference),reference)


if __name__=='__main__':unittest.main()
