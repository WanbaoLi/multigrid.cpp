#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hardware-bandwidth
#DSUB -N 1
#DSUB -R "cpu=592;mem=192G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/run-r5.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/run-r5.stderr
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
python probe_memory.py "$TASK/actual-probe" "$SDK/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001"
timeout --signal=TERM --kill-after=10s 1500 python run_suite.py \
  --compiler /work_ssd/software/soft/tool/hpckit/2026.1.RC1/HPCKit/26.1.RC1/compiler/bisheng/bin/clang++ \
  --output "$TASK/compute-r5" --kupl-lib "$SDK/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001"
date -Is
