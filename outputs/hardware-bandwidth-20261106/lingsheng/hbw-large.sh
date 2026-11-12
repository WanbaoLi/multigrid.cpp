#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hbw-large-working-set
#DSUB -N 1
#DSUB -R "cpu=592;mem=192G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/hbw-large.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/hbw-large.stderr
#DSUB -T 900
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105
SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
export LD_LIBRARY_PATH="$SDK/kupl/gcc/release/lib:$SDK/compiler/gcc/lib64:${LD_LIBRARY_PATH}"
export LD_PRELOAD="$SDK/compiler/gcc/lib64/libstdc++.so.6"
cd "$TASK"
python - "$TASK/matched-ddr.plan" "$TASK/matched-hbw.plan" <<'PY'
from pathlib import Path
import os,sys

def ids(s):
 a=list(map(int,s.strip().split('-')));return list(range(a[0],a[-1]+1))
allowed=set(os.sched_getaffinity(0)); plans=[[],[]]
for group in range(15):
 cpus=[c for c in ids((Path('/sys/devices/system/node')/f'node{group}'/'cpulist').read_text()) if c in allowed][:37]
 plans[0]+=[f'{group} {c} {group}' for c in cpus]
 plans[1]+=[f'{group} {c} {16+group}' for c in cpus]
for path,lines in zip(sys.argv[1:],plans):Path(path).write_text('\n'.join(lines)+'\n')
PY
./compute-r5/bandwidth_bench --plan "$TASK/matched-hbw.plan" --kupl-lib "$SDK/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001" --mib-per-array-per-group 1024 --passes 16 --repeats 5 > "$TASK/hbw-large.json"
python - <<'CHECK'
import json
p=json.load(open('hbw-large.json'));assert p['status']=='PASS'
assert all(a['sdk_verify_before']==1 and a['sdk_verify_after']==1 for g in p['placement'] for a in g['arrays'])
print('HBW_LARGE_PASS',[(k['kernel'],k['median_gb_per_second']) for k in p['kernels']])
CHECK
