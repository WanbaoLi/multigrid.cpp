"""Fresh three-case default-runtime confirmation after excessive control drift."""
from pathlib import Path
import file_integrity as integrity
import phase5_runtime_only_v6 as initial
parent=initial.parent;base=initial.base

class Phase5(parent.Phase5):
    def __init__(self,args):
        super().__init__(args)
        proof=dict(entry_sha256=parent.sha(__file__),parent_sha256=initial.PARENT_SHA,
            inherited_runtime_audit_ast=initial.AUDIT_PROOF,scope='Fresh SDK-default / old-default / SDK-default only',
            reason='Prior five-case controls drifted beyond5%; PASSIVE was consistently much slower. Confirm default runtimes under subsequent resource conditions.',
            old_samples_imported=False,scientific_trial_precision_and_decision_methods_unchanged=True)
        old=self.state.get('runtime_confirm_v7_contract');self.require(old is None or old==proof,'Confirmation contract changed')
        self.state['runtime_confirm_v7_contract']=proof;self.save()
    def run(self):
        self.require(not self.state['complete'],'New confirmation identity required')
        all_cases=base.runtime_variants(self.state['initial_configuration'],self.args.prefix,self.shim_manifest)
        variants=[all_cases[i]for i in(0,2,4)]
        if not self.run_group('runtime',variants,'147 default control drift exceeded5%; repeat all default-runtime measurements in three fresh processes. No old controls or candidate timings are reused.',runtime=True):return
        self.state.update(complete=True,status='complete',pending_reason=None,finished=self.ledger.now());self.save()

def main():
    integrity.read_dual(parent.__file__,initial.PARENT_SHA)
    base.Phase5.runtime_audit=initial.AUDIT;base.SetupObserver=parent.SetupObserver;base.Phase5=Phase5;base.main()
if __name__=='__main__':main()
