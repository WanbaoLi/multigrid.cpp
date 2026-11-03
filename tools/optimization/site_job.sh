#!/bin/bash
# Single-node, bounded queue worker. Tasks are atomically renamed *.ready.json.
# A task executes through campaign.run_stage when registered; raw argv is also
# accepted for initial acquisition. Ordinary benchmarks never overlap workers.
set -eo pipefail
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
task_sdk=${LQCD_HPCKIT_ROOT:-/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001}
task_sysroot=${LQCD_SYSROOT:-/work_ssd/system/os_jasmine_v01/vroot}
task_python=${LQCD_SITE_PYTHON:-$HOME/.cache/multigrid-arm-20261025-env/bin/python}
source "$task_sdk/setvars.sh" --use-bisheng --force
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++ OMPI_CC=$task_sysroot/usr/bin/gcc OMPI_CXX=$task_sysroot/usr/bin/g++
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
# The validated KUPL binary needs the SDK C++ runtime (GLIBCXX_3.4.30).
# Compiler/includes stay on GCC10; runtime search order is recorded separately.
export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export PATH="$(dirname "$task_python"):$PATH"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export OMP_PROC_BIND=close
export LQCD_TEST_PYTHON=$task_python
export CMAKE_CXX_COMPILER_LAUNCHER="$LQCD_TEST_PYTHON;$project_dir/tools/pin_build.py"
export CMAKE_C_COMPILER_LAUNCHER="$CMAKE_CXX_COMPILER_LAUNCHER"
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
export LQCD_EXPERIMENT_CXX_RUNTIME=$task_sdk/compiler/gcc/lib64
export LQCD_EXPERIMENT_KUPL_ROOT=$task_sdk/kupl/gcc/release
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
exec "$task_python" -u "$project_dir/tools/optimization/worker.py" "$@"
