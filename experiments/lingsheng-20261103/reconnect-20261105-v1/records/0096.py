"""Check the prepared request and actual worker exec use the same NEW queue."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
import prepare_worker12 as prepare
import submit_worker12_terminal_v2 as submit
import worker12_entry as entry


class QueueBinding(unittest.TestCase):
    def fixture(self):
        root = Path(__file__).resolve().parent
        source = root/'multigrid.cpp'
        plan = prepare.plan(str(source), 'f'*40, str(root))
        plan['wrapper_sha256'] = {name:entry.sha(root/name) for name in entry.WRAPPERS}
        return root, source, plan

    def test_preparation_authentication_and_exec_bind_queue12(self):
        root, source, plan = self.fixture()
        submit.validate_plan(root, plan, prepare)
        argv = entry.worker_argv(sys.executable, source, root, 12000)
        self.assertEqual(plan['queue'], 'queue12')
        self.assertEqual(argv[argv.index('--queue')+1], str(root/plan['queue']))
        self.assertEqual(argv[argv.index('--lifetime')+1], '12000')
        self.assertNotIn(str(root/'queue11'), argv)

    def test_old_queue_cannot_be_authenticated_as_future_worker(self):
        root, _, plan = self.fixture()
        old = deepcopy(plan)
        old['queue'] = 'queue11'
        with self.assertRaises(RuntimeError):
            submit.validate_plan(root, old, prepare)


if __name__ == '__main__':
    unittest.main(verbosity=2)
