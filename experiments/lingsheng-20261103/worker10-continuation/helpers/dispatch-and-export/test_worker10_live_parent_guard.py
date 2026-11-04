import unittest
import worker10_live_parent_guard_v1 as guard

class Contracts(unittest.TestCase):
    def test_only_exact_owned_live_parent_accepted(self):
        cpus=list(range(592));root=str(guard.root)
        startup=dict(host='cn19486',allocation='mg-opt-20261103-worker10',source_root='/source',
            safe_deadline_epoch=10000,before_worker_exec_parent_state=dict(cpus=cpus))
        status=dict(status='running',task_tag='owned')
        argv=['python','/source/tools/optimization/worker.py','--queue',root+'/queue10']
        args=[startup,dict(pid=42),status,'cn19486',42,7,7,argv,'mg-opt-20261103-worker10',cpus,cpus,False,'owned',9000,5000]
        guard.validate(*args)
        for index,value in ((1,dict(pid=99)),(2,dict(status='passed',task_tag='owned')),(3,'cn19483'),(5,8),
            (7,['python','/other/worker.py','--queue',root+'/queue10']),(8,'old'),(9,cpus[:1]),(10,cpus[:1]),
            (11,True),(12,'other'),(13,8089),(13,10001),(13,float('nan'))):
            changed=list(args);changed[index]=value
            with self.subTest(index=index),self.assertRaises(RuntimeError):guard.validate(*changed)
if __name__=='__main__':unittest.main(verbosity=2)
