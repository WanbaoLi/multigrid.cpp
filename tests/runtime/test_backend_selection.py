"""CPU architecture selection; no native library or solver allocation required."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from lqcd_cpu import _resolve_backend


class Selection(unittest.TestCase):
    def test_architectures(self):
        for architecture, expected in [('aarch64','arm'),('arm64','arm'),('x86_64','x86'),('AMD64','x86')]:
            with self.subTest(architecture=architecture), patch('platform.machine',return_value=architecture):
                self.assertEqual(_resolve_backend(),expected)

    def test_explicit_override(self):
        with patch('platform.machine',return_value='aarch64'):
            self.assertEqual(_resolve_backend('x86'),'x86')
            self.assertEqual(_resolve_backend('reference-ddalphaamg'),'reference-ddalphaamg')

    def test_unsupported_and_invalid(self):
        with patch('platform.machine',return_value='sw_64'), self.assertRaises(ValueError):
            _resolve_backend()
        for value in ('',3,False):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _resolve_backend(value)


if __name__=='__main__':unittest.main()
