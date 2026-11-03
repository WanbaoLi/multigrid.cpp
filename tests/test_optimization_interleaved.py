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
