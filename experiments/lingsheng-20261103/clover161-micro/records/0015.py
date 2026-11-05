import json
from pathlib import Path
import statistics
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');status=json.loads((root/'queue13/161-clover-reuse-micro-worker13.status.json').read_text())
out={k:status.get(k)for k in('status','started','ended','returncode','cleanup')}
path=root/'clover-micro-161-v1/result.json'
if path.exists():
    data=json.loads(path.read_text());out['micro']=[dict(sites=r['sites'],label=r['label'],median_seconds=statistics.median(v['seconds']for v in r['results']),maximum_oracle_error=max(v['max_abs_oracle_error']for v in r['results']))for r in data['rows']]
print(json.dumps(out,indent=2))
