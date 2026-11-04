"""Small real Linux read windows; production constants remain SHA-pinned."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import file_integrity as integrity
import fresh_publication_v2 as fresh


def npy(payload=b'x'*96,descr='<c16'):
    text=repr(dict(descr=descr,fortran_order=False,shape=(2,3))).encode('latin1')
    header=text+b' '*(117-len(text))+b'\n'
    return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+payload


@unittest.skipUnless(hasattr(os,'pread')and os.name=='posix','Linux explicit pread/fsync required')
class Contracts(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.output=self.root/'new-output';self.audit=self.root/'audit'
        self.payload=npy();self.sha=hashlib.sha256(self.payload).hexdigest()
        self.parent=self.root/'parent-protocol.json';self.parent.write_text('{"complete":true,"scope":"test"}\n')
        self.binding=dict(path=str(self.parent),sha256=integrity.read_dual(self.parent)['openssl_sha256'])
        self.patch1=mock.patch.object(fresh,'PROP_BYTES',len(self.payload));self.patch1.start();self.addCleanup(self.patch1.stop)
        self.patch2=mock.patch.object(fresh,'PROP_SHAPE',(2,3));self.patch2.start();self.addCleanup(self.patch2.stop)

    def scope(self,reader=None,known=False,payload=None):
        content=self.payload if payload is None else payload
        if known:
            for name,value in(('GAUGE_BYTES',len(content)),('GAUGE_SHA',hashlib.sha256(content).hexdigest())):
                patch=mock.patch.object(fresh,name,value);patch.start();self.addCleanup(patch.stop)
            expected=fresh.GAUGE_SHA;kind='canonical-gauge';relative='gauge.bin'
        else:expected=None;kind='npy-propagator';relative='case/propagator.npy'
        publication=fresh.FreshPublication(self.output,[dict(relative=relative,kind=kind,expected_sha256=expected,bytes=len(content))],
            self.audit,reader=reader)
        self.path=self.output/relative;self.path.parent.mkdir(parents=True);self.path.write_bytes(content)
        return publication,expected,len(content)

    def reader(self,boundary='before',later=None,wrong=False,extra=False):
        calls=[]
        def read(path,expected,size,**options):
            index=len(calls);calls.append(index);path=Path(path);stat_calls=[]
            if later is not None:later(index,path)
            def stat():
                value=path.stat();stat_calls.append(1)
                if index==0 and boundary=='before'and len(stat_calls)==1:
                    os.utime(path,ns=(value.st_atime_ns,value.st_mtime_ns+1000000))
                return value
            def pread(fd,n,offset):
                data=os.pread(fd,n,offset)
                if index==0 and offset==0 and boundary=='during':
                    value=path.stat();os.utime(path,ns=(value.st_atime_ns,value.st_mtime_ns+1000000))
                if index==0 and wrong and offset==0:return b'!'+data[1:]
                if index==0 and extra and offset==size:return b'!'
                return data
            return integrity.read_dual(path,expected,size,block=64,path_stat=stat,pread=pread,**options)
        return read,calls

    def read(self,scope,expected,size):return scope.read(self.path,expected,size,parent_protocol=self.binding)

    def test_original_strict_pass_and_exact_closed_npy_header(self):
        scope,expected,size=self.scope();row=self.read(scope,expected,size)
        proof=row['fresh_output_publication']['full_proof']
        self.assertTrue(row['passed']);self.assertEqual(proof['strict_calls'],1);self.assertEqual(proof['full_reads'],1)
        self.assertTrue(proof['closed_npy_header']['passed']);self.assertEqual(self.path.read_bytes(),self.payload)

    def test_real_utime_between_pathstat_and_fstat_empty_digest_is_not_candidate(self):
        reader,calls=self.reader();scope,expected,size=self.scope(reader)
        row=self.read(scope,expected,size);proof=row['fresh_output_publication']['full_proof']
        first,second,third=proof['reads'];self.assertEqual(calls,[0,1,2])
        self.assertEqual(fresh.rejection_kind(first,None,size),'before-read-timestamp-only-zero-bytes')
        self.assertEqual(first['read_bytes'],0);self.assertEqual(first['pread_calls'],0);self.assertIsNone(first['eof_probe_bytes'])
        self.assertEqual(first['openssl_sha256'],fresh.EMPTY_SHA);self.assertIsNone(second['expected_sha256'])
        self.assertEqual(third['expected_sha256'],self.sha);self.assertEqual(proof['strict_calls'],3);self.assertEqual(proof['full_reads'],2)
        self.assertEqual(proof['published_sha256'],self.sha);self.assertFalse(proof['empty_digest_is_payload_candidate'])
        self.assertEqual(Path(first['bad_view_snapshot']).read_bytes(),b'')
        self.assertEqual(json.loads((self.audit/'output-000/read-0.json').read_text()),first)
        for item in proof['progress']:self.assertEqual(integrity.read_dual(item['path'])['openssl_sha256'],item['sha256'])

    def test_real_utime_during_full_read_requires_two_additional_strict_reads(self):
        reader,calls=self.reader('during');scope,expected,size=self.scope(reader)
        proof=self.read(scope,expected,size)['fresh_output_publication']['full_proof']
        self.assertEqual(calls,[0,1,2]);self.assertEqual(proof['full_reads'],3)
        self.assertEqual(proof['mode'],'full-read-timestamp-only');self.assertFalse(proof['reads'][0]['passed'])
        self.assertEqual(Path(proof['reads'][0]['bad_view_snapshot']).read_bytes(),self.payload)

    def test_known_scratch_before_read_window_still_requires_fixed_digest_on_both_full_reads(self):
        reader,calls=self.reader();scope,expected,size=self.scope(reader,known=True,payload=b'canonical scratch'*137)
        proof=self.read(scope,expected,size)['fresh_output_publication']['full_proof']
        self.assertEqual(calls,[0,1,2]);self.assertEqual(proof['full_reads'],2)
        self.assertTrue(all(row['expected_sha256']==expected==row['openssl_sha256']for row in proof['reads'][1:]))

    def test_second_timestamp_change_cannot_reset_first_ending_baseline(self):
        def later(index,path):
            if index==1:
                value=path.stat();os.utime(path,ns=(value.st_atime_ns,value.st_mtime_ns+1000000))
        reader,calls=self.reader(later=later);scope,expected,size=self.scope(reader)
        with self.assertRaises(RuntimeError):self.read(scope,expected,size)
        self.assertEqual(calls,[0,1]);self.assertTrue((self.audit/'output-000/failure.json').exists())
        with self.assertRaises(RuntimeError):self.read(scope,expected,size)
        self.assertEqual(calls,[0,1])

    def test_wrong_read_view_and_extra_eof_are_never_timestamp_only_acceptance(self):
        for mode in('wrong','extra'):
            with self.subTest(mode=mode):
                self.output=self.root/('output-'+mode);self.audit=self.root/('audit-'+mode)
                reader,calls=self.reader('during',wrong=mode=='wrong',extra=mode=='extra')
                scope,expected,size=self.scope(reader)
                with self.assertRaises(RuntimeError):self.read(scope,expected,size)
                self.assertFalse((self.audit/'output-000/receipt.json').exists())
                self.assertLessEqual(len(calls),2)

    def test_existing_output_symlink_undeclared_or_wrong_expected_cannot_publish(self):
        self.output.mkdir()
        declaration=[dict(relative='case/propagator.npy',kind='npy-propagator',bytes=len(self.payload),expected_sha256=None)]
        with self.assertRaises(RuntimeError):fresh.FreshPublication(self.output,declaration,self.audit)
        self.output.rmdir();self.output.symlink_to(self.root/'absent',target_is_directory=True)
        with self.assertRaises(RuntimeError):fresh.FreshPublication(self.output,declaration,self.audit)
        self.output.unlink();scope,expected,size=self.scope()
        with self.assertRaises(RuntimeError):scope.read(self.parent,None,size,parent_protocol=self.binding)
        with self.assertRaises(RuntimeError):scope.read(self.path,self.sha,size,parent_protocol=self.binding)

    def test_published_token_cannot_be_reused_even_with_none_expected(self):
        scope,expected,size=self.scope();self.read(scope,expected,size)
        with self.assertRaises(RuntimeError):self.read(scope,expected,size)

    def test_bad_npy_header_is_rejected_after_strict_hash_not_reconstructed(self):
        broken=npy(descr='>c16');scope,expected,size=self.scope(payload=broken)
        with self.assertRaises(RuntimeError):self.read(scope,expected,size)
        self.assertEqual(self.path.read_bytes(),broken)
        self.assertFalse((self.audit/'output-000/receipt.json').exists())

    def test_parent_receipt_hash_is_checked_before_payload_reads(self):
        reader,calls=self.reader();scope,expected,size=self.scope(reader)
        self.parent.write_text('changed')
        with self.assertRaises(RuntimeError):self.read(scope,expected,size)
        self.assertEqual(calls,[])


if __name__=='__main__':unittest.main()
