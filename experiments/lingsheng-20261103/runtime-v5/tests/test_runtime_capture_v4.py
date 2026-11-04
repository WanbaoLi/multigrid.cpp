from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import runtime_benchmark_capture_v4 as capture
import raw_controller_setup_capture_v4 as adapter
import prepare_phase5_setup_capture_v4 as prepare


class Contracts(unittest.TestCase):
    def test_only_ordinary_producer_is_extended_without_mutating_original(self):
        command=dict(argv=['mpiexec','python','/aux/raw_benchmark_publication_v2.py',
            '--benchmark','/snapshot/bench_full12.py','--output','/fresh'])
        before=deepcopy(command)
        result=adapter.extend_stage(command,'case',Path('/aux/runtime_benchmark_capture_v4.py'),'a'*64,Path('/audit'))
        self.assertEqual(command,before)
        self.assertEqual(result['argv'][:3],['mpiexec','python','/aux/runtime_benchmark_capture_v4.py'])
        boundary=result['argv'].index('--')
        self.assertEqual(result['argv'][boundary+1:],command['argv'][3:])
        self.assertIn('/audit/case.json',result['argv'])
        verify=dict(argv=command['argv']+['--verify','/old'])
        self.assertEqual(adapter.extend_stage(verify,'case',Path('/wrapper'),'a'*64,Path('/audit')),verify)
        other=dict(argv=['cmake','--build','/build'])
        self.assertEqual(adapter.extend_stage(other,'case',Path('/wrapper'),'a'*64,Path('/audit')),other)

    def test_deleted_mapped_library_and_missing_required_family_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'Deleted mapped'):
            capture.mapped_libraries('0-1 r-x 0 0 0 /old/libgomp.so.1 (deleted)')
        with self.assertRaisesRegex(RuntimeError,'exactly one actual runtime'):
            capture.mapped_libraries('')

    def test_all_actual_shared_files_are_read_and_family_duplicates_rejected(self):
        names=['libgomp.so.1','libstdc++.so.6','libgcc_s.so.1','libc.so.6','libmpi.so.40','liblqcd_cpu.so','libkupl.so','other.so']
        with tempfile.TemporaryDirectory()as directory:
            base=Path(directory);maps=[]
            for name in names:
                path=base/name;path.write_bytes(name.encode());maps.append('0-1 r-x 0 0 0 '+str(path))
            rows=capture.mapped_libraries('\n'.join(maps))
            self.assertEqual({Path(r['path']).name for r in rows},set(names))
            self.assertTrue(all(len(r['sha256'])==64 for r in rows))
            with self.assertRaisesRegex(RuntimeError,'exceeded30s'):
                capture.mapped_libraries('\n'.join(maps),clock=lambda:2,deadline=1)
            path=base/'libmpi.so.41';path.write_bytes(b'other')
            with self.assertRaisesRegex(RuntimeError,'exactly one actual runtime mapping: mpi'):
                capture.mapped_libraries('\n'.join([*maps,'0-1 r-x 0 0 0 '+str(path)]))

    def test_task_keeps_original_controller_and_adds_exact_capture_boundary(self):
        protocol=SimpleNamespace(command=lambda *args,**kwargs:['python','/aux/raw_controller_publication_v2.py',
            '--entry','/aux/guard.py','--adapter-sha',adapter.BASE_SHA,'--','--contract','/prepared/contract.json'])
        task=prepare.build_task(protocol,Path('/aux'),Path('/aux/guard.py'),'a'*64,'python',
            Path('/prepared/contract.json'),'b'*64,'case',Path('/tools'),'c'*64,6500,'sdk:rest',Path('/runtime'))
        argv=task['argv']
        self.assertEqual(argv[:2],['python','/aux/raw_controller_setup_capture_v4.py'])
        self.assertEqual(argv[argv.index('--adapter-sha')+1],adapter.BASE_SHA)
        self.assertIn('/aux/guard.py',argv)
        self.assertEqual(task['environment']['LQCD_OPT_CAPTURE_DIR'],'/runtime')
        self.assertEqual(task['environment']['LQCD_OPT_CAPTURE_BASE_LD'],'sdk:rest')
        self.assertEqual(prepare.BUDGET,4700)
        self.assertEqual(len(prepare.case_ids('case',32)),8)


if __name__=='__main__':unittest.main(verbosity=2)
