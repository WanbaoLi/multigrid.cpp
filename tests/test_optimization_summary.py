"""Read-only experience aggregation gates; synthetic data is not HPC evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('optimization_summary',ROOT/'tools/optimization/summarize.py')
summary=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(summary)
ledger=summary.ledger


class SummaryTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.root=self.directory/'campaign'
        self.root.mkdir()
        for name in ['attempts','events','best-history']:
            (self.root/name).mkdir()
        self.config=dict(objective='full12_api_wall_seconds',input_sha256='a'*64,
            reference_sha256='b'*64,residual_limit=1e-8,solution_relative_error_limit=1e-6,
            minimum_gain=.03,maximum_relative_spread=.10,minimum_steady_samples=3)
        ledger.atomic(self.root/'campaign.json',self.config)
        self.serial=0

    def add(self,name,status='measured',ingested=True,scope='full12_api',conclusion=None,
            values=(10.,10.1,9.9),group='host-one',stage_status='passed'):
        path=self.root/'attempts'/name
        path.mkdir()
        source='c'*64
        report=dict(complete=True,measurements_complete=True,timing_scope=scope,zero_initial_guess=True,
            input_sha256='a'*64,source_manifest_sha256=source,library_sha256='d'*64,
            library_path='/frozen/library.so',comparison_key=group,
            configuration=dict(ranks=16,threads=37,batch=2),
            samples=[dict(repeat=i,warmup=(i==0),wall_seconds=value,
                     stats=[dict(converged=1,true_residual=4.8e-9,iterations=24) for _ in range(12)])
                     for i,value in enumerate((11.,*values))],
            verification=dict(complete=True,passed=True,columns=12,reference_sha256='b'*64,
                              max_true_residual=4.9e-9,solution_relative_error=1e-7))
        data=dict(id=name,status=status,created='test',proposal=dict(bottleneck='Measured SAP profile',
            hypothesis='Reuse coefficient loads',change='One explicit change',mechanism='Cache reuse',
            history_links=['old/experience.md'],retry_conditions='New evidence is required'),
            snapshot=dict(source_manifest_sha256=source,git_head='test-head'),
            stages={'benchmark':dict(status=stage_status,argv=['profile','--profile-output','/profile/evidence'],
                                    log='benchmark-000.log')},conclusions=[])
        if conclusion:
            data['conclusions']=[dict(time='test',status=status,conclusion=conclusion,evidence=['profile.json'])]
        if ingested:
            data['report']=dict(sha256=ledger.object_digest(report),library_sha256=report['library_sha256'])
            ledger.atomic(path/'report.json',report)
        (path/'measurements'/'full12').mkdir(parents=True)
        ledger.atomic(path/'measurements'/'full12'/'result.json',report)
        ledger.atomic(path/'attempt.json',data)
        (path/'benchmark-000.log').write_text('profile or measurement evidence\n')
        return path

    def accept(self,name):
        self.serial+=1
        decision=dict(attempt=name,time='test',median_seconds=10.,kind='promote')
        ledger.atomic(self.root/'events'/f'{self.serial:03d}.json',decision)
        ledger.atomic(self.root/'best.json',{k:v for k,v in decision.items() if k!='kind'})

    def test_uningested_and_diagnostic_reports_never_complete_or_rank(self):
        self.add('accepted',status='best');self.accept('accepted')
        self.add('raw-complete',ingested=False)
        self.add('diagnostic',ingested=False,scope='profile_full12_api',status='inconclusive',conclusion='Profile only')
        self.add('bad-ingested-profile',scope='profile_full12_api')
        result=summary.collect(self.root)
        self.assertEqual(result['counts']['ingested_complete_full12'],1)
        self.assertEqual(result['counts']['rank_eligible'],1)
        ids={row['attempt'] for group in result['comparable_groups'].values() for row in group['rows']}
        self.assertEqual(ids,{'accepted'})
        raw=next(r for r in result['attempts'] if r['id']=='raw-complete')
        self.assertTrue(raw['unregistered_measurements'][0]['complete'])
        self.assertFalse(raw['unregistered_measurements'][0]['counted_as_completed'])

    def test_summary_is_read_only_and_lists_failures_blocked_and_unresolved(self):
        self.add('baseline',status='best');self.accept('baseline')
        self.add('control')
        self.add('failed',status='snapshotted',ingested=False,stage_status='timeout')
        self.add('blocked',status='blocked',ingested=False,conclusion='No allocated HBM nodes')
        before=summary.fingerprint(sorted(p for p in self.root.rglob('*') if p.is_file()))
        output=self.directory/'writable-experience'
        result=summary.write_summary(self.root,output)
        after=summary.fingerprint(sorted(p for p in self.root.rglob('*') if p.is_file()))
        self.assertEqual(before,after)
        self.assertEqual(result['counts']['failed'],1)
        self.assertEqual(result['counts']['blocked'],1)
        self.assertEqual(set(result['unresolved_attempts']),{'control','failed'})
        self.assertEqual(result['best']['attempt'],'baseline')
        text=(output/'experience.md').read_text(encoding='utf-8')
        self.assertIn('尚未记录结论',text)
        self.assertIn('--retry-interrupted',text)
        self.assertIn('rollback ACCEPTED_ID',text)
        self.assertTrue((output/'experience.json').is_file())
        self.assertFalse((self.root/'history-read.json').exists())
        with self.assertRaisesRegex(ValueError,'outside'):
            summary.write_summary(self.root,self.root/'accidental-output')

    def test_report_tampering_noise_and_cross_host_groups_are_explicit(self):
        corrupted=self.add('corrupted',status='best');self.accept('corrupted')
        report=ledger.read(corrupted/'report.json')
        report['samples'][1]['wall_seconds']=1.
        ledger.atomic(corrupted/'report.json',report)
        self.add('host-one',values=(8.,8.1,7.9))
        self.add('host-two',values=(3.,3.01,2.99),group='other-host')
        self.add('noisy',values=(3.,10.,20.))
        result=summary.collect(self.root)
        self.assertEqual(result['counts']['rank_eligible'],2)
        self.assertEqual(len(result['comparable_groups']),2)
        self.assertEqual(result['best']['attempt'],'corrupted')
        self.assertFalse(result['best_report_contract_valid'])
        noisy=next(r for r in result['attempts'] if r['id']=='noisy')
        self.assertTrue(noisy['complete_full12'])
        self.assertFalse(noisy['rank_eligible'])
        self.assertIn('digest changed',next(r for r in result['attempts'] if r['id']=='corrupted')['errors'][0])

    def test_best_and_rollback_history_retained_without_automatic_promotion(self):
        self.add('baseline',status='best');self.accept('baseline')
        self.add('faster',values=(8.,8.1,7.9));self.accept('faster')
        ledger.atomic(self.root/'best-history'/'001.json',dict(attempt='baseline',median_seconds=10.))
        ledger.atomic(self.root/'events'/'003.json',dict(kind='rollback',attempt='baseline',time='later',reason='Extended validation regression'))
        ledger.atomic(self.root/'best.json',dict(attempt='baseline',median_seconds=10.))
        result=summary.collect(self.root)
        self.assertEqual(result['best']['attempt'],'baseline')
        self.assertEqual([r['record']['kind'] for r in result['best_events']],['promote','promote','rollback'])
        self.assertEqual(result['best_history'][0]['record']['attempt'],'baseline')
        ranked=next(iter(result['comparable_groups'].values()))['rows']
        self.assertEqual(ranked[0]['attempt'],'faster')
        self.assertEqual(ledger.read(self.root/'best.json')['attempt'],'baseline')

    def test_inherited_fixture_timing_fields_cannot_replace_measured_samples(self):
        path=self.add('measured')
        report=ledger.read(path/'report.json')
        report.update(first_seconds=103.,second_seconds=103.,steady_median_seconds=103.,
                      max_true_residual=.5,solver_seconds=103.)
        ledger.atomic(path/'report.json',report)
        data=ledger.read(path/'attempt.json')
        data['report']['sha256']=ledger.object_digest(report)
        data['report']['median_seconds']=103. # A cached summary is not the data source either.
        ledger.atomic(path/'attempt.json',data)
        result=summary.collect(self.root)
        actual=result['attempts'][0]
        self.assertEqual(actual['performance']['median_seconds'],10.)
        self.assertEqual(actual['performance']['steady_samples'],[10.,10.1,9.9])
        self.assertNotIn('steady_median_seconds',actual['report'])
        self.assertTrue(actual['complete_full12'])


if __name__=='__main__':
    unittest.main()
