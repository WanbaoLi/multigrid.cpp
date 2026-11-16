#!/usr/bin/env bash
# Run on an allocated SVE compute node. Sources must be committed/published exports.
set -eo pipefail
if [[ $# != 4 ]]; then
    echo 'usage: run_fine_site_comparison.sh BASELINE_SOURCE CANDIDATE_SOURCE NEW_OUTPUT FIXTURE' >&2
    exit 2
fi
task_project=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
task_sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
task_python=$HOME/.cache/multigrid-arm-20261025-env/bin/python
source "$task_sdk/setvars.sh" --use-bisheng --force
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export PATH=$(dirname "$task_python"):$PATH
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
# Start from the recorded context plan, not an inherited previous experiment.
while IFS='=' read -r task_key task_value; do
    case "$task_key" in LQCD_*|NATIVE_*) unset "$task_key";; esac
done < <(env)
export LQCD_COMPARISON_SDK=$task_sdk
export PYTHONPATH=$task_project/bindings:${PYTHONPATH:-}
"$task_python" -c 'from pathlib import Path; assert "sve" in Path("/proc/cpuinfo").read_text().split(), "Use an allocated SVE node"'
exec "$task_python" -u "$task_project/tools/optimization/compare_fine_sites.py" \
    --backend arm --baseline "$1" --candidate "$2" --output "$3" \
    --fixture "$4" --gold "$4/propagator.npy"
