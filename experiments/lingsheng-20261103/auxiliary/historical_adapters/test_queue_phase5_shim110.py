"""No remote execution: predecessor, complete-group budget and drift contracts."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('queue_phase5_shim110',Path(__file__).with_name('queue_phase5_shim110.py'))
queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)


class Contracts(unittest.TestCase):
    def fixture(self):
        return (dict(status='passed',returncode=0,cleanup=dict(complete=True)),
            dict(complete=True,status='complete',best='best',allocation='mg-opt-20261103-worker6',host='cn19483'),
            dict(attempt='best'),dict(complete=True,allocation='mg-opt-20261103-worker6',host='cn19483',safe_deadline_epoch=9000))

    def test_cannot_start_until100_passed_cleaned_complete_and_matching_best(self):
        self.assertTrue(queue.dependency_gate(*self.fixture(),now=1000)['passed'])
        for index,key,value in [(0,'status','running'),(0,'returncode',1),(0,'cleanup',dict(complete=False)),
                                (1,'complete',False),(1,'best','different'),(1,'allocation','old'),(3,'complete',False)]:
            values=list(self.fixture());values[index][key]=value
            self.assertFalse(queue.dependency_gate(*values,now=1000)['passed'])

    def test_full_eight_trials_and_cleanup_reserve_required_before_starting(self):
        values=list(self.fixture());values[3]['safe_deadline_epoch']=4790
        self.assertTrue(queue.dependency_gate(*values,now=0)['passed'])
        values[3]['safe_deadline_epoch']=4789
        result=queue.dependency_gate(*values,now=0)
        self.assertFalse(result['passed']);self.assertEqual(result['status'],'pending')
        self.assertEqual(result['task_budget_seconds'],4700)
        self.assertEqual(queue.dependency_gate(*self.fixture(),now=1000)['task_timeout_seconds'],6500)
        values[3]['safe_deadline_epoch']=5200
        self.assertEqual(queue.dependency_gate(*values,now=0)['task_timeout_seconds'],5110)
        for bad in (float('nan'),float('inf'),'tomorrow'):
            values[3]['safe_deadline_epoch']=bad
            self.assertFalse(queue.dependency_gate(*values,now=0)['passed'])


if __name__=='__main__':unittest.main()
