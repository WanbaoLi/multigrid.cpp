import errno
import hashlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('integrity',Path(__file__).with_name('file_integrity.py'))
integrity=importlib.util.module_from_spec(spec);spec.loader.exec_module(integrity)


def portable_test_pread(fd,count,offset):
    # Only test injection on Windows. Production reader has no seek/read fallback.
    os.lseek(fd,offset,os.SEEK_SET)
    return os.read(fd,count)


class RawIntegrityContract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.path=self.root/'original';self.payload=bytes(range(256))*8+b't'*128
        self.path.write_bytes(self.payload)
        self.initial=self.path.stat()
        self.expected=hashlib.sha256(self.payload).hexdigest()
        self.pread=getattr(os,'pread',portable_test_pread)

    def tearDown(self):self.temp.cleanup()

    def read(self,**kwargs):
        if not hasattr(os,'pread'):
            # Production deliberately has no Windows fallback. Contract tests
            # inject seek/read plus a stable mock stat; Windows path/FD ctime
            # observations can differ during initial write timestamp updates.
            kwargs.setdefault('fstat',lambda fd:self.initial)
            kwargs.setdefault('path_stat',lambda:self.initial)
        return integrity.read_dual(self.path,self.expected,len(self.payload),block=1024,
                                   pread=kwargs.pop('pread',self.pread),**kwargs)

    def test_known_vectors_and_exact_tail128_and_eof(self):
        self.assertEqual(integrity.known_vectors()['known_vectors_passed'],3)
        requests=[]
        def recorded(fd,n,offset):requests.append((offset,n));return self.pread(fd,n,offset)
        result=self.read(pread=recorded)
        self.assertTrue(result['passed']);self.assertEqual(result['read_bytes'],len(self.payload))
        self.assertEqual(requests[-2:],[(2048,128),(2176,1)])
        self.assertEqual(result['eof_probe_bytes'],0)

    def test_positive_short_reads_advance_exact_offsets(self):
        def short(fd,n,offset):return self.pread(fd,min(17,n),offset)
        row=self.read(pread=short)
        self.assertTrue(row['passed']);self.assertGreater(row['positive_short_reads'],0)

    def test_eintr_retries_same_explicit_offset(self):
        calls=[]
        def interrupt(fd,n,offset):
            calls.append((offset,n))
            if len(calls)==1:raise InterruptedError(errno.EINTR,'injected')
            return self.pread(fd,n,offset)
        self.assertTrue(self.read(pread=interrupt)['passed'])
        self.assertEqual(calls[0],calls[1])

    def test_oversized_read_rejected_and_preserved_private(self):
        snapshot=self.root/'bad-view'
        with self.assertRaises(integrity.IntegrityError) as captured:
            self.read(pread=lambda fd,n,offset:b'x'*(n+1),snapshot=snapshot)
        row=captured.exception.report
        self.assertFalse(row['passed']);self.assertEqual(row['last_returned_bytes'],1025)
        self.assertEqual(snapshot.read_bytes(),b'x'*1025)
        self.assertEqual(self.path.read_bytes(),self.payload)
        if os.name=='posix':self.assertEqual(snapshot.stat().st_mode&0o777,0o600)

    def test_nonempty_eof_not_silently_truncated(self):
        def extra(fd,n,offset):return b'X' if offset==len(self.payload) else self.pread(fd,n,offset)
        with self.assertRaises(integrity.IntegrityError) as captured:self.read(pread=extra)
        self.assertEqual(captured.exception.report['eof_probe_bytes'],1)
        self.assertTrue(captured.exception.report['byte_count_exact'])
        self.assertFalse(captured.exception.report['passed'])

    def test_early_eof_rejected(self):
        def early(fd,n,offset):return b'' if offset>=1024 else self.pread(fd,n,offset)
        with self.assertRaises(integrity.IntegrityError):self.read(pread=early)

    def test_changed_path_identity_rejected(self):
        original=self.path.stat();calls=[]
        def changed():
            calls.append(1)
            values={key:getattr(original,key) for key in ['st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns']}
            if len(calls)>1:values['st_ino']+=1
            return SimpleNamespace(**values)
        with self.assertRaises(integrity.IntegrityError) as captured:self.read(path_stat=changed)
        self.assertFalse(captured.exception.report['metadata_stable'])


if __name__=='__main__':unittest.main()
