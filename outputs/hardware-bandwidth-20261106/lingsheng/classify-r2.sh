#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hbwmemory-classify
#DSUB -N 1
#DSUB -R "cpu=592;mem=192G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/classify-r2.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/classify-r2.stderr
#DSUB -T 1800
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105
SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
export LD_LIBRARY_PATH="$SDK/kupl/gcc/release/lib:$SDK/compiler/gcc/lib64:${LD_LIBRARY_PATH}"
export LD_PRELOAD="$SDK/compiler/gcc/lib64/libstdc++.so.6"
cd "$TASK"
date -Is
hostname
python probe_classes.py "$SDK/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001" /work_ssd/software/soft/tool/hpckit/2026.1.RC1/HPCKit/26.1.RC1/kupl/bisheng/release/lib/libkupl.so.1.26.1.RC1 "$TASK/classes-r2.json"
