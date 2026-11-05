#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
mode=$1
case "$mode" in
baseline) export NATIVE_OUTER_FLOAT=1 ;;
mixed-single) export NATIVE_OUTER_FLOAT=1 LQCD_RHS_BATCH=1 ;;
double-outer) export NATIVE_OUTER_FLOAT=0 ;;
*) echo "mode baseline or double-outer" >&2; exit 2 ;;
esac
export LQCD_VERBOSE=0
SOURCE=/home/share/nsls_lwb/.cache/mg-opt-20261103/source-delivery-297
LIB=/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so
"$FAIR_PYTHON" "$SOURCE/tools/run_numa.py" --threads 37 -- \
  "$FAIR_PYTHON" -u "$TASK/ours_full.py" --out "$TASK/results/$mode" \
  --library "$LIB" --threads 37 --setup-threads 37
