from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_submit_worker8_once as original
import submit_worker8_terminal_v2 as submit


class PreviousContracts(original.Contracts):
    def setUp(self):
        self.binding = patch.object(original, 'submit', submit)
        self.binding.start()
        self.addCleanup(self.binding.stop)


class NaturalExit(unittest.TestCase):
    def test_real_log_success_accepts_without_fabricating_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root/'worker7.log'
            log.write_text('prior tasks\nBounded worker finished; no active task\n')
            proof = dict(exit_kind='natural-idle', scheduler_end_time='actual-time',
                         worker_log_sha256=submit.sha(log))
            job = dict(state='SUCCEEDED', exitCode=0, jobExitCode=0, endTime='actual-time')
            submit.validate_exit(root, proof, job)
            self.assertFalse((root/'queue7/STOP').exists())
            for key, bad in [('state','RUNNING'), ('exitCode',1), ('jobExitCode',1), ('endTime','other')]:
                with self.subTest(key=key), self.assertRaises(RuntimeError):
                    submit.validate_exit(root, proof, dict(job, **{key:bad}))
            log.write_text('Bounded worker finished; no active task\nnew task\n')
            proof['worker_log_sha256'] = submit.sha(log)
            with self.assertRaisesRegex(RuntimeError, 'terminal idle marker'):
                submit.validate_exit(root, proof, job)

    def test_changed_log_and_missing_stop_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root/'worker7.log'
            log.write_text('Bounded worker finished; no active task\n')
            proof = dict(exit_kind='natural-idle', scheduler_end_time='actual-time',
                         worker_log_sha256=submit.sha(log))
            job = dict(state='SUCCEEDED', exitCode=0, jobExitCode=0, endTime='actual-time')
            log.write_text('different\n')
            with self.assertRaises(RuntimeError):submit.validate_exit(root, proof, job)
            with self.assertRaisesRegex(RuntimeError, 'graceful worker7'):
                submit.validate_exit(root, {}, job)


if __name__ == '__main__':
    unittest.main(verbosity=2)
