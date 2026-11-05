import json,statistics
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
rows=[]
for node,cores in(('login',128),('compute',128),('compute',592)):
    for solver in('ours','pyqcu'):
        p=root/'results'/f'{node}-{cores}-{solver}-full/result.json'
        if not p.exists():continue
        r=json.loads(p.read_text());samples=r.get('samples',[])
        ready=r.get('complete',False)if solver=='ours'else r.get('status')=='PASS'and len(samples)==2
        if not ready:continue
        key='native_api_seconds'if solver=='ours'else'native_seconds'
        steady=[s[key]for s in samples if not s['warmup']]
        residual=max(st['true_residual']for s in samples for st in s['stats'])if solver=='ours'else max(s['max_residual']for s in samples)
        assert residual<=1e-8
        row=dict(node=node,allocated_measurement_cores=cores,solver=solver,first_seconds=samples[0][key],steady_seconds=steady,
            steady_median_seconds=statistics.median(steady),max_residual=residual,sample_count=len(samples),
            timing='Sum of original native solve API wall times; shared batch timer counted once; all necessary corrections included')
        if solver=='ours':row.update(internal_solver_steady_seconds=[s['internal_seconds']for s in samples if not s['warmup']],setup_seconds=r['setup_seconds'])
        else:row.update(residual_restarts=sum(s['restarts']for s in samples),algorithm=r['solver_path'])
        rows.append(row)
result=dict(complete=len(rows)==6,stout_steps=1,requested_relative_tolerance=1e-8,rows=rows,scope='one source12zero-start columns; preprocessed common gauge; initialization reused')
if result['complete']:
    target=root/'summary.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
