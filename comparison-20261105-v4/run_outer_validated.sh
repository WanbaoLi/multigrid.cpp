#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
test -f "$TASK/outer-build-passed"
mode=$1
unset NATIVE_OUTER_FLOAT
case "$mode" in
baseline-v2) export LQCD_OUTER_FLOAT=1 ;;
mixed-single-v2) export LQCD_OUTER_FLOAT=1 LQCD_RHS_BATCH=1 ;;
double-outer-v2) export LQCD_OUTER_FLOAT=0 ;;
*) echo 'Invalid precision experiment mode' >&2; exit 2 ;;
esac
export LQCD_VERBOSE=0 LQCD_HBW_ALLOC=require
SOURCE=$TASK/source-outer
LIB=$TASK/build-outer/liblqcd_cpu.so
"$FAIR_PYTHON" "$SOURCE/tools/run_numa.py" --threads 37 -- \
 "$FAIR_PYTHON" -u "$TASK/ours_mode.py" --out "$TASK/results/$mode" \
 --library "$LIB" --threads 37 --setup-threads 37
