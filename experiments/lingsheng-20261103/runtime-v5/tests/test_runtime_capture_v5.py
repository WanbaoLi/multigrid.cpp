from pathlib import Path
import unittest

import phase5_setup_capture_v5 as controller
import runtime_benchmark_capture_v5 as capture
import prepare_phase5_setup_capture_v5 as prepare


class Contracts(unittest.TestCase):
    def test_scientific_trials_and_decision_methods_still_inherit_unchanged(self):
        for name in ('trial','decide','run','run_group','runtime_loader_preflight','freeze_group','check_best'):
            self.assertIs(getattr(controller.Phase5,name),getattr(controller.parent.Phase5,name))
        self.assertEqual(prepare.BUDGET,4700)
        self.assertEqual(len(prepare.case_ids('case',32)),8)
        self.assertEqual(controller.MPI_PREFIX,capture.MPI_PREFIX)

    def test_only_one_expected_ld_expression_changed(self):
        self.assertEqual(controller.AUDIT_PROOF['changed_expressions'],1)
        self.assertFalse(controller.AUDIT_PROOF['actual_sidecars_modified'])
        self.assertNotEqual(controller.AUDIT_PROOF['original_ast_sha256'],controller.AUDIT_PROOF['transformed_ast_sha256'])
        changed,proof=controller.patched_runtime_audit(controller.base.Phase5.runtime_audit)
        self.assertEqual(proof,controller.AUDIT_PROOF)

    def test_exact_prefix_and_wait_controls_remain_enforced(self):
        policy=capture.policy
        requested='original-sdk-path:other:'
        actual=controller.effective_search_path(requested)
        for context in ({},{'OMP_WAIT_POLICY':'PASSIVE','GOMP_SPINCOUNT':0}):
            expected=dict(context,LD_LIBRARY_PATH=actual)
            lines=[(key+'='+str(value)).encode()for key,value in expected.items()]
            row=policy.runtime_environment_snapshot(lines,expected,actual)
            self.assertEqual(row['LD_LIBRARY_PATH'],actual)
            with self.assertRaises(ValueError):
                policy.runtime_environment_snapshot([*lines,b'LD_PRELOAD=/unrequested.so'],expected,actual)
            with self.assertRaises(ValueError):
                policy.runtime_environment_snapshot([v for v in lines if not v.startswith(b'LD_LIBRARY_PATH=')]+[b'LD_LIBRARY_PATH=unrequested'],expected,actual)
        with self.assertRaises(RuntimeError):controller.effective_search_path('')


if __name__=='__main__':unittest.main(verbosity=2)
