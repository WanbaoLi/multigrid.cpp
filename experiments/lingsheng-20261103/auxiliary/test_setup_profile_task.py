"""Task description contracts only; no task is submitted or executed."""
import contextlib
import importlib.util
import io
import json
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('setup_profile_task',Path(__file__).with_name('queue_setup_profile.py'))
task=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(task)


class TaskContracts(unittest.TestCase):
    def test_emit_is_posix_bounded_and_never_a_ready_file_write(self):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            task.main(['--root','/remote/root','--aux-dir','/remote/root/aux-cold','--after-attempt','053-reviewed',
                '--python','/remote/python','--emit-task'])
        value=json.loads(stream.getvalue())
        self.assertEqual(value['argv'][1],'/remote/root/aux-cold/queue_setup_profile.py')
        self.assertEqual(value['cwd'],'/remote/root')
        self.assertEqual(value['timeout'],1000)
        self.assertNotIn('--emit-task',value['argv'])
        self.assertFalse(any('ready.json' in part for part in value['argv']))
        self.assertNotIn('\\',json.dumps(value['argv']))

    def test_x86_requires_ordinary_mode_and_retains_explicit_dependency(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            task.main(['--backend','x86','--after-attempt','001-canonical','--emit-task'])
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            task.main(['--root','/x86/root','--aux-dir','/x86/root/aux-cold','--backend','x86',
                '--ordinary','--after-attempt','001-canonical','--allocation','node5005-cold','--emit-task'])
        value=json.loads(stream.getvalue())
        self.assertIn('--ordinary',value['argv'])
        self.assertEqual(value['argv'][value['argv'].index('--after-attempt')+1],'001-canonical')

    def test_validated_diagnostic_dependency_does_not_require_ingested_report(self):
        with tempfile.TemporaryDirectory() as value:
            root=Path(value);attempt=root/'attempts/053-best-profile';run=attempt/'measurements/full12'
            (run/'independent').mkdir(parents=True)
            library=root/'lib.so';library.write_bytes(b'library')
            digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
            validation=dict(complete=True,passed=True,columns=12,reference_sha256='b'*64,
                max_true_residual=5e-9,solution_relative_error=1e-7)
            report=dict(complete=True,measurements_complete=True,timing_scope='profile_full12_api',verification=validation,
                source_manifest_sha256='a'*64,library_sha256=digest(library),library_path=str(library),input_sha256='c'*64,
                samples=[dict(stats=[dict(converged=True,true_residual=5e-9) for _ in range(12)])])
            report_path=run/'result.json';report_path.write_text(json.dumps(report))
            record=dict(snapshot=dict(source_manifest_sha256='a'*64))
            (attempt/'attempt.json').write_text(json.dumps(record))
            state_path=root/'053-state.json'
            state=dict(complete=True,cleanup=dict(complete=True),host='compute',allocation='job',report=str(report_path),
                report_sha256=digest(report_path),verification=validation,source_manifest_sha256='a'*64,library_sha256=digest(library))
            state_path.write_text(json.dumps(state))
            evidence=run/'independent/verification.json'
            evidence.write_text(json.dumps(dict(complete=True,columns=[dict(source_spin=i//3,source_color=i%3,residual=5e-9) for i in range(12)])))
            def require(condition,message):
                if not condition:raise RuntimeError(message)
            ledger=SimpleNamespace(read=lambda p:json.loads(Path(p).read_text()),digest=digest,require=require,
                check_snapshot=mock.Mock(),checked_attempt=mock.Mock(side_effect=AssertionError('Diagnostic is not ingested')))
            verifier=SimpleNamespace(check_cached_verification=mock.Mock(),verification_evidence_path=lambda *args:evidence)
            with mock.patch.object(task,'load',return_value=verifier):
                result,provenance=task.dependency_report(ledger,root,'053-best-profile',
                    dict(reference_sha256='b'*64,input_sha256='c'*64),'compute','job','arm',state_path,root/'verifier.py')
                self.assertEqual(result['timing_scope'],'profile_full12_api')
                self.assertFalse(provenance['rank_eligible'])
                ledger.checked_attempt.assert_not_called()
                ledger.check_snapshot.assert_called_once()
                verifier.check_cached_verification.assert_called_once()
                state['report_sha256']='0'*64;state_path.write_text(json.dumps(state))
                with self.assertRaisesRegex(RuntimeError,'report SHA changed'):
                    task.dependency_report(ledger,root,'053-best-profile',dict(reference_sha256='b'*64,input_sha256='c'*64),
                        'compute','job','arm',state_path,root/'verifier.py')


if __name__=='__main__':unittest.main()
