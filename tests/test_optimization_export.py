"""Synthetic evidence export contracts; these are not solver performance tests."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('optimization_export',ROOT/'tools/optimization/export_evidence.py')
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)
ledger = exporter.ledger


class ExportTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base/'campaign'
        self.root.mkdir()
        for name in ['attempts','events','best-history']:
            (self.root/name).mkdir()
        self.reference = self.base/'frozen-reference'
        self.reference.mkdir()
        for name in ['SKILL.md','manifest.json','a.md','b.md','c.md','evidence.json']:
            (self.reference/name).write_text('Frozen reference '+name,encoding='utf-8')
        self.config = dict(schema=1,objective='full12_api_wall_seconds',reference_skill=str(self.reference),
            reference_manifest=ledger.tree_manifest(self.reference),input_sha256='a'*64,
            reference_sha256='b'*64,residual_limit=1e-8,solution_relative_error_limit=1e-6,
            minimum_gain=.03,maximum_relative_spread=.10,minimum_steady_samples=3)
        ledger.atomic(self.root/'campaign.json',self.config)

    def attempt(self,name='best',active=False):
        path = self.root/'attempts'/name
        (path/'source').mkdir(parents=True)
        (path/'source/main.cpp').write_text('int main() {return 0;}\n')
        source_manifest = dict(git_head='frozen-head',files=[dict(path='main.cpp',
            sha256=ledger.digest(path/'source/main.cpp'),bytes=(path/'source/main.cpp').stat().st_size)])
        ledger.atomic(path/'source-manifest.json',source_manifest)
        with tarfile.open(path/'source.tar.gz','w:gz') as stream:
            stream.add(path/'source/main.cpp',arcname='main.cpp')
        data = dict(id=name,status='snapshotted' if active else 'best',proposal=dict(
            hypothesis='Reuse fine coefficients',change='One profile-led change',mechanism='Less traffic'),
            stages={'benchmark':dict(status='running' if active else 'passed',argv=['python','bench.py'],
                env_overrides={'OMP_NUM_THREADS':'32','PRIVATE_TOKEN':'do-not-export-this'},
                prior_runs=[dict(env_overrides={'UNLISTED_VALUE':'private-previous-run'})])},
            snapshot=dict(source_manifest_sha256=ledger.digest(path/'source-manifest.json'),
                archive_sha256=ledger.digest(path/'source.tar.gz')))
        ledger.atomic(path/'plan.json',dict(context_environment={'OMP_WAIT_POLICY':'active',
            'CUSTOM_SECRET':'hidden-plan-secret'},cases=[dict(threads=32)]))
        (path/'benchmark-000.log').write_text('PRIVATE_TOKEN=hidden-log-value\ncomplete twelve columns\n')
        (path/'source.diff').write_text('')
        (path/'build').mkdir()
        (path/'build'/'large.npy').write_bytes(b'not bundled')
        run = path/'measurements'/'full12'
        independent = run/'independent'
        independent.mkdir(parents=True)
        (run/'propagator.npy').write_bytes(b'large scientific data must not be read')
        (run/'gauge_rank00000.npy').write_bytes(b'gauge data')
        columns = [dict(source_spin=i//3,source_color=i%3,residual=5e-9) for i in range(12)]
        verification = dict(complete=True,columns=columns,reference_sha256='b'*64,
            propagator_sha256='e'*64,method='independent scalar C++')
        ledger.atomic(independent/'verification.json',verification)
        for i in range(12):
            (independent/f'column{i}.log').write_text('true relative residual 5e-9\n')
            (independent/f'verified{i}.residual').write_text('5e-9\n')
        report = dict(complete=True,measurements_complete=True,timing_scope='full12_api',
            zero_initial_guess=True,input_sha256='a'*64,
            source_manifest_sha256=data['snapshot']['source_manifest_sha256'],
            library_sha256='c'*64,propagator_sha256='e'*64,saved_gauge_sha256=['f'*64],
            comparison_key=dict(host='test',allocation='same'),configuration=dict(threads=32),
            samples=[dict(repeat=i,warmup=i==0,wall_seconds=10.+i*.01,
                stats=[dict(converged=True,true_residual=5e-9,iterations=24) for _ in range(12)]) for i in range(4)],
            verification=dict(complete=True,passed=True,columns=12,max_true_residual=5e-9,
                reference_sha256='b'*64,propagator_sha256='e'*64,
                evidence_sha256=ledger.digest(independent/'verification.json')))
        if not active:
            (path/'artifacts').mkdir()
            (path/'artifacts/liblqcd_cpu.so').write_bytes(b'actual measured library')
            report['library_sha256'] = ledger.digest(path/'artifacts/liblqcd_cpu.so')
            data['report'] = dict(sha256=ledger.object_digest(report),library_sha256=report['library_sha256'])
            ledger.atomic(path/'report.json',report)
        ledger.atomic(run/'result.json',report)
        ledger.atomic(path/'attempt.json',data)
        return path

    def accept(self,name='best'):
        ledger.atomic(self.root/'best.json',dict(attempt=name,median_seconds=10.02))
        ledger.atomic(self.root/'best-history'/'old.json',dict(attempt='older'))
        ledger.atomic(self.root/'events'/'accept.json',dict(kind='promote',attempt=name))

    def test_read_only_small_export_retains_status_full12_and_best(self):
        path = self.attempt()
        self.attempt('ongoing',active=True)
        self.accept()
        before = exporter.fingerprint(sorted(p for p in self.root.rglob('*') if p.is_file()))
        output = self.base/'export'
        original_read = Path.read_bytes
        def no_arrays(target):
            self.assertNotEqual(target.suffix,'.npy','Exporter must not read scientific arrays')
            return original_read(target)
        with mock.patch.object(Path,'read_bytes',no_arrays):
            result = exporter.export(self.root,output)
        self.assertTrue(result['read_consistent'])
        self.assertTrue(result['ongoing'])
        self.assertFalse(result['errors'])
        self.assertEqual(before,exporter.fingerprint(sorted(p for p in self.root.rglob('*') if p.is_file())))
        self.assertFalse((self.root/'history-read.json').exists())
        self.assertFalse(list(self.root.rglob('seal.json')))
        self.assertEqual(len(list((output/'reference-skill').iterdir())),6)
        self.assertTrue((output/'best/source/main.cpp').is_file())
        self.assertEqual(ledger.digest(output/'best/liblqcd_cpu.so'),ledger.digest(path/'artifacts/liblqcd_cpu.so'))
        best = next(x for x in result['attempts'] if x['id']=='best')
        self.assertTrue(best['review']['complete_review_material'])
        self.assertFalse(best['review']['numerical_verification_rerun'])
        ongoing = next(x for x in result['attempts'] if x['id']=='ongoing')
        self.assertFalse(ongoing['payload_included'])
        self.assertTrue((output/'campaign/attempts/ongoing/attempt.json').is_file())
        self.assertTrue((output/'campaign/attempts/ongoing/plan.json').is_file())
        self.assertFalse((output/'campaign/attempts/ongoing/benchmark-000.log').exists())
        prop = next(x for x in result['entries'] if Path(x['source_path']).as_posix().endswith('best/measurements/full12/propagator.npy'))
        self.assertIsNone(prop['sha256'])
        self.assertEqual(prop['declared_sha256'],'e'*64)

    def test_private_values_removed_nested_fields_argv_and_logs_with_distinct_hashes(self):
        path = self.attempt();self.accept()
        data = ledger.read(path/'attempt.json')
        data['stages']['benchmark']['argv'] += ['--password','private-argument','TOKEN=private-assignment']
        ledger.atomic(path/'attempt.json',data)
        output = self.base/'export'
        result = exporter.export(self.root,output)
        for target in output.rglob('*'):
            if target.is_file() and target.suffix != '.gz':
                raw = target.read_bytes()
                for secret in [b'do-not-export-this',b'private-previous-run',b'hidden-plan-secret',
                               b'hidden-log-value',b'private-argument',b'private-assignment']:
                    self.assertNotIn(secret,raw,str(target))
        metadata = next(x for x in result['entries'] if x['source_path']==str(path/'attempt.json'))
        self.assertNotEqual(metadata['sha256'],metadata['export_sha256'])
        self.assertTrue(metadata['transformations'])

    def test_missing_or_changed_independent_evidence_never_claims_complete_material(self):
        path = self.attempt();self.accept()
        (path/'measurements/full12/independent/column11.log').unlink()
        result = exporter.export(self.root,self.base/'missing-log')
        self.assertTrue(result['attempts'][0]['review']['registered_report_contract'])
        self.assertFalse(result['attempts'][0]['review']['complete_review_material'])
        (path/'measurements/full12/independent/verification.json').write_text('{}\n')
        result = exporter.export(self.root,self.base/'changed-verification')
        self.assertFalse(result['attempts'][0]['review']['complete_review_material'])
        self.assertIn('digest mismatch',result['attempts'][0]['review']['errors'][0])

    def test_shared_interleaved_verification_is_linked_without_completing_parent(self):
        best = self.attempt();self.accept()
        parent = self.attempt('parent',active=True)
        original = best/'measurements/full12/independent'
        linked = parent/'measurements/candidate/independent'
        linked.parent.mkdir()
        original.rename(linked)
        result = exporter.export(self.root,self.base/'export')
        best_row = next(row for row in result['attempts'] if row['id']=='best')
        parent_row = next(row for row in result['attempts'] if row['id']=='parent')
        self.assertTrue(best_row['review']['complete_review_material'])
        self.assertFalse(parent_row['review']['registered_report_contract'])
        self.assertTrue(parent_row['running_checkpoint'])
        self.assertFalse(parent_row['payload_included'])
        self.assertTrue((self.base/'export/campaign/attempts/parent/measurements/candidate/independent/column11.log').is_file())

    def test_named_recovery_verification_supports_parent_lookup_and_rejects_unsafe_path(self):
        best = self.attempt();self.accept()
        parent = self.attempt('parent',active=True)
        original = best/'measurements/full12/independent'
        linked = parent/'measurements/candidate/validation-retry'
        linked.parent.mkdir()
        original.rename(linked)
        report = ledger.read(best/'report.json')
        report['verification']['evidence_relative_path'] = 'validation-retry/verification.json'
        ledger.atomic(best/'report.json',report)
        data = ledger.read(best/'attempt.json')
        data['report']['sha256'] = ledger.object_digest(report)
        ledger.atomic(best/'attempt.json',data)
        result = exporter.export(self.root,self.base/'named')
        best_row = next(row for row in result['attempts'] if row['id']=='best')
        self.assertTrue(best_row['review']['complete_review_material'])
        self.assertEqual(best_row['review']['independent_path'],str(linked/'verification.json'))
        report['verification']['evidence_relative_path'] = '../validation-retry/verification.json'
        ledger.atomic(best/'report.json',report)
        data['report']['sha256'] = ledger.object_digest(report)
        ledger.atomic(best/'attempt.json',data)
        result = exporter.export(self.root,self.base/'unsafe')
        best_row = next(row for row in result['attempts'] if row['id']=='best')
        self.assertFalse(best_row['review']['complete_review_material'])
        self.assertIn('Unsafe evidence path',best_row['review']['errors'][0])
        report['verification']['evidence_relative_path'] = 'validation-retry/verification.json'
        ledger.atomic(best/'report.json',report)
        data['report']['sha256'] = ledger.object_digest(report)
        ledger.atomic(best/'attempt.json',data)
        original_is_symlink = Path.is_symlink
        def simulate_symlink(target):
            return target == linked/'verification.json' or original_is_symlink(target)
        with mock.patch.object(Path,'is_symlink',simulate_symlink):
            result = exporter.export(self.root,self.base/'symlink')
        best_row = next(row for row in result['attempts'] if row['id']=='best')
        self.assertFalse(best_row['review']['complete_review_material'])
        self.assertFalse(any(row['included'] and row['source_path']==str(linked/'verification.json')
                             for row in result['entries']))

    def test_mutation_during_export_is_marked_inconsistent(self):
        self.attempt();self.accept()
        original = exporter.Exporter.write
        changed = False
        def write(instance,source,*args,**kwargs):
            nonlocal changed
            value = original(instance,source,*args,**kwargs)
            if Path(source).name=='best.json' and not changed:
                changed = True
                ledger.atomic(self.root/'events/new-event.json',dict(kind='conclude',attempt='best'))
            return value
        with mock.patch.object(exporter.Exporter,'write',write):
            result = exporter.export(self.root,self.base/'export')
        self.assertFalse(result['read_consistent'])
        self.assertNotEqual(result['metadata_before_sha256'],result['metadata_after_sha256'])

    def test_unsafe_source_archive_and_output_locations_are_rejected(self):
        path = self.attempt();self.accept()
        with self.assertRaisesRegex(ValueError,'outside'):
            exporter.export(self.root,self.root/'export')
        with self.assertRaisesRegex(ValueError,'outside'):
            exporter.export(self.root,self.reference/'export')
        with tarfile.open(path/'source.tar.gz','w:gz') as stream:
            item = tarfile.TarInfo('../escape')
            item.size = 1
            stream.addfile(item,io.BytesIO(b'x'))
        data = ledger.read(path/'attempt.json')
        data['snapshot']['archive_sha256'] = ledger.digest(path/'source.tar.gz')
        ledger.atomic(path/'attempt.json',data)
        result = exporter.export(self.root,self.base/'export')
        self.assertTrue(result['errors'])
        self.assertFalse((self.base/'escape').exists())
        self.assertFalse((self.base/'export/best/source/main.cpp').exists())

    def test_truncated_logs_and_modified_reference_remain_explicit(self):
        path = self.attempt();self.accept()
        (path/'measurements/full12/independent/column0.log').write_text('x'*4096)
        (self.reference/'a.md').write_text('changed frozen reference')
        result = exporter.export(self.root,self.base/'export',max_log_bytes=128)
        self.assertFalse(result['attempts'][0]['review']['complete_review_material'])
        self.assertTrue(any('reference' in x['error'].lower() for x in result['errors']))
        excerpt = next(x for x in result['entries'] if x['source_path'].endswith('column0.log'))
        self.assertLessEqual(excerpt['export_bytes'],128)
        self.assertNotEqual(excerpt['sha256'],excerpt['export_sha256'])


if __name__=='__main__':
    unittest.main()
