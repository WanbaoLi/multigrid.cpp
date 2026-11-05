import json,os,signal,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v1')
for q in('login','compute'):
    queue=root/(q+'-queue')
    (queue/'STOP').write_text('User superseded1e-10 with1e-8; new directory and runs required\n')
    for path in queue.glob('*.status.json'):
        r=json.loads(path.read_text())
        if r['status']!='running':continue
        pid=r['pid'];proc=Path('/proc')/str(pid)
        try:
            assert proc.stat().st_uid==os.getuid()
            assert ('LQCD_OPT_TASK_ID='+r['task_tag']).encode()in(proc/'environ').read_bytes().split(b'\0')
            os.kill(pid,signal.SIGTERM)
            print('SUPERSEDED_TASK_TERM',q,pid)
        except FileNotFoundError:pass
(root/'superseded.json').write_text(json.dumps(dict(epoch=time.time(),reason='User changed precision to1e-8; keep old results excluded',replacement='/home/share/nsls_lwb/.cache/fair-solve-20261105-v2'),indent=2)+'\n')
