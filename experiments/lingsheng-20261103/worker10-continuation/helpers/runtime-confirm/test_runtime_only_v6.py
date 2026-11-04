import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import phase5_runtime_only_v6 as controller
import runtime_benchmark_capture_v6 as capture
import runtime_only_scope_v6 as scope
import prepare_runtime_only_v6 as prepare
from runtime_search_path_v6 import expected_search_path

class Contracts(unittest.TestCase):
    def test_all_scientific_trial_and_acceptance_methods_are_inherited(self):
        for name in ('trial','decide','run_group','registered','runtime_loader_preflight','freeze_group','check_best'):
            self.assertIs(getattr(controller.Phase5,name),getattr(controller.parent.Phase5,name))
        self.assertIsNot(controller.Phase5.run,controller.parent.Phase5.run)
        self.assertEqual(controller.AUDIT_PROOF['changed_expressions'],1)
        self.assertFalse(controller.AUDIT_PROOF['actual_sidecars_modified'])

    def test_expected_path_matches_real_frozen_benchmark_context_application(self):
        # Extract the exact original function; no native, MPI or benchmark run.
        target=Path(__file__).with_name('bench_full12_contract_source.py')
        module=ast.parse(target.read_text());function=next(n for n in module.body if isinstance(n,ast.FunctionDef)and n.name=='apply_context_environment')
        space={'os':os};exec(compile(ast.Module(body=[function],type_ignores=[]),str(target),'exec'),space)
        for old in (False,True):
            for passive in (False,True):
                context={}
                if old:context['LD_LIBRARY_PATH']='old-only:SDK:'
                if passive:context.update(OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT=0)
                with patch.dict(os.environ,{'LD_LIBRARY_PATH':controller.MPI_PREFIX+'SDK:'},clear=True):
                    space['apply_context_environment'](context,[])
                    expected=expected_search_path(context,'SDK:',controller.MPI_PREFIX)
                    self.assertEqual(os.environ['LD_LIBRARY_PATH'],expected)
                    row=capture.policy.runtime_environment_snapshot([(k+'='+v).encode()for k,v in os.environ.items()],
                        dict(context,LD_LIBRARY_PATH=expected),expected)
                    self.assertEqual(row['LD_LIBRARY_PATH'],expected)

    def test_wrong_environment_is_rejected_for_both_explicit_and_inherited_paths(self):
        for context in ({},{'LD_LIBRARY_PATH':'old:SDK:'}):
            expected=expected_search_path(context,'SDK:',controller.MPI_PREFIX)
            request=dict(context,LD_LIBRARY_PATH=expected)
            for lines in ([b'LD_LIBRARY_PATH=wrong'],[("LD_LIBRARY_PATH="+expected).encode(),b'LD_PRELOAD=/extra.so']):
                with self.assertRaises(ValueError):capture.policy.runtime_environment_snapshot(lines,request,expected)
        for context,base in (({},''),({'LD_LIBRARY_PATH':''},'SDK'),({'LD_LIBRARY_PATH':None},'SDK')):
            with self.assertRaises(ValueError):expected_search_path(context,base,controller.MPI_PREFIX)

    def test_dispatch_requires_full_budget_and_same_actual_parent(self):
        contract=dict(schema='runtime-only-scope-v6',complete=True,host='cn',allocation='new',expected_parent_cpus=[1,2],startup_ld_library_path='SDK')
        args=[contract,'cn','new',1000,6000,[1,2],False,'SDK'];scope.validate(*args)
        for index,value in ((1,'other'),(2,'old'),(4,5889),(5,[1]),(6,True),(7,'extra')):
            bad=list(args);bad[index]=value
            with self.assertRaises(RuntimeError):scope.validate(*bad)

    def test_terminal_cleanup_requires_integer_code_and_no_survivors(self):
        row=dict(status='failed',returncode=1,task_tag='owned',cleanup=dict(complete=True,surviving_pids=[]))
        self.assertTrue(prepare.closed(row,'failed'));self.assertFalse(prepare.closed(row,'passed'))
        for changed in (dict(row,returncode=True),dict(row,returncode=0),dict(row,status='running'),dict(row,task_tag=''),
            dict(row,cleanup=dict(complete=True,surviving_pids=[42]))):self.assertFalse(prepare.closed(changed,'failed'))

if __name__=='__main__':unittest.main(verbosity=2)
