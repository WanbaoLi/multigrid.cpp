from copy import deepcopy
import unittest
import clover_full12_worker13_v1 as trial

class Contracts(unittest.TestCase):
    def test_context_cached_flag_is_never_a_dynamic_solve_case(self):
        base=dict(context_environment={'LQCD_ARM_SVE':1},solve_environment={'LQCD_COARSE_BATCH_REDUCE':1})
        before=deepcopy(base)
        for value in(0,1):
            plan=trial.case_plan(base,value)
            self.assertEqual(plan['context_environment']['LQCD_ARM_SVE_CLOVER_REUSE'],value)
            self.assertNotIn('LQCD_ARM_SVE_CLOVER_REUSE',plan['cases'][0]['environment'])
            self.assertEqual((plan['placement_threads'],plan['setup_threads'],plan['cases'][0]['threads'],plan['cases'][0]['batch']),(37,37,32,2))
            self.assertEqual(len(plan['cases']),1)
        self.assertEqual(base,before)
        self.assertNotIn('LQCD_ARM_SVE_CLOVER_REUSE',trial.case_plan(base,None)['context_environment'])

    def test_gate_retains_two_controls_noise_and_gain_threshold(self):
        def row(m,lo=None,hi=None,spread=0):return dict(median=m,minimum=lo or m,maximum=hi or m,spread=spread)
        limits=dict(minimum_gain=.03,maximum_relative_spread=.1)
        self.assertTrue(trial.gate(row(9.5),row(10),row(10.01),limits)['passed'])
        for candidate,a,b in[(row(9.8),row(10),row(10)),(row(9.5,hi=10),row(10),row(10)),
                (row(9.5),row(10),row(10.6)),(row(9.5,spread=.11),row(10),row(10))]:
            self.assertFalse(trial.gate(candidate,a,b,limits)['passed'])
        # The completed154-size gain remains insufficient.
        self.assertFalse(trial.gate(row(14.45743),row(14.70760),row(14.73636),limits)['passed'])

if __name__=='__main__':unittest.main(verbosity=2)
