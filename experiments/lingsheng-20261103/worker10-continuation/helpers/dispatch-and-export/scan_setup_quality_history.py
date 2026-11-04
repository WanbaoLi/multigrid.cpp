"""Read only declared hierarchy-quality choices in retained campaign plans."""
import json
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');keys={'LQCD_MG_SETUP_PASSES','LQCD_MG_SETUP_ITERATIONS','LQCD_MG_SETUP_SMOOTH','LQCD_SETUP_UPDATE'}
rows=[];count=0
for campaign in sorted(root.glob('campaign*')):
    if not campaign.is_dir():continue
    for path in sorted(campaign.glob('attempts/*/plan.json')):
        count+=1;plan=json.loads(path.read_text());context=plan.get('context_environment',{})
        values={k:v for k,v in context.items()if k in keys}
        if values:rows.append(dict(campaign=campaign.name,attempt=path.parent.name,choices=values))
print(json.dumps(dict(plans_examined=count,explicit_quality_cases=rows),indent=2))
