#!/usr/bin/env bash
# Small correctness probe only; this is not a full-solver performance benchmark.
set -eo pipefail
out=$1
build=$2
root=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$out"
exec > >(tee "$out/probe.log") 2>&1
source "$root/tools/multinode/ls_env.sh"
git -C "$root" rev-parse HEAD > "$out/driver-commit.txt"
hostname
date -u
getconf PAGESIZE
grep -E 'Cpus_allowed_list|Mems_allowed_list' /proc/self/status
lscpu -J > "$out/lscpu.json"
cat /proc/meminfo > "$out/meminfo.txt"
export OMP_NUM_THREADS=32 OMP_PLACES=cores OMP_PROC_BIND=close
export LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1 LQCD_ARM_SVE_PLANNED=0
sha256sum "$build/arm_sve_test" "$build/arm_sve_plan_test" > "$out/binaries.sha256"
timeout 60s "$build/arm_sve_test"
timeout 60s "$build/arm_sve_plan_test"
echo SVE_REPORT_PROBE_FINISHED
