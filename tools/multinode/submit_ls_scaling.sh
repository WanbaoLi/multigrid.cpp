#!/usr/bin/env bash
set -euo pipefail

work=$(cd "$1" && pwd)
revision=$2
branch=$3
sdk=/work_ssd/software/HPCKit/25.2.1
c32="$HOME/multigrid.cpp/data/C32P23/beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime"
c64="$HOME/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime"
test "$(git bundle list-heads "$work/project-delta.bundle" "refs/heads/$branch" | cut -d' ' -f1)" = "$revision"
test -r "$c32" && test -r "$c64"

submit() {
    local name=$1
    shift
    local dir="$work/$name"
    mkdir "$dir"
    ln -s "$work/project.bundle" "$dir/project.bundle"
    ln -s "$work/project-delta.bundle" "$dir/project-delta.bundle"
    if [[ $name != build ]]; then ln -s "$work/build/native-build" "$dir/native-build"; fi
    dsub -q q_hpcapp -A common --mpi hmpi --cwd "$dir" -o "$dir/job.log" -n "lqcd_$name" \
        "$@" | tee "$dir/job.id" >&2
    sed -n 's/^Submit job <\([0-9]*\)> successfully\.$/\1/p' "$dir/job.id"
}

common=(/usr/bin/env "LQCD_LS_SDK=$sdk" "LQCD_BUNDLE_BRANCH=$branch")
node_filter=()
if [[ -n ${LS_SCALE_NODE_LIST:-} ]]; then node_filter=(-nl "$LS_SCALE_NODE_LIST"); fi
build=$(submit build -nn 1 -N 1 -rpn 1 -R 'cpu=8,mem=64000MB' -RL 'mem=64000MB' -T 7200 \
    "${common[@]}" LS_BUILD_RUNTIME=1 LS_BUILD_JOBS=8 LS_NATIVE_FIXTURE=c32 \
    /bin/bash "$work/launch.sh" native-build "$work/build" "$revision" "$c32")
test -n "$build"

scale() {
    local name=$1 nodes=$2 per_node=$3 weak=$4 dep=$5 fixture=$6 gauge=$7 memory=$8
    submit "$name" -D "$dep=SUCCEEDED" -nn "$nodes" -N "$((nodes * per_node))" -rpn "$per_node" -x job \
        -R "cpu=$((592 / per_node)),mem=${memory}MB" -T 14400 "${node_filter[@]}" "${common[@]}" \
        "LS_NATIVE_FIXTURE=$fixture" LS_MPI_TRANSPORT=ucx "LS_NATIVE_NODES=$nodes" \
        "LS_RANKS_PER_NODE=$per_node" "LS_NATIVE_WEAK=$weak" LS_NATIVE_BLOCK_T=2 \
        LQCD_REUSE_HALO_PAGES=1 LQCD_COARSE_THREADS=8 LQCD_HBW_ALLOC=off \
        /bin/bash "$work/launch.sh" native-scale "$work/$name" "$revision" "$gauge"
}

last=$build
for nodes in 1 2 4; do
    last=$(scale "strong_$nodes" "$nodes" 8 0 "$last" c32 "$c32" 20000)
    test -n "$last"
done

last=$build
for nodes in 1 2 4 8 16 32; do
    last=$(scale "weak_$nodes" "$nodes" 16 1 "$last" c32 "$c32" 12000)
    test -n "$last"
    if [[ $nodes == 4 ]]; then weak4=$last; fi
done

for nodes in 2 4; do
    job=$(scale "c64_$nodes" "$nodes" 16 0 "$weak4" f64p14 "$c64" 30000)
    test -n "$job"
done
