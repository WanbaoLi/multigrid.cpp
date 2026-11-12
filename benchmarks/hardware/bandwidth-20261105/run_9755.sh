#!/usr/bin/env bash
set -eo pipefail
TASK=/public2/home/lwb_720/.cache/hardware-bandwidth-v20261105
export LD_LIBRARY_PATH=/public2/home/lwb_720/miniconda3/lib:${LD_LIBRARY_PATH:-}
unset LD_PRELOAD
cd "$TASK"
date -Is
hostname
/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python probe_memory.py "$TASK/actual-probe"
timeout --signal=TERM --kill-after=10s 1500 /public2/home/lwb_720/miniconda3/envs/pyquda/bin/python run_suite.py \
  --compiler /public2/home/lwb_720/miniconda3/bin/g++ --output "$TASK/amd9755-r4"
date -Is
