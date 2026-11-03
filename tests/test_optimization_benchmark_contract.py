"""Stdlib checks for benchmark provenance and durable worker termination."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / 'optimization' / (name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench, worker = load('bench_full12'), load('worker')


class BenchmarkContractTest(unittest.TestCase):
    def test_fixture_rejects_changed_physics_or_preprocessing(self):
        good = dict(complete=True, mass=-.277, csw=1.160920226,
            lattice_xyzt=[24,24,24,64], grid_xyzt=[1,1,1,16],
            normalization='mass', source_xyzt=[0,0,0,0], source_scale=1.,
            gamma_basis='DeGrand-Rossi', fermion_t_boundary=-1, gauge_t_boundary=1,
            gauge_reunitarized=False, stout=dict(steps=1,rho=.125,dir_ignore=4),
            gauge_sha256='a'*64)
        bench.validate_fixture(good)
        provenance=bench.fixture_metadata({**good, 'first_seconds':103.,
            'steady_median_seconds':103.,'complete':True,'verification':{'passed':True}})
        self.assertEqual(provenance['mass'],good['mass'])
        self.assertEqual(provenance['stout'],good['stout'])
        for stale in ['first_seconds','steady_median_seconds','complete','verification']:
            self.assertNotIn(stale,provenance)
        for field, value in [('complete', False), ('mass', -.2), ('csw', 1.),
                             ('stout', dict(steps=0,rho=.125,dir_ignore=4)),
                             ('fermion_t_boundary', 1), ('normalization', 'kappa'),
                             ('lattice_xyzt', [8,8,8,8]), ('grid_xyzt', [1,1,1,3])]:
            with self.subTest(field=field):
                with self.assertRaises(RuntimeError):
                    bench.validate_fixture({**good, field:value})

    def test_cached_flags_cannot_masquerade_as_dynamic_cases(self):
        plan = {'cases':[{'id':'baseline','threads':37,'batch':2,
                          'environment':{'LQCD_GCR_FUSED':1}}]}
        bench.validate_plan(plan, {'LQCD_GCR_FUSED'})
        for flag in ['LQCD_ARM_SVE_PLANNED','LQCD_COARSE_FUSED','OMP_WAIT_POLICY']:
            bad = copy.deepcopy(plan)
            bad['cases'][0]['environment'] = {flag:1}
            with self.assertRaises(RuntimeError):
                bench.validate_plan(bad, {'LQCD_GCR_FUSED'})

    def test_diagnostic_environment_does_not_leak_between_cases(self):
        original = dict(os.environ)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(original)))
        base = {'FIXED':'yes'}
        bench.apply_case_environment(base, {'batch':2,'environment':{'LQCD_COARSE_CGS2':1}}, diagnostic=True)
        self.assertEqual(os.environ['LQCD_COARSE_CGS2'], '1')
        bench.apply_case_environment(base, {'batch':1}, diagnostic=True)
        self.assertNotIn('LQCD_COARSE_CGS2', os.environ)
        self.assertEqual(os.environ['LQCD_VERBOSE'], '1')

    def test_inherited_solve_tuning_cannot_silently_change_setup(self):
        original=dict(os.environ)
        self.addCleanup(lambda:(os.environ.clear(),os.environ.update(original)))
        os.environ['LQCD_MG_SAP_STEPS']='31'
        bench.apply_context_environment({'LQCD_COARSE_FUSED':1},{'LQCD_MG_SAP_STEPS'})
        self.assertNotIn('LQCD_MG_SAP_STEPS',os.environ)
        self.assertEqual(os.environ['LQCD_COARSE_FUSED'],'1')

    def test_fixed_placement_and_setup_allow_smaller_solve_teams(self):
        plan = dict(placement_threads=37,setup_threads=37,cases=[
            dict(id='full',threads=37,batch=2),dict(id='reduced',threads=16,batch=2)])
        bench.validate_plan(plan,set())
        for key,value in [('placement_threads',32),('setup_threads',38),
                          ('placement_threads',0),('setup_threads',True)]:
            with self.subTest(key=key,value=value):
                with self.assertRaises(RuntimeError):
                    bench.validate_plan({**plan,key:value},set())

    def test_context_runtime_options_cannot_override_managed_placement_or_timing(self):
        plan=dict(cases=[dict(id='base',threads=37,batch=2)])
        bench.validate_plan({**plan,'context_environment':{'OMP_WAIT_POLICY':'passive'}},set())
        for key,value in [('OMP_NUM_THREADS',1),('OMP_PLACES','threads'),
                          ('LQCD_VERBOSE',1),('LQCD_HALO_PROFILE',1),
                          ('LQCD_ARM_SVE',True),('LQCD_ARM_SVE',float('nan'))]:
            with self.subTest(key=key,value=value):
                with self.assertRaises(RuntimeError):
                    bench.validate_plan({**plan,'context_environment':{key:value}},set())

    def test_cached_verification_rechecks_all_saved_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'independent').mkdir()
            paths = [root/'reference', root/'extractor', root/'propagator.npy',
                     root/'gauge_rank00000.npy', root/'independent'/'verification.json',
                     root/'baseline.npy']
            for i,path in enumerate(paths):
                path.write_bytes(f'frozen {i}'.encode())
            reference, extractor, prop, gauge, evidence, baseline = paths
            report = dict(propagator_sha256=bench.sha(prop), output_gauge_files=[[0,bench.sha(gauge)]],
                reference_propagator=str(baseline), verification=dict(complete=True, passed=True,columns=12,
                    max_true_residual=4e-9, reference_sha256=bench.sha(reference),
                    extractor_sha256=bench.sha(extractor), evidence_sha256=bench.sha(evidence),
                    propagator_sha256=bench.sha(prop), reference_propagator_sha256=bench.sha(baseline)))
            bench.check_cached_verification(root, report, reference, extractor)
            for path in paths:
                with self.subTest(path=path.name):
                    original = path.read_bytes()
                    path.write_bytes(b'changed after validation')
                    with self.assertRaises(RuntimeError):
                        bench.check_cached_verification(root, report, reference, extractor)
                    path.write_bytes(original)

    def test_nonfinite_timeouts_and_shell_strings_are_rejected(self):
        for timeout in [float('nan'), float('inf'), -1, 0, 101]:
            with self.assertRaises(RuntimeError):
                worker.validate_task({'timeout':timeout,'argv':['true']},100)
        with self.assertRaises(RuntimeError):
            worker.validate_task({'timeout':1,'argv':'sh -c something'},100)
        self.assertEqual(worker.validate_task({'timeout':1,'argv':['true']},100),1)

    def test_termination_waits_and_escalates_before_return(self):
        process = mock.Mock(pid=12345)
        result = dict(complete=True,surviving_pids=[])
        with mock.patch.object(worker.process_tree,'terminate_owned',return_value=result) as cleanup:
            self.assertIs(worker.terminate_group(process,grace=0,tag='owned'),result)
        cleanup.assert_called_once_with(process,worker.process_tree.TASK_KEY,'owned',0)

    @unittest.skipUnless(os.name == 'posix','Linux queue worker lifecycle')
    def test_sigterm_retains_interrupted_claim_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'001.ready.json').write_text(json.dumps(dict(timeout=20,
                argv=[sys.executable,'-c','import time; time.sleep(20)'])))
            process = subprocess.Popen([sys.executable,str(ROOT/'tools/optimization/worker.py'),
                '--queue',str(root),'--lifetime','30','--idle-timeout','5'],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            try:
                deadline = time.monotonic()+5
                status = {}
                while time.monotonic()<deadline:
                    if (root/'001.status.json').exists():
                        status = json.loads((root/'001.status.json').read_text())
                        if status.get('pid'):
                            break
                    time.sleep(.02)
                self.assertIn('pid',status)
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=15)
                final = json.loads((root/'001.status.json').read_text())
                self.assertEqual(final['status'],'interrupted')
                self.assertTrue((root/'001.running.json').exists())
                self.assertFalse((root/'001.finished.json').exists())
                with self.assertRaises(ProcessLookupError):
                    os.kill(status['pid'],0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    @unittest.skipUnless(sys.platform.startswith('linux'),'Linux detached-session ownership lifecycle')
    def test_sigterm_cleans_nested_setsid_grandchild_without_touching_unrelated_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            grandchild = ("import os,signal,time; from pathlib import Path; "
                          "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                          "Path('grandchild.pid').write_text(str(os.getpid())); time.sleep(60)")
            middle = ("import os,subprocess,sys,time; from pathlib import Path; "
                      f"subprocess.Popen([sys.executable,'-c',{grandchild!r}],start_new_session=True); "
                      "Path('middle.pid').write_text(str(os.getpid())); time.sleep(60)")
            task = ("import os,subprocess,sys,time; from pathlib import Path; "
                    f"subprocess.Popen([sys.executable,'-c',{middle!r}],start_new_session=True); "
                    "Path('task.pid').write_text(str(os.getpid())); time.sleep(60)")
            (root/'001.ready.json').write_text(json.dumps(dict(timeout=50,cwd=str(root),
                environment={'LQCD_OPT_TASK_ID':'caller-supplied-must-be-replaced'},
                argv=[sys.executable,'-c',task])))
            unrelated = subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)
            process = subprocess.Popen([sys.executable,str(ROOT/'tools/optimization/worker.py'),
                '--queue',str(root),'--lifetime','60','--idle-timeout','5'],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            owned = []
            try:
                deadline = time.monotonic()+8
                pidfiles = [root/f'{name}.pid' for name in ['task','middle','grandchild']]
                while time.monotonic()<deadline and not all(p.exists() and p.stat().st_size for p in pidfiles):
                    time.sleep(.03)
                self.assertTrue(all(p.exists() and p.stat().st_size for p in pidfiles))
                owned = [int((root/f'{name}.pid').read_text()) for name in ['task','middle','grandchild']]
                self.assertEqual(len({os.getsid(pid) for pid in owned}),3)
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=20)
                final = json.loads((root/'001.status.json').read_text())
                self.assertEqual(final['status'],'interrupted')
                self.assertNotEqual(final['task_tag'],'caller-supplied-must-be-replaced')
                self.assertTrue(final['cleanup']['complete'])
                self.assertGreaterEqual(final['cleanup']['kill_signals'],1)
                self.assertTrue((root/'001.running.json').exists())
                self.assertFalse((root/'001.finished.json').exists())
                for pid in owned:
                    with self.assertRaises(ProcessLookupError):
                        os.kill(pid,0)
                self.assertIsNone(unrelated.poll())
            finally:
                if process.poll() is None:
                    process.kill();process.communicate()
                for pid in owned:
                    try:os.kill(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                unrelated.kill();unrelated.wait()


if __name__=='__main__':
    unittest.main()
