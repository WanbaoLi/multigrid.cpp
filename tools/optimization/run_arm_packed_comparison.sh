#!/usr/bin/env bash
# Run inside one exclusive whole-node allocation; reuse the acceptance driver.
set -euo pipefail
if [[ $# != 2 ]]; then
    echo "usage: $0 NEW_RUN_ROOT GAUGE24" >&2
    exit 2
fi
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
run_root=$(realpath -m "$1")
gauge=$(realpath "$2")
[[ ! -e "$run_root" ]] || { echo 'Run root exists' >&2; exit 2; }
mkdir -p "$run_root"
git -C "$project_dir" rev-parse HEAD > "$run_root/source-commit.txt"
export LQCD_HEALTH_GEOMETRIES=24 LQCD_HEALTH_DIAGNOSTIC=1
for attempt in baseline-a packed baseline-b; do
    if [[ "$attempt" == packed ]]; then
        export LQCD_HEALTH_PLAN="$project_dir/profiles/optimization/lingsheng-packed-coefficients.json"
    else
        export LQCD_HEALTH_PLAN="$project_dir/profiles/optimization/lingsheng-shared-uniform.json"
    fi
    bash "$project_dir/tools/health/run_single_node.sh" arm "$run_root/$attempt" "$gauge" "$gauge"
done
echo "ARM_PACKED_COMPARISON_COMPLETE $run_root"
