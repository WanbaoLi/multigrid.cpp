import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).parent))
import raw_scalar_helper as helper
import raw_benchmark_v4 as wrapper


class Protocol4Contract(unittest.TestCase):
    def test_actual_frozen_helper_changes_only_sha_body(self):
        path=Path(__file__).parent/'multigrid.cpp/benchmarks/runtime/verify_fixture_propagator.py'
        source=path.read_bytes();tree,proof=helper.transform(source,str(path))
        self.assertTrue(proof['only_sha_body_changed'])
        self.assertEqual(proof['unchanged_nodes_original_sha256'],proof['unchanged_nodes_transformed_sha256'])
        original=ast.parse(source)
        old=[n for n in original.body if not isinstance(n,ast.FunctionDef) or n.name!='sha']
        new=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='sha']
        self.assertEqual([ast.dump(n,include_attributes=False) for n in old],
                         [ast.dump(n,include_attributes=False) for n in new])

    def test_only_callback_changes_under_execution(self):
        source='def sha(path):\n return "OLD"\ndef physics(x):\n return x*x+3\nobserved=(sha("FILE"),physics(4))\n'
        tree,_=helper.transform(source,'synthetic.py');calls=[]
        namespace={'_raw_verified_sha':lambda path:calls.append(path) or 'RAW'}
        exec(compile(tree,'synthetic.py','exec'),namespace)
        self.assertEqual(namespace['observed'],('RAW',19));self.assertEqual(calls,['FILE'])

    def test_helper_full_file_sha_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'helper.py';path.write_bytes(b'def sha(path):\n return path\n')
            def pread(fd,n,offset):os.lseek(fd,offset,os.SEEK_SET);return os.read(fd,n)
            with mock.patch.object(helper.os,'pread',getattr(os,'pread',pread),create=True):
                self.assertEqual(helper.source_bytes(path,hashlib.sha256(path.read_bytes()).hexdigest()),path.read_bytes())
                with self.assertRaises(RuntimeError):helper.source_bytes(path,'0'*64)

    def test_candidate_pass_and_failure_never_publish_acceptable_report(self):
        initial={'complete':True,'samples':[{'wall_seconds':17.1}],'propagator_sha256':'ORIGINAL',
                 'verification':{'complete':True,'propagator_sha256':'OLD_WRONG'}}
        preserved=deepcopy(initial);candidate={'complete':True,'passed':True,'propagator_sha256':'ORIGINAL','columns':12}
        for state in ['running','pending_final_checks','failed']:
            result=wrapper.guarded_report(initial,candidate,'priorSHA',state,RuntimeError('gate failure') if state=='failed' else None)
            self.assertFalse(result['verification']['complete']);self.assertFalse(result['verification']['passed'])
            self.assertFalse(result['verification']['checksum_audit']['complete'])
            self.assertEqual({k:v for k,v in result.items() if k!='verification'},
                             {k:v for k,v in initial.items() if k!='verification'})
            self.assertEqual(result['verification']['candidate_verification'],candidate)
        self.assertEqual(initial,preserved)

    def test_missing_or_duplicate_sha_definition_is_rejected(self):
        for source in ['x=1','def sha(x):\n return x\ndef sha(y):\n return y\n']:
            with self.assertRaises(RuntimeError):helper.transform(source,'bad.py')


if __name__=='__main__':unittest.main()
