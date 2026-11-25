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
lattice=24
time_extent=64
block=6
block_t=2
case "${LS_NATIVE_FIXTURE:-c24}" in
    c24) ;;
    c32)
        lattice=32; block=8; csw=1.1606789224
        gauge_sha=bc2918403eee5d1e10a409fc0e69ac03b22cc7f0cf71be760b44a593ff0d0828
        ;;
    f64p14)
        lattice=64; time_extent=128; block=8; block_t=4; mass=-.2334; csw=1.140825606017
        gauge_sha=30790de7907dc66a6555bd62fb276d365aceedb07cb9eb3bc7e567847a250183
        ;;
    *) echo "Unknown native fixture: $LS_NATIVE_FIXTURE" >&2; exit 2 ;;
esac

case "$stage" in
    native-one-sweep)
        for layout in 16:0 16:8 32:0 32:8; do
            if ! LS_RANKS_PER_NODE=${layout%:*} LQCD_COARSE_THREADS=${layout#*:} \
                LS_RESULT_SUFFIX="mpi${layout%:*}-coarse${layout#*:}" \
                bash "$0" native-one "$work" "$gauge"; then
                echo "Single-node case failed: $layout" >&2
            fi
        done
        python3 "$root/tools/multinode/summarize_wall.py" "$work"
        exit 0
        ;;
    native-one-pair)
        LS_RANKS_PER_NODE=16 LS_RESULT_SUFFIX=16 bash "$0" native-one "$work" "$gauge"
        LS_RANKS_PER_NODE=32 LS_RESULT_SUFFIX=32 bash "$0" native-one "$work" "$gauge"
        exit 0
        ;;
    native-one-block-pair)
        for time_block in 2 4; do
            LS_RANKS_PER_NODE=16 LS_NATIVE_BLOCK_T=$time_block LS_RESULT_SUFFIX="block-t$time_block" \
                bash "$0" native-one "$work" "$gauge"
        done
        exit 0
        ;;
    native-two-pair)
        LS_MPI_TRANSPORT=tcp LS_RESULT_SUFFIX=tcp bash "$0" native-two "$work" "$gauge"
        LS_MPI_TRANSPORT=ucx LS_RESULT_SUFFIX=ucx bash "$0" native-two "$work" "$gauge"
        exit 0
        ;;
    native-two-coarse-pair)
        for coarse_threads in 0 8; do
            LS_MPI_TRANSPORT=ucx LQCD_COARSE_THREADS=$coarse_threads LS_RESULT_SUFFIX="coarse$coarse_threads" \
                bash "$0" native-two "$work" "$gauge"
        done
        exit 0
        ;;
    grid-build|grid-shard|grid-assemble|grid|halo-layout|hmc-c24|native-build|native-one|native-two|native-scale) ;;
    *) echo "Unknown stage: $stage" >&2; exit 2 ;;
esac

out="$work/$stage"
if [[ -n ${LS_RESULT_SUFFIX:-} ]]; then out="$out-$LS_RESULT_SUFFIX"; fi
if [[ $stage == grid-shard ]]; then out="$work/shards/shard-$GRID_SHARD"; fi
if [[ $stage == grid-assemble ]]; then out="$work/grid-build"; fi
mkdir -p "$out"
git -C "$root" rev-parse HEAD > "$out/source-commit.txt"
if [[ $stage == grid || $stage == native-build || $stage == native-one || $stage == native-two || $stage == native-scale ]]; then
    printf '%s  %s\n' "$gauge_sha" "$gauge" | sha256sum -c
fi
source "$root/tools/multinode/ls_env.sh"
hostname -s
lscpu

if [[ $stage == native-build || $stage == native-one && ! -s $work/native-build/build/verify_slab ]]; then
    native_tmp=$(mktemp -d /tmp/ls-wall-native.XXXXXXXX)
    trap 'rm -rf -- "$native_tmp"' EXIT
    if [[ ${LS_BUILD_RUNTIME:-0} == 1 ]]; then
        bash "$root/tools/multinode/gate_ls.sh" "$native_tmp" || {
            cp "$native_tmp/gates.log" "$out/"
            exit 1
        }
        mkdir -p "$work/native-build/build"
        cp "$native_tmp/build/"{liblqcd_cpu.so,verify_slab,multigrid} "$work/native-build/build/"
        if [[ ${LS_BUILD_HMC:-OFF} == ON ]]; then
            cp "$native_tmp/build/liblqcd_hmc_kernels.so" "$work/native-build/build/"
        fi
        cp "$out/source-commit.txt" "$work/native-build/library-source-commit.txt"
        cp "$out/source-commit.txt" "$work/native-build/oracle-source-commit.txt"
        cp "$native_tmp/"{gates,ctest}.log "$out/"
    else
        native_commit=5b99879f84f647d267dde6156e637ced64ca694f
        native_library="$HOME/lqcd-run/mg-l24-coarse-rescue-run01/liblqcd_cpu.so"
        git -C "$root" diff --exit-code "$native_commit" HEAD -- src include cmake CMakeLists.txt bindings
        printf '%s  %s\n' 8d1e7374d9e765225f20a0eb79cd61785e7fdadf092f22649e37da1a7662236d \
            "$native_library" | sha256sum -c
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
if [[ $stage == hmc-c24 ]]; then
    cmp "$out/source-commit.txt" "$work/native-build/library-source-commit.txt"
    bash "$root/tools/hmc/run_c24_ls.sh" "$out" "$gauge" "$work/native-build/build"
    exit 0
fi

if [[ $stage == grid || $stage == grid-build || $stage == grid-shard || $stage == grid-assemble ]]; then
    test "$lattice" -eq 24
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
case "$ranks_per_node" in
    4|8|16|32) ;;
    *) echo "Unsupported ranks per node: $ranks_per_node" >&2; exit 2 ;;
esac
nodes=1
replicas=1
case "$stage" in
    native-two) nodes=2 ;;
    native-scale)
        nodes=${LS_NATIVE_NODES:?expected LS_NATIVE_NODES}
        case "$nodes" in
            1|2|4|8|16|32) ;;
            *) echo "Unsupported scaling node count: $nodes" >&2; exit 2 ;;
        esac
        if [[ ${LS_NATIVE_WEAK:-0} == 1 ]]; then replicas=$nodes; fi
        ;;
esac
ranks=$((nodes * ranks_per_node))
total_time=$((time_extent * replicas))
block_t=${LS_NATIVE_BLOCK_T:-$block_t}
case "$block_t" in
    2|4) ;;
    *) echo "Unsupported temporal aggregation block: $block_t" >&2; exit 2 ;;
esac
if (( total_time % ranks != 0 || total_time / ranks % 2 != 0 || total_time / ranks % block_t != 0 )); then
    echo "Temporal aggregation block $block_t does not divide the rank-local time extent" >&2
    exit 2
fi
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
export LQCD_HBW_ALLOC=${LQCD_HBW_ALLOC:-prefer} LQCD_HBM=off
mapping=()
if [[ $stage == native-scale ]]; then mapping=(--map-by "ppr:$ranks_per_node:node" --rank-by slot); fi
mpi=(mpirun -n "$ranks" "${mapping[@]}" --bind-to none)
run=("${mpi[@]}" python "$root/tools/multinode/rank_exec.py")
if (( nodes > 1 )); then
    gate_timeout=120
    if [[ $stage == native-scale ]]; then gate_timeout=$((120 + 6 * nodes)); fi
    UCX_LOG_LEVEL=info timeout "$gate_timeout" "${run[@]}" \
        python -u "$root/tests/runtime/test_multinode_communication.py" --benchmark --ranks-per-node "$ranks_per_node"
    if [[ ${LS_MPI_PROBE_ONLY:-0} == 1 ]]; then exit 0; fi
fi
scratch="/tmp/lqcd-ls-wall-${CCS_JOB_ID:-manual}-$(basename "$out")"
rhs_args=(--single-only)
oracle_columns=1
oracle_period=()
if (( replicas > 1 )); then oracle_period=("$time_extent"); fi
if [[ ${LS_BENCHMARK_FULL12:-0} == 1 ]]; then
    rhs_args=()
    oracle_columns=13
fi
"${run[@]}" python -u "$root/benchmarks/runtime/benchmark_multinode.py" \
    --gauge "$gauge" --library "$build/liblqcd_cpu.so" --output "$out/measurements" --scratch "$scratch" \
    --lattice "$lattice" "$lattice" "$lattice" "$total_time" --time-replicas "$replicas" \
    --block "$block" "$block" "$block" "$block_t" --mass "$mass" --csw "$csw" --tol 1e-8 --source wall \
    --ranks-per-node "$ranks_per_node" "${rhs_args[@]}"
"${run[@]}" "$build/verify_slab" "$scratch" "$lattice" "$total_time" "$mass" "$csw" 1e-8 0 "$oracle_columns" wall "${oracle_period[@]}" \
    | tee "$out/second-round-residuals.log"
grep -qx SCALAR_ALL_PASSED "$out/second-round-residuals.log"
python - "$out" "$oracle_columns" <<'PY'
import json
import math
from pathlib import Path
import sys

output = Path(sys.argv[1])
report = json.loads((output / "measurements/result.json").read_text())
rows = []
for line in (output / "second-round-residuals.log").read_text().splitlines():
    fields = line.split()
    if fields and fields[0] == "SCALAR_COLUMN":
        rows.append({"column": int(fields[1]), "residual": float(fields[2])})
if ([row["column"] for row in rows] != list(range(int(sys.argv[2])))
        or any(not math.isfinite(row["residual"]) or row["residual"] > report["tol"] for row in rows)):
    raise RuntimeError("Missing or invalid independent full residual")
report.update(complete=True, independent_verification={
    "passed": True, "method": "independent scalar full-spin padded slabs", "columns": rows})
tmp = output / "result.json.tmp"
tmp.write_text(json.dumps(report, indent=2) + "\n")
tmp.replace(output / "result.json")
PY
if [[ $stage == native-two && ( -f "$work/native-one-mpi16-coarse0/result.json" || ${LS_REQUIRE_SCALING:-0} == 1 ) ]]; then
    python "$root/tools/multinode/summarize_wall.py" "$work" --two "$out"
fi

"${mpi[@]}" python -c '
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
