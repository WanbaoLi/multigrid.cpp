import json
from pathlib import Path
import sys
from types import SimpleNamespace
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');aux=root/'aux-halo-v2-publication-v5';sys.path.insert(0,str(aux))
import file_integrity as integrity
import halo_v2_trial_publication_v5 as trial
strict=trial.StrictFiles(integrity)
strict.sha(aux/'halo_v2_trial_publication_v5.py','a9afbc64994d5c48587d09e27f70dd74cd797516feb4c7adcf1ec45a6e61bb59')
state=strict.read(root/'153-halo-v2-remainder-worker10-state.json')
attempt=strict.read(root/'campaign-halo-v2/attempts/000-halo-v2-tests/attempt.json')
files=trial.validate_recovery(state,attempt,strict,aux)
status=strict.read(root/'queue10/153-halo-v2-remainder-worker10.status.json')
argv,guard=trial.external_test_argv(SimpleNamespace(root=root),strict,status)
print(json.dumps(dict(actual_closed13_case_provenance_passed=True,verified_pins=len(files),guard_pins=len(guard),original_entry=argv[2],whole_sve_matrix_complete=state.get('full_numerical_complete'),physical12_performance=False)))
