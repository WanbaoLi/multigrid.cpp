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
    native-one-pair)
        LS_RANKS_PER_NODE=16 LS_RESULT_SUFFIX=16 bash "$0" native-one "$work" "$gauge"
        LS_RANKS_PER_NODE=32 LS_RESULT_SUFFIX=32 bash "$0" native-one "$work" "$gauge"
        exit 0
        ;;
    native-two-pair)
        LS_MPI_TRANSPORT=tcp LS_RESULT_SUFFIX=tcp bash "$0" native-two "$work" "$gauge"
        LS_MPI_TRANSPORT=ucx LS_RESULT_SUFFIX=ucx bash "$0" native-two "$work" "$gauge"
        exit 0
        ;;
    grid-build|grid-shard|grid-assemble|grid|halo-layout|native-build|native-one|native-two) ;;
    *) echo "Unknown stage: $stage" >&2; exit 2 ;;
esac

out="$work/$stage"
if [[ -n ${LS_RESULT_SUFFIX:-} ]]; then out="$out-$LS_RESULT_SUFFIX"; fi
if [[ $stage == grid-shard ]]; then out="$work/shards/shard-$GRID_SHARD"; fi
if [[ $stage == grid-assemble ]]; then out="$work/grid-build"; fi
mkdir -p "$out"
git -C "$root" rev-parse HEAD > "$out/source-commit.txt"
if [[ $stage == grid || $stage == native-build || $stage == native-one || $stage == native-two ]]; then
    printf '%s  %s\n' "$gauge_sha" "$gauge" | sha256sum -c
fi
source "$root/tools/multinode/ls_env.sh"
hostname -s
lscpu

if [[ $stage == native-build || $stage == native-one && ! -s $work/native-build/build/verify_slab ]]; then
    native_commit=5b99879f84f647d267dde6156e637ced64ca694f
    native_library="$HOME/lqcd-run/mg-l24-coarse-rescue-run01/liblqcd_cpu.so"
    git -C "$root" diff --exit-code "$native_commit" HEAD -- src include cmake CMakeLists.txt bindings
    printf '%s  %s\n' 8d1e7374d9e765225f20a0eb79cd61785e7fdadf092f22649e37da1a7662236d \
        "$native_library" | sha256sum -c
    native_tmp=$(mktemp -d /tmp/ls-wall-native.XXXXXXXX)
    trap 'rm -rf -- "$native_tmp"' EXIT
    if ! LS_SCALAR_GATE=1 bash "$root/tools/multinode/gate_ls.sh" "$native_tmp"; then
        cp "$native_tmp/gates.log" "$out/"
        exit 1
    fi
    mkdir -p "$work/native-build/build"
    cp "$native_library" "$native_tmp/build/verify_slab" "$work/native-build/build/"
    printf '%s\n' "$native_commit" > "$work/native-build/library-source-commit.txt"
    cp "$out/source-commit.txt" "$work/native-build/oracle-source-commit.txt"
    cp "$native_tmp/gates.log" "$native_tmp/ctest.log" "$out/"
fi
if [[ $stage == native-build ]]; then exit 0; fi

unset OMPI_MCA_ras OMPI_MCA_plm
export OMPI_MCA_coll=basic,tuned,self,libnbc
export OMPI_MCA_btl_tcp_if_include=10.36.0.0/16 OMPI_MCA_oob_tcp_if_include=10.36.0.0/16
export OMP_WAIT_POLICY=PASSIVE
case "${LS_MPI_TRANSPORT:-tcp}" in
    tcp) export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp ;;
    ucx)
        export OMPI_MCA_pml=ucx
        export UCX_TLS="${LS_UCX_TLS:-self,sm,rc}"
        # Explicitly select a routable IPv4 RoCE GID on the compute fabric.
        export UCX_NET_DEVICES="${UCX_NET_DEVICES:-roceroh0:1}"
        export UCX_IB_GID_INDEX="${UCX_IB_GID_INDEX:-1}"
        export UCX_MAX_RNDV_RAILS="${UCX_MAX_RNDV_RAILS:-1}"
        export LD_LIBRARY_PATH="$task_sdk/hmpi/bisheng/release/hucx/lib:$LD_LIBRARY_PATH"
        ;;
    *) echo "Unknown MPI transport: $LS_MPI_TRANSPORT" >&2; exit 2 ;;
esac

if [[ $stage == halo-layout ]]; then
    mpirun -n 32 --bind-to none python "$root/tools/multinode/rank_exec.py" \
        python -u "$root/experiments/ls-grid-wall-20261123/halo_layout_probe.py"
    exit 0
fi

if [[ $stage == grid || $stage == grid-build || $stage == grid-shard || $stage == grid-assemble ]]; then
    grid_tmp=$(mktemp -d /tmp/ls-wall-grid.XXXXXXXX)
    export GRID_PLATFORM=ls GRID_WORK="$grid_tmp/build-grid" GRID_GAUGE="$gauge" GRID_RESULTS="$out"
    export GRID_SOURCE="$grid_tmp/Grid" GRID_CHEBYSHEV_SETUP=1 GRID_BUILD_JOBS=24
    trap 'for log in configure build compile-driver-chebyshev; do
              if [[ -f "$GRID_WORK/$log.log" ]]; then cp "$GRID_WORK/$log.log" "$out/"; fi
          done; rm -rf -- "$grid_tmp"' EXIT
    if [[ $stage == grid ]]; then
        if [[ ${LS_BENCHMARK_FULL12:-0} != 1 ]]; then export GRID_SINGLE_RHS_ONLY=1; fi
        binary_revision=$(cat "$work/grid-build/source-commit.txt")
        git -C "$root" diff --exit-code "$binary_revision" HEAD -- \
            experiments/node5006-grid-wall-20261122/grid_wall.cc \
            'experiments/node5006-grid-wall-20261122/*.patch'
        printf '%s\n' "$binary_revision" > "$out/binary-source-commit.txt"
        (cd "$work/grid-build"; sha256sum -c runtime.sha256)
        mkdir -p "$GRID_WORK"
        tar -xzf "$work/grid-build/runtime.tar.gz" -C "$GRID_WORK"
        GRID_SKIP_BUILD=1 bash "$root/experiments/node5006-grid-wall-20261122/run.sh"
        exit 0
    fi
    tar -xzf "$work/upstream.tar.gz" -C "$grid_tmp"
    # Grid's Eigen bootstrap writes absolute links tied to the original checkout.
    ln -sfn ../Eigen/Eigen "$GRID_SOURCE/Grid/Eigen"
    ln -sfn ../unsupported/Eigen "$GRID_SOURCE/Eigen/Eigen/unsupported"
    test -f "$GRID_SOURCE/Grid/Eigen/Dense"
    test -f "$GRID_SOURCE/Grid/Eigen/unsupported/CXX11/Tensor"
    lime="$grid_tmp/.cache/grid-node5006-wall/lime-src"
    test "$(git -C "$GRID_SOURCE" rev-parse HEAD)" = "$grid_sha"
    test "$(git -C "$lime" rev-parse HEAD)" = "$lime_sha"
    cmake -S "$lime" -B "$grid_tmp/lime-build" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_INSTALL_LIBDIR=lib \
        -DCMAKE_INSTALL_PREFIX="$GRID_WORK/lime-install"
    cmake --build "$grid_tmp/lime-build" -j 8
    cmake --install "$grid_tmp/lime-build"
    if [[ $stage == grid-shard ]]; then
        bash "$root/experiments/node5006-grid-wall-20261122/run.sh"
        exit 0
    fi
    if [[ $stage == grid-assemble ]]; then
        shard_revision=${GRID_SHARD_REVISION:-$(cat "$out/source-commit.txt")}
        for ((i=0; i<GRID_SHARDS; ++i)); do
            test "$(cat "$work/shards/shard-$i/source-commit.txt")" = "$shard_revision"
        done
        printf '%s\n' "$shard_revision" > "$out/objects-source-commit.txt"
        export GRID_SHARD_ARCHIVES="$work/shards"
    fi
    GRID_BUILD_ONLY=1 bash "$root/experiments/node5006-grid-wall-20261122/run.sh"
    tar -czf "$out/runtime.tar.gz" -C "$GRID_WORK" grid_wall-chebyshev lime-install
    (cd "$out"; sha256sum runtime.tar.gz > runtime.sha256)
    exit 0
fi

ranks_per_node=${LS_RANKS_PER_NODE:-16}
if [[ $stage == native-one ]]; then ranks=$ranks_per_node; else ranks=$((2 * ranks_per_node)); fi
build="$work/native-build/build"
oracle_revision=$(cat "$work/native-build/oracle-source-commit.txt")
git -C "$root" diff --exit-code "$oracle_revision" HEAD -- \
    benchmarks/runtime/verify_slab.cpp src include cmake CMakeLists.txt tools/multinode/gate_ls.sh
printf '%s\n' "$oracle_revision" > "$out/oracle-source-commit.txt"
sha256sum "$build/liblqcd_cpu.so" "$build/verify_slab" > "$out/build.sha256"
export PYTHONPATH="$root/bindings"
export LQCD_DISTRIBUTED_STORAGE=1 LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1
export LQCD_ARM_COARSE_SVE=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_COARSE_FUSED=0 LQCD_COARSE_SPATIAL_OVERLAP=1 LQCD_COARSE_BATCH_REDUCE=1
export LQCD_HBW_ALLOC=prefer LQCD_HBM=off
run=(mpirun -n "$ranks" --bind-to none python "$root/tools/multinode/rank_exec.py")
if [[ $stage == native-two ]]; then
    UCX_LOG_LEVEL=info timeout 120 "${run[@]}" \
        python -u "$root/tests/runtime/test_multinode_communication.py" --benchmark
    if [[ ${LS_MPI_PROBE_ONLY:-0} == 1 ]]; then exit 0; fi
fi
scratch="/tmp/lqcd-ls-wall-${CCS_JOB_ID:-manual}-$(basename "$out")"
rhs_args=(--single-only)
oracle_columns=1
if [[ ${LS_BENCHMARK_FULL12:-0} == 1 ]]; then
    rhs_args=()
    oracle_columns=13
fi
"${run[@]}" python -u "$root/benchmarks/runtime/benchmark_multinode.py" \
    --gauge "$gauge" --library "$build/liblqcd_cpu.so" --output "$out/measurements" --scratch "$scratch" \
    --lattice 24 24 24 64 --block 6 6 6 2 --mass "$mass" --csw "$csw" --tol 1e-8 --source wall \
    --ranks-per-node "$ranks_per_node" "${rhs_args[@]}"
"${run[@]}" "$build/verify_slab" "$scratch" 24 64 "$mass" "$csw" 1e-8 0 "$oracle_columns" wall \
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
