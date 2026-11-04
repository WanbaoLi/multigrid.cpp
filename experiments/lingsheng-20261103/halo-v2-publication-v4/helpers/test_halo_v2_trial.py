"""Pure provenance/argv/budget tests plus small Linux strict-reader contracts."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import halo_v2_trial as trial
import phase6_halo as phase
import raw_protocol_derived as derived

H='1'*64


def external_fixture():
    snapshot=dict(git_head=trial.HEAD,source_manifest_sha256=H)
    stages={name:dict(status='passed',returncode=0,cleanup=dict(complete=True),log_sha256=H)
            for name in trial.REQUIRED_TEST_STAGES}
    state=dict(complete=True,status='passed',scope='full',full_numerical_complete=True,mpi_status='passed',
        sve_matrix_status='passed',arm_codegen_complete=True,unit_complete=True,source_head=trial.HEAD,
        library_sha256=H,host='cn19483',snapshot=snapshot,sve_matrix={})
    for width in (16,32,64):
        state['sve_matrix'][str(width)]=dict(ranks=dict(complete=True,library_sha256=H,requested_bytes=width,
            ranks=[dict(rank=rank,actual_bytes=width,inherit_exec=True) for rank in range(4)]),
            actual=[dict(calls=4,max_width=2)])
    status=dict(status='passed',returncode=0,cleanup=dict(complete=True),host='cn19483')
    return state,status,dict(snapshot=snapshot,stages=stages)


class ExternalProof(unittest.TestCase):
    def test_complete_matrix_is_accepted(self):
        trial.validate_test_contract(*external_fixture(),H)

    def test_codegen_only_cannot_be_performance_prerequisite(self):
        state,status,attempt=external_fixture();state.update(scope='codegen',full_numerical_complete=False)
        with self.assertRaisesRegex(RuntimeError,'codegen-only118'):
            trial.validate_test_contract(state,status,attempt,H)

    def test_failed_cleanup_or_stage_and_changed_library_are_rejected(self):
        for mutate in [lambda s,q,a:q['cleanup'].update(complete=False),
            lambda s,q,a:a['stages']['mpi-numerical-ctest'].update(returncode=1),
            lambda s,q,a:s.update(library_sha256='2'*64),
            lambda s,q,a:s.update(source_head='711'+'0'*37)]:
            s,q,a=external_fixture();mutate(s,q,a)
            with self.assertRaises(RuntimeError):trial.validate_test_contract(s,q,a,H)

    def test_actual_vl_rank_set_inherit_and_calls_required(self):
        for mutate in [lambda r:r['ranks'][0].update(actual_bytes=64),
            lambda r:r['ranks'][0].update(rank=3),lambda r:r['ranks'][0].update(inherit_exec=False)]:
            s,q,a=external_fixture();mutate(s['sve_matrix']['16']['ranks'])
            with self.assertRaises(RuntimeError):trial.validate_test_contract(s,q,a,H)
        s,q,a=external_fixture();s['sve_matrix']['32']['actual'][0]['calls']=0
        with self.assertRaises(RuntimeError):trial.validate_test_contract(s,q,a,H)


class BudgetsAndGates(unittest.TestCase):
    def test_only_remaining_ordinary_scopes_are_charged(self):
        self.assertEqual(trial.remaining_floor([]),4000)
        self.assertEqual(trial.remaining_floor(['a-benchmark']),3400)
        self.assertEqual(trial.remaining_floor(['a-benchmark','a-verify']),3100)
        self.assertEqual(trial.remaining_floor(list(trial.GROUP_FLOORS)),0)
        self.assertFalse(any('test' in key or 'build' in key for key in trial.GROUP_FLOORS))

    def test_frozen_gate_source_and_overlap_rejection(self):
        self.assertEqual(hashlib.sha256(Path(phase.__file__).read_bytes()).hexdigest(),trial.PHASE_SHA)
        item=lambda m,lo,hi:dict(median_seconds=m,minimum_seconds=lo,maximum_seconds=hi,
            relative_spread=(hi-lo)/m,steady_repeats=list(range(1,8)))
        controls=item(16,15.9,16.1)
        self.assertFalse(phase.bracket_gate(item(15.8,15.7,16),controls,controls,
            dict(minimum_gain=.03,maximum_relative_spread=.1))['passed'])
        self.assertFalse(phase.halo_effect_gate(item(15.8,15.7,16),controls)['passed'])
        self.assertTrue(phase.bracket_gate(item(15,14.9,15.1),controls,controls,
            dict(minimum_gain=.03,maximum_relative_spread=.1))['passed'])

    def test_evidence_paths_cannot_escape(self):
        for value in ['../x','/tmp/x','C:\\tmp\\x','a/../x','.','']:
            with self.assertRaises(RuntimeError):trial.safe_relative(value)
        self.assertEqual(str(trial.safe_relative('codegen/proof.json')).replace('\\','/'),'codegen/proof.json')


class DirectArgv(unittest.TestCase):
    def test_same_hierarchy_two_cases_raw_factory_exactly_once_and_seven_samples(self):
        base=dict(context_environment={'LQCD_HBW_ALLOC':'require'},threads=32,batch=2,
            placement_threads=37,setup_threads=37,solve_environment={'LQCD_COARSE_BATCH_REDUCE':1})
        cases=phase.comparison_cases(base);plan=phase.plan_for(base,cases)
        self.assertEqual([c['id'] for c in cases],['new-off','halo-on'])
        with tempfile.TemporaryDirectory() as directory:
            c=trial.Trial.__new__(trial.Trial);c.campaign=Path(directory);c.base=base;c.phase=phase
            c.args=SimpleNamespace(fixture=Path('/fixture'),reference=Path('/reference/multigrid'),auxiliary=Path('/aux'))
            c.allocation='new-owned-allocation';c.state={};c.save=Mock();c.ledger=SimpleNamespace(atomic=Mock())
            captured=[];c.stage=lambda *args:captured.append(args)
            c.protocol=SimpleNamespace(benchmark_command=lambda *args,**kw:derived.benchmark_command(*args,verify=False,**kw))
            def read(path):
                case=next(value for value in cases if value['id']==path.parent.name)
                return dict(configuration=phase.configuration_for(base,plan,case),library_sha256=H,
                    verification=dict(complete=True,passed=True,columns=12,checksum_audit=dict(helper_wrapper_sha256=trial.DERIVED_SHA)),
                    samples=[dict(repeat=i,warmup=i==0) for i in range(8)])
            c.strict=SimpleNamespace(read=read,sha=lambda *args:H)
            trial.Trial.benchmark(c,'new-off',dict(source='/snapshot',source_manifest_sha256=H),Path('/tested/lib.so'),plan)
            benchmark=captured[0][2]
            self.assertEqual(sum(Path(v).name=='raw_benchmark_v4.py' for v in map(str,benchmark)),1)
            self.assertEqual(benchmark[benchmark.index('--repeats')+1],'7')
            self.assertEqual(sum(Path(v)==Path('/tested/lib.so') for v in benchmark),1)
            self.assertEqual(Path(benchmark[benchmark.index('--plan')+1]),Path(directory)/'attempts/new-off/plan.json')
            for name,key,argv,*rest in captured[1:]:
                self.assertEqual(argv[argv.index('--expected-helper-wrapper-sha')+1],trial.DERIVED_SHA)
                self.assertEqual(argv[argv.index('--verification-output')+1],'independent-derived')
                self.assertEqual(sum(Path(v).name=='raw_benchmark_v4.py' for v in argv),1)
            self.assertEqual(len(captured),3)


class ActualClosedEvidence(unittest.TestCase):
    """Shape regression using actual closed old-V1 data, never a V2 full pass."""
    root=Path(os.environ.get('HALO_V2_REVIEW_EVIDENCE',str(Path(__file__).resolve().parent.parent/'outputs/optimization-20261103')))

    def test_real_090_103_all142_reduction_keys_and_coverage(self):
        path=self.root/'halo103-comparison/comparison.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        fields=('nrhs','coarse_it_limit','coarse_tolerance','iterations','restarts','refreshes','capped','reduction_rounds','allreduce_calls')
        old,new=data['old_reduction_records'],data['new_reduction_records']
        self.assertEqual(len(old),142);self.assertEqual(len(new),142)
        self.assertEqual([{key:row[key] for key in fields} for row in old],[{key:row[key] for key in fields} for row in new])
        coverage=phase.coarse_coverage(new)
        self.assertEqual(coverage['restarts'],172);self.assertEqual(coverage['refreshes'],427)
        self.assertEqual(coverage['packed_allreduce_calls'],19746)
        self.assertTrue(coverage['different_refresh_counts'])

    def test_real103_sve_inherit_rank_and_width_shape(self):
        path=self.root/'halo103-comparison/closed-state-proof.json'
        state=json.loads(path.read_text(encoding='utf-8'))['state']
        actual=state['arm_sve_execution']
        # Adapt field names solely to check the shared probe's actual JSON
        # shape. Keep the original V1 library SHA; never relabel it as V2.
        matrix={width:dict(ranks=row['rank_check'],actual=row['actual_halo_diagnostics']) for width,row in actual.items()}
        library=matrix['16']['ranks']['library_sha256']
        self.assertNotEqual(library,'e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330')
        trial.validate_sve_matrix(matrix,library)

    def test_actual118_codegen_state_is_rejected_as_full_proof(self):
        proof=json.loads((self.root/'halo-v2-arm-codegen118/collection-proof.json').read_text(encoding='utf-8'))
        path=self.root/'halo-v2-arm-codegen118/closed-evidence/campaign-halo-v2/attempts/000-halo-v2-tests/attempt.json'
        attempt=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(proof['state']['test_attempt'],'000-halo-v2-tests')
        self.assertTrue(proof['state']['arm_codegen_complete'])
        with self.assertRaisesRegex(RuntimeError,'codegen-only118'):
            trial.validate_test_contract(proof['state'],proof['status'],attempt,proof['state']['library_sha256'])


@unittest.skipUnless(hasattr(os,'pread') and hasattr(os,'O_NOFOLLOW'),'Production explicit-offset reader needs Linux')
class StrictRead(unittest.TestCase):
    def test_exact_small_payload_and_expected_sha(self):
        import file_integrity
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'metadata.json';payload=b'{"correct":true}\n';path.write_bytes(payload)
            s=trial.StrictFiles(file_integrity)
            self.assertEqual(s.read(path,hashlib.sha256(payload).hexdigest()),{'correct':True})
            with self.assertRaisesRegex(RuntimeError,'SHA mismatch'):s.read(path,'0'*64)
            link=Path(directory)/'link.json';link.symlink_to(path)
            with self.assertRaisesRegex(RuntimeError,'Strict metadata path'):s.read(link)


if __name__=='__main__':unittest.main(verbosity=2)
