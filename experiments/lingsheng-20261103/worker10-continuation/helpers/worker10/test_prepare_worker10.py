"""Pure preparation: explicit source identity and no implicit submission."""
import unittest
import prepare_worker10 as prepare


class Contracts(unittest.TestCase):
    def test_exact_source_args_bound_in_submit_and_login_writer(self):
        value=prepare.plan('/reviewed/source-f94','f'*40)
        expected=['--source','/reviewed/source-f94','--expected-source-head','f'*40]
        self.assertEqual(value['argv'][-4:],expected)
        self.assertEqual(value['login_record_writer_argv_after_submit'][-4:],expected)
        self.assertTrue(value['prepared_only_not_submitted']);self.assertFalse(value['authorized_submission'])
        self.assertEqual(value['wall_seconds'],14400);self.assertEqual(value['idle_timeout_seconds'],3600)
    def test_implicit_head_or_relative_source_rejected(self):
        for source,head in [('relative','f'*40),('/source','HEAD'),('/source/../other','f'*40)]:
            with self.assertRaises(ValueError):prepare.plan(source,head)


if __name__=='__main__':unittest.main()
