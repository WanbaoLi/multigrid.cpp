"""Recipe generation contracts; no solver, compiler or remote task runs."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('prepare_best_replay',Path(__file__).with_name('prepare_best_replay.py'))
replay=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(replay)


class RecipeContracts(unittest.TestCase):
    def test_selected_profile_build_and_cold_recipes_are_read_only_and_quoted(self):
        with tempfile.TemporaryDirectory() as value:
            root=Path(value)/'space root'
            tools=root/'tools-project';(tools/'tools/optimization').mkdir(parents=True)
            (tools/'tools/optimization/bench_full12.py').write_text('# verifier')
            campaign=root/'campaign';attempt=campaign/'attempts/accepted'
            source=attempt/'source';(source/'python/lqcd_cpu').mkdir(parents=True)
            (source/'python/lqcd_cpu/propagator.py').write_text("SOLVE_TUNING_KEYS={'LQCD_COARSE_THREADS'}\n")
            (attempt/'artifacts').mkdir();library=attempt/'artifacts/liblqcd_cpu.so';library.write_bytes(b'library')
            (attempt/'source-manifest.json').write_text('{}')
            (campaign/'best.json').write_text('{"attempt":"accepted"}')
            reference=root/'scalar';reference.write_bytes(b'scalar')
            extractor=root/'extractor';extractor.write_bytes(b'extractor')
            baseline=root/'gold.npy';baseline.write_bytes(b'gold')
            cfg=dict(context_environment={'LQCD_HBW_ALLOC':'require'},solve_environment={'LQCD_COARSE_THREADS':0},
                threads=32,batch=2,placement_threads=37,setup_threads=37,ranks=16,seed=1024,block=[6,6,6,4])
            report=dict(backend='arm',configuration=cfg,library_sha256=replay.sha(library),reference_propagator=str(baseline),
                verification=dict(extractor_sha256=replay.sha(extractor),reference_propagator_sha256=replay.sha(baseline)))
            def atomic(path,data):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))
            ledger=SimpleNamespace(campaign=lambda path:(path,dict(reference_sha256=replay.sha(reference))),
                checked_attempt=lambda *args:(dict(snapshot=dict(source_manifest_sha256=replay.sha(attempt/'source-manifest.json'))),report,dict(median_seconds=17)),
                read=lambda path:json.loads(path.read_text()),atomic=atomic,now=lambda:'synthetic')
            output=root/'recipes'
            before={str(path):replay.sha(path) for path in campaign.rglob('*') if path.is_file()}
            with mock.patch.dict(replay.sys.modules,{'campaign':ledger}),contextlib.redirect_stdout(io.StringIO()):
                args=['--tools-project',str(tools),'--campaign',str(campaign),'--fixture',str(root/'canonical'),
                    '--gauge',str(root/'input.lime'),'--backend','arm','--allocation','synthetic','--output',str(output),
                    '--reference',str(reference),'--extractor',str(extractor)]
                replay.main(args)
                bad=root/'wrong-gold.npy';bad.write_bytes(b'not the validated reference')
                retry=list(args);retry[retry.index('--output')+1]=str(root/'bad-reference-recipes')
                with self.assertRaisesRegex(ValueError,'independently validated reference SHA'):
                    replay.main(retry+['--reference-propagator',str(bad)])
            self.assertEqual(before,{str(path):replay.sha(path) for path in campaign.rglob('*') if path.is_file()})
            self.assertEqual(json.loads((output/'plan.json').read_text())['cases'][0]['threads'],32)
            self.assertEqual(json.loads((output/'plan.json').read_text())['setup_threads'],37)
            selection=json.loads((output/'selection.json').read_text())
            self.assertEqual(selection['selected_attempt'],'accepted')
            for name in ('run-cold-fixture.sh','run-cold-lime.sh','run-rebuilt-cold-fixture.sh','run-steady.sh'):
                text=(output/name).read_text()
                self.assertIn('site-environment.sh',text)
                self.assertIn('--verify',text)
                self.assertIn('-u OMP_WAIT_POLICY',text)
                self.assertIn('-u GOMP_SPINCOUNT',text)
                self.assertIn('-u LQCD_MG_SETUP_PASSES',text)
                self.assertIn('-u LQCD_SETUP_UPDATE',text)
                self.assertIn('-u LQCD_SAP_EO',text)
                self.assertNotIn('-u LQCD_NUMA_NODE',text)
                self.assertNotIn('-u LQCD_OPT_TASK_ID',text)
                self.assertNotIn('eval ',text)
            self.assertIn('-Wl,-rpath,',(output/'build-source.sh').read_text())
            self.assertIn('sve_vector_bytes',(output/'build-source.sh').read_text())
            self.assertIn('--expected-library-sha "$rebuilt_sha"',(output/'run-rebuilt-cold-fixture.sh').read_text())
            bash=Path('C:/Program Files/Git/bin/bash.exe') if replay.os.name=='nt' else Path('/bin/bash')
            if bash.is_file():
                for script in output.glob('*.sh'):
                    result=subprocess.run([str(bash),'-n',str(script)],capture_output=True,text=True)
                    self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
