#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hardware-flops-probe
#DSUB -N 1
#DSUB -R "cpu=592;mem=16G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-flops-v20261105/probe.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-flops-v20261105/probe.stderr
#DSUB -T 300
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-flops-v20261105
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
hostname
lscpu
command -v g++
command -v clang++
g++ --version | head -n 1
clang++ --version | head -n 1
python - "$TASK" <<'PY'
import ctypes,json,os,platform,subprocess,sys
from pathlib import Path
libc=ctypes.CDLL(None)
vl=libc.prctl(51,0,0,0,0)
d=dict(hostname=platform.node(),allowed_cpus=sorted(os.sched_getaffinity(0)),
 allowed_status=[s for s in Path('/proc/self/status').read_text().splitlines() if s.startswith(('Cpus_allowed_list:','Mems_allowed_list:'))],
 cpuinfo=Path('/proc/cpuinfo').read_text().split('\n\n')[0],
 lscpu=subprocess.check_output(['lscpu','-J'],text=True),
 sve_vl_bytes=(vl&65535) if vl>=0 else None,
 numa_cpus={p.parent.name:p.read_text().strip() for p in Path('/sys/devices/system/node').glob('node*/cpulist')})
(Path(sys.argv[1])/'results'/'probe-host.json').write_text(json.dumps(d,indent=2)+'\n')
print('PROBE_READY',json.dumps(dict(hostname=d['hostname'],allowed_cpus=len(d['allowed_cpus']),sve_vl_bytes=d['sve_vl_bytes'])))
PY
