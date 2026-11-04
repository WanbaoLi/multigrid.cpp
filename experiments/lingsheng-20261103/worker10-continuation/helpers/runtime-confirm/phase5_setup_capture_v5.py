"""Frozen scientific phase5 with explicit observed HMPI loader-prefix contract."""
import ast
from copy import deepcopy
import hashlib
import inspect
from pathlib import Path
import textwrap

import file_integrity as integrity
import phase5_worker7_v3 as parent

PARENT_SHA='84c71468e4bf64da1aa5ea254caf2de65b92531421cbad3a18faf896337f3937'
HMPI_LIB='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/hmpi/bisheng/release/hmpi/lib'
MPI_PREFIX=HMPI_LIB+':'+HMPI_LIB+':'
base=parent.base


def effective_search_path(requested):
    integrity.require(isinstance(requested,str)and bool(requested),'Explicit requested loader path required')
    return MPI_PREFIX+requested


def patched_runtime_audit(original):
    """Change exactly the expected LD expression; actual sidecars stay untouched."""
    source=textwrap.dedent(inspect.getsource(original));tree=ast.parse(source)
    candidates=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='expected_runtime'for t in node.targets):
            candidates.extend(k for k in node.value.keywords if k.arg=='LD_LIBRARY_PATH')
    integrity.require(len(candidates)==1,'Frozen runtime audit must contain exactly one expected LD expression')
    selected=candidates[0];before=deepcopy(tree);old=selected.value
    selected.value=ast.Call(func=ast.Name(id='_effective_search_path_v5',ctx=ast.Load()),args=[old],keywords=[])
    changed=ast.dump(tree,include_attributes=False)
    selected.value=old
    integrity.require(ast.dump(tree,include_attributes=False)==ast.dump(before,include_attributes=False),'Unexpected audit AST mutation')
    selected.value=ast.Call(func=ast.Name(id='_effective_search_path_v5',ctx=ast.Load()),args=[old],keywords=[])
    ast.fix_missing_locations(tree)
    scope=dict(original.__globals__,_effective_search_path_v5=effective_search_path)
    exec(compile(tree,str(Path(__file__).resolve())+':runtime-audit-expected-LD-only','exec'),scope)
    proof=dict(original_ast_sha256=hashlib.sha256(ast.dump(before,include_attributes=False).encode()).hexdigest(),
               transformed_ast_sha256=hashlib.sha256(changed.encode()).hexdigest(),
               changed_expressions=1,actual_sidecars_modified=False,
               change='Expected LD_LIBRARY_PATH = fixed observed HMPI prefix + requested per-case search string')
    return scope[original.__name__],proof


class Phase5(parent.Phase5):
    def __init__(self,args):
        super().__init__(args)
        proof=dict(entry_sha256=parent.sha(__file__),parent_sha256=PARENT_SHA,
            mpi_prefix=MPI_PREFIX,capture_point='after gauge load, before original setup',
            audit_expression_change=AUDIT_PROOF,ordinary_timing_and_numerical_methods_unchanged=True)
        prior=self.state.get('runtime_capture_v5_contract')
        self.require(prior is None or prior==proof,'New runtime capture policy changed; retain old state')
        self.state['runtime_capture_v5_contract']=proof;self.save()


AUDIT, AUDIT_PROOF=patched_runtime_audit(base.Phase5.runtime_audit)


def main():
    integrity.read_dual(parent.__file__,PARENT_SHA)
    base.Phase5.runtime_audit=AUDIT
    base.SetupObserver=parent.SetupObserver;base.Phase5=Phase5
    base.main()


if __name__=='__main__':main()
