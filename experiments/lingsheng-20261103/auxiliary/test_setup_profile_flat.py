"""Profile preparation contracts only: no perf, MPI, native load or solver."""
import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import shlex
import unittest

import prepare_setup_profile_flat as prepare
import raw_protocol_derived as derived


class Contracts(unittest.TestCase):
    def test_exact_frozen_derivative_changes_only_report_callgraph_decode(self):
        root=Path(__file__).parent;original=(root/'profile_setup.py').read_bytes();flat=(root/'profile_setup_flat.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),prepare.FILES['profile_setup.py'])
        before=b"'report','--stdio','--no-children','--sort','symbol'"
        after=b"'report','--stdio','--no-children','--call-graph','none','--sort','symbol'"
        self.assertEqual(original.count(before),1)
        self.assertEqual(original.replace(before,after),flat)
        self.assertEqual(hashlib.sha256(flat).hexdigest(),prepare.FILES['profile_setup_flat.py'])
        left,right=ast.parse(original),ast.parse(flat);changed=[]
        for node in ast.walk(right):
            if isinstance(node,ast.List):
                values=[value.value if isinstance(value,ast.Constant)else None for value in node.elts]
                if values[1:6]==['report','--stdio','--no-children','--call-graph','none']:
                    node.elts[4:6]=[];changed.append(node)
        self.assertEqual(len(changed),1)
        self.assertEqual(ast.dump(left,include_attributes=False),ast.dump(right,include_attributes=False),
                         'Record sampling, setup function, timer, return and cleanup AST must be identical')

    def fixture(self):
        launcher=['env','-u','LQCD_MG_SETUP_PASSES','LQCD_SETUP_SOURCE_OWNED=1','LQCD_VERBOSE=0',
            '/python','/source/tools/run_numa.py','--threads','37','--','/python','-u']
        cold=launcher+['/aux/cold_full12.py','--project','/source','--source-manifest','/source-manifest.json',
            '--snapshot-sha','a'*64,'--library','/frozen/liblqcd_cpu.so','--expected-library-sha','b'*64,
            '--plan','/plan.json','--fixture','/canonical','--backend','arm','--allocation','new-allocation',
            '--reference-propagator','/gold/propagator.npy','--output','/old-cold']
        verify=['env','OMP_NUM_THREADS=4','OPENBLAS_NUM_THREADS=1','/python','/source/tools/optimization/bench_full12.py',
            '--verify','/old-cold','--reference','/scalar','--extractor','/extractor']
        return cold,verify

    def build(self,cold=None,verify=None,**changes):
        original_cold,original_verify=self.fixture()
        return prepare.build(cold or original_cold,verify or original_verify,'/aux','/tools/profile_full12.py',
            changes.pop('run_output','/fresh/numerical'),changes.pop('profile_output','/fresh/profile'),
            changes.pop('audit_output','/fresh/audit'),changes.pop('publication_output','/fresh/publication'),**changes)

    def test_existing_five_line_recipe_is_parsed_without_running_or_eval(self):
        cold,verify=self.fixture()
        text='\n'.join(['#!/bin/bash','set -eo pipefail',"source '/site/env with space.sh'",shlex.join(cold),shlex.join(verify)])+'\n'
        bootstrap,actual_cold,actual_verify=prepare.recipe_commands(text)
        self.assertEqual(actual_cold,cold);self.assertEqual(actual_verify,verify)
        self.assertEqual(bootstrap,"source '/site/env with space.sh'")
        for wrong in (text+'echo extra\n',text.replace('set -eo pipefail','set -e'),text.replace(shlex.join(cold),shlex.join(cold)+' | cat')):
            with self.assertRaises(ValueError):prepare.recipe_commands(wrong)

    def test_compose_preserves_environment_numa_and_numerics_while_pinning_all_layers(self):
        cold,_=self.fixture();before=deepcopy(cold);result=self.build()
        argv=result['profile_argv'];index=cold.index('/aux/cold_full12.py')
        self.assertEqual(argv[:index],cold[:index]);self.assertEqual(cold,before)
        self.assertEqual(argv[index],'/aux/phase7_cold_entry.py')
        publication=argv[index+1:];boundary=publication.index('--')
        self.assertEqual(prepare.option(publication[:boundary],'--expected-entry-sha'),prepare.FILES['phase7_cold_entry.py'])
        self.assertEqual(prepare.option(publication[:boundary],'--expected-publication-sha'),prepare.FILES['phase7_publication.py'])
        adapter=publication[boundary+1:];boundary=adapter.index('--');profile=adapter[boundary+1:]
        self.assertEqual(prepare.option(adapter[:boundary],'--profile-setup'),'/aux/profile_setup_flat.py')
        self.assertEqual(prepare.option(adapter[:boundary],'--expected-profile-sha'),prepare.FILES['profile_setup_flat.py'])
        self.assertEqual(prepare.option(profile,'--frequency'),'19')
        self.assertEqual(prepare.option(profile,'--project'),'/source')
        self.assertEqual(prepare.option(profile,'--library'),'/frozen/liblqcd_cpu.so')
        self.assertEqual(prepare.option(profile,'--expected-library-sha'),'b'*64)
        self.assertEqual(prepare.option(profile,'--fixture'),'/canonical')
        self.assertEqual(prepare.option(profile,'--output'),'/fresh/numerical')
        self.assertIn('--diagnostic',profile);self.assertFalse(result['ordinary_ranking_allowed'])

    def test_independent_all12_uses_derived_helper_and_same_reference_gold(self):
        result=self.build();argv=result['independent_argv']
        self.assertEqual(argv[:4],['env','OMP_NUM_THREADS=4','OPENBLAS_NUM_THREADS=1','/python'])
        self.assertEqual(prepare.option(argv,'--verify'),'/fresh/numerical')
        self.assertEqual(prepare.option(argv,'--reference'),'/scalar')
        self.assertEqual(prepare.option(argv,'--extractor'),'/extractor')
        self.assertEqual(prepare.option(argv,'--helper-wrapper'),'/aux/raw_scalar_helper_derived.py')
        self.assertEqual(prepare.option(argv,'--expected-helper-wrapper-sha'),derived.DERIVED_FILES['raw_scalar_helper_derived.py'])
        self.assertEqual(prepare.option(argv,'--expected-gold-sha'),prepare.protocol.GOLD_SHA)
        self.assertEqual(prepare.option(argv,'--verification-output'),'independent-setup-flat')
        self.assertNotIn('--diagnostic',argv);self.assertNotIn('perf',argv)

    def test_bad_scope_alias_or_reference_pair_cannot_prepare_a_profile(self):
        for change in (dict(audit_output='/fresh/numerical/audit'),dict(publication_output='/fresh/numerical'),
                       dict(verification_output='../old'),dict(benchmark_sha='HEAD')):
            with self.assertRaises(ValueError):self.build(**change)
        cold,verify=self.fixture();cold[cold.index('--fixture')]='--gauge'
        with self.assertRaises(ValueError):self.build(cold=cold)
        cold,verify=self.fixture();verify[verify.index('--verify')+1]='/different'
        with self.assertRaises(ValueError):self.build(verify=verify)


if __name__=='__main__':unittest.main()
