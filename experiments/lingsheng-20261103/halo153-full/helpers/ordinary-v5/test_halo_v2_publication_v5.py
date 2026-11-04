import ast
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
import halo_v2_trial_publication_v5 as trial
import test_halo_v2_publication_v4 as previous
previous.trial=trial
previous.prior.trial=trial
previous.prior.previous.trial=trial
H='1'*64
class Recovery(unittest.TestCase):
    def test_scientific_trial_class_unchanged(self):
        def tree(name):
            t=ast.parse(Path(__file__).with_name(name).read_text());c=next(x for x in t.body if isinstance(x,ast.ClassDef)and x.name=='Trial')
            for x in ast.walk(c):
                if isinstance(x,ast.Constant)and x.value=='halo-v2-trial-publication-v5-helpers.json':x.value='halo-v2-trial-publication-v4-helpers.json'
            return ast.dump(c)
        self.assertEqual(tree('halo_v2_trial_publication_v4.py'),tree('halo_v2_trial_publication_v5.py'))
    def fixture(self):
        names=['case'+str(i)for i in range(13)];old=names[:11];remaining=names[11:]
        prior=dict(status='timeout',timeout_seconds=1000,cleanup=dict(complete=True,surviving_pids=[]))
        code=Path(__file__).with_name('ctest_remainder_v1.py').read_text();digest=hashlib.sha256(code.encode()).hexdigest()
        plan=dict(id='153-halo-v2-remainder-worker10',scope='full-with-ctest-remainder-v1',numerical_tests_or_limits_changed=False,
            prior_stage=prior,prior_log='/old.log',prior_log_sha256=H,catalog_path='/catalog.json',catalog_sha256=H,
            all_tests=names,completed_tests=old,remaining_tests=remaining,pinned_files=[dict(path='/root/ctest_remainder_v1.py',sha256=digest)])
        recovery=dict(plan,complete=True,plan_path='/plan.json',plan_sha256=H,remainder_log='/new.log',remainder_log_sha256=H,
            full_test_coverage=names,executed_remaining_tests=remaining)
        oldtext=''.join(str(i+1)+'/13 Test #'+str(i)+': '+n+' .... Passed 1.00 sec\n'for i,n in enumerate(old))
        newtext=''.join(str(i+1)+'/2 Test #'+str(i)+': '+n+' .... Passed 1.00 sec\n'for i,n in enumerate(remaining))+'100% tests passed, 0 tests failed out of 2\n'
        docs={'/plan.json':plan,'/catalog.json':dict(tests=[dict(name=n)for n in names])}
        texts={'/old.log':oldtext,'/new.log':newtext,'/aux/ctest_remainder_v1.py':code}
        attempt=dict(stages={'mpi-numerical-ctest':deepcopy(prior),'mpi-numerical-ctest-remainder-v1':dict(status='passed',returncode=0,cleanup=dict(complete=True),log_sha256=H)})
        strict=SimpleNamespace(read=lambda path,*args:deepcopy(docs[str(path)]),text=lambda path,*args:texts[str(path)],sha=lambda path,*args:digest if Path(path).name=='ctest_remainder_v1.py'else H)
        return dict(ctest_recovery=recovery),attempt,strict,texts,docs
    def test_all13_cases_need_pinned_prefix_and_completed_remainder(self):
        state,attempt,strict,_,_=self.fixture();pins=trial.validate_recovery(state,attempt,strict,Path('/aux'))
        self.assertIn('/old.log',pins)if '/old.log'in pins else self.assertIn('/plan.json',pins)
        self.assertIn('/new.log',pins)
    def test_incomplete_changed_duplicate_or_failed_evidence_is_rejected(self):
        for mode in ['incomplete','changedcoverage','oldfailed','oldchanged','newfailed','wronghash','duplicate','missingterminal']:
            state,attempt,strict,texts,docs=self.fixture();r=state['ctest_recovery']
            if mode=='incomplete':r['complete']=False
            elif mode=='changedcoverage':r['full_test_coverage']=r['full_test_coverage'][:-1]
            elif mode=='oldfailed':attempt['stages']['mpi-numerical-ctest']['status']='failed'
            elif mode=='oldchanged':r['prior_log']='other'
            elif mode=='newfailed':attempt['stages']['mpi-numerical-ctest-remainder-v1']['returncode']=1
            elif mode=='wronghash':attempt['stages']['mpi-numerical-ctest-remainder-v1']['log_sha256']='2'*64
            elif mode=='duplicate':texts['/new.log']=texts['/new.log'].replace('case12','case11')
            else:texts['/new.log']=texts['/new.log'].split('100%')[0]
            with self.subTest(mode=mode),self.assertRaises(RuntimeError):trial.validate_recovery(state,attempt,strict,Path('/aux'))
if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in [Recovery,previous.Envelope,previous.prior.Structure,previous.prior.DirectRouting,previous.prior.Cases,
        previous.prior.RealTwoCasePublication,previous.prior.previous.ExternalProof,previous.prior.previous.BudgetsAndGates,
        previous.prior.previous.ActualClosedEvidence,previous.prior.previous.StrictRead]:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
