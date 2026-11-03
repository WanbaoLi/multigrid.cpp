import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import raw_cold_adapter as adapter
import raw_cold_controller as controller


def portable_pread(fd,count,offset):
    position=os.lseek(fd,0,os.SEEK_CUR)
    try:os.lseek(fd,offset,os.SEEK_SET);return os.read(fd,count)
    finally:os.lseek(fd,position,os.SEEK_SET)


class ColdAdapters(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.pread=mock.patch.object(os,'pread',side_effect=portable_pread,create=True);self.pread.start()
    def tearDown(self):self.pread.stop();self.temp.cleanup()

    def options(self,profile=False):
        cold=self.root/'cold_full12.py';helper=self.root/'profile_full12.py';prof=self.root/'profile_setup.py'
        data=self.root/'source-data.bin';data.write_bytes(b'logical bytes'*50)
        cold.write_text("import hashlib\nfrom pathlib import Path\ndef sha(path):\n return 'BROKEN-BUFFERED-SHA'\ndef prepared_hash(data):\n return hashlib.sha256(data).hexdigest()\ndef main():\n import sys,json\n p=Path(sys.argv[sys.argv.index('--payload')+1]);q=Path(sys.argv[sys.argv.index('--marker')+1]);q.write_text(json.dumps({'sha':sha(p),'memory':prepared_hash(b'canonical'),'argv':sys.argv[1:]}))\n")
        helper.write_text("def sha(path):\n return 'BROKEN-HELPER-SHA'\ndef untouched(x):\n return x+1\n")
        prof.write_text("import sys,importlib.util,runpy\nfrom pathlib import Path\ndef main():\n args=sys.argv[1:];h=Path(args[args.index('--profile-helper')+1]);c=Path(args[args.index('--cold-wrapper')+1]);s=importlib.util.spec_from_file_location('_fake_perf_helpers',h);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p=Path(args[args.index('--payload')+1]);assert m.sha(p)!='BROKEN-HELPER-SHA';assert m.untouched(4)==5;runpy.run_path(str(c),run_name='__main__');return 0\n")
        options=SimpleNamespace(cold_wrapper=cold,expected_cold_sha=hashlib.sha256(cold.read_bytes()).hexdigest(),
            expected_adapter_sha=hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
            expected_reader_sha=hashlib.sha256(Path(adapter.integrity.__file__).read_bytes()).hexdigest(),
            audit_output=self.root/'audits',retain_mib=1,profile_setup=prof if profile else None,
            expected_profile_sha=hashlib.sha256(prof.read_bytes()).hexdigest(),profile_helper=helper,
            expected_profile_helper_sha=hashlib.sha256(helper.read_bytes()).hexdigest())
        args=['--output',str(self.root/'numeric-output'),'--library',str(data),'--expected-library-sha',hashlib.sha256(data.read_bytes()).hexdigest(),
              '--source-manifest',str(data),'--snapshot-sha',hashlib.sha256(data.read_bytes()).hexdigest(),
              '--payload',str(data),'--marker',str(self.root/'marker.json')]
        if profile:args=['--cold-wrapper',str(cold),'--profile-helper',str(helper),*args]
        return options,args,data

    def test_direct_changes_only_file_callback_keeps_memory_and_args(self):
        options,args,data=self.options();before=options.cold_wrapper.read_bytes()
        with mock.patch.dict(os.environ,OMPI_COMM_WORLD_RANK='0'):adapter.run(options,args)
        marker=json.loads((self.root/'marker.json').read_text());self.assertEqual(marker['sha'],hashlib.sha256(data.read_bytes()).hexdigest())
        self.assertEqual(marker['memory'],hashlib.sha256(b'canonical').hexdigest());self.assertEqual(marker['argv'],args)
        self.assertEqual(before,options.cold_wrapper.read_bytes())
        p=json.loads((options.audit_output/'rank00000/protocol.json').read_text());self.assertEqual(p['patched_functions'],['cold_full12.sha'])
        self.assertEqual(p['source_proofs'][0]['original_other_ast_sha256'],p['source_proofs'][0]['executed_other_ast_sha256'])

    def test_profile_runpy_reaches_cold_and_helper_raw_sha(self):
        options,args,data=self.options(True)
        with mock.patch.dict(os.environ,OMPI_COMM_WORLD_RANK='8'):adapter.run(options,args)
        p=json.loads((options.audit_output/'rank00008/protocol.json').read_text())
        self.assertEqual(set(p['patched_functions']),{'cold_full12.sha','profile_full12.sha'})
        self.assertEqual(json.loads((self.root/'marker.json').read_text())['sha'],hashlib.sha256(data.read_bytes()).hexdigest())
        self.assertTrue(all(v['original_other_ast_sha256']==v['executed_other_ast_sha256'] for v in p['source_proofs']))

    def test_reused_rank_audit_fails_without_overwrite(self):
        options,args,_=self.options();options.audit_output.mkdir();(options.audit_output/'rank00000').mkdir()
        with self.assertRaises(FileExistsError):adapter.run(options,args)
        self.assertFalse((self.root/'marker.json').exists())

    def test_source_change_rejected_before_main(self):
        options,args,_=self.options();options.cold_wrapper.write_text(options.cold_wrapper.read_text()+'\n#changed')
        with self.assertRaisesRegex(RuntimeError,'source SHA changed'):adapter.run(options,args)
        self.assertFalse((self.root/'marker.json').exists())

    def test_profile_frozen_main_ast_and_clock_are_not_rewritten(self):
        payload=(HERE/'cold_full12.py').read_bytes();tree=ast.parse(payload)
        original=adapter.ast_proof(payload,['sha'])
        sha_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='sha')
        sha_node.body=ast.parse("return __raw_sha(path)").body
        self.assertEqual(original,adapter.ast_proof(ast.unparse(tree).encode(),['sha']))
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        main.body.append(ast.parse("__changed_clock()").body[0])
        self.assertNotEqual(original,adapter.ast_proof(ast.unparse(tree).encode(),['sha']))

    def shell_options(self):
        cold=self.root/'cold_full12.py';profile=self.root/'profile_setup.py';helper=self.root/'profile_full12.py';boot=self.root/'site environment.sh'
        for p in [cold,profile,helper,boot]:p.write_text('# fixture\n')
        return SimpleNamespace(cold_source=cold,profile_source=profile,profile_helper=helper,cold_adapter=HERE/'raw_cold_adapter.py',
            expected_cold_sha='c'*64,expected_profile_sha='p'*64,expected_profile_helper_sha='h'*64,reader_sha='r'*64,cold_adapter_sha='a'*64),boot

    def test_derived_bash_preserves_numa_env_clock_args_and_resumes(self):
        options,boot=self.shell_options();script=self.root/'run-reviewed-cold-task.sh'
        original=['env','LQCD_HBW_ALLOC=hot','python','/frozen/tools/run_numa.py','--threads','37','--','python','-u',str(options.profile_source),
            '--cold-wrapper',str(options.cold_source),'--profile-helper',str(options.profile_helper),'--frequency','19','--diagnostic','--output','/fresh/cold']
        body='#!/bin/bash\nset -eo pipefail\nsource '+shlex.quote(str(boot))+'\n'+shlex.join(original)+'\n';script.write_text(body)
        command=dict(argv=['/bin/bash',str(script)],env={'X':'same'},cwd='/build',timeout_seconds=650)
        result,proof=controller.transform_bash(options,'/campaign','092-setup','cold-setup-profile',command)
        self.assertEqual(script.read_text(),body);self.assertEqual(result['env'],command['env']);self.assertEqual(result['cwd'],command['cwd']);self.assertEqual(result['timeout_seconds'],650)
        replaced=proof['derived_inner_argv'];self.assertEqual(replaced[:9],original[:9]);self.assertIn('--profile-setup',replaced)
        self.assertEqual(proof['original_inner_argv'],original)
        self.assertEqual(replaced[-len(original[10:]):],original[10:])
        again,proof2=controller.transform_bash(options,'/campaign','092-setup','cold-setup-profile',command)
        self.assertEqual(again,result);self.assertEqual(proof2['derived_script_sha256'],proof['derived_script_sha256'])

    def test_actual_profile_argv_entry_not_cold_wrapper_argument(self):
        options,_=self.shell_options();python='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'
        original=['env','-u','LD_PRELOAD','-u','OMP_WAIT_POLICY','LQCD_HBW_ALLOC=hot','LQCD_ARM_SVE=1',python,
            '/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign/attempts/092/source/tools/run_numa.py','--threads','37','--',python,'-u',str(options.profile_source),
            '--cold-wrapper',str(options.cold_source),'--profile-helper',str(options.profile_helper),'--profile-output','/campaign/attempts/092/setup-profile',
            '--frequency','19','--diagnostic','--project','/campaign/attempts/092/source','--source-manifest','/campaign/attempts/092/source-manifest.json',
            '--snapshot-sha','s'*64,'--library','/frozen/liblqcd_cpu.so','--expected-library-sha','l'*64,'--plan','/recipes/092/plan.json',
            '--fixture','/frozen/canonical','--reference-propagator','/frozen/gold.npy','--backend','arm','--allocation','mg-opt-20261103-worker6','--output','/campaign/attempts/092/measurements/cold-first12']
        replacement,kind=controller.adapter_command(options,original,self.root/'audit')
        self.assertEqual(kind,'profile');index=original.index(str(options.profile_source))
        self.assertEqual(replacement[:index],original[:index]);self.assertEqual(replacement[-len(original[index+1:]):],original[index+1:])
        self.assertIn('--profile-setup',replacement)

    def test_unrelated_bash_stage_passes_through(self):
        options,_=self.shell_options();script=self.root/'build.sh';script.write_text('#!/bin/bash\ncmake --build build\n')
        command={'argv':['/bin/bash',str(script)],'env':{}};self.assertEqual(controller.transform_bash(options,'/c','id','build',command),(command,None))

    def test_outer_controller_preserves_base_hook_and_memory_digest(self):
        options,boot=self.shell_options();data=self.root/'reference.bin';data.write_bytes(b'fixed reference')
        script=self.root/'run-cold.sh';script.write_text('#!/bin/bash\nset -eo pipefail\nsource '+shlex.quote(str(boot))+'\n'+shlex.join(['python','-u',str(options.profile_source),'--cold-wrapper',str(options.cold_source)])+'\n')
        marker=self.root/'stage.json';campaign=self.root/'campaign.py';prepare=self.root/'prepare_best_replay.py';base=self.root/'raw_controller_v4.py'
        campaign.write_text("import hashlib,json\nfrom pathlib import Path\ndef digest(path):\n return 'BROKEN-LEDGER-FILE-SHA'\ndef object_digest(value):\n return hashlib.sha256(value).hexdigest()\ndef run_stage(root,name,stage,command,*args,**kwargs):\n Path(command['marker']).write_text(json.dumps(command))\n")
        prepare.write_text("def sha(path):\n return 'BROKEN-PREPARE-FILE-SHA'\n")
        base.write_text("import campaign,importlib.util,json\nfrom pathlib import Path\ndef main():\n s=importlib.util.spec_from_file_location('_fixture_prepare',"+repr(str(prepare))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p=Path("+repr(str(data))+");assert m.sha(p)==campaign.digest(p);assert campaign.object_digest(b'canonical')=="+repr(hashlib.sha256(b'canonical').hexdigest())+";old=campaign.run_stage\n def strengthened(root,name,stage,command,*args,**kwargs):\n  command=dict(command,base_hook_seen=True);return old(root,name,stage,command,*args,**kwargs)\n campaign.run_stage=strengthened\n campaign.run_stage("+repr(str(self.root/'ledger'))+",'092','cold-setup-profile',dict(argv=['/bin/bash',"+repr(str(script))+"],marker="+repr(str(marker))+",cwd='/unchanged',timeout_seconds=900,env={'A':'same'}))\n")
        def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
        options=SimpleNamespace(**vars(options),base_controller=base,prepare_source=prepare,campaign_source=campaign,
            base_sha=digest(base),prepare_sha=digest(prepare),campaign_sha=digest(campaign),audit_root=self.root/'outer-audit',
            controller_sha=digest(Path(controller.__file__)))
        options.reader_sha=digest(Path(adapter.integrity.__file__));options.cold_adapter_sha=digest(options.cold_adapter)
        options.expected_cold_sha=digest(options.cold_source);options.expected_profile_sha=digest(options.profile_source);options.expected_profile_helper_sha=digest(options.profile_helper)
        old_campaign=sys.modules.pop('campaign',None);old_path=list(sys.path)
        try:
            controller.run(options,[])
            request=json.loads(marker.read_text());self.assertTrue(request['base_hook_seen']);self.assertEqual(request['env'],{'A':'same'})
            self.assertEqual(request['cwd'],'/unchanged');self.assertEqual(request['timeout_seconds'],900);self.assertNotEqual(request['argv'][1],str(script))
            protocol=json.loads(next(options.audit_root.glob('cold-controller-*/protocol.json')).read_text())
            self.assertTrue(protocol['complete']);self.assertEqual(set(protocol['patched_functions']),{'prepare_best_replay.sha','campaign.digest'})
            self.assertTrue(all(p['original_other_ast_sha256']==p['executed_other_ast_sha256'] for p in protocol['source_proofs']))
            self.assertEqual(sys.modules['campaign'].digest(data),'BROKEN-LEDGER-FILE-SHA')
        finally:
            sys.path[:]=old_path;sys.modules.pop('campaign',None)
            if old_campaign is not None:sys.modules['campaign']=old_campaign


if __name__=='__main__':unittest.main()
