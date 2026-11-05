import json,os,signal,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
for node in('compute','login'):
    q=root/(node+'-queue');(q/'STOP').write_text('User changed to one full12 with all cores; preserve all old records\n')
    if node=='compute':
        for p in q.glob('*.status.json'):
            r=json.loads(p.read_text())
            if r['status']!='running':continue
            proc=Path('/proc')/str(r['pid'])
            try:
                assert ('LQCD_OPT_TASK_ID='+r['task_tag']).encode()in(proc/'environ').read_bytes().split(b'\0')
                os.kill(r['pid'],signal.SIGTERM);print('TERM_COMPUTE_SUPERSEDED',r['pid'])
            except FileNotFoundError:pass
target=root/'results/login-128-pyqcu-full/result.json'
while True:
    r=json.loads(target.read_text())
    if len(r.get('samples',[]))>=1:
        s=r['samples'][0];assert s['max_residual']<=1e-8 and len(s['columns'])==12
        p=root/'login-queue/pyqcu-128-full.status.json';task=json.loads(p.read_text())
        # One completed full12 call is retained; suppress second repetition.
        if task['status']=='running':
            proc=Path('/proc')/str(task['pid'])
            assert ('LQCD_OPT_TASK_ID='+task['task_tag']).encode()in(proc/'environ').read_bytes().split(b'\0')
            os.kill(task['pid'],signal.SIGTERM)
        (root/'login-single-accepted.json').write_text(json.dumps(dict(complete=True,user_requested_one_call=True,source=str(target),sample=s,epoch=time.time()),indent=2)+'\n')
        print('LOGIN_ONE_FULL12_COMPLETE',s['native_seconds'],flush=True);break
    time.sleep(2)
