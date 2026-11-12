#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n memory261-large
#DSUB -N 1
#DSUB -R "cpu=592;mem=192G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/memory261-large.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/memory261-large.stderr
#DSUB -T 900
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105
HP=/work_ssd/software/soft/tool/hpckit/2026.1.RC1/HPCKit/26.1.RC1
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
export LD_LIBRARY_PATH="$HP/kupl/gcc/release/lib:$HP/compiler/gcc/lib64:${LD_LIBRARY_PATH}"
cd "$TASK"
python - "$TASK/hbw261.plan" <<'PY'
from pathlib import Path
import os
out=Path(__import__('sys').argv[1]);lines=[];allowed=set(os.sched_getaffinity(0))
def ids(s):
 a=list(map(int,s.strip().split('-')));return list(range(a[0],a[-1]+1))
for group in range(16):
 cpus=[c for c in ids((Path('/sys/devices/system/node')/f'node{group}'/'cpulist').read_text()) if c in allowed][:37]
 lines += [f'{group} {c} {16+group}' for c in cpus]
out.write_text('\n'.join(lines)+'\n')
PY
python - <<'PLAN'
from pathlib import Path
rows=[]
for line in Path('hbw261.plan').read_text().splitlines():
 g,c,n=map(int,line.split());rows.append(f'{g} {c} {g}')
Path('ddr261.plan').write_text('\n'.join(rows)+'\n')
PLAN
./compute-r5/bandwidth_bench --plan "$TASK/ddr261.plan" --kupl-lib "$HP/kupl/gcc/release/lib/libkupl.so.1.26.1.RC1" --mib-per-array-per-group 1024 --passes 16 --repeats 5 > "$TASK/ddr261-large.json"
./compute-r5/bandwidth_bench --plan "$TASK/hbw261.plan" --kupl-lib "$HP/kupl/gcc/release/lib/libkupl.so.1.26.1.RC1" --mib-per-array-per-group 1024 --passes 16 --repeats 5 > "$TASK/hbw261-large.json"
python - <<'CHECK'
import json
for name,expected in [('ddr261-large',0),('hbw261-large',1)]:
 p=json.load(open(name+'.json'));assert p['status']=='PASS'
 assert all(a['sdk_verify_before']==expected and a['sdk_verify_after']==expected for g in p['placement'] for a in g['arrays'])
 print(name,[(k['kernel'],k['median_gb_per_second']) for k in p['kernels']])
CHECK
