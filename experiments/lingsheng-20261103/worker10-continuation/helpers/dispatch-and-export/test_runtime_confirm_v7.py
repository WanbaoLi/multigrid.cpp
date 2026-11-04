from pathlib import Path
import unittest
import phase5_runtime_confirm_v7 as current
import runtime_confirm_scope_v7 as guard

class Contracts(unittest.TestCase):
    def test_all_numerical_trial_and_acceptance_methods_inherited(self):
        for name in ('trial','decide','registered','runtime_audit','runtime_loader_preflight','check_best','run_group'):
            self.assertIs(getattr(current.Phase5,name),getattr(current.parent.Phase5,name))
        self.assertEqual(current.initial.AUDIT_PROOF['changed_expressions'],1)
        self.assertFalse(current.initial.AUDIT_PROOF['actual_sidecars_modified'])
    def test_complete_three_case_budget_and_actual_parent_required(self):
        c=dict(schema='runtime-confirm-scope-v7',complete=True,host='cn',allocation='epoch',expected_parent_cpus=[1,2],startup_ld_library_path='SDK')
        good=[c,'cn','epoch',1000,4200,[1,2],False,'SDK'];guard.validate(*good)
        for index,value in ((1,'other'),(2,'old'),(4,4089),(5,[1]),(6,True),(7,'extra')):
            bad=list(good);bad[index]=value
            with self.assertRaises(RuntimeError):guard.validate(*bad)
if __name__=='__main__':unittest.main(verbosity=2)
