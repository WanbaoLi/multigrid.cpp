"""No scheduler submissions, subprocesses, runtime loading or compute in tests."""
import copy
import ast
import importlib.util
import json
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('worker10_test_entry', HERE/'worker10_entry.py')
entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
# Synthetic terminal scheduler row for authentication contracts only. This
# is never written as actual predecessor evidence or a scheduler record.
previous = dict(jobId='2023152',jobName='mg-opt-worker8',state='SUCCEEDED',user='nsls_lwb',
    startTime='2026-11-04T00:00:00Z',endTime='2026-11-04T04:00:00Z',jobWallClockLimit=14400,
    exclusive=True,taskExecNodes='cn19486',taskExecNodesCount=1,queue='q_hpcapp',account='common',
    resGroups=[dict(replica=1,nnodes='1',preferNodes='cn19486',resAlloc=dict(cpu=592,mem=480000),
        resReq=dict(cpu=592,mem=480000),nodeResUsages=[dict(execNode='cn19486')])])
probe_spec = importlib.util.spec_from_file_location('worker10_test_preflight', HERE/'worker10_preflight.py')
preflight = importlib.util.module_from_spec(probe_spec); probe_spec.loader.exec_module(preflight)


class Authentication(unittest.TestCase):
    def setUp(self):
        self.root = HERE.resolve()
        self.source = HERE/'multigrid.cpp'
        self.expected_source_head='1'*40
        self.job = copy.deepcopy(previous)
        self.job.update(jobId='2022000', jobName='mg-opt-worker10', state='RUNNING',
            startTime='2026-11-04T04:30:00Z', cmd=shlex.join(['/bin/bash',str(self.root/'worker10.sh'),'--source',str(self.source),'--expected-source-head',self.expected_source_head]),
            execPath=str(self.root))
        self.now = entry.epoch(self.job['startTime'])+20
        self.record = dict(source_root=str(self.source),expected_source_head=self.expected_source_head,
            source_tools_sha256={name:entry.sha(self.source/name)for name in entry.SOURCE_TOOLS},schema='worker10-login-allocation-v1',complete=True,allocation=entry.ALLOCATION,
            expected_host=entry.HOST,scheduler_job='2022000',requested_job_id='2022000',
            previous_job=entry.PREVIOUS_JOB,writer_host='login04',writer_uid=123,djob_path=str(self.root/'fake-djob'),
            query_epoch=self.now,scheduler_start_epoch=self.now-20,scheduler_hard_end_epoch=self.now-20+14400,
            safe_deadline_epoch=self.now-20+14100,
            scheduler_authentication=dict(job=self.job,previous=copy.deepcopy(previous)),
            wrapper_sha256={name:entry.sha(HERE/name) for name in entry.WRAPPERS})

    def validate(self):
        with patch.object(os,'getuid',return_value=123,create=True):
            return entry.validate_record(self.record,self.root,self.now,source=self.source,expected_source_head=self.expected_source_head)

    def test_actual_scheduler_shape_accepted(self):
        self.assertEqual(self.validate()['jobId'],'2022000')
        self.assertEqual(entry.deadline(self.job,self.now)[2],14080)

    def test_identity_mismatches_rejected(self):
        for key,value in [('jobId','2022001'),('state','PENDING'),('jobName','mg-opt-worker3'),
                          ('taskExecNodes','cn19516'),('user','another_user'),('exclusive',False),
                          ('jobWallClockLimit',7200),('cmd','/bin/bash /tmp/worker10.sh')]:
            with self.subTest(key=key):
                old=self.job[key];self.job[key]=value
                with self.assertRaises(RuntimeError):self.validate()
                self.job[key]=old

    def test_resource_mismatches_rejected(self):
        for key,value in [('cpu',591),('mem',479999),('mem',480001)]:
            old=self.job['resGroups'][0]['resAlloc'][key]
            self.job['resGroups'][0]['resAlloc'][key]=value
            with self.assertRaises(RuntimeError):self.validate()
            self.job['resGroups'][0]['resAlloc'][key]=old

    def test_predecessor_not_terminal_rejected(self):
        self.record['scheduler_authentication']['previous']['state']='RUNNING'
        with self.assertRaises(RuntimeError):self.validate()

    def test_predecessor_overlapping_rejected(self):
        self.record['scheduler_authentication']['previous']['endTime']='2026-11-04T04:31:00Z'
        with self.assertRaises(RuntimeError):self.validate()

    def test_stale_and_future_record_rejected(self):
        for age in (601,-6):
            self.record['query_epoch']=self.now-age
            with self.assertRaises(RuntimeError):self.validate()

    def test_threehundred_second_prehook_delay_accepted(self):
        self.now += 300
        self.assertEqual(self.validate()['jobId'],'2022000')

    def test_incorrect_deadline_rejected(self):
        self.record['safe_deadline_epoch']+=1
        with self.assertRaises(RuntimeError):self.validate()

    def test_wrong_exact_job_id_rejected(self):
        self.record['requested_job_id']='2022001'
        with self.assertRaises(RuntimeError):self.validate()

    def test_wrapper_changed_rejected(self):
        self.record['wrapper_sha256']['worker10.sh']='0'*64
        with self.assertRaises(RuntimeError):self.validate()

    def test_explicit_source_path_head_and_every_core_tool_are_bound(self):
        for key,value in [('source_root','/unreviewed/source'),('expected_source_head','2'*40),
                          ('source_tools_sha256',{}),('expected_source_head','HEAD')]:
            old=self.record[key];self.record[key]=value
            with self.assertRaises(RuntimeError):self.validate()
            self.record[key]=old
        self.record['source_tools_sha256']['tools/optimization/worker.py']='0'*64
        with self.assertRaises(RuntimeError):self.validate()

    def test_scheduler_command_requires_same_explicit_source_options(self):
        self.job['cmd']=shlex.join(['/bin/bash',str(self.root/'worker10.sh')])
        with self.assertRaises(RuntimeError):self.validate()

    def test_insufficient_time_rejected(self):
        with self.assertRaises(RuntimeError):entry.deadline(self.job,self.now+14000)

    def test_bounded_wait_does_not_query_scheduler(self):
        class Absent:
            def exists(self):return False
            def is_symlink(self):return False
        with patch.object(entry.time,'monotonic',side_effect=[0,181]),patch.object(entry.time,'sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError,'bounded180'):entry.read_record(Absent())
            sleep.assert_not_called()


class ParentIsolation(unittest.TestCase):
    def test_shell_requires_reviewed_source_and_uses_its_build_pin_tool(self):
        script=(HERE/'worker10.sh').read_text()
        self.assertIn('"$3" != --expected-source-head',script)
        self.assertIn('$task_source/tools/pin_build.py',script)
        self.assertIn('--source "$task_source" --expected-source-head "$task_source_head"',script)
    def test_no_ctypes_or_dlopen_in_parent_files(self):
        for name in ('worker10_entry.py','worker10_preflight.py'):
            tree=ast.parse((HERE/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertNotIn('ctypes',[v.name for v in node.names])
                if isinstance(node,ast.ImportFrom):self.assertNotEqual(node.module,'ctypes')
                if isinstance(node,ast.Attribute):self.assertNotIn(node.attr,('CDLL','dlopen'))

    def test_parent_mask_change_or_gomp_load_rejected(self):
        for module in (entry,preflight):
            with patch.object(os,'sched_getaffinity',return_value=set(range(592)),create=True),patch.object(Path,'read_text',return_value=''):
                self.assertEqual(len(module.parent_state(list(range(592)))['cpus']),592)
            with patch.object(os,'sched_getaffinity',return_value={0},create=True),patch.object(Path,'read_text',return_value=''):
                with self.assertRaises(RuntimeError):module.parent_state(list(range(592)))
            with patch.object(os,'sched_getaffinity',return_value=set(range(592)),create=True),patch.object(Path,'read_text',return_value='0-1 /fake/libgomp.so.1'):
                with self.assertRaises(RuntimeError):module.parent_state(list(range(592)))

    def preflight_case(self,fail=None):
        import subprocess,sys
        cpus=list(range(592))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'probes').mkdir();(root/'probes/hbw_probe').write_bytes(b'fixture-probe')
            (root/'worker2-preflight').mkdir();(root/'worker2-preflight/result.json').write_text(json.dumps(dict(binary_sha256=preflight.sha(root/'probes/hbw_probe'))))
            (root/'worker10_runtime_probe.py').write_bytes(b'child-only-fixture')
            calls=[]
            def fake_run(argv,**kwargs):
                calls.append(argv)
                if 'probe_host.py' in argv[1]:
                    data=dict(host='cn19486',machine='aarch64',sve_vector_bytes=64,allowed_cpus=[0] if fail=='host-mask' else cpus)
                    return subprocess.CompletedProcess(argv,0,json.dumps(data),'')
                if 'worker10_runtime_probe.py' in argv[1]:
                    data=dict(complete=True,passed=True,host='cn19486',before_load_cpus=cpus,after_load_cpus=[0])
                    return subprocess.CompletedProcess(argv,1 if fail=='runtime-exit' else 0,json.dumps(data),'diagnostic' if fail else '')
                self.assertIn('run_numa.py',argv[1])
                lines=[dict(rank=i,available=1,allocated=True,sdk_verify=1,query_rc=0,nodes=[16+i]) for i in range(16)]
                return subprocess.CompletedProcess(argv,0,'\n'.join('HBW_PROBE '+json.dumps(v) for v in lines),'')
            real_read=Path.read_text
            def read(path,*args,**kwargs):return '' if path.as_posix()=='/proc/self/maps' else real_read(path,*args,**kwargs)
            with patch.object(os,'sched_getaffinity',return_value=set(cpus),create=True),patch.object(Path,'read_text',read),\
                 patch.object(preflight.socket,'gethostname',return_value='cn19486'),patch.object(preflight.subprocess,'run',side_effect=fake_run),\
                 patch.dict(os.environ,LQCD_OPT_ALLOCATION='mg-opt-20261103-worker10'),\
                 patch.object(sys,'argv',['worker10_preflight.py','--root',str(root),'--expected-affinity-sha256',preflight.affinity_sha(cpus),'--source',str(root)]):
                if fail:
                    with self.assertRaises(Exception):preflight.main()
                else:preflight.main()
            output=root/'worker10-preflight'
            if fail:
                self.assertFalse((output/'result.json').exists())
                self.assertFalse(json.loads((output/'failure.json').read_text())['complete'])
                self.assertTrue((output/'host-stage.json').exists())
                self.assertEqual(len(calls),1 if fail=='host-mask' else 2)
            else:
                self.assertTrue(json.loads((output/'result.json').read_text())['complete'])
                self.assertEqual(len(calls),3)
                for name in ('host','runtime','hbw'):
                    stage=json.loads((output/(name+'-stage.json')).read_text())
                    self.assertEqual(stage['before_parent_state']['cpus'],cpus)
                    self.assertEqual(stage['after_parent_state']['cpus'],cpus)

    def test_runtime_child_can_pin_itself_while_parent_retains592(self):self.preflight_case()
    def test_host1cpu_failure_keeps_evidence_and_stops(self):self.preflight_case('host-mask')
    def test_runtime_failure_keeps_evidence_and_stops_before_hbw(self):self.preflight_case('runtime-exit')

    def test_entry_does_not_mark_success_when_preflight_fails(self):
        self.entry_case(False)

    def test_successful_entry_executes_only_queue10(self):
        self.entry_case(True)

    def test_final_execv_exact_worker_queue10_lifetime_and_idle_arguments(self):
        executable,argv=self.entry_case(True)
        import sys
        self.assertEqual(executable,sys.executable)
        self.assertEqual(argv[0],sys.executable)
        self.assertEqual(argv[1],'-u')
        self.assertEqual(Path(argv[2]).parts[-3:],('tools','optimization','worker.py'))
        self.assertEqual(Path(argv[4]).name,'queue10')
        self.assertEqual(argv[3:],['--queue',argv[4],'--lifetime','14070','--idle-timeout','3600'])
        self.assertNotIn('queue8',[Path(value).name for value in argv])

    def entry_case(self,success):
        import subprocess,sys
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';(source/'tools/optimization').mkdir(parents=True)
            (source/'tools/optimization/process_tree.py').write_text("TASK_KEY='LQCD_OPT_TASK_ID'\ndef tagged_processes(*args):return []\n")
            (source/'tools/optimization/worker.py').write_text('# fixture')
            (root/'worker10-allocation.json').write_text('{}')
            job=dict(startTime='2026-11-04T04:30:00Z',jobWallClockLimit=14400)
            def git(argv):return '1'*40+'\n' if argv[-2:]==['rev-parse','HEAD'] else ''
            def child(argv,**kwargs):
                if not success:raise subprocess.CalledProcessError(1,['preflight'])
                self.assertIn('worker10_preflight.py',argv[1])
                (root/'worker10-preflight').mkdir()
                (root/'worker10-preflight/result.json').write_text(json.dumps(dict(complete=True,passed=True)))
                return subprocess.CompletedProcess(argv,0)
            with patch.object(entry,'read_record',return_value=dict(scheduler_job='2022000')),patch.object(entry,'validate_record',return_value=job),\
                 patch.object(entry,'run',side_effect=git),patch.object(entry,'parent_state',return_value=dict(cpus=list(range(592)))),\
                 patch.object(os,'sched_getaffinity',return_value=set(range(592)),create=True),\
                 patch.object(entry.socket,'gethostname',return_value='cn19486'),patch.object(entry.time,'time',return_value=entry.epoch(job['startTime'])+30),\
                 patch.object(entry.subprocess,'run',side_effect=child),\
                 patch.dict(os.environ,LQCD_OPT_ALLOCATION='mg-opt-20261103-worker10'),\
                 patch.object(sys,'argv',['worker10_entry.py','--root',str(root),'--previous-job','2023152','--source',str(source),'--expected-source-head','1'*40]),\
                 patch.object(os,'execv') as execute:
                if success:
                    entry.main()
                    argv=execute.call_args.args[1]
                    execute.assert_called_once_with(sys.executable,[sys.executable,'-u',
                        str(source/'tools/optimization/worker.py'),'--queue',str(root/'queue10'),
                        '--lifetime','14070','--idle-timeout','3600'])
                else:
                    with self.assertRaises(subprocess.CalledProcessError):entry.main()
                    execute.assert_not_called()
            self.assertEqual((root/'worker10-startup.json').exists(),success)
            self.assertFalse(json.loads((root/'worker10-startup-attempt.json').read_text())['complete'])
            if success:self.assertTrue(json.loads((root/'worker10-startup.json').read_text())['complete'])
            else:self.assertFalse(json.loads((root/'worker10-startup-failure.json').read_text())['complete'])
            return execute.call_args.args if success else None


if __name__ == '__main__':
    unittest.main()
