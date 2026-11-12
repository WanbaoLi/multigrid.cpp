#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
unset NATIVE_OUTER_FLOAT LQCD_OUTER_FLOAT
export LQCD_VERBOSE=0 LQCD_HBW_ALLOC=require
SOURCE=/home/share/nsls_lwb/.cache/mg-opt-20261103/source-delivery-297
LIB=/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so
"$FAIR_PYTHON" "$SOURCE/tools/run_numa.py" --threads 37 -- \
 "$FAIR_PYTHON" -u "$TASK/ours_original.py" --out "$TASK/results/original-control" \
 --library "$LIB" --threads 37 --setup-threads 37
