from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parent))
import raw_protocol_v4 as protocol


class PrefixContract(unittest.TestCase):
    def test_parameterized_entry_changes_target_only(self):
        one=protocol.command('/root','/root/setup.py','a'*64,'092-setup','python',['--id','092'],verify=False)
        two=protocol.command('/root','/root/phase6.py','b'*64,'100-halo','python',['--prefix','100'],verify=False)
        for option in ['--wrapper-sha','--reader-sha','--adapter-sha','--helper-sha','--helper-wrapper-sha']:
            self.assertEqual(one[one.index(option)+1],two[two.index(option)+1])
        self.assertEqual(one[-3:],['--','--id','092']);self.assertEqual(two[-3:],['--','--prefix','100'])

    def test_unsafe_tag_or_inexact_source_binding_rejected(self):
        for sha,tag in [('a'*63,'safe'),('a'*64,'../escape')]:
            with self.assertRaises(ValueError):protocol.prefix('/root','entry',sha,tag,'python',verify=False)


if __name__=='__main__':unittest.main()
