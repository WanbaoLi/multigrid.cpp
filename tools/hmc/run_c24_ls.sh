#!/usr/bin/env bash
# Start a reproducible heavy-mass C24 RHMC pilot in a Donau allocation.
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
input=$2
build=$3
python=${LS_HMC_PYTHON:-/work_ssd/software/soft/tool/anaconda3/2023.3/bin/python3}
deps=${LS_HMC_PYTHON_DEPS:-"$HOME/lqcd-run/pyqcu-review-deps-cp310"}
export PYTHONPATH="$deps:$root/bindings${PYTHONPATH:+:$PYTHONPATH}"
export LQCD_HMC_SCHUR_LIBRARY="$build/liblqcd_hmc_kernels.so"
export OMP_WAIT_POLICY=PASSIVE

# The initial field and pilot parameters match the previously validated C24 chain.
printf '%s  %s\n' 8d7cafc34cbdc2af6ac694b78c6be73fd8d0b7621f83267ef3c10c2ea9304942 "$input" | sha256sum -c
test -x "$build/multigrid"
test -s "$LQCD_HMC_SCHUR_LIBRARY"
sha256sum "$build/multigrid" "$LQCD_HMC_SCHUR_LIBRARY" > "$out/build.sha256"
"$python" -c 'import mpi4py, numpy, scipy, torch'

"$python" "$root/tools/run_numa.py" --lattice 24 24 24 64 --time-slab \
    --threads 1 --ranks-per-numa 4 -- "$python" -u "$root/tools/hmc/generate_mpi.py" \
    --output "$out/chain" --initial-lime "$input" --lattice 24 24 24 64 \
    --beta 5.6 --mass-light 0.5 --mass-strange 0.8 --csw 1 \
    --trajectories 8 --warmup 2 --length 0.036 --steps 2 --gauge-steps 2 --save-every 2 \
    --threads 1 --md-order 16 --seed 6451 --packed-faces --direct-clover --compact-spin \
    --zolotarev --force-pole-batch 11 --projected-force-faces
OMP_NUM_THREADS=2 "$python" "$root/tools/hmc/verify_configs.py" "$out/chain" \
    --reference "$build/multigrid"
