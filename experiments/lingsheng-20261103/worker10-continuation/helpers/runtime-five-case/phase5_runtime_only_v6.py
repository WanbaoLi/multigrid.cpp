"""Fresh five-case runtime bracket after attributed pre-setup capture failure.

No old trial is retried, imported, overwritten or treated as complete. Frozen
c5 numerical trials, loader tests, precision, closure and promotion gates stay.
"""
import ast
from copy import deepcopy
import hashlib
import inspect
from pathlib import Path
import textwrap
import file_integrity as integrity
import phase5_worker7_v3 as parent
from runtime_search_path_v6 import expected_search_path

PARENT_SHA='84c71468e4bf64da1aa5ea254caf2de65b92531421cbad3a18faf896337f3937'
MPI_PREFIX='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/hmpi/bisheng/release/hmpi/lib:'*2
base=parent.base

def patched_runtime_audit(original):
    tree=ast.parse(textwrap.dedent(inspect.getsource(original)));before=deepcopy(tree)
    candidates=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='expected_runtime'for t in node.targets):
            candidates.extend(k for k in node.value.keywords if k.arg=='LD_LIBRARY_PATH')
    integrity.require(len(candidates)==1,'Exactly one frozen expected LD expression required')
    selected=candidates[0];old=selected.value
    selected.value=ast.parse("_expected_search_path_v6(context,self.shim_manifest['base_ld_library_path'],_MPI_PREFIX_V6)",mode='eval').body
    changed=ast.dump(tree,include_attributes=False);selected.value=old
    integrity.require(ast.dump(tree,include_attributes=False)==ast.dump(before,include_attributes=False),'Unrequested audit AST change')
    selected.value=ast.parse("_expected_search_path_v6(context,self.shim_manifest['base_ld_library_path'],_MPI_PREFIX_V6)",mode='eval').body
    ast.fix_missing_locations(tree)
    scope=dict(original.__globals__,_expected_search_path_v6=expected_search_path,_MPI_PREFIX_V6=MPI_PREFIX)
    exec(compile(tree,str(Path(__file__).resolve())+':expected-environment-only','exec'),scope)
    return scope[original.__name__],dict(changed_expressions=1,actual_sidecars_modified=False,
        original_ast_sha256=hashlib.sha256(ast.dump(before,include_attributes=False).encode()).hexdigest(),
        transformed_ast_sha256=hashlib.sha256(changed.encode()).hexdigest())

AUDIT,AUDIT_PROOF=patched_runtime_audit(base.Phase5.runtime_audit)

class Phase5(parent.Phase5):
    def __init__(self,args):
        super().__init__(args)
        proof=dict(entry_sha256=parent.sha(__file__),parent_sha256=PARENT_SHA,
            expected_ld_policy='Explicit context overrides launch environment; absent key preserves fixed MPI prefix plus startup path',
            audit_expression=AUDIT_PROOF,scope='Five fresh runtime cases only; fixed-team group not repeated or reclassified',
            inherited_trial_precision_closure_and_decision_methods=True)
        prior=self.state.get('runtime_only_v6_contract')
        self.require(prior is None or prior==proof,'Runtime-only boundary changed; use a new identity')
        self.state['runtime_only_v6_contract']=proof;self.save()

    def run(self):
        self.require(not self.state['complete'],'New fresh runtime-only phase required')
        cfg=self.state['initial_configuration']
        variants=base.runtime_variants(cfg,self.args.prefix,self.shim_manifest)
        if not self.run_group('runtime',variants,
            '141 failed before setup because its capture expected an MPI prefix after an explicit benchmark context overwrite. '
            'New five-case bracket repeats all runtime measurements with exact post-context expectation; no prior timing reuse.',runtime=True):return
        self.state.update(complete=True,status='complete',pending_reason=None,finished=self.ledger.now())
        self.save()

def main():
    integrity.read_dual(parent.__file__,PARENT_SHA)
    base.Phase5.runtime_audit=AUDIT
    base.SetupObserver=parent.SetupObserver;base.Phase5=Phase5
    base.main()

if __name__=='__main__':main()
