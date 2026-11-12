#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n hardware-flops
#DSUB -N 1
#DSUB -R "cpu=592;mem=16G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-flops-v20261105/run.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-flops-v20261105/run.stderr
#DSUB -T 900
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-flops-v20261105
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
unset LD_PRELOAD
cd "$TASK"
date -Is
hostname
timeout --signal=TERM --kill-after=10s 600 python run_suite.py \
  --compiler /work_ssd/software/soft/tool/hpckit/2026.1.RC1/HPCKit/26.1.RC1/compiler/bisheng/bin/clang++ \
  --output "$TASK/compute" --seconds 2 --repeats 3
date -Is
