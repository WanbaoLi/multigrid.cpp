#!/usr/bin/env python3
"""Linux infrastructure contracts; no scheduler, SSH, solver or scientific job."""
import os
from pathlib import Path
import sys
import unittest


class ExternalFixtureAbsent(unittest.TestCase):
    def __init__(self,original_id,reason):
        super().__init__();self.original_id=original_id;self.reason=reason
    def id(self):return self.original_id
    def runTest(self):raise unittest.SkipTest(self.reason)


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item


def main():
    if os.name!='posix' or not hasattr(os,'pread'):
        print('Run these strict file-identity contracts under Linux/WSL with os.pread.',file=sys.stderr)
        return 2
    root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
    suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
    external=root.parent/'outputs/optimization-20261103/profile-hbw-evidence/rank00000.perf-flat.txt'
    result=unittest.TestSuite()
    for case in flatten(suite):
        if case.id().endswith('.test_real_old_flat_keeps_partition_and_exact_header') and not external.is_file():
            case=ExternalFixtureAbsent(case.id(),'Historical perf-flat input is exported separately in results; no fabricated fixture')
        result.addTest(case)
    outcome=unittest.TextTestRunner(verbosity=2).run(result)
    return 0 if outcome.wasSuccessful() else 1


if __name__=='__main__':sys.exit(main())
