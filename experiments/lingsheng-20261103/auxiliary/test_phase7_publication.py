"""Publication acceptance contracts; no MPI/solver/old-experiment recovery."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import file_integrity as integrity
import phase7_publication as publication

PAYLOAD=bytes(range(256))*8+b't'*128
SHA=hashlib.sha256(PAYLOAD).hexdigest()


def row(stable=True,stamp=2):
    metadata=dict(dev=1,inode=2,bytes=len(PAYLOAD),mtime_ns=stamp,ctime_ns=stamp)
    return dict(complete=True,passed=stable,expected_sha256=None,required_bytes=len(PAYLOAD),
        initial=deepcopy(metadata if stable else dict(metadata,mtime_ns=1,ctime_ns=1)),
        fd_before=deepcopy(metadata if stable else dict(metadata,mtime_ns=1,ctime_ns=1)),
        fd_after=deepcopy(metadata),path_after=deepcopy(metadata),metadata_stable=stable,byte_count_exact=True,
        eof_probe_bytes=0,original_open_mode='O_RDONLY',same_immutable_bytes=True,read_bytes=len(PAYLOAD),
        openssl_sha256=SHA,software_sha256=SHA,error='Strict digest/identity/count/EOF gate failed' if not stable else None)


class PublicationContracts(unittest.TestCase):
    def reader(self,rows):
        calls=[]
        def strict(path,expected,size,**kwargs):
            calls.append(dict(path=str(path),expected=expected,size=size,kwargs=kwargs));value=deepcopy(rows[len(calls)-1])
            if not value['passed']:raise integrity.IntegrityError(value['error'],value)
            return value
        return strict,calls

    def publish(self,rows,**kwargs):
        strict,calls=self.reader(rows);receipts=[]
        result=publication.publish(Path('new/propagator.npy'),strict,integrity.IntegrityError,
            expected_size=len(PAYLOAD),receipt_writer=lambda r:receipts.append(deepcopy(r)),**kwargs)
        return result,calls,receipts

    def test_first_stable_strict_read_publishes_once(self):
        (final,receipt),calls,_=self.publish([row()])
        self.assertEqual(final['openssl_sha256'],SHA);self.assertTrue(receipt['passed']);self.assertEqual(len(calls),1)
        self.assertEqual(receipt['mode'],'first-strict-read')

    def test_one_unpublished_timestamp_rejection_requires_two_full_stable_windows(self):
        (final,receipt),calls,receipts=self.publish([row(False),row(),row()])
        self.assertTrue(receipt['passed']);self.assertEqual(receipt['full_reads'],3)
        self.assertEqual([c['expected'] for c in calls],[None,SHA,SHA])
        self.assertTrue(all(c['size']==len(PAYLOAD) for c in calls))
        self.assertFalse(receipt['reads'][0]['strict_pass']);self.assertFalse(receipt['reads'][0]['report']['passed'])
        self.assertFalse(receipt['first_rejection_accepted']);self.assertEqual(final['openssl_sha256'],SHA)
        self.assertTrue(any(not r['passed'] for r in receipts));self.assertFalse(receipt['sleep_used'])

    def test_any_identity_size_count_eof_algorithm_or_io_failure_stops_at_first_read(self):
        mutators=[lambda r:r['fd_after'].update(inode=3),lambda r:r['fd_after'].update(bytes=len(PAYLOAD)+1),
            lambda r:r.update(byte_count_exact=False),lambda r:r.update(eof_probe_bytes=1),
            lambda r:r.update(software_sha256='0'*64),lambda r:r.update(read_bytes=len(PAYLOAD)-1),
            lambda r:r.update(error='actual read error'),lambda r:r.update(expected_sha256=SHA),
            lambda r:r['path_after'].update(mtime_ns=3),lambda r:r['fd_before'].update(ctime_ns=0)]
        for mutate in mutators:
            rejected=row(False);mutate(rejected);strict,calls=self.reader([rejected,row(),row()])
            with self.subTest(rejected=rejected),self.assertRaises(publication.PublicationFailure):
                publication.publish('new/propagator.npy',strict,integrity.IntegrityError,expected_size=len(PAYLOAD))
            self.assertEqual(len(calls),1)

    def test_second_or_third_timestamp_change_is_not_retried(self):
        for sequence,expected_calls in [([row(False),row(False),row()],2),([row(False),row(),row(False)],3),
            ([row(False),row(True,3),row(True,3)],2),([row(False),row(),row(True,3)],3)]:
            strict,calls=self.reader(sequence)
            with self.assertRaises(publication.PublicationFailure):publication.publish('new/propagator.npy',strict,integrity.IntegrityError)
            self.assertEqual(len(calls),expected_calls)

    def test_equal_time_windows_cannot_hide_different_bytes(self):
        changed=row();changed.update(openssl_sha256='0'*64,software_sha256='0'*64)
        strict,calls=self.reader([row(False),changed,row()])
        with self.assertRaises(publication.PublicationFailure):publication.publish('new/propagator.npy',strict,integrity.IntegrityError)
        self.assertEqual(len(calls),2)

    def test_existing_expected_hash_never_enters_publication(self):
        strict,calls=self.reader([row()])
        with self.assertRaisesRegex(RuntimeError,'expected SHA'):publication.publish('immutable/gold.npy',strict,integrity.IntegrityError,expected=SHA)
        self.assertEqual(calls,[])

    def test_unpublished_rejection_cannot_be_relabelled_pass(self):
        initial=row(False);original=deepcopy(initial)
        self.publish([initial,row(),row()]);self.assertEqual(initial,original);self.assertFalse(initial['passed'])

    def test_first_rejection_persisted_before_interrupted_followup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);calls=[]
            def save(value):
                path=root/('receipt-%d.json'%len(list(root.glob('receipt-*.json'))))
                with path.open('x') as stream:json.dump(value,stream)
            def strict(path,expected,size,**kwargs):
                calls.append(expected)
                if len(calls)==1:raise integrity.IntegrityError('metadata',row(False))
                persisted=json.loads((root/'receipt-0.json').read_text())
                self.assertFalse(persisted['reads'][0]['strict_pass']);self.assertFalse(persisted['passed'])
                raise KeyboardInterrupt('Simulated interrupt during follow-up')
            with self.assertRaises(publication.PublicationFailure):
                publication.publish('new/propagator.npy',strict,integrity.IntegrityError,receipt_writer=save)
            self.assertEqual(len(calls),2);self.assertTrue((root/'receipt-0.json').exists())

    @unittest.skipUnless(hasattr(os,'pread'),'Production entry requires Linux os.pread; pure gates run on both platforms')
    def test_real_entry_metadata_rejection_uses_three_reads_and_durable_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'toy_metadata_adapter.py';output=root/'numeric-output'
            source.write_text("import json,os,sys\nfrom pathlib import Path\nimport file_integrity as integrity\ndef main():\n a=sys.argv[1:];args=a[a.index('--')+1:];out=Path(args[args.index('--output')+1]);out.mkdir();target=out/'propagator.npy';payload=b'new exact output';target.write_bytes(payload);changed=[False];reads=[]\n def once(fd,count,offset):\n  result=os.pread(fd,count,offset);reads.append((offset,count))\n  if not changed[0]:\n   s=target.stat();os.utime(target,ns=(s.st_atime_ns,s.st_mtime_ns+1000000));changed[0]=True\n  return result\n result=integrity.read_dual(target,None,len(payload),pread=once);(out/'observed.json').write_text(json.dumps({'publication':result['new_output_publication'],'read_requests':reads}))\n")
            sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            command=[sys.executable,str(HERE/'phase7_cold_entry.py'),'--adapter',str(source),'--publication-output',str(root/'receipts'),
                '--expected-entry-sha',sha(HERE/'phase7_cold_entry.py'),'--expected-adapter-sha',sha(source),
                '--expected-publication-sha',sha(HERE/'phase7_publication.py'),'--expected-reader-sha',sha(HERE/'file_integrity.py'),
                '--','--','--output',str(output)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            observed=json.loads((output/'observed.json').read_text());self.assertEqual(observed['publication']['full_reads'],3)
            self.assertEqual(len(observed['read_requests']),6)  # data+EOF for each full read
            directory=root/'receipts/rank00000';proof=json.loads((directory/'protocol.json').read_text());self.assertEqual(len(proof['receipt_snapshots']),4)
            first=json.loads((directory/proof['receipt_snapshots'][0]['path']).read_text())
            self.assertFalse(first['complete']);self.assertFalse(first['passed']);self.assertFalse(first['reads'][0]['strict_pass'])
            self.assertFalse(first['reads'][0]['report']['metadata_stable'])
            for item in proof['receipt_snapshots']:self.assertEqual(sha(directory/item['path']),item['sha256'])
            receipt=json.loads((directory/'receipt.json').read_text());self.assertTrue(receipt['passed']);self.assertFalse(receipt['first_rejection_accepted'])
            self.assertEqual((output/'propagator.npy').read_bytes(),b'new exact output')

    @unittest.skipUnless(hasattr(os,'pread'),'Production entry requires Linux os.pread; pure gates run on both platforms')
    def test_real_new_output_entry_keeps_immutable_reads_strict_and_frozen_source_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'toy_adapter.py';input_path=root/'input';input_path.write_bytes(PAYLOAD)
            source.write_text("import json,sys\nfrom pathlib import Path\nimport file_integrity as integrity\ndef main():\n a=sys.argv[1:];i=a.index('--');args=a[i+1:];out=Path(args[args.index('--output')+1]);out.mkdir();target=out/'propagator.npy';target.write_bytes(b'new exact output');immutable=integrity.read_dual(Path(args[args.index('--input')+1]));result=integrity.read_dual(target,None,len(b'new exact output'));(out/'observed.json').write_text(json.dumps({'immutable_has_publication':'new_output_publication' in immutable,'output_has_publication':'new_output_publication' in result}))\n")
            sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=source.read_bytes();output=root/'numeric-output'
            command=[sys.executable,str(HERE/'phase7_cold_entry.py'),'--adapter',str(source),'--publication-output',str(root/'receipts'),
                '--expected-entry-sha',sha(HERE/'phase7_cold_entry.py'),'--expected-adapter-sha',sha(source),
                '--expected-publication-sha',sha(HERE/'phase7_publication.py'),'--expected-reader-sha',sha(HERE/'file_integrity.py'),
                '--','--','--output',str(output),'--input',str(input_path)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            observed=json.loads((output/'observed.json').read_text());self.assertFalse(observed['immutable_has_publication']);self.assertTrue(observed['output_has_publication'])
            self.assertEqual(source.read_bytes(),before);self.assertEqual(input_path.read_bytes(),PAYLOAD)
            receipt=json.loads((root/'receipts/rank00000/receipt.json').read_text());self.assertTrue(receipt['passed']);self.assertEqual(receipt['full_reads'],1)
            second=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertNotEqual(second.returncode,0);self.assertIn('NEW absent output',second.stderr)
            dangling=root/'dangling-output';dangling.symlink_to(root/'absent-target',target_is_directory=True)
            new_command=list(command);new_command[new_command.index('--output')+1]=str(dangling)
            third=subprocess.run(new_command,capture_output=True,text=True,timeout=30)
            self.assertNotEqual(third.returncode,0);self.assertIn('without symlink',third.stderr)
            self.assertFalse((root/'absent-target').exists())

if __name__=='__main__':unittest.main()
