"""Only add exact original-task resolution for a completed guarded148 task."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import halo_v2_trial_publication_v4 as trial
import test_halo_v2_publication_v3 as prior
prior.trial=trial
prior.previous.trial=trial
H='1'*64
class Envelope(unittest.TestCase):
    def test_all_existing_trial_methods_unchanged(self):
        def methods(name):
            t=ast.parse(Path(__file__).with_name(name).read_text())
            c=next(x for x in t.body if isinstance(x,ast.ClassDef)and x.name=='Trial')
            for x in ast.walk(c):
                if isinstance(x,ast.Constant)and x.value=='halo-v2-trial-publication-v4-helpers.json':
                    x.value='halo-v2-trial-publication-v3-helpers.json'
            return ast.dump(c)
        self.assertEqual(methods('halo_v2_trial_publication_v3.py'),methods('halo_v2_trial_publication_v4.py'))
    def fixture(self):
        root=Path('/root');guard=root/'worker10_live_task_guard_v2.py';planpath=root/'envelope/guard-plan.json'
        taskpath=root/'prepared-halo148-worker10/task.json';entry='/root/aux/arm_halo_v2_qualify.py'
        argv=['/python','-u',str(guard),'--plan',str(planpath),'--plan-sha',H]
        original=['/python','-u',entry,'--scope','full']
        plan=dict(id='148-halo-v2-full-worker10',numerical_or_acceptance_gate_changes=False,
            original_task=dict(path=str(taskpath),sha256=H),guard_sha256=H,original_entry_sha256=H)
        task=dict(argv=original,timeout=4500)
        receipt=dict(complete=True,task_tag='owned',host='cn19486',guard_plan_sha256=H,
            original_task_sha256=H,original_argv_and_scientific_scope_preserved=True,
            parallel_runtime_loaded=False,parent_cpus=list(range(592)))
        docs={str(planpath):plan,str(taskpath):task,str(root/'148-halo-v2-full-worker10-actual-parent-guard-v2.json'):receipt}
        status=dict(argv=argv,task_tag='owned',host='cn19486')
        return SimpleNamespace(root=root),status,docs,original
    def run_fixture(self,args,status,docs,original):
        strict=SimpleNamespace(read=lambda path,*x:deepcopy(docs[str(path)]),sha=lambda *x:H)
        return trial.external_test_argv(args,strict,status)
    def test_closed_matching_original_task_is_resolved(self):
        value=self.fixture();argv,pins=self.run_fixture(*value)
        self.assertEqual(argv,value[3]);self.assertEqual(len(pins),5)
    def test_other_task_or_receipt_not_accepted(self):
        for key,value in [('task_tag','wrong'),('host','other'),('guard_plan_sha256','2'*64),
            ('original_task_sha256','2'*64),('original_argv_and_scientific_scope_preserved',False),
            ('parallel_runtime_loaded',True),('parent_cpus',[1]),('complete',False)]:
            args,status,docs,original=self.fixture()
            docs[str(args.root/'148-halo-v2-full-worker10-actual-parent-guard-v2.json')][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):self.run_fixture(args,status,docs,original)
    def test_original_direct_task_remains_supported(self):
        argv=['/python','-u','/aux/arm_halo_v2_qualify.py','--scope','full']
        self.assertEqual(trial.external_test_argv(None,None,dict(argv=argv)),(argv,{}))
if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in [Envelope,prior.Structure,prior.DirectRouting,prior.Cases,prior.RealTwoCasePublication,
        prior.previous.ExternalProof,prior.previous.BudgetsAndGates,prior.previous.ActualClosedEvidence,prior.previous.StrictRead]:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
