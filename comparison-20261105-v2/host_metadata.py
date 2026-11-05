import ctypes,json,os,platform,subprocess,sys,time
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2');label=sys.argv[1]
data=dict(epoch=time.time(),host=platform.node(),machine=platform.machine(),cpus=sorted(os.sched_getaffinity(0)),
    status=[s for s in Path('/proc/self/status').read_text().splitlines()if s.startswith(('Cpus_allowed_list','Mems_allowed_list'))],
    lscpu=subprocess.check_output(['lscpu'],text=True),load=Path('/proc/loadavg').read_text(),
    meminfo=Path('/proc/meminfo').read_text())
out=root/(label+'-host.json');assert not out.exists();out.write_text(json.dumps(data,indent=2)+'\n')
print('RECORDED_HOST',label,data['host'],len(data['cpus']),flush=True)
