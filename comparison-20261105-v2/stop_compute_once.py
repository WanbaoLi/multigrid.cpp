import json,os,signal,socket
from pathlib import Path
assert socket.gethostname()=='cn19486'
q=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2/compute-queue')
for p in q.glob('*.status.json'):
    r=json.loads(p.read_text())
    if r['status']!='running':continue
    proc=Path('/proc')/str(r['pid'])
    assert proc.stat().st_uid==os.getuid()and ('LQCD_OPT_TASK_ID='+r['task_tag']).encode()in(proc/'environ').read_bytes().split(b'\0')
    os.kill(r['pid'],signal.SIGTERM);print('TERM_OWNED',r['pid'])
