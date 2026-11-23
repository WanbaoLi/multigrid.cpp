#!/usr/bin/env bash
set -eo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
stage=$1
work=$2
gauge=$3
grid_sha=3232b438f2cf729e515c185e2dbf29d7cc276bb7
lime_sha=924aa0fce27a6cd73d94c9adc4b995f00e13232b
gauge_sha=f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326
mass=-0.279
csw=1.160678675188

case "$stage" in
    grid|native-one|native-two) ;;
    *) echo "Unknown stage: $stage" >&2; exit 2 ;;
esac

out="$work/$stage"
mkdir -p "$out"
git -C "$root" rev-parse HEAD > "$out/source-commit.txt"
printf '%s  %s\n' "$gauge_sha" "$gauge" | sha256sum -c
source "$root/tools/multinode/ls_env.sh"
hostname -s
lscpu

if [[ $stage == native-one ]]; then
    bash "$root/tools/multinode/gate_ls.sh" "$work/native-build"
fi

unset OMPI_MCA_ras OMPI_MCA_plm
export OMPI_MCA_coll=basic,tuned,self,libnbc
export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export OMPI_MCA_btl_tcp_if_include=10.36.0.0/16 OMPI_MCA_oob_tcp_if_include=10.36.0.0/16
export OMP_WAIT_POLICY=PASSIVE

if [[ $stage == grid ]]; then
    export GRID_PLATFORM=ls GRID_WORK="$out" GRID_GAUGE="$gauge"
    export GRID_SOURCE="$work/upstream/Grid" GRID_CHEBYSHEV_SETUP=1 GRID_BUILD_JOBS=24
    lime="$work/upstream/.cache/grid-node5006-wall/lime-src"
    test "$(git -C "$GRID_SOURCE" rev-parse HEAD)" = "$grid_sha"
    test "$(git -C "$lime" rev-parse HEAD)" = "$lime_sha"
    cmake -S "$lime" -B "$out/lime-build" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_INSTALL_LIBDIR=lib \
        -DCMAKE_INSTALL_PREFIX="$out/lime-install"
    cmake --build "$out/lime-build" -j 8
    cmake --install "$out/lime-build"
    exec bash "$root/experiments/node5006-grid-wall-20261122/run.sh"
fi

if [[ $stage == native-one ]]; then ranks=16; else ranks=32; fi
build="$work/native-build/build"
sha256sum "$build/liblqcd_cpu.so" "$build/verify_slab" > "$out/build.sha256"
export PYTHONPATH="$root/bindings"
export LQCD_DISTRIBUTED_STORAGE=1 LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1
export LQCD_ARM_COARSE_SVE=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_COARSE_FUSED=0 LQCD_COARSE_SPATIAL_OVERLAP=1 LQCD_COARSE_BATCH_REDUCE=1
export LQCD_HBW_ALLOC=prefer LQCD_HBM=off
run=(mpirun -n "$ranks" --bind-to none python "$root/tools/multinode/rank_exec.py")
if [[ $stage == native-two ]]; then
    timeout 120 "${run[@]}" python -u "$root/tests/runtime/test_multinode_communication.py"
fi
scratch="/tmp/lqcd-ls-wall-${CCS_JOB_ID:-manual}-$(basename "$out")"
"${run[@]}" python -u "$root/benchmarks/runtime/benchmark_multinode.py" \
    --gauge "$gauge" --library "$build/liblqcd_cpu.so" --output "$out/measurements" --scratch "$scratch" \
    --lattice 24 24 24 64 --block 6 6 6 2 --mass "$mass" --csw "$csw" --tol 1e-8 --source wall
"${run[@]}" "$build/verify_slab" "$scratch" 24 64 "$mass" "$csw" 1e-8 0 13 wall \
    | tee "$out/second-round-residuals.log"
grep -qx SCALAR_ALL_PASSED "$out/second-round-residuals.log"

mpirun -n "$ranks" --bind-to none python -c '
import os
from pathlib import Path
import sys
if int(os.environ["OMPI_COMM_WORLD_LOCAL_RANK"]) == 0:
    root = Path(sys.argv[1])
    assert root.parent == Path("/tmp") and root.name.startswith("lqcd-ls-wall-")
    for path in root.glob("*.bin"):
        path.unlink()
    root.rmdir()
' "$scratch"
