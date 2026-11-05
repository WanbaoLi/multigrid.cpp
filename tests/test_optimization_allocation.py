"""Meaningful protections against the two observed old-queue clone failures."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('allocation_contract',Path(__file__).resolve().parents[1]/'tools/optimization/allocation_contract.py')
allocation=importlib.util.module_from_spec(spec);spec.loader.exec_module(allocation)


class Contracts(unittest.TestCase):
    def fixture(self,root):
        def write(name,value):
            p=root/name;p.write_text(value if isinstance(value,str)else json.dumps(value));return hashlib.sha256(p.read_bytes()).hexdigest()
        entry=write('worker_entry.py',"QUEUE='queue73'\nALLOCATION='actual-epoch'\nHOST='compute-7'\n")
        job=dict(jobId='31000',taskExecNodes='compute-7',exclusive=True,resGroups=[dict(resAlloc=dict(cpu=4))])
        auth=write('allocation.json',dict(complete=True,allocation='actual-epoch',scheduler_job='31000',scheduler_authentication=dict(job=job)))
        startup=write('startup.json',dict(complete=True,allocation='actual-epoch',host='compute-7',scheduler_job='31000',entry_sha256=entry,
            allocation_record_sha256=auth,safe_deadline_epoch=9999999999,before_worker_exec_parent_state=dict(cpus=[0,2,4,6],gomp_kupl_loaded=False)))
        context=allocation.load(root/'startup.json',startup,root/'worker_entry.py',root/'allocation.json')
        return context,write

    def test_queue_is_derived_from_exact_entry_and_rejects_changed_entry(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();context,_=self.fixture(root)
            self.assertEqual(context['queue'],str(root/'queue73'))
            (root/'worker_entry.py').write_text("QUEUE='queue12'\nALLOCATION='actual-epoch'\nHOST='compute-7'\n")
            with self.assertRaisesRegex(ValueError,'Pinned input differs'):
                allocation.load(root/'startup.json',context['startup_sha256'],root/'worker_entry.py',root/'allocation.json')

    def test_qualification_cannot_be_taken_from_old_queue_or_epoch(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();context,write=self.fixture(root);(root/'queue73').mkdir();(root/'queue12').mkdir()
            task='qualified-source';state=dict(complete=True,status='passed',host='compute-7',allocation='actual-epoch',source_head='a'*40)
            status=dict(status='passed',returncode=0,host='compute-7',cleanup=dict(complete=True,surviving_pids=[]))
            state_sha=write('state.json',state);status_sha=write('queue12/'+task+'.status.json',status)
            with self.assertRaises(FileNotFoundError):allocation.dependency(context,task,status_sha,root/'state.json',state_sha)
            write('queue73/'+task+'.status.json',status)
            self.assertTrue(allocation.dependency(context,task,status_sha,root/'state.json',state_sha,'a'*40)['complete'])
            for mutation in [dict(state,allocation='old-epoch'),dict(state,complete=False),dict(state,source_head='b'*40)]:
                changed=write('state.json',mutation)
                with self.assertRaises(ValueError):allocation.dependency(context,task,status_sha,root/'state.json',changed,'a'*40)
            status['cleanup']['surviving_pids']=[123];changed=write('queue73/'+task+'.status.json',status)
            with self.assertRaisesRegex(ValueError,'descendants'):allocation.dependency(context,task,changed,root/'state.json',write('state.json',state))

if __name__=='__main__':unittest.main()
