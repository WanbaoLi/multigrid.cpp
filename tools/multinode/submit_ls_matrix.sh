#!/usr/bin/env bash
# Submit one immutable source revision and keep each measurement's output separate.
set -euo pipefail
work=$(cd "$1" && pwd)
revision=$2
branch=$3
sdk=/work_ssd/software/HPCKit/25.2.1
input24="$HOME/inputs/grid-wall/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
input32="$HOME/multigrid.cpp/data/C32P23/beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime"
input64="$HOME/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime"
hmc_input="$HOME/lqcd-run/hmc-l24t64-publication-run01/published/hmc_000003.lime"

test "$(git bundle list-heads "$work/project-delta.bundle" "refs/heads/$branch" | cut -d' ' -f1)" = "$revision"
for input in "$input24" "$input32" "$input64" "$hmc_input"; do test -r "$input"; done
for slot in build c24 c32 c64 hmc; do
    mkdir "$work/$slot"
    ln -s "$work/project.bundle" "$work/$slot/project.bundle"
    ln -s "$work/project-delta.bundle" "$work/$slot/project-delta.bundle"
    if [[ $slot != build ]]; then
        ln -s "$work/build/native-build" "$work/$slot/native-build"
    fi
done

submit() {
    local slot=$1 marker=$2
    shift 2
    local dir="$work/$slot"
    dsub -q q_hpcapp -A common --mpi hmpi --cwd "$dir" \
        -o "$dir/$marker.log" "$@" | tee "$dir/$marker.job" >&2
    sed -n 's/^Submit job <\([0-9]*\)> successfully\.$/\1/p' "$dir/$marker.job"
}
common=(/usr/bin/env "LQCD_LS_SDK=$sdk" "LQCD_BUNDLE_BRANCH=$branch")

build=$(submit build build -n lqcd_matrix_build -nn 1 -N 1 -rpn 1 \
    -R 'cpu=8,mem=64000MB' -RL 'mem=64000MB' -T 7200 \
    "${common[@]}" LS_BUILD_RUNTIME=1 LS_BUILD_HMC=ON LS_BUILD_JOBS=8 \
    LS_MPI_GATE_BIND_NONE=1 \
    /bin/bash "$work/launch.sh" native-build "$work/build" "$revision" "$input24")
test -n "$build"

declare -A two
for slot in c24 c32; do
    if [[ $slot == c24 ]]; then gauge=$input24; else gauge=$input32; fi
    single=$(submit "$slot" single -D "$build=SUCCEEDED" \
        -n "lqcd_${slot}_single" -nn 1 -N 32 -rpn 32 -x job \
        -R 'cpu=18,mem=15000MB' -T 10800 \
        "${common[@]}" "LS_NATIVE_FIXTURE=$slot" /bin/bash "$work/launch.sh" \
        native-one-sweep "$work/$slot" "$revision" "$gauge")
    test -n "$single"
    two[$slot]=$(submit "$slot" two -D "$single=SUCCEEDED" \
        -n "lqcd_${slot}_two" -nn 2 -N 32 -rpn 16 -x job \
        -R 'cpu=37,mem=30000MB' -T 7200 \
        "${common[@]}" "LS_NATIVE_FIXTURE=$slot" LS_MPI_TRANSPORT=ucx LQCD_COARSE_THREADS=0 LS_REQUIRE_SCALING=1 \
        /bin/bash "$work/launch.sh" native-two "$work/$slot" "$revision" "$gauge")
    test -n "${two[$slot]}"
done

submit c64 two -D "${two[c24]}=SUCCEEDED&&${two[c32]}=SUCCEEDED" \
    -n lqcd_c64_two -nn 2 -N 32 -rpn 16 -x job -R 'cpu=37,mem=30000MB' -T 14400 \
    "${common[@]}" LS_NATIVE_FIXTURE=f64p14 LS_MPI_TRANSPORT=ucx LQCD_REUSE_HALO_PAGES=1 \
    /bin/bash "$work/launch.sh" native-two "$work/c64" "$revision" "$input64"
submit hmc hmc -D "$build=SUCCEEDED" \
    -n lqcd_c24_hmc -nn 1 -N 64 -rpn 64 -x job -R 'cpu=4,mem=7000MB' -T 14400 \
    "${common[@]}" /bin/bash "$work/launch.sh" hmc-c24 "$work/hmc" "$revision" "$hmc_input"
