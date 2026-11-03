"""Pure phase5 revision contracts: no SSH, ldd, MPI or solver execution."""
from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import json
import unittest
from unittest import mock

spec=importlib.util.spec_from_file_location('phase5_shim',Path(__file__).with_name('phase5_validation_shim.py'))
phase=importlib.util.module_from_spec(spec);spec.loader.exec_module(phase)


class Contracts(unittest.TestCase):
    def manifest(self):
        return dict(directory='/private/old-only',base_ld_library_path='/sdk/gcc:/sdk/hmpi:/sdk/kupl:',
            old_gomp=dict(path=phase.OLD_GOMP,sha256=phase.OLD_GOMP_SHA),
            sdk_gomp=dict(path=phase.SDK_GOMP,sha256=phase.SDK_GOMP_SHA),
            sdk_stdcpp=dict(path='/sdk/gcc/libstdc++.so.6.0.30',sha256='f'*64))

    def configuration(self):
        return dict(context_environment={'LQCD_ARM_SVE':1,'LQCD_HBW_ALLOC':'require'},
            solve_environment={'LQCD_COARSE_BATCH_REDUCE':1},threads=32,batch=2,
            placement_threads=37,setup_threads=37,ranks=16,block=[6,6,6,4],seed=1024)

    def test_old_source_remains_exact_dependency_and_no_existing_archive_modified(self):
        original=Path(__file__).with_name('phase5_validation.py')
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),phase.ORIGINAL_CONTROLLER_SHA)

    def test_two_sdk_controls_are_exact_current_best_not_extra_configuration_keys(self):
        cfg=self.configuration();before=deepcopy(cfg)
        variants=phase.runtime_variants(cfg,'new',self.manifest())
        self.assertEqual(phase.configuration_for(cfg,variants[0][1]),cfg)
        self.assertEqual(phase.configuration_for(cfg,variants[-1][1]),cfg)
        self.assertEqual(cfg,before)
        self.assertEqual(len(variants),5)
        for _,plan,_ in variants:
            self.assertNotIn('LD_PRELOAD',plan['context_environment'])
            self.assertEqual(plan['placement_threads'],37)
            self.assertEqual(plan['setup_threads'],37)

    def test_old_context_records_full_search_string_and_exact_sdk_suffix_order(self):
        manifest=self.manifest();cfg=self.configuration()
        variants=phase.runtime_variants(cfg,'new',manifest)
        old=variants[2][1]['context_environment'];both=variants[3][1]['context_environment']
        self.assertEqual(old['LD_LIBRARY_PATH'],manifest['directory']+':'+manifest['base_ld_library_path'])
        self.assertEqual(old,dict(cfg['context_environment'],LD_LIBRARY_PATH=phase.old_search_path(manifest)))
        self.assertEqual(both,dict(old,OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT=0))
        self.assertEqual(variants[1][1]['context_environment'],dict(cfg['context_environment'],OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT=0))
        self.assertTrue(old['LD_LIBRARY_PATH'].endswith(':'),'Do not silently normalize inherited baseline search string')
        cfg['context_environment']['LD_LIBRARY_PATH']=manifest['base_ld_library_path']
        self.assertEqual(phase.configuration_for(cfg,phase.runtime_variants(cfg,'new',manifest)[0][1]),cfg)

    def test_preload_and_unmatched_control_environment_cannot_become_candidates(self):
        cfg=self.configuration();cfg['context_environment']['LD_PRELOAD']=''
        with self.assertRaises(ValueError):phase.runtime_variants(cfg,'new',self.manifest())
        cfg=self.configuration();cfg['context_environment']['LD_LIBRARY_PATH']='/vroot/all-libraries'
        with self.assertRaises(ValueError):phase.runtime_variants(cfg,'new',self.manifest())

    def test_loader_requires_exact_one_expected_gomp_and_same_sdk_cpp(self):
        manifest=self.manifest();hashes={row['path']:row['sha256']for row in (manifest['old_gomp'],manifest['sdk_gomp'],manifest['sdk_stdcpp'])}
        def trace(gomp,std=None):
            return '\tlibgomp.so.1 => '+gomp+' (0x1)\n\tlibstdc++.so.6 => '+(std or manifest['sdk_stdcpp']['path'])+' (0x2)\n'
        # The real traced old form may be direct rather than arrow; preserve both.
        valid=trace(phase.OLD_GOMP)
        self.assertTrue(phase.loader_gate(valid,'',0,'old',manifest,hashes.__getitem__))
        direct='\t'+phase.OLD_GOMP+' (0x1)\n'+valid.splitlines(True)[1]
        self.assertTrue(phase.loader_gate(direct,'',0,'old',manifest,hashes.__getitem__))
        self.assertFalse(phase.loader_gate(valid+'\t'+phase.SDK_GOMP+' (0x3)\n','',0,'old',manifest,hashes.__getitem__))
        self.assertFalse(phase.loader_gate(trace(phase.SDK_GOMP),'',0,'old',manifest,hashes.__getitem__))
        self.assertFalse(phase.loader_gate(trace(phase.OLD_GOMP,'/vroot/libstdc++.so.6'),' ',0,'old',manifest,hashes.__getitem__))
        self.assertFalse(phase.loader_gate(valid,'undefined symbol: new_api',0,'old',manifest,hashes.__getitem__))
        self.assertFalse(phase.loader_gate(valid,'',1,'old',manifest,hashes.__getitem__))

    def test_actual_process_environment_is_selected_explicitly_and_filtered(self):
        context=dict(LD_LIBRARY_PATH=phase.old_search_path(self.manifest()),OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT=0)
        lines=[(key+'='+str(value)).encode()for key,value in context.items()]+[b'PRIVATE_TOKEN=keep-private']
        actual=phase.runtime_environment_snapshot(lines,context,self.manifest()['base_ld_library_path'])
        self.assertEqual(actual['LD_LIBRARY_PATH'],context['LD_LIBRARY_PATH'])
        self.assertNotIn('PRIVATE_TOKEN',repr(actual))
        for extra in (b'LD_PRELOAD=/old/libgomp.so.1',b'LD_DEBUG=libs',b'GOMP_SPINCOUNT=10'):
            with self.assertRaises(ValueError):phase.runtime_environment_snapshot(lines+[extra],context,self.manifest()['base_ld_library_path'])
        with self.assertRaises(ValueError):phase.runtime_environment_snapshot([b'LD_LIBRARY_PATH=/wrong'],{},self.manifest()['base_ld_library_path'])

    def test_glibc_real_filename_family_positive_and_unrelated_libs_negative(self):
        for name in ('libc.so','libc.so.6','libc.so.6.1','libc-2.28.so','libc-2.so'):
            self.assertEqual(phase.library_family(name),'libc',name)
        for name in ('libcrypt.so.1','libcrypto.so.3','libcap.so.2','libc_malloc_debug.so.0',
                     'libc-2.28.so.bak','libc-2x28.so','libc.so.6.extra','libc-.so'):
            self.assertIsNone(phase.library_family(name),name)
        for name,family in (('libgomp.so.1.0.0','gomp'),('libstdc++.so.6.0.30','stdcpp'),
                            ('libgcc_s.so.1','gcc'),('libmpi.so.40.30.2','mpi'),('liblqcd_cpu.so','solver')):
            self.assertEqual(phase.library_family(name),family)

    @unittest.skipUnless(os.name=='posix','Linux permission/symlink contract')
    def test_shim_directory_rejects_extra_library_and_changed_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);directory=root/'private';directory.mkdir(mode=0o700)
            sdk=root/'sdk';sdk.mkdir();old=root/'old';old.write_bytes(b'old')
            new=sdk/'libgomp.so.1.0.0';new.write_bytes(b'new')
            std=sdk/'libstdc++.so.6.0.30';std.write_bytes(b'std')
            link=directory/'libgomp.so.1';link.symlink_to(old)
            digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
            closure=[dict(path='/python',passed=True,resolved_libgomp=[]),dict(path='/mpi',passed=True,resolved_libgomp=[])]
            manifest=dict(protocol='phase5-single-gomp-search-directory-v1',complete=True,passed=True,
                directory=str(directory),old_gomp=dict(path=str(old),sha256=digest(old)),
                sdk_gomp=dict(path=str(new),sha256=digest(new)),sdk_stdcpp=dict(path=str(std),sha256=digest(std)),
                base_ld_library_path=str(sdk),checks=[dict(label=label,passed=True,ld_preload_present=False,
                    launcher_loader_closure=closure,stdlib_launcher=dict(returncode=0,gomp_maps=[],allowed=[1,2]))for label in ('sdk','old')])
            with mock.patch.multiple(phase,OLD_GOMP=str(old),SDK_GOMP=str(new),OLD_GOMP_SHA=digest(old),SDK_GOMP_SHA=digest(new)):
                phase.check_shim_manifest(manifest,digest)
                (directory/'libstdc++.so.6').write_bytes(b'bad')
                with self.assertRaises(ValueError):phase.check_shim_manifest(manifest,digest)
                (directory/'libstdc++.so.6').unlink()
                old.write_bytes(b'changed')
                with self.assertRaises(ValueError):phase.check_shim_manifest(manifest,digest)

    def test_thread_affinity_snapshot_exposes_only_resource_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);task=root/'task/5';task.mkdir(parents=True)
            (task/'status').write_text('Name:\tworker\nState:\tR (running)\nCpus_allowed_list:\t1,5\nMems_allowed_list:\t0\nPrivate:\tsecret\n')
            original=phase.Path
            def redirect(value):return root.parent if value=='/proc' else original(value)
            # /proc/<pid>/task resolves to the synthetic process directory.
            process=root.parent/root.name
            with mock.patch.object(phase,'Path',redirect):rows=phase.thread_affinity_snapshot(root.name)
            self.assertEqual(rows,[dict(tid=5,Name='worker',State='R (running)',Cpus_allowed_list='1,5',Mems_allowed_list='0')])
            self.assertNotIn('secret',repr(rows))

    def test_runtime_audit_accepts_full_ld_selection_and_rejects_wrong_cpp_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);sdk=root/'sdk';sdk.mkdir();old_dir=root/'old';old_dir.mkdir()
            def library(directory,name,payload):
                path=directory/name;path.write_bytes(payload)
                return dict(path=str(path),sha256=hashlib.sha256(payload).hexdigest())
            sdk_gomp=library(sdk,'libgomp.so.1.0.0',b'sdk')
            old_gomp=library(old_dir,'libgomp.so.1.0.0',b'old')
            std=library(sdk,'libstdc++.so.6.0.30',b'std')
            other=[library(sdk,name,name.encode())for name in ('libgcc_s.so.1','libc-2.28.so','libmpi.so.40','liblqcd_cpu.so')]
            manifest=dict(self.manifest(),directory=str(root/'shim'),sdk_gomp=sdk_gomp,old_gomp=old_gomp,sdk_stdcpp=std)
            cfg=self.configuration();variants=phase.runtime_variants(cfg,'new',manifest)
            trials={};audits={}
            c=phase.Phase5.__new__(phase.Phase5)
            c.campaign=root/'campaign';c.shim_manifest=manifest;c.host='host';c.allocation='allocation'
            c.state=dict(frozen_library_sha256=other[-1]['sha256']);c.save=lambda:None
            c.ledger=SimpleNamespace(read=lambda path:json.loads(Path(path).read_text()),
                digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                require=lambda condition,message:None if condition else (_ for _ in ()).throw(ValueError(message)))
            for i,(name,plan,_) in enumerate(variants):
                attempt=c.campaign/'attempts'/name;attempt.mkdir(parents=True)
                (attempt/'attempt.json').write_text(json.dumps(dict(stages=dict(benchmark=dict(stage_tag=name)))))
                context=plan['context_environment']
                values=[(key+'='+str(value)).encode()for key,value in context.items()if key in ('LD_LIBRARY_PATH','OMP_WAIT_POLICY','GOMP_SPINCOUNT')]
                if 'LD_LIBRARY_PATH'not in context:values.append(('LD_LIBRARY_PATH='+manifest['base_ld_library_path']).encode())
                runtime=phase.runtime_environment_snapshot(values,context,manifest['base_ld_library_path'])
                gomp=old_gomp if i in (2,3) else sdk_gomp
                libraries=[gomp,std,*other]
                audit=dict(complete=True,completed_before_steady=True,attempt=name,host=c.host,allocation=c.allocation,
                    library_sha256=c.state['frozen_library_sha256'],benchmark_stage_tag=name,task_tag='task',
                    ranks=[dict(rank=rank,libraries=libraries,runtime_environment=runtime,thread_affinity=[dict(tid=rank+1,Cpus_allowed_list='0')])for rank in (0,8)])
                path=root/(name+'.json');path.write_text(json.dumps(audit));audits[name]=path
                trials[name]=dict(runtime_audit_path=str(path),runs=[dict(task_tag='task')])
            group=dict(trials=trials,variants=variants)
            names=[row[0]for row in variants]
            with mock.patch.multiple(phase,OLD_GOMP=old_gomp['path'],SDK_GOMP=sdk_gomp['path'],
                                     OLD_GOMP_SHA=old_gomp['sha256'],SDK_GOMP_SHA=sdk_gomp['sha256']):
                self.assertTrue(c.runtime_audit(group,names))
                # Simulate a first audit with honest but incorrect C++ identity.
                for trial in group['trials'].values():trial.pop('runtime_audit_sha256',None)
                changed=json.loads(audits[names[2]].read_text())
                changed['ranks'][0]['libraries'][1]=dict(std,sha256='0'*64)
                audits[names[2]].write_text(json.dumps(changed))
                self.assertFalse(c.runtime_audit(group,names))
                self.assertTrue(any('SDK libstdc++'in reason for reason in group['runtime_audit']['issues']))


if __name__=='__main__':unittest.main()
