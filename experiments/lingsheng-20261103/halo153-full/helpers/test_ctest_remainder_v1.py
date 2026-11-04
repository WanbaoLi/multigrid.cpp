import unittest
import ctest_remainder_v1 as proof


class Coverage(unittest.TestCase):
    def test_only_completed_prefix_can_be_reused(self):
        text = ' 1/3 Test #30: first .... Passed 61.64 sec\n 2/3 Test #31: second .... Passed 60.84 sec\n Start 32: third\n'
        self.assertEqual(proof.passed_prefix(text, ['first', 'second', 'third']), ['first', 'second'])
        for changed in [text.replace('Passed 60.84', 'Failed 60.84'), text.replace('2/3', '1/3'),
                        text.replace('second', 'first'), text.replace('2/3', '2/4')]:
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                proof.passed_prefix(changed, ['first', 'second', 'third'])

    def test_remainder_needs_all_exact_cases_and_terminal_pass(self):
        text = ' 1/2 Test #42: last .... Passed 105.2 sec\n 2/2 Test #51: tuning .... Passed 12.3 sec\n100% tests passed, 0 tests failed out of 2\n'
        self.assertEqual(proof.completed_remainder(text, ['last', 'tuning']), ['last', 'tuning'])
        for changed in [text.replace('tuning', 'last'), text.replace('Passed 12.3', 'Timeout 12.3'),
                        text.replace('out of 2', 'out of 3'), text.split('100%')[0]]:
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                proof.completed_remainder(changed, ['last', 'tuning'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
