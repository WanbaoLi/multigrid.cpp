"""Pure argv contracts: no ledger, SSH, native library or numerical execution."""
from pathlib import Path
import unittest

import raw_protocol_derived as derived
import raw_protocol_v4 as legacy


class Contracts(unittest.TestCase):
    def args(self):return (Path('/root'),Path('/root/controller.py'),'a'*64,'new-stage','/python')

    def test_legacy_option_preserves_byte_for_byte_old_passed_command_identity(self):
        self.assertEqual(derived.prefix(*self.args(),legacy_helper=True,verify=False),legacy.prefix(*self.args(),verify=False))

    def test_new_controller_prefix_changes_only_explicit_helper_path_and_sha(self):
        before=legacy.prefix(*self.args(),verify=False);after=derived.prefix(*self.args(),verify=False)
        indices={before.index('--helper-wrapper')+1,before.index('--helper-wrapper-sha')+1}
        self.assertEqual({i for i,(a,b)in enumerate(zip(before,after))if a!=b},indices)
        self.assertEqual(after[after.index('--helper-wrapper')+1],'/root/raw_scalar_helper_derived.py')
        self.assertEqual(after[after.index('--helper-wrapper-sha')+1],derived.DERIVED_FILES['raw_scalar_helper_derived.py'])

    def test_direct_verification_stage_pins_original_gold_and_prior_failed_report(self):
        original=['--verify','/root/case','--reference','/reference','--extractor','/extractor',
                  '--verification-output','independent-derived-retry1']
        argv=derived.benchmark_command('/root','/root/source/tools/optimization/bench_full12.py',
            '/root/case/checksum-audit/new-stage','/python',original,retry_existing_verification_sha='f'*64,verify=False)
        self.assertEqual(argv[-len(original):],original)
        self.assertEqual(argv[argv.index('--expected-gold-sha')+1],legacy.GOLD_SHA)
        self.assertEqual(argv[argv.index('--retry-existing-verification-sha')+1],'f'*64)
        with self.assertRaises(ValueError):derived.benchmark_command('/root','/bench','/audit','/python',['--verify','/case'],verify=False)


if __name__=='__main__':unittest.main()
