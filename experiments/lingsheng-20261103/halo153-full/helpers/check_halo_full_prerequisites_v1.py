import json
from pathlib import Path
from types import SimpleNamespace
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-halo-v2-publication-v5';sys.path.insert(0,str(aux))
import file_integrity as integrity
import halo_v2_trial_publication_v5 as trial
strict=trial.StrictFiles(integrity);strict.sha(aux/'halo_v2_trial_publication_v5.py','a9afbc64994d5c48587d09e27f70dd74cd797516feb4c7adcf1ec45a6e61bb59')
argv=strict.read(root/'prepared-halo154-worker10/original-task.json')['argv']
a=SimpleNamespace(root=root,auxiliary=aux)
for key in('tests-state','tests-status','tests-state-sha','tests-status-sha','library-sha'):
 value=trial.option(argv,'--'+key);setattr(a,key.replace('-','_'),Path(value)if key in('tests-state','tests-status')else value)
sys.path.insert(0,str(root/'source-halo-v2-760/tools/optimization'));import campaign as ledger
ledger.digest=strict.sha;ledger.read=strict.read
proof=trial.external_tests(a,strict,ledger)
print(json.dumps(dict(complete=proof['complete'],full_actual_numerical_prerequisites=True,library_sha256=proof['library_sha256'],vector_lengths=proof['actual_vector_lengths'],stages=proof['test_stages'],pinned_files=len(proof['files']),physical_full12_evidence=proof['physical_full12_evidence'])))
