#!/usr/bin/env bash
# Run inside an allocated compute node after loading a coherent compiler/MPI.
set -euo pipefail
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_dir"
python_bin=${LQCD_TEST_PYTHON:-python3}
export BUILD_DIR=${BUILD_DIR:-$project_dir/build/validation}
export LQCD_TEST_PYTHON="$python_bin"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$BUILD_DIR"
"$python_bin" tools/probe_host.py > "$BUILD_DIR/host.json"
"$python_bin" -c 'from mpi4py import MPI; import numpy; print(MPI.Get_library_version()); print(numpy.__version__)'
# Full wrapper tests exercise PyQUDA host fields (no GPU initialization).
"$python_bin" -c 'from pyquda.field import LatticeInfo, LatticePropagator; from pyquda_utils.source import point'
bash tools/build_runtime.sh
ctest --test-dir "$BUILD_DIR" --output-on-failure
if [[ -n ${LQCD_GAUGE:-} ]]; then
    # The launcher assigns rank-local threads from the allocation's physical CPUs.
    unset OMP_NUM_THREADS OMP_PLACES OMP_PROC_BIND
    export LQCD_CPU_LIBRARY="$BUILD_DIR/liblqcd_cpu.so"
    "$python_bin" tools/run_numa.py -- "$python_bin" -u tools/solve_propagator.py \
        --gauge "$LQCD_GAUGE" --mass -0.277 --csw 1.160920226 \
        --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
        --repeats "${LQCD_REPEATS:-2}" --save-gauge \
        --output "${LQCD_OUTPUT:?set a new output directory}"
fi
