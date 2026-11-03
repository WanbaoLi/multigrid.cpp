"""Strict fresh-derived publication contracts; small real files, no solver/MPI."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import derived_publication as derived
import file_integrity as integrity
import raw_scalar_helper_derived as helper


@unittest.skipUnless(hasattr(os,'pread')and os.name=='posix','Linux raw reader/fsync contract')
class Contracts(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.output=self.root/'new-output'
        self.payload=bytes(range(256))*9+b't'*128;self.expected=hashlib.sha256(self.payload).hexdigest()
        self.audit=self.root/'audit'

    def publication(self,reader=None):
        publication=derived.FreshDerivedPublication(self.output,self.expected,len(self.payload),self.audit,reader=reader)
        self.output.mkdir();publication.path.write_bytes(self.payload)
        return publication

    def read_with_initial_mtime_change(self,later=None):
        calls=[]
        def reader(path,expected,size,**kwargs):
            calls.append(len(calls));index=calls[-1]
            def changed(fd,n,offset):
                data=os.pread(fd,n,offset)
                if index==0 and offset==0:
                    before=Path(path).stat();os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
                if later is not None:later(index,path,fd,n,offset)
                return data
            return integrity.read_dual(path,expected,size,block=1024,pread=changed,**kwargs)
        return reader,calls

    def test_strict_first_pass_is_unchanged_reader_not_timestamp_exception(self):
        publication=self.publication();row=publication.read()
        self.assertTrue(row['passed']);self.assertTrue(row['metadata_stable'])
        proof=row['derived_publication'];self.assertEqual(proof['read_count'],1)
        self.assertFalse(proof['first_rejection_preserved']);self.assertTrue(proof['passed'])
        self.assertEqual(publication.path.read_bytes(),self.payload)
        with self.assertRaises(RuntimeError):publication.read()

    def test_actual_tmp_mtime_publication_requires_two_strict_reads_and_keeps_rejection(self):
        reader,calls=self.read_with_initial_mtime_change();publication=self.publication(reader)
        row=publication.read();proof=row['derived_publication']
        self.assertTrue(row['passed']);self.assertEqual(calls,[0,1,2]);self.assertEqual(proof['read_count'],3)
        first,*stable=proof['reads'];self.assertFalse(first['passed'])
        self.assertTrue(derived.timestamp_only_rejection(first,self.expected,len(self.payload)))
        self.assertTrue(all(derived.strict_row(value,self.expected,len(self.payload),first['fd_after'])for value in stable))
        self.assertEqual(json.loads((self.audit/'read-0.json').read_text()),first)
        snapshot=Path(first['bad_view_snapshot']);self.assertEqual(snapshot.read_bytes(),self.payload)
        self.assertEqual(snapshot.stat().st_mode&0o777,0o600)
        self.assertEqual(publication.path.read_bytes(),self.payload,'Never rewrite derived bytes to make them match')

    def test_existing_output_or_dangling_alias_cannot_receive_publication_exception(self):
        self.output.mkdir()
        with self.assertRaises(RuntimeError):derived.FreshDerivedPublication(self.output,self.expected,len(self.payload),self.audit)
        self.output.rmdir();self.output.symlink_to(self.root/'missing',target_is_directory=True)
        with self.assertRaises(RuntimeError):derived.FreshDerivedPublication(self.output,self.expected,len(self.payload),self.audit)

    def test_second_metadata_change_between_reads_immediately_fails_not_resets_baseline(self):
        original,calls=self.read_with_initial_mtime_change()
        def reader(path,expected,size,**kwargs):
            if len(calls)==1:
                before=Path(path).stat();os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+2000000))
            return original(path,expected,size,**kwargs)
        publication=self.publication(reader)
        with self.assertRaises(RuntimeError):publication.read()
        self.assertEqual(calls,[0,1]);self.assertTrue((self.audit/'failure.json').exists())
        self.assertFalse((self.audit/'publication.json').exists())

    def test_second_metadata_change_during_read_immediately_fails_no_third_read(self):
        def later(index,path,fd,n,offset):
            if index==1 and offset==0:
                before=Path(path).stat();os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+2000000))
        reader,calls=self.read_with_initial_mtime_change(later);publication=self.publication(reader)
        with self.assertRaises(integrity.IntegrityError):publication.read()
        failure=json.loads((self.audit/'failure.json').read_text())
        self.assertEqual(calls,[0,1]);self.assertEqual(failure['read_count'],2);self.assertFalse(failure['passed'])

    def test_bad_bytes_or_extra_eof_never_qualify_for_metadata_retries(self):
        for mode in ('wrong-content','extra-eof'):
            with self.subTest(mode=mode):
                # Fresh protocol and identity, not a reset of a rejected one.
                self.output=self.root/('output-'+mode);self.audit=self.root/('audit-'+mode)
                calls=[]
                def reader(path,expected,size,**kwargs):
                    calls.append(1)
                    def changed(fd,n,offset):
                        data=os.pread(fd,n,offset)
                        if offset==0:
                            before=Path(path).stat();os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
                            if mode=='wrong-content':return b'X'+data[1:]
                        return b'X'if mode=='extra-eof'and offset==size else data
                    return integrity.read_dual(path,expected,size,block=1024,pread=changed,**kwargs)
                publication=self.publication(reader)
                with self.assertRaises(RuntimeError):publication.read()
                self.assertEqual(len(calls),1)
                self.assertFalse((self.audit/'publication.json').exists())

    def test_identity_change_cannot_be_misclassified_as_timestamps(self):
        reader,calls=self.read_with_initial_mtime_change()
        publication=self.publication(reader);row=publication.read()['derived_publication']['reads'][0]
        for key in ('dev','inode','bytes'):
            changed=deepcopy(row);changed['fd_after'][key]+=1;changed['path_after'][key]+=1
            self.assertFalse(derived.timestamp_only_rejection(changed,self.expected,len(self.payload)))
        changed=deepcopy(row);changed['software_sha256']='0'*64
        self.assertFalse(derived.timestamp_only_rejection(changed,self.expected,len(self.payload)))

    def test_unrelated_immutable_file_stays_strict_even_if_timestamp_only(self):
        publication=self.publication();self.root.joinpath('helper-audit').mkdir()
        immutable=self.root/'gold';immutable.write_bytes(self.payload)
        checks=helper.HelperChecks(self.root/'helper-audit',{str(immutable):self.expected},publication)
        original=integrity.read_dual
        def changing(path,expected=None,size=None,**kwargs):
            def changed(fd,n,offset):
                data=os.pread(fd,n,offset)
                if offset==0:
                    before=Path(path).stat();os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
                return data
            return original(path,expected,size,pread=changed,**kwargs)
        with mock.patch.object(integrity,'read_dual',changing):
            with self.assertRaises(integrity.IntegrityError):checks(immutable)
        self.assertFalse(publication.used);self.assertEqual(checks.rows,[])

    def test_sha_only_ast_keeps_every_other_original_helper_node_identical(self):
        frozen=Path(__file__).parent/'multigrid.cpp/benchmarks/runtime/verify_fixture_propagator.py'
        source=helper.source_bytes(frozen,helper.ORIGINAL_HELPER_SHA)
        _,proof=helper.transform(source,str(frozen))
        self.assertTrue(proof['only_sha_body_changed'])
        self.assertEqual(proof['unchanged_nodes_original_sha256'],proof['unchanged_nodes_transformed_sha256'])


if __name__=='__main__':unittest.main()
