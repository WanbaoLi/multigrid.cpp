#!/usr/bin/env bash
set -eo pipefail

checkout() {
    git clone --no-checkout "$workspace/project.bundle" "$1"
    git -C "$1" fetch "$workspace/project-delta.bundle" "refs/heads/$branch"
    git -C "$1" sparse-checkout init --cone
    git -C "$1" sparse-checkout set src include bindings cmake tests tools benchmarks/runtime \
        experiments/ls-grid-wall-20261123 experiments/node5006-grid-wall-20261122
    git -C "$1" checkout -B "$branch" FETCH_HEAD
    test "$(git -C "$1" rev-parse HEAD)" = "$revision"
}

stage=$1
workspace=$2
revision=$3
branch=${LQCD_BUNDLE_BRANCH:-codex/ls-grid-wall-20261123}
if [[ $stage == stage-native-host ]]; then
    mkdir -p "$(dirname "$4")"
    checkout "$4"
    exit 0
fi
gauge=$4

temp=$(mktemp -d /tmp/ls-wall-src.XXXXXXXX)
trap 'rm -rf -- "$temp"' EXIT
checkout "$temp/project"
if [[ $stage == native-two || $stage == native-two-pair || $stage == native-two-coarse-pair || $stage == native-scale ]]; then
    source "$temp/project/tools/multinode/ls_env.sh"
    unset OMPI_MCA_ras OMPI_MCA_plm
    host_source="$temp/worker-project"
    nodes=2
    if [[ $stage == native-scale ]]; then nodes=${LS_NATIVE_NODES:?expected LS_NATIVE_NODES}; fi
    mpirun -n "$nodes" --map-by ppr:1:node --bind-to none \
        /bin/bash "$0" stage-native-host "$workspace" "$revision" "$host_source"
    bash "$host_source/experiments/ls-grid-wall-20261123/run.sh" "$stage" "$workspace" "$gauge"
else
    bash "$temp/project/experiments/ls-grid-wall-20261123/run.sh" "$stage" "$workspace" "$gauge"
fi
