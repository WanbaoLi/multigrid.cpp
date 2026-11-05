"""Read only per-thread CPU/affinity for owned active experimental descendants."""
import json,os
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v1')
rows=[]
for status in(root/'login-queue').glob('*.status.json'):
    r=json.loads(status.read_text())
    if r['status']!='running':continue
    marker=('LQCD_OPT_TASK_ID='+r['task_tag']).encode()
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if p.stat().st_uid!=os.getuid()or marker not in(p/'environ').read_bytes().split(b'\0'):continue
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            tids=list((p/'task').glob('[0-9]*'))
            if len(tids)<16:continue
            cpus=[];widths=[]
            for t in tids:
                text=(t/'stat').read_text();f=text[text.rfind(')')+2:].split();cpus.append(int(f[36]))
                widths.append(len(os.sched_getaffinity(int(t.name))))
            rows.append(dict(pid=int(p.name),threads=len(tids),last_cpu_distinct=len(set(cpus)),affinity_widths=sorted(set(widths)),cpu_list=sorted(set(cpus))))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
print(json.dumps(rows,indent=2))
