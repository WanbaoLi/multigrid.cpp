#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hbw15-bandwidth
#DSUB -N 1
#DSUB -R "cpu=592;mem=192G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/hbw15.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/hbw15.stderr
#DSUB -T 900
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105
SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
export LD_LIBRARY_PATH="$SDK/kupl/gcc/release/lib:$SDK/compiler/gcc/lib64:${LD_LIBRARY_PATH}"
export LD_PRELOAD="$SDK/compiler/gcc/lib64/libstdc++.so.6"
cd "$TASK"
python - "$TASK/hbw15.plan" <<'PY'
from pathlib import Path
out=Path(__import__('sys').argv[1]); lines=[]
def ids(s):
 a=list(map(int,s.strip().split('-'))); return list(range(a[0],a[-1]+1))
for group in range(15):
 cpus=ids((Path('/sys/devices/system/node')/f'node{group}'/'cpulist').read_text())
 allowed=set(__import__('os').sched_getaffinity(0)); cpus=[c for c in cpus if c in allowed][:8]
 lines += [f'{group} {cpu} {16+group}' for cpu in cpus]
out.write_text('\n'.join(lines)+'\n')
print(out.read_text())
PY
./compute-r5/bandwidth_bench --plan "$TASK/hbw15.plan" --kupl-lib "$SDK/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001" --mib-per-array-per-group 512 --passes 16 --repeats 5 > "$TASK/hbw15.json"
python - "$TASK/hbw15.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['status']=='PASS'
assert all(a['sdk_verify_before']==1 and a['sdk_verify_after']==1 for g in p['placement'] for a in g['arrays'])
print('HBW15_PASS',[(k['kernel'],k['median_gb_per_second']) for k in p['kernels']])
PY