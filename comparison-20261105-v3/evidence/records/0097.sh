#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v3
source "$TASK/ours_env.sh"
SOURCE=/home/share/nsls_lwb/.cache/mg-opt-20261103/source-delivery-297
label=$1; configuration=$2; mode=${3:-full}
if [[ $label == login ]]; then
 LIB=$TASK/build-login/liblqcd_cpu.so
else
 LIB=/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so
fi
if [[ $configuration == 128 ]]; then placement=(--numa-nodes 0,1,2,3 --threads 32); threads=32
else placement=(--threads 37);threads=37;export LQCD_HBW_ALLOC=require;fi
extra=();if [[ $mode == pilot ]]; then extra=(--pilot);fi
"$FAIR_PYTHON" "$SOURCE/tools/run_numa.py" "${placement[@]}" -- \
 "$FAIR_PYTHON" -u "$TASK/ours_full.py" --out "$TASK/results/$label-$configuration-ours-$mode" --library "$LIB" --threads "$threads" --setup-threads "$([[ $configuration == 128 ]] && echo 32 || echo 37)" "${extra[@]}"
