#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
test -f "$TASK/sap-build-passed"
mode=$1
case "$mode" in
sap-control) export LQCD_SAP_SCHEDULE=0 ;;
sap-compact) export LQCD_SAP_SCHEDULE=1 ;;
sap-columns) export LQCD_SAP_SCHEDULE=2 ;;
*) exit 2 ;;
esac
export LQCD_OUTER_FLOAT=1 LQCD_RELIABLE_FUSED=1 LQCD_VERBOSE=0 LQCD_HBW_ALLOC=require
"$FAIR_PYTHON" "$TASK/source-sap/tools/run_numa.py" --threads 37 -- \
 "$FAIR_PYTHON" -u "$TASK/ours_sap.py" --out "$TASK/results/$mode" \
 --library "$TASK/build-sap/liblqcd_cpu.so" --threads 37 --setup-threads 37
