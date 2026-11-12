#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
test -f "$TASK/reliable-build-passed"
mode=$1
unset NATIVE_OUTER_FLOAT
case "$mode" in
reliable-off) export LQCD_OUTER_FLOAT=1 LQCD_RELIABLE_FUSED=0 ;;
reliable-on) export LQCD_OUTER_FLOAT=1 LQCD_RELIABLE_FUSED=1 ;;
*) exit 2 ;;
esac
export LQCD_VERBOSE=0 LQCD_HBW_ALLOC=require
SOURCE=$TASK/source-reliable
"$FAIR_PYTHON" "$SOURCE/tools/run_numa.py" --threads 37 -- \
 "$FAIR_PYTHON" -u "$TASK/ours_reliable.py" --out "$TASK/results/$mode" \
 --library "$TASK/build-reliable/liblqcd_cpu.so" --threads 37 --setup-threads 37
