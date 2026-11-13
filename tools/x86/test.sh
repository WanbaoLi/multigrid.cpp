#!/usr/bin/env bash
# Run CTest and one real 24^3x64 LIME propagator test on an AMD node.
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
build_dir=${BUILD_DIR:-$project_dir/build/amd9755}
python_bin=${PYTHON:-${LQCD_TEST_PYTHON:-python3}}

gauge_default=${HOME}/lqcd-inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
gauge=${1:-${GAUGE:-$gauge_default}}
output=${2:-${OUTPUT:-$project_dir/results/amd9755-c24}}

ranks_per_numa=${RANKS_PER_NUMA:-1}
threads=${THREADS:-32}
block_x=${BLOCK_X:-6}
block_y=${BLOCK_Y:-6}
block_z=${BLOCK_Z:-6}
block_t=${BLOCK_T:-4}
mass=${MASS:--0.277}
csw=${CSW:-1.160920226}
stout_steps=${STOUT_STEPS:-1}
stout_rho=${STOUT_RHO:-0.125}
stout_dir_ignore=${STOUT_DIR_IGNORE:-4}
tol=${TOL:-1e-8}
repeats=${REPEATS:-3}
seed=${SEED:-1024}
rhs_batch=${RHS_BATCH:-1}
run_ctest=${RUN_CTEST:-1}

if [[ "$python_bin" == */* ]]; then
    [[ -x "$python_bin" ]] || { echo "Python not found: $python_bin" >&2; exit 2; }
else
    command -v "$python_bin" >/dev/null || { echo "Python not found: $python_bin" >&2; exit 2; }
fi
[[ -f "$build_dir/liblqcd_cpu.so" ]] || {
    echo "Missing $build_dir/liblqcd_cpu.so; run tools/x86/build.sh first." >&2
    exit 2
}
[[ -f "$gauge" ]] || {
    echo "Missing raw LIME gauge: $gauge" >&2
    echo "Set GAUGE=/path/to/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime" >&2
    exit 2
}
[[ ! -e "$output" ]] || { echo "Output already exists: $output" >&2; exit 2; }

export PYTHONPATH="$project_dir/bindings${PYTHONPATH:+:$PYTHONPATH}"
export LQCD_CPU_LIBRARY="$build_dir/liblqcd_cpu.so"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export LQCD_RHS_BATCH="$rhs_batch"

if [[ "$run_ctest" == 1 ]]; then
    OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close \
        ctest --test-dir "$build_dir" --output-on-failure
fi

mkdir -p "$(dirname "$output")"
"$python_bin" tools/run_numa.py \
    --lattice 24 24 24 64 \
    --block "$block_x" "$block_y" "$block_z" "$block_t" \
    --ranks-per-numa "$ranks_per_numa" \
    --threads "$threads" -- \
    "$python_bin" -u tools/solve_propagator.py \
    --backend x86 \
    --library "$LQCD_CPU_LIBRARY" \
    --gauge "$gauge" \
    --mass "$mass" --csw "$csw" --normalization mass \
    --block "$block_x" "$block_y" "$block_z" "$block_t" \
    --source 0 0 0 0 --source-scale 1 \
    --stout-steps "$stout_steps" --stout-rho "$stout_rho" \
    --stout-dir-ignore "$stout_dir_ignore" \
    --tol "$tol" --seed "$seed" --threads "$threads" \
    --repeats "$repeats" --save-gauge --output "$output"

"$python_bin" - "$output/result.json" <<'PY'
import json, sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
assert report['complete']
assert all(row['converged'] and row['true_residual'] <= 1e-8
           for sample in report['samples'] for row in sample['stats'])
print('PASS: 24^3x64 x86 propagator')
print('setup_seconds:', report['setup_seconds'])
print('stout_seconds:', report['stout_seconds'])
print('first_seconds:', report['first_seconds'])
print('second_seconds:', report.get('second_seconds'))
print('steady_median_seconds:', report.get('steady_median_seconds'))
print('max_true_residual:', report['max_true_residual'])
print('result:', sys.argv[1])
PY
