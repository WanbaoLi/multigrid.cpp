"""Clock/provenance contracts using tiny fake fields, never LQCD computation."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('cold_full12',Path(__file__).with_name('cold_full12.py'))
cold=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cold)


class ColdContracts(unittest.TestCase):
    def fixture(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory=Path(temporary.name)
        for name,raw in [('lib.so',b'library'),('gauge.lime',b'original-input'),('gold.npy',b'gold'),('manifest.json',b'{}')]:
            (directory/name).write_bytes(raw)
        plan=dict(context_environment={},placement_threads=1,setup_threads=1,
            cases=[dict(id='full12',threads=1,batch=2,environment={})])
        (directory/'plan.json').write_text(json.dumps(plan))
        clock=[0.]
        events=[]
        def step(name,seconds):
            events.append(name)
            clock[0]+=seconds
        class Gauge:
            shape=(64,24,24,24,4,3,3)
            dtype='<c16'
            flags=SimpleNamespace(c_contiguous=True)
            nbytes=len(b'canonical-bits')
            def view(self,kind):return memoryview(b'canonical-bits')
        class Solver:
            def __init__(self,*args,**kwargs):step('constructor',30)
            @property
            def capabilities(self):return dict(backend='arm',device='cpu')
            def load_gauge(self,*args):step('load',40)
            def setup(self):step('setup',50);return 50.
            def set_threads(self,*args):step('set_threads',60)
            def solve_propagator(self,*args,**kwargs):
                step('solve12',70)
                return b'propagator', [dict(converged=True,true_residual=5e-9,iterations=24) for _ in range(12)]
            def close(self):step('close',1000)
        package=ModuleType('lqcd_cpu');package.Solver=Solver
        io_module=ModuleType('lqcd_cpu.io')
        def metadata(path):step('metadata',1);return dict(lattice_xyzt=(24,24,24,64))
        def read(*args,**kwargs):step('read',10);return Gauge()
        io_module.read_lime_metadata=metadata;io_module.read_lime_gauge=read
        smearing=ModuleType('lqcd_cpu.smearing')
        def smear(*args,**kwargs):step('stout',20);return Gauge()
        smearing.stout_smear=smear
        propagator=ModuleType('lqcd_cpu.propagator')
        propagator.SOLVE_TUNING_KEYS=set()
        propagator._solve_options=lambda settings:contextlib.nullcontext()
        output_io=ModuleType('lqcd_cpu.propagator_io')
        def write(path,*args):step('write',2000);Path(path).write_bytes(b'output-propagator')
        output_io.write_propagator=write
        numpy=ModuleType('numpy')
        numpy.dtype=lambda value:value;numpy.uint8='u1';numpy.empty=lambda size,**kwargs:bytearray(size)
        numpy.isfinite=lambda value:True
        def save(path,*args,**kwargs):step('save_gauge',500);Path(path).write_bytes(b'output-gauge')
        numpy.save=save
        comm=SimpleNamespace(rank=0,size=1,allgather=lambda value:[value],bcast=lambda value,root:value,
            allreduce=lambda value,op:value,Barrier=lambda:None)
        mpi4py=ModuleType('mpi4py');mpi4py.MPI=SimpleNamespace(COMM_WORLD=comm,MAX='max',BYTE='byte',Is_thread_main=lambda:True)
        modules={'numpy':numpy,'mpi4py':mpi4py,'lqcd_cpu':package,'lqcd_cpu.io':io_module,
            'lqcd_cpu.smearing':smearing,'lqcd_cpu.propagator':propagator,'lqcd_cpu.propagator_io':output_io}
        args=['--project',str(directory),'--source-manifest',str(directory/'manifest.json'),'--snapshot-sha','a'*64,
            '--library',str(directory/'lib.so'),'--expected-library-sha',cold.sha(directory/'lib.so'),
            '--plan',str(directory/'plan.json'),'--gauge',str(directory/'gauge.lime'),
            '--expected-input-sha',cold.sha(directory/'gauge.lime'),
            '--expected-prepared-sha',hashlib.sha256(b'canonical-bits').hexdigest(),
            '--reference-propagator',str(directory/'gold.npy'),'--backend','arm','--allocation','synthetic',
            '--output',str(directory/'output')]
        return directory,args,modules,clock,events

    def execute(self,args,modules,clock):
        with mock.patch.dict(cold.sys.modules,modules),mock.patch.object(cold,'source_check'),\
             mock.patch.dict(cold.os.environ,{'LQCD_CPU_THREADS':'1'},clear=True),\
             mock.patch.object(cold.time,'perf_counter',lambda:clock[0]),\
             mock.patch.object(cold.os,'sched_getaffinity',lambda pid:{0},create=True),\
             contextlib.redirect_stdout(io.StringIO()):
            cold.main(args)

    def test_continuous_clock_ends_before_close_and_output_and_is_not_steady_scope(self):
        directory,args,modules,clock,events=self.fixture()
        self.execute(args,modules,clock)
        report=json.loads((directory/'output/result.json').read_text())
        self.assertEqual(report['cold_wall_seconds'],281.)
        self.assertEqual(report['first12_api_seconds'],70.)
        self.assertEqual(report['timing_scope'],'cold_lime_to_first12')
        self.assertEqual(len(report['samples']),1)
        self.assertEqual(len(report['samples'][0]['stats']),12)
        self.assertFalse(report['samples'][0]['warmup'])
        self.assertTrue(report['measurements_complete'])
        self.assertFalse(report['verification']['complete'])
        self.assertEqual(events,['metadata','read','stout','constructor','load','setup','set_threads','solve12','close','save_gauge','write'])
        self.assertGreater(clock[0],report['cold_wall_seconds']+3000)

    def test_prepared_gauge_mismatch_is_preserved_and_solver_never_constructed(self):
        directory,args,modules,clock,events=self.fixture()
        args[args.index('--expected-prepared-sha')+1]='f'*64
        with self.assertRaisesRegex(ValueError,'Prepared gauge differs'):
            self.execute(args,modules,clock)
        report=json.loads((directory/'output/result.json').read_text())
        self.assertFalse(report['complete'])
        self.assertFalse(report['measurements_complete'])
        self.assertEqual(report['prepared_gauge_sha256'],hashlib.sha256(b'canonical-bits').hexdigest())
        self.assertEqual(report['samples'],[])
        self.assertNotIn('constructor',events)

    def test_profile_scope_explicitly_unranked(self):
        directory,args,modules,clock,events=self.fixture()
        self.execute(args+['--diagnostic'],modules,clock)
        report=json.loads((directory/'output/result.json').read_text())
        self.assertEqual(report['timing_scope'],'profile_cold_lime_to_first12')
        self.assertTrue(report['diagnostic'])
        self.assertFalse(report['rank_eligible'])

    def test_source_checks_reject_changed_or_deleted_files(self):
        with tempfile.TemporaryDirectory() as value:
            root=Path(value);(root/'a.cpp').write_bytes(b'source')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps(dict(files=[dict(path='a.cpp',sha256=cold.sha(root/'a.cpp'))])))
            expected=cold.sha(manifest)
            cold.source_check(root,manifest,expected)
            (root/'a.cpp').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'source file changed'):
                cold.source_check(root,manifest,expected)

    def test_ambient_setup_and_new_cached_flags_rejected_but_ownership_numa_preserved(self):
        with tempfile.TemporaryDirectory() as value:
            root=Path(value);(root/'src').mkdir()
            (root/'src/example.cpp').write_text('auto x = setting("LQCD_TEST_NEW_CACHED", 1); '
                'auto n = getenv("LQCD_NUMA_NODE"); auto t = getenv("LQCD_OPT_TASK_ID");')
            (root/'python/lqcd_cpu').mkdir(parents=True)
            (root/'python/lqcd_cpu/__init__.py').write_text("requested=os.environ.get('LQCD_CPU_THREADS')\n")
            resources=dict(LQCD_CPU_THREADS='37',LQCD_NUMA_NODE='16',LQCD_OPT_TASK_ID='owned',LQCD_OPT_STAGE_ID='stage',OMP_PLACES='cores')
            policy=cold.audit_numerical_environment(root,{},resources)
            self.assertNotIn('LQCD_NUMA_NODE',policy['known_keys'])
            self.assertNotIn('LQCD_OPT_TASK_ID',policy['known_keys'])
            self.assertNotIn('LQCD_CPU_THREADS',policy['known_keys'])
            self.assertEqual(cold.validate_launcher_resources(resources,37)['cpu_threads'],37)
            with self.assertRaisesRegex(ValueError,'placement_threads'):
                cold.validate_launcher_resources(resources,16)
            for key in ('LQCD_MG_SETUP_PASSES','LQCD_SETUP_UPDATE','LQCD_SAP_EO','LQCD_TEST_NEW_CACHED'):
                with self.assertRaisesRegex(ValueError,key):
                    cold.audit_numerical_environment(root,{},dict(resources,**{key:'0'}))
            policy=cold.audit_numerical_environment(root,{'LQCD_MG_SETUP_PASSES':0},
                dict(resources,LQCD_MG_SETUP_PASSES='0'))
            self.assertEqual(policy['explicit_context_values']['LQCD_MG_SETUP_PASSES'],0)


if __name__=='__main__':
    unittest.main()
