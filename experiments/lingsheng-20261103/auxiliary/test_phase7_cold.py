"""Pure acceptance/rollback contracts; no solver, SSH, MPI or HPC claim."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cold_acceptance',HERE/'phase7_cold.py')
cold=importlib.util.module_from_spec(spec);spec.loader.exec_module(cold)
sys.path.insert(0,str(HERE/'multigrid.cpp/tools/optimization'))
import campaign as ledger


def fixture():
    parent=dict(configuration=dict(context_environment={},solve_environment={},threads=32,ranks=16,batch=2),
        source_manifest_sha256='a'*64,library_sha256='b'*64,input_sha256='c'*64)
    report=dict(complete=True,measurements_complete=True,zero_initial_guess=True,timing_scope=cold.SCOPE,diagnostic=False,
        **deepcopy(parent),propagator_sha256='d'*64,prepared_gauge_sha256=cold.CANONICAL,
        cold_wall_seconds=200.,first12_api_seconds=15.,comparison_key=dict(host='test-node',allocation='test-job',scope=cold.SCOPE,
            prepared_gauge_manifest_sha256=cold.CANONICAL),samples=[dict(repeat=0,warmup=False,wall_seconds=200.,
                stats=[dict(converged=True,true_residual=4e-9) for _ in range(12)])],
        verification=dict(complete=True,passed=True,columns=12,max_true_residual=4e-9,solution_relative_error=1e-9,
            solution_relative_errors=[1e-9]*12,propagator_sha256='d'*64,
            checksum_audit=dict(protocol_version=4,complete=True,passed=True,status='passed')))
    return parent,report


class ColdGates(unittest.TestCase):
    def test_runtime_libc_real_soname_and_versioned_file_families(self):
        for name in ('/usr/lib64/libc-2.28.so','/lib64/libc.so.6','/lib64/libc.so'):
            self.assertTrue(cold.runtime_family_matches(name,'libc.so'),name)
        for name in ('libcrypto.so.3','libc_fake.so','libc-evil.so','libc-2.28.so.backup','libc.so.evil'):
            self.assertFalse(cold.runtime_family_matches(name,'libc.so'),name)

    def test_observed_group_budget_shortage_keeps_pending_checkpoint(self):
        controller=cold.ColdAcceptance.__new__(cold.ColdAcceptance)
        controller.state=dict(complete=False,status='prepared');saved=[]
        controller.save=lambda:saved.append(deepcopy(controller.state))
        with mock.patch.object(cold.time,'time',return_value=100.):
            controller.deadline=100.+7000.
            with self.assertRaisesRegex(RuntimeError,'no cross-allocation mixing'):
                controller.time_for(cold.MINIMUM_GROUP_SECONDS)
            self.assertEqual(saved[-1]['status'],'pending');self.assertFalse(saved[-1]['complete'])
            self.assertGreater(saved[-1]['required_seconds'],7000)
            controller.deadline=100.+cold.MINIMUM_GROUP_SECONDS
            controller.time_for(cold.MINIMUM_GROUP_SECONDS)
            self.assertEqual(len(saved),1)

    @unittest.skipUnless(os.name=='posix' and hasattr(os,'pread'),'Real CMake-style symlink contract requires Linux strict reader')
    def test_ctest_resolves_known_versioned_library_only_inside_canonical_build(self):
        import file_integrity as integrity
        with tempfile.TemporaryDirectory() as temporary:
            build=Path(temporary).resolve()/'build';build.mkdir()
            actual=build/'liblqcd_cpu.so.0.2.0';actual.write_bytes(b'actual compiled shared library')
            version=build/'liblqcd_cpu.so.0';version.symlink_to(actual.name)
            logical=build/'liblqcd_cpu.so';logical.symlink_to(version.name)
            expected=hashlib.sha256(actual.read_bytes()).hexdigest()
            strict_sha=lambda path:integrity.read_dual(path)['openssl_sha256']
            with self.assertRaisesRegex(RuntimeError,'Symlink path rejected'):strict_sha(logical)
            binding=cold.ctest_library_binding(build,expected,strict_sha)
            self.assertEqual(binding['logical_path'],str(logical));self.assertEqual(binding['resolved_path'],str(actual))
            self.assertEqual(binding['sha256'],expected)
            with self.assertRaisesRegex(RuntimeError,'measured candidate bytes'):
                cold.ctest_library_binding(build,'0'*64,strict_sha)
            logical.unlink();outside=build.parent/'outside-library.so';outside.write_bytes(actual.read_bytes());logical.symlink_to(outside)
            with self.assertRaisesRegex(RuntimeError,'outside its build'):
                cold.ctest_library_binding(build,expected,strict_sha)
            with self.assertRaisesRegex(RuntimeError,'Symlink path rejected'):strict_sha(logical)

    def test_clear_cold_win_requires_full_fresh_bracket(self):
        result=cold.cold_gate([200.,201.,199.,200.],[180.,181.,179.])
        self.assertTrue(result['passed']);self.assertAlmostEqual(result['gain'],.1)
        with self.assertRaisesRegex(RuntimeError,'Four bracketed'):cold.cold_gate([200.]*3,[180.]*3)
        with self.assertRaises(RuntimeError):cold.cold_gate([200.]*4,[180.]*2)

    def test_cold_drift_noise_small_gain_and_overlap_are_independent_rejections(self):
        examples=[([200.,201.,230.,231.],[180.]*3,'drift'),
                  ([200.,201.,199.,200.],[170.,180.,190.],'spread'),
                  ([200.]*4,[195.]*3,'below3%'),
                  ([190.,200.,200.,190.],[180.,185.,190.],'overlap')]
        for baseline,candidate,reason in examples:
            with self.subTest(reason=reason):
                result=cold.cold_gate(baseline,candidate);self.assertFalse(result['passed'])
                self.assertTrue(any(reason in r for r in result['reasons']))

    def test_warm_median_flat_but_uncertainty_cannot_hide_regression(self):
        self.assertTrue(cold.warm_gate([15.,15.05,15.02],[15.03,15.06,15.01],[15.01,15.02,15.03])['passed'])
        value=cold.warm_gate([15.,15.1,15.05],[14.9,15.05,15.4],[15.1,15.0,15.05])
        self.assertFalse(value['passed']);self.assertTrue(any('not isolated' in s for s in value['reasons']))

    def test_cold_continuous_clock_and_precision_contract(self):
        parent,report=fixture();self.assertEqual(cold.inspect_cold(report,parent,'test-node','test-job'),200.)
        for mutate in [lambda r:r.update(timing_scope='profile_'+cold.SCOPE),
                       lambda r:r.update(cold_wall_seconds=199.),
                       lambda r:r['verification']['solution_relative_errors'].pop(),
                       lambda r:r['samples'][0]['stats'].pop(),
                       lambda r:r['verification']['checksum_audit'].update(status='running'),
                       lambda r:r['verification'].update(propagator_sha256='e'*64),
                       lambda r:r['comparison_key'].update(allocation='other-job'),
                       lambda r:r.update(prepared_gauge_sha256='f'*64),
                       lambda r:r['configuration'].update(threads=37)]:
            bad=deepcopy(report);mutate(bad)
            with self.subTest(mutation=bad):
                with self.assertRaises(RuntimeError):cold.inspect_cold(bad,parent,'test-node','test-job')

    def test_resource_equivalence_preserves_placement_and_setup(self):
        a=dict(threads=32,ranks=16,batch=2,placement_threads=37,setup_threads=37)
        b=dict(a,context_environment={'LQCD_SETUP_EXPERIMENT':1})
        self.assertEqual(cold.resource_configuration(a),cold.resource_configuration(b))
        del b['setup_threads'];self.assertNotEqual(cold.resource_configuration(a),cold.resource_configuration(b))

    def test_invalid_time_never_ranked(self):
        for value in [True,0,-1,float('nan'),float('inf')]:
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):cold.summary([value])

    def test_rollback_restores_only_frozen_prior_cold_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=Path(temporary).resolve();(store/'cold-artifacts').mkdir();(store/'cold-decisions').mkdir();(store/'best-cold-history').mkdir()
            library=store/'cold-artifacts/prior.so';library.write_bytes(b'prior validated library')
            proof=store/'cold-decisions/prior.json'
            ledger.atomic(proof,dict(complete=True,status='eligible',cold_assessment={'passed':True},warm_assessment={'passed':True},runtime_assessment={'passed':True}))
            sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            prior=dict(attempt='prior',library_path=str(library),library_sha256=sha(library),state_snapshot=str(proof),state_sha256=sha(proof))
            record=store/'best-cold-history/1.json';ledger.atomic(record,prior);ledger.atomic(store/'best-cold.json',{'attempt':'later'})
            result=cold.rollback(store,record,'Real-input regression found',ledger,sha)
            self.assertEqual(result['attempt'],'prior');self.assertEqual(result['rollback_from'],'later')
            self.assertEqual(library.read_bytes(),b'prior validated library');self.assertGreater(len(list((store/'best-cold-history').glob('*.json'))),1)
            library.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'changed'):cold.rollback(store,record,'Bad retained library',ledger,sha)

    def test_rollback_cannot_introduce_unaccepted_record_or_weaken_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();path=root/'arbitrary.json';path.write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'reason'):cold.rollback(root,path,'',ledger,lambda p:'x')
            with self.assertRaisesRegex(RuntimeError,'previously accepted'):cold.rollback(root,path,'Reason',ledger,lambda p:'x')


if __name__=='__main__':unittest.main()
