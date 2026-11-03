"""Stdlib checks for benchmark provenance and durable worker termination."""
import copy
import argparse
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
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / 'optimization' / (name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench, worker = load('bench_full12'), load('worker')


class BenchmarkContractTest(unittest.TestCase):
    def test_reject_helper_hash_or_duplicate_columns_before_publishing_pass(self):
        for fault in ('digest','columns'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                args,report=self.verification_run(root)
                def helper(argv,**kwargs):
                    self.verifier_result(args,report,argv,**kwargs)
                    evidence=Path(argv[-1])/'verification.json'
                    row=json.loads(evidence.read_text())
                    if fault=='digest':row['propagator_sha256']='0'*64
                    else:row['columns'][1]=row['columns'][0].copy()
                    bench.atomic(evidence,row)
                with mock.patch.object(bench.subprocess,'run',side_effect=helper):
                    with self.assertRaisesRegex(RuntimeError,'digests differ|unique spin/color'):
                        bench.verify(args)
                self.assertFalse(json.loads((root/'result.json').read_text())['verification']['complete'])
                self.assertTrue((root/'independent/verification.json').is_file())

    def verification_run(self, root):
        reference, extractor = root/'reference', root/'extractor'
        prop, gauge = root/'propagator.npy', root/'gauge_rank00000.npy'
        for index, path in enumerate([reference, extractor, prop, gauge]):
            path.write_bytes(f'frozen artifact {index}'.encode())
        report = dict(measurements_complete=True, complete=True,
            propagator_sha256=bench.sha(prop), output_gauge_files=[[0,bench.sha(gauge)]],
            verification=dict(complete=False, passed=False))
        bench.atomic(root/'result.json', report)
        args = SimpleNamespace(verify=str(root), reference=str(reference), extractor=str(extractor),
                               verification_output='independent')
        return args, report

    def verifier_result(self, args, report, argv, **kwargs):
        # An orchestration fixture, not a substitute numerical oracle. Assert
        # that retry invokes the same fixed full12 verifier and executables.
        self.assertEqual(argv[:2], [sys.executable, str(ROOT/'benchmarks/runtime/verify_fixture_propagator.py')])
        self.assertEqual(argv[2:5], [str(Path(args.verify).resolve()), args.reference, args.extractor])
        self.assertTrue(kwargs['check'])
        output = Path(argv[-1])
        output.mkdir(exist_ok=False)
        independent = dict(complete=True, columns=[dict(source_spin=i//3, source_color=i%3,
            residual=4e-9) for i in range(12)], reference_sha256=bench.sha(args.reference),
            propagator_sha256=report['propagator_sha256'], method='byte-only column extraction + independent scalar C++')
        bench.atomic(output/'verification.json', independent)

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

    def test_cached_verification_uses_named_evidence_and_accepts_legacy_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, report = self.verification_run(root)
            for name in ['independent', 'independent-retry']:
                (root/name).mkdir()
                (root/name/'verification.json').write_bytes(name.encode())
            validation = dict(complete=True, passed=True, columns=12, max_true_residual=4e-9,
                reference_sha256=bench.sha(args.reference), extractor_sha256=bench.sha(args.extractor),
                evidence_sha256=bench.sha(root/'independent-retry/verification.json'),
                evidence_relative_path='independent-retry/verification.json',
                verification_driver_sha256='a'*64, propagator_sha256=report['propagator_sha256'])
            report['verification'] = validation
            bench.check_cached_verification(root, report, args.reference, args.extractor)
            # Driver provenance is historical bookkeeping, not a requirement
            # that an already accepted report was made by today's Python file.
            self.assertNotEqual(validation['verification_driver_sha256'], bench.sha(bench.__file__))
            target = root/'independent-retry/verification.json'
            original = target.read_bytes()
            target.write_bytes(b'changed named evidence')
            with self.assertRaises(RuntimeError):
                bench.check_cached_verification(root, report, args.reference, args.extractor)
            target.write_bytes(original)
            validation.pop('evidence_relative_path')
            validation.pop('verification_driver_sha256')
            validation['evidence_sha256'] = bench.sha(root/'independent/verification.json')
            bench.check_cached_verification(root, report, args.reference, args.extractor)

    def test_verification_paths_reject_unsafe_names_and_cached_escapes(self):
        for name in ['', '.', '..', '../retry', '/retry', 'retry/child', r'retry\child',
                     'retry.name', 'C:retry', 'UPPER', 'a'*81]:
            with self.subTest(name=name), self.assertRaises(argparse.ArgumentTypeError):
                bench.verification_output_name(name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, report = self.verification_run(root)
            report['verification'] = dict(complete=True, passed=True, columns=12,
                max_true_residual=4e-9, reference_sha256=bench.sha(args.reference),
                extractor_sha256=bench.sha(args.extractor), evidence_sha256='a'*64,
                propagator_sha256=report['propagator_sha256'])
            for relative in ['', '../verification.json', '/tmp/verification.json',
                             'C:/tmp/verification.json', 'retry/../verification.json',
                             'retry/child/verification.json', './retry/verification.json',
                             r'retry\verification.json', 'retry/other.json']:
                with self.subTest(relative=relative), self.assertRaises(RuntimeError):
                    bench.check_cached_verification(root, {**report,'verification':{
                        **report['verification'],'evidence_relative_path':relative}},
                        args.reference, args.extractor)

    def test_verification_paths_reject_directory_and_evidence_symlinks(self):
        for kind in ['directory', 'file']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                run, outside = root/'run', root/'outside'
                run.mkdir(); outside.mkdir()
                (outside/'verification.json').write_bytes(b'external evidence')
                try:
                    if kind == 'directory':
                        (run/'retry').symlink_to(outside, target_is_directory=True)
                    else:
                        (run/'retry').mkdir()
                        (run/'retry/verification.json').symlink_to(outside/'verification.json')
                except OSError as failure:
                    self.skipTest(f'OS cannot create fixture symlink: {failure}')
                with self.assertRaisesRegex(RuntimeError, 'symlink|escape'):
                    bench.verification_evidence_path(run, 'retry/verification.json')

    def test_cli_rejects_output_escape_before_opening_measurement_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            process = subprocess.run([sys.executable, str(ROOT/'tools/optimization/bench_full12.py'),
                '--verify', str(root/'absent-run'), '--reference', 'unchanged-reference',
                '--extractor', 'unchanged-extractor', '--verification-output', '../escaped'],
                capture_output=True, text=True, timeout=10)
            self.assertEqual(process.returncode, 2)
            self.assertIn('single safe name', process.stderr)
            self.assertEqual(list(root.iterdir()), [])

    def test_failed_verification_is_retained_and_explicit_retry_uses_new_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, report = self.verification_run(root)
            original_report = (root/'result.json').read_bytes()
            checks = bench.check_saved_artifacts
            calls = 0
            def fail_postcheck(run, value):
                nonlocal calls
                checks(run, value)
                calls += 1
                if calls == 2:
                    raise RuntimeError('post-verification digest read rejected')
            def scalar(argv, **kwargs):
                self.verifier_result(args, report, argv, **kwargs)
            with mock.patch.object(bench.subprocess,'run',side_effect=scalar), \
                 mock.patch.object(bench,'check_saved_artifacts',side_effect=fail_postcheck):
                with self.assertRaisesRegex(RuntimeError, 'post-verification'):
                    bench.verify(args)
            old_evidence = (root/'independent/verification.json').read_bytes()
            self.assertEqual((root/'result.json').read_bytes(), original_report)
            with mock.patch.object(bench.subprocess,'run') as runner:
                with self.assertRaisesRegex(RuntimeError, 'retained'):
                    bench.verify(args)
                runner.assert_not_called()
            args.verification_output = 'independent-retry'
            with mock.patch.object(bench.subprocess,'run',side_effect=scalar):
                bench.verify(args)
            saved = json.loads((root/'result.json').read_text())
            self.assertEqual((root/'independent/verification.json').read_bytes(), old_evidence)
            self.assertEqual(saved['propagator_sha256'], report['propagator_sha256'])
            self.assertEqual(saved['verification']['evidence_relative_path'], 'independent-retry/verification.json')
            self.assertEqual(saved['verification']['verification_driver_sha256'], bench.sha(bench.__file__))
            # The default cached call follows the accepted report's path rather
            # than attempting to overwrite the older failed directory.
            args.verification_output = 'independent'
            with mock.patch.object(bench.subprocess,'run') as runner:
                bench.verify(args)
                runner.assert_not_called()

    def test_retry_cannot_rebaseline_a_changed_frozen_propagator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, report = self.verification_run(root)
            original_report = (root/'result.json').read_bytes()
            def corrupt(argv, **kwargs):
                self.verifier_result(args, report, argv, **kwargs)
                (root/'propagator.npy').write_bytes(b'changed during scalar validation')
            with mock.patch.object(bench.subprocess,'run',side_effect=corrupt):
                with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
                    bench.verify(args)
            self.assertTrue((root/'independent/verification.json').is_file())
            args.verification_output = 'independent-retry'
            with mock.patch.object(bench.subprocess,'run') as runner:
                with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
                    bench.verify(args)
                runner.assert_not_called()
            self.assertEqual((root/'result.json').read_bytes(), original_report)
            self.assertFalse((root/'independent-retry').exists())

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
