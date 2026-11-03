"""Local controller contracts only: no SSH, solver, MPI or benchmark launched."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('phase5_validation',Path(__file__).with_name('phase5_validation.py'))
phase=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase)


class Contracts(unittest.TestCase):
    def test_loader_parses_real_preload_and_dependency_forms_without_ignoring_second_gomp(self):
        direct='\t/work_ssd/system/os_jasmine_v01/vroot/usr/lib64/libgomp.so.1.0.0 (0x0000400011a90000)\n'
        arrow='\tlibgomp.so.1 => '+phase.OLD_GOMP+' (0x0000400011a90000)\n'
        expected=str(Path(phase.OLD_GOMP).resolve())
        self.assertEqual(phase.gomp_loader_paths(direct),[expected])
        self.assertEqual(phase.gomp_loader_paths(arrow),[expected])
        self.assertEqual(phase.gomp_loader_paths(direct+arrow),[expected])
        sdk='\tlibgomp.so.1 => '+phase.SDK_GOMP+' (0x0000400011a90000)\n'
        self.assertEqual(len(phase.gomp_loader_paths(direct+sdk)),2,'Two different runtimes must fail exact-one gating')
        self.assertEqual(phase.gomp_loader_paths('\tlibgomp.so.1 => not found\n'),[])
        self.assertEqual(phase.gomp_loader_paths('\tlibc.so.6 => /usr/lib64/libc.so.6 (0x1)\n'),[])

    def test_both_control_gates_noise_range_and_drift(self):
        limits=dict(minimum_gain=.03,maximum_relative_spread=.10)
        def summary(median,low,high):
            return dict(median_seconds=median,minimum_seconds=low,maximum_seconds=high,
                relative_spread=(high-low)/median,steady_repeats=[1,2,3])
        fast=summary(16,15.9,16.1)
        first=summary(18,17.9,18.1)
        last=summary(18.5,18.4,18.6)
        self.assertTrue(phase.bracket_gate(fast,first,last,limits)['passed'])
        self.assertFalse(phase.bracket_gate(summary(17.6,17.5,17.7),first,last,limits)['passed'])
        self.assertFalse(phase.bracket_gate(fast,first,summary(20,19.9,20.1),limits)['passed'])
        noisy=summary(16,14,18)
        self.assertFalse(phase.bracket_gate(noisy,first,last,limits)['passed'])
        overlap=summary(17.2,16.5,18.)
        self.assertFalse(phase.bracket_gate(overlap,first,last,limits)['passed'])

    def test_plan_separates_setup_placement_and_normalizes_report_configuration(self):
        base=dict(context_environment={'LQCD_HBW_ALLOC':'require'},solve_environment={'LQCD_GCR_FUSED':1},
            threads=32,batch=4,placement_threads=37,setup_threads=37,ranks=16,block=[6,6,6,4],seed=1024)
        control=phase.plan_for(base)
        self.assertEqual(phase.configuration_for(base,control),base)
        candidate=phase.plan_for(base,threads=37)
        actual=phase.configuration_for(base,candidate)
        self.assertNotIn('setup_threads',actual)
        self.assertNotIn('placement_threads',actual)
        self.assertEqual(candidate['setup_threads'],37)
        self.assertEqual(candidate['placement_threads'],37)
        self.assertEqual(base['threads'],32)

    def observer_fixture(self,marker=False,age=0):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root=Path(temporary.name)
        attempt=root/'campaign/attempts/case'
        attempt.mkdir(parents=True)
        (attempt/'benchmark-007.log').write_text('FULL12 warmup complete\n' if marker else 'MG setup beginning\n')
        stage=dict(status='running',stage_tag='exact-stage',started=datetime.fromtimestamp(
            phase.time.time()-age,tz=timezone.utc).isoformat(),log='benchmark-007.log')
        (attempt/'attempt.json').write_text(json.dumps(dict(stages={'benchmark':stage})))
        library_dir=root/'libraries'
        library_dir.mkdir()
        libraries=[]
        for name in ('libgomp.so.1','libstdc++.so.6','libc.so.6','libmpi.so.40','liblqcd_cpu.so'):
            path=library_dir/name
            path.write_bytes(name.encode())
            libraries.append(path)
        proc=root/'proc'
        proc.mkdir()
        for pid,rank in [(100,0),(108,8)]:
            directory=proc/str(pid)
            directory.mkdir()
            (directory/'environ').write_bytes(b'LQCD_OPT_STAGE_ID=exact-stage\0OMPI_COMM_WORLD_RANK='+str(rank).encode()+
                b'\0PRIVATE_TOKEN=do-not-leak-this\0')
            (directory/'cmdline').write_bytes(b'python\0/frozen/bench_full12.py\0--output\0'+
                str(attempt/'measurements').encode()+b'\0')
            (directory/'maps').write_text(''.join('0000-1000 r-xp 0 00:00 1 /mapped/'+path.name+'\n' for path in libraries))
        def atomic(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value))
        fake_process=SimpleNamespace(STAGE_KEY='LQCD_OPT_STAGE_ID',
            tagged_processes=mock.Mock(return_value=[dict(pid=100,starttime=7),dict(pid=108,starttime=8)]),
            identity=lambda pid:dict(pid=pid,starttime=7 if pid==100 else 8))
        c=SimpleNamespace(campaign=root/'campaign',host='compute',allocation='allocation',task_tag='task',
            state=dict(frozen_library_sha256=hashlib.sha256((library_dir/'liblqcd_cpu.so').read_bytes()).hexdigest()),
            ledger=SimpleNamespace(read=lambda path:json.loads(path.read_text()),atomic=atomic),process_tree=fake_process)
        observer=phase.SetupObserver(c,'case',root/'audit/case.json')
        original_path=phase.Path
        def redirected(value):
            if value=='/proc':
                return proc
            if str(value).startswith('/mapped/'):
                return library_dir/original_path(value).name
            return original_path(value)
        return observer,redirected,c

    def test_observer_captures_only_tagged_two_ranks_and_never_exports_environment(self):
        observer,redirected,c=self.observer_fixture()
        with mock.patch.object(phase,'Path',redirected):
            observer.run()
        result=json.loads(observer.path.read_text())
        self.assertTrue(result['complete'])
        self.assertTrue(result['completed_before_steady'])
        self.assertEqual({row['rank'] for row in result['ranks']},{0,8})
        self.assertEqual(len(observer.cache),5,'Hash identical library paths once across both representative ranks')
        self.assertNotIn('PRIVATE_TOKEN',observer.path.read_text())
        self.assertNotIn('do-not-leak-this',observer.path.read_text())
        self.assertTrue(all(row['last_setup_log']['path'].endswith('benchmark-007.log') for row in result['ranks']))

    def test_observer_refuses_warmup_marker_or_expired_window_without_scanning_processes(self):
        for marker,age in [(True,0),(False,21)]:
            observer,redirected,c=self.observer_fixture(marker=marker,age=age)
            with mock.patch.object(phase,'Path',redirected):
                observer.run()
            result=json.loads(observer.path.read_text())
            self.assertFalse(result['complete'])
            self.assertFalse(result['completed_before_steady'])
            c.process_tree.tagged_processes.assert_not_called()

    def test_observer_never_overwrites_original_sidecar(self):
        observer,redirected,c=self.observer_fixture()
        observer.path.parent.mkdir()
        observer.path.write_text('{"preserve":true}')
        with mock.patch.object(phase,'Path',redirected):
            observer.run()
        self.assertEqual(observer.path.read_text(),'{"preserve":true}')
        c.process_tree.tagged_processes.assert_not_called()


if __name__=='__main__':
    unittest.main()
