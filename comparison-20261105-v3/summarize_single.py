import json,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v3');old=root.with_name('fair-solve-20261105-v2')
rows=[]
for label,solver,path in(('login','ours',old/'results/login-128-ours-full/result.json'),
 ('login','pyqcu',old/'login-single-accepted.json'),('compute','ours',root/'results/compute-592-ours-full/result.json'),
 ('compute','pyqcu',root/'results/compute-592-pyqcu-full/result.json')):
    if not path.exists():continue
    r=json.loads(path.read_text())
    if label=='login'and solver=='pyqcu':
        assert r['complete'];s=r['sample'];cols=s['columns'];residual=max(c['independent_true_relative_residual']for c in cols)
    else:
        if solver=='ours'and not r.get('complete'):continue
        if solver=='pyqcu'and(r.get('status')!='PASS'or len(r.get('samples',[]))!=1):continue
        s=r['samples'][0];cols=s['stats']if solver=='ours'else s['columns']
        residual=max(c['true_residual']if solver=='ours'else c['independent_true_relative_residual']for c in cols)
    assert len(cols)==12 and residual<=1e-8
    value=s['native_api_seconds']if solver=='ours'else s['native_seconds']
    row=dict(node=label,solver=solver,cores=128 if label=='login'else 592,native_solve_seconds=value,
        max_relative_residual=residual,columns=12,requested_stop=1e-8,selected_sample='first and only requested full12',source=str(path))
    if solver=='ours':row.update(internal_seconds=s['internal_seconds'],python_api_seconds=s['api_seconds'],iterations=[c['iterations']for c in cols])
    else:row.update(iterations=[c['total_known_iterations']for c in cols],residual_restarts=s['restarts'])
    rows.append(row)
result=dict(complete=len(rows)==4,epoch=time.time(),rows=rows,one_source_columns=12,stout_steps=1,tol=1e-8,
    timing='Native solve API only; init/smear/Clover/setup/IO/external verification excluded')
if result['complete']:
    out=root/'summary.json'
    if out.exists():assert json.loads(out.read_text())['rows']==rows
    else:out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
