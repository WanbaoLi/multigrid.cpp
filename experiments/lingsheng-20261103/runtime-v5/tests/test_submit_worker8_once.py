"""Real small-file receipts, mocked scheduler execution; never submit a job."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import submit_worker8_once as submit


class Contracts(unittest.TestCase):
    def test_success_writes_distinct_immutable_intent_and_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = Mock(return_value=subprocess.CompletedProcess(['dsub'], 0, 'actual-stdout', ''))
            result = submit.submit_once(root, ['dsub','reviewed'], {'test_only':True}, runner)
            runner.assert_called_once_with(['dsub','reviewed'], capture_output=True, text=True, timeout=45)
            self.assertTrue(result['submitted'])
            intent = submit.read(root/'worker8-submission-intent.json')
            final = submit.read(root/'worker8-submission-result.json')
            self.assertFalse(intent['submitted'])
            self.assertEqual(final, result)
            self.assertEqual(final['intent_sha256'], submit.sha(root/'worker8-submission-intent.json'))
            self.assertNotEqual(root/'worker8-submission-intent.json', root/'worker8-submission-result.json')
            with self.assertRaisesRegex(RuntimeError, 'never retry automatically'):
                submit.submit_once(root, ['dsub','reviewed'], {}, runner)
            self.assertEqual(runner.call_count, 1)

    def test_nonzero_exit_is_recorded_and_cannot_be_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = Mock(return_value=subprocess.CompletedProcess(['dsub'], 3, '', 'scheduler-error'))
            result = submit.submit_once(directory, ['dsub'], {}, runner)
            self.assertFalse(result['submitted'])
            self.assertEqual(result['returncode'], 3)
            with self.assertRaises(RuntimeError):submit.submit_once(directory, ['dsub'], {}, runner)
            self.assertEqual(runner.call_count, 1)

    def test_timeout_preserves_uncertainty_and_blocks_resubmission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = Mock(side_effect=subprocess.TimeoutExpired(['dsub'], 45))
            with self.assertRaises(subprocess.TimeoutExpired):submit.submit_once(root, ['dsub'], {}, runner)
            proof = submit.read(root/'worker8-submission-uncertain.json')
            self.assertTrue(proof['submission_result_uncertain'])
            self.assertFalse((root/'worker8-submission-result.json').exists())
            with self.assertRaises(RuntimeError):submit.submit_once(root, ['dsub'], {}, runner)
            self.assertEqual(runner.call_count, 1)

    def test_result_receipt_failure_after_success_still_blocks_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = Mock(return_value=subprocess.CompletedProcess(['dsub'], 0, 'submitted', ''))
            original = submit.integrity.write_json_private
            def write(path, value):
                if Path(path).name == 'worker8-submission-result.json':raise OSError('injected result publication failure')
                return original(path, value)
            with patch.object(submit.integrity,'write_json_private',side_effect=write):
                with self.assertRaisesRegex(OSError,'injected'):submit.submit_once(root, ['dsub'], {}, runner)
            self.assertTrue((root/'worker8-submission-intent.json').is_file())
            with self.assertRaises(RuntimeError):submit.submit_once(root, ['dsub'], {}, runner)
            self.assertEqual(runner.call_count, 1)

    def test_changed_payload_after_verified_digest_cannot_replace_expected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'metadata.json'
            path.write_text('{"value":1}\n')
            expected = submit.sha(path)
            actual = submit.sha
            def changed(target, fixed=None):
                digest = actual(target, fixed)
                path.write_text('{"value":2}\n')
                return digest
            with patch.object(submit,'sha',side_effect=changed):
                with self.assertRaises(Exception):submit.read(path, expected)
            self.assertEqual(json.loads(path.read_text()), {'value':2})

    def test_failed_identity_or_dangling_link_cannot_reuse_worker_namespace(self):
        for name in submit.WORKER_IDENTITIES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                submit.fresh_worker_namespace(root)
                path = root/name
                path.symlink_to(root/'absent-target')
                self.assertFalse(path.exists())
                with self.assertRaisesRegex(RuntimeError, 'Existing worker8 identity'):
                    submit.fresh_worker_namespace(root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
