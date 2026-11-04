"""Offline provenance/argv/multi-case closure checks; no numerical execution."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import halo_v2_trial_publication_v3 as trial
import halo_publication_audit_v3 as audit
import phase6_halo as phase
import raw_protocol_publication_v2 as factory
import raw_controller_publication_v2 as dispatcher
import test_halo_v2_trial as previous
import os

H='1'*64
previous.trial=trial
packaged_evidence=Path(__file__).resolve().parent/'validation-evidence'
if packaged_evidence.is_dir():previous.ActualClosedEvidence.root=packaged_evidence


class Structure(unittest.TestCase):
    def test_numeric_scheduling_gcr_and_gates_unchanged(self):
        def methods(name):
            tree=ast.parse(Path(__file__).with_name(name).read_text(encoding='utf-8'))
            value=next(row for row in tree.body if isinstance(row,ast.ClassDef) and row.name=='Trial')
            return {row.name:row for row in value.body if isinstance(row,ast.FunctionDef)}
        old,new=methods('halo_v2_trial.py'),methods('halo_v2_trial_publication_v3.py')
        self.assertEqual(set(old),set(new))
        for name in old:
            if name=='unchanged':
                self.assertIsInstance(new[name].body[-1],ast.For)
                self.assertIn('fresh_publication_audits',ast.dump(new[name].body[-1]))
                new[name].body=new[name].body[:-1]
            for row in ast.walk(new[name]):
                if isinstance(row,ast.Constant) and row.value=='halo-v2-trial-publication-v3-helpers.json':
                    row.value='halo-v2-trial-helpers.json'
            if name!='benchmark':self.assertEqual(ast.dump(old[name]),ast.dump(new[name]),name)
        body=new['benchmark'].body
        start=next(i for i,row in enumerate(body) if isinstance(row,ast.ImportFrom) and row.module=='halo_publication_audit_v3')
        new['benchmark'].body=body[:start]+[body[-1]]
        for row in ast.walk(new['benchmark']):
            if isinstance(row,ast.Constant) and row.value=='independent-publication-v2':row.value='independent-derived'
        self.assertEqual(ast.dump(old['benchmark']),ast.dump(new['benchmark']))
        self.assertEqual(hashlib.sha256(Path(phase.__file__).read_bytes()).hexdigest(),trial.PHASE_SHA)
        self.assertEqual(hashlib.sha256(Path(__file__).with_name('halo_v2_trial.py').read_bytes()).hexdigest(),
            '0864909721d0f482c77a06b6a862ac98c9a4ef5de70330be9f9f3d0800ab4be9')


class DirectRouting(unittest.TestCase):
    def exercise(self,diagnostic):
        base=dict(context_environment={'LQCD_HBW_ALLOC':'require'},threads=32,batch=2,placement_threads=37,
            setup_threads=37,solve_environment={'LQCD_COARSE_BATCH_REDUCE':1})
        cases=phase.comparison_cases(base)
        if diagnostic:cases=cases[-1:]
        plan=phase.plan_for(base,cases)
        with tempfile.TemporaryDirectory() as directory:
            c=trial.Trial.__new__(trial.Trial);c.campaign=Path(directory);c.base=base;c.phase=phase
            c.args=SimpleNamespace(fixture=Path('/fixture'),reference=Path('/reference/multigrid'),auxiliary=Path('/aux'),
                helper_manifest={'files':factory.FILES})
            c.allocation='new-owned-allocation';c.state={};c.save=Mock();c.ledger=SimpleNamespace(atomic=Mock())
            captured=[];c.stage=lambda *args:captured.append(args)
            c.protocol=SimpleNamespace(benchmark_command=lambda *args,**kw:factory.benchmark_command(*args,verify=False,**kw))
            def read(path):
                case=next(value for value in cases if value['id']==path.parent.name)
                return dict(configuration=phase.configuration_for(base,plan,case),library_sha256=H,
                    verification=dict(complete=True,passed=True,columns=12,checksum_audit=dict(helper_wrapper_sha256=trial.DERIVED_SHA)),
                    samples=[dict(repeat=i,warmup=i==0) for i in range(4 if diagnostic else 8)])
            c.strict=SimpleNamespace(read=read,sha=lambda *args:H)
            with patch.object(audit,'warm',return_value={}) as checked:
                trial.Trial.benchmark(c,'test',dict(source='/snapshot',source_manifest_sha256=H),Path('/tested/lib.so'),plan,diagnostic)
            self.assertEqual(set(checked.call_args.args[2]),{row['id'] for row in cases})
            self.assertEqual(checked.call_args.kwargs['stage'],'diagnostic' if diagnostic else 'benchmark')
            options=SimpleNamespace(wrapper=Path('/aux/raw_benchmark_publication_v2.py'),wrapper_sha=factory.NEW_FILES['raw_benchmark_publication_v2.py'],
                helper_wrapper_sha=trial.DERIVED_SHA,reader_sha=factory.FILES['file_integrity.py'],benchmark_sha=factory.BENCHMARK_SHA)
            for _,key,argv,*_ in captured:
                argv=list(map(str,argv));self.assertEqual(sum(Path(v).name=='raw_benchmark_publication_v2.py' for v in argv),1)
                self.assertNotIn('/aux/raw_benchmark_v4.py',argv)
                command={'argv':argv};self.assertEqual(dispatcher.transform_stage(options,'/campaign','test',key,command),command)
                if '--verify' in argv:
                    self.assertEqual(argv[argv.index('--verification-output')+1],'independent-publication-v2')
                    self.assertEqual(argv[argv.index('--expected-helper-wrapper-sha')+1],trial.DERIVED_SHA)
            first=list(map(str,captured[0][2]));self.assertEqual(first[first.index('--repeats')+1],str(3 if diagnostic else 7))
            self.assertEqual(len(captured),1+len(cases))
    def test_two_cases_benchmark(self):self.exercise(False)
    def test_single_case_diagnostic(self):self.exercise(True)


class Cases(unittest.TestCase):
    def fixture(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup);attempt=Path(directory.name).resolve()
        names=['new-off','halo-on'];plan={'cases':[{'id':name} for name in names]}
        reports={name:dict(configuration=dict(ranks=2),propagator_sha256=H) for name in names}
        stage_audit=attempt/'checksum-audit/benchmark';docs={str(attempt/'plan.json'):plan}
        argv=['python','/aux/raw_benchmark_publication_v2.py','--benchmark','/snapshot/bench_full12.py',
            '--plan',str(attempt/'plan.json'),'--output',str(attempt/'measurements'),'--expected-wrapper-sha',H]
        docs[str(attempt/'attempt.json')]=dict(stages=dict(benchmark=dict(returncode=0,cleanup=dict(complete=True),argv=argv)))
        declarations=[dict(relative=name+'/propagator.npy',kind='npy-propagator',expected_sha256=None,bytes=2038431872) for name in names]
        eligibility=dict(output=str(attempt/'measurements'),declarations=declarations)
        module=SimpleNamespace(PROP_BYTES=2038431872,PROTOCOL='fresh-output-publication-v2')
        for rank in range(2):
            root=stage_audit.parent/(stage_audit.name+'-fresh-publication-v2')/('rank%05d'%rank)
            startup=dict(numeric_and_clock_bodies_unchanged=True,immutable_reader_unchanged=True,mode='benchmark',rank=rank,
                plan=dict(path=str(attempt/'plan.json'),sha256=H,cases=names) if rank==0 else None,
                eligibility=eligibility if rank==0 else None)
            items=[]
            if rank==0:
                for name in names:
                    items.append(dict(full_proof=dict(path=str(attempt/'measurements'/name/'propagator.npy'),eligibility=eligibility),
                        parent_protocol=dict(path=str(stage_audit/'rank00000/protocol.json'),startup_path=str(root/'startup.json'))))
            manifest=dict(complete=True,passed=True,protocol=module.PROTOCOL,rank=rank,entry_sha256=H,base_wrapper_sha256=H,
                publication_module_sha256=H,startup_sha256=H,published_outputs=items,parent_raw_artifacts={
                    name:dict(path=str(stage_audit/('rank%05d'%rank)/name),sha256=H) for name in ['protocol.json','manifest.json']})
            docs[str(root/'startup.json')]=startup;docs[str(root/'manifest.json')]=manifest
            for name in ['protocol.json','manifest.json']:docs[str(stage_audit/('rank%05d'%rank)/name)]={'complete':True}
        for name in names:docs[str(attempt/'measurements'/name/'result.json')]=reports[name]
        files={name:H for name in ['raw_benchmark_publication_v2.py','raw_benchmark_v4.py','fresh_publication_v2.py']}
        return attempt,plan,reports,stage_audit,docs,module,files
    def run_fixture(self,value):
        attempt,plan,reports,stage,docs,module,files=value
        with patch.object(audit,'read',side_effect=lambda path,*_:deepcopy(docs[str(path)])),\
            patch.object(audit.single,'core',return_value=module),patch.object(audit.single,'stage_audit',return_value=stage),\
            patch.object(audit.single,'publication',return_value={}) as published,\
            patch.object(audit.single,'verification',return_value={}) as verified:
            result=audit.warm(attempt,plan,reports,'/aux',lambda *args:H,files)
        return result,published,verified
    def test_two_case_coverage_and_exact_verify_stages(self):
        result,published,verified=self.run_fixture(self.fixture())
        self.assertEqual(published.call_count,2)
        self.assertEqual([call.kwargs['stage'] for call in verified.call_args_list],['verify-new-off','verify-halo-on'])
    def test_missing_extra_duplicate_cases_rejected(self):
        for mode in ['missing','extra','duplicate']:
            value=self.fixture();reports=value[2];plan=value[1]
            if mode=='missing':reports.pop('halo-on')
            elif mode=='extra':reports['unexpected']=reports['new-off']
            else:plan['cases'][1]['id']='new-off'
            with self.assertRaises(RuntimeError):self.run_fixture(value)
    def test_missing_extra_duplicate_receipts_rejected(self):
        for mode in ['missing','extra','duplicate']:
            value=self.fixture();stage=value[3];docs=value[4]
            root=stage.parent/(stage.name+'-fresh-publication-v2')/'rank00000'
            items=docs[str(root/'manifest.json')]['published_outputs']
            if mode=='missing':items.pop()
            elif mode=='extra':items.append(deepcopy(items[0]))
            else:items[1]=deepcopy(items[0])
            with self.assertRaises(RuntimeError):self.run_fixture(value)
    def test_changed_plan_or_parent_incomplete_rejected(self):
        for mode in ['plan','parent']:
            value=self.fixture();stage=value[3];docs=value[4]
            if mode=='plan':docs[str(stage.parent/(stage.name+'-fresh-publication-v2')/'rank00000/startup.json')]['plan']['cases']=['halo-on','new-off']
            else:docs[str(stage/'rank00001/manifest.json')]['complete']=False
            with self.assertRaises(RuntimeError):self.run_fixture(value)


@unittest.skipUnless(os.name=='posix' and hasattr(os,'pread'),'Real Linux tiny producer windows')
class RealTwoCasePublication(unittest.TestCase):
    def test_two_real_outputs_same_plan_with_separate_bounded_receipts(self):
        import file_integrity as integrity
        import fresh_publication_v2 as fresh
        import test_fresh_publication_v2 as kernel
        with tempfile.TemporaryDirectory() as directory:
            attempt=Path(directory).resolve();output=attempt/'measurements';names=['new-off','halo-on']
            plan={'cases':[{'id':name} for name in names]};plan_path=attempt/'plan.json'
            plan_path.write_text(json.dumps(plan));sha=lambda p,*_:integrity.read_dual(p)['openssl_sha256']
            payload=kernel.npy();digest=hashlib.sha256(payload).hexdigest();stage=attempt/'checksum-audit/benchmark'
            root=stage.parent/(stage.name+'-fresh-publication-v2')/'rank00000'
            root.mkdir(parents=True)
            declarations=[dict(relative=name+'/propagator.npy',kind='npy-propagator',expected_sha256=None,bytes=len(payload)) for name in names]
            calls=[]
            def reader(path,expected,size,**options):
                current=len(calls);calls.append(str(path));observations=[]
                def stat():
                    value=Path(path).stat();observations.append(1)
                    if current==0 and len(observations)==1:os.utime(path,ns=(value.st_atime_ns,value.st_mtime_ns+1000000))
                    return value
                return integrity.read_dual(path,expected,size,block=64,path_stat=stat,**options)
            with patch.object(fresh,'PROP_BYTES',len(payload)),patch.object(fresh,'PROP_SHAPE',(2,3)):
                scope=fresh.FreshPublication(output,declarations,root/'publications',reader=reader)
                startup=dict(numeric_and_clock_bodies_unchanged=True,immutable_reader_unchanged=True,mode='benchmark',rank=0,
                    plan=dict(path=str(plan_path),sha256=sha(plan_path),cases=names),eligibility=scope.eligibility)
                startup_path=root/'startup.json';startup_path.write_text(json.dumps(startup))
                parent=stage/'rank00000/protocol.json';parent.parent.mkdir(parents=True)
                parent.write_text('{"complete":true}');(parent.parent/'manifest.json').write_text('{"complete":true}')
                binding=dict(path=str(parent),sha256=sha(parent),startup_path=str(startup_path),startup_sha256=sha(startup_path))
                values=[];reports={}
                for name in names:
                    path=output/name/'propagator.npy';path.parent.mkdir(parents=True);path.write_bytes(payload)
                    value=scope.read(path,None,len(payload),parent_protocol=binding)['fresh_output_publication'];values.append(value)
                    reports[name]=dict(configuration=dict(ranks=1),propagator_sha256=digest)
                    (path.parent/'result.json').write_text(json.dumps(reports[name]))
                files={name:H for name in ['raw_benchmark_publication_v2.py','raw_benchmark_v4.py','fresh_publication_v2.py']}
                manifest=dict(complete=True,passed=True,protocol=fresh.PROTOCOL,rank=0,entry_sha256=H,base_wrapper_sha256=H,
                    publication_module_sha256=H,startup_sha256=sha(startup_path),published_outputs=values,parent_raw_artifacts={
                        name:dict(path=str(parent.parent/name),sha256=sha(parent.parent/name)) for name in ['protocol.json','manifest.json']})
                (root/'manifest.json').write_text(json.dumps(manifest))
                argv=['python','/aux/raw_benchmark_publication_v2.py','--benchmark','/snapshot/bench_full12.py',
                    '--plan',str(plan_path),'--output',str(output),'--expected-wrapper-sha',H]
                (attempt/'attempt.json').write_text(json.dumps(dict(stages=dict(benchmark=dict(returncode=0,cleanup=dict(complete=True),argv=argv)))))
                with patch.object(audit.single,'core',return_value=fresh),patch.object(audit.single,'stage_audit',return_value=stage),\
                    patch.object(audit.single,'verification',return_value={}) as verified:
                    evidence=audit.warm(attempt,plan,reports,'/aux',sha,files)
                self.assertEqual(verified.call_count,2)
                self.assertTrue(all(value['receipt'] in evidence for value in values))
                self.assertEqual([value['full_reads'] for value in values],[2,1])
                self.assertEqual(values[0]['full_proof']['reads'][0]['openssl_sha256'],fresh.EMPTY_SHA)
                self.assertFalse(values[0]['full_proof']['empty_digest_is_payload_candidate'])


if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in [Structure,DirectRouting,Cases,RealTwoCasePublication,previous.ExternalProof,previous.BudgetsAndGates,previous.ActualClosedEvidence,previous.StrictRead]:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
