#!/bin/bash
# Login-record gate; submit only after review. This never changes ROOT/source.
set -eo pipefail
task_root=/home/share/nsls_lwb/.cache/mg-opt-20261103
task_sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
task_python=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
if [[ $# -ne 4 || "$1" != --source || "$3" != --expected-source-head ]]; then
  echo 'Require explicit reviewed --source PATH --expected-source-head SHA.' >&2
  exit 2
fi
task_source=$2
task_source_head=$4
if [[ "$(hostname -s)" != "cn19483" ]]; then
  echo 'Worker9 node differs from the reviewed allocation; no automatic fallback.' >&2
  exit 2
fi
source "$task_sdk/setvars.sh" --use-bisheng --force
set -u
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
# Keep GCC10 compiler/includes, but use the already validated SDK12 C++/GOMP
# runtime and GCC KUPL first. Do not call site_job.sh, which prepends vroot LD.
export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export PATH="$(dirname "$task_python"):$PATH"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export OMP_PROC_BIND=close
export LQCD_TEST_PYTHON=$task_python
export CMAKE_CXX_COMPILER_LAUNCHER="$task_python;$task_source/tools/pin_build.py"
export CMAKE_C_COMPILER_LAUNCHER="$CMAKE_CXX_COMPILER_LAUNCHER"
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
export LQCD_EXPERIMENT_CXX_RUNTIME=$task_sdk/compiler/gcc/lib64
export LQCD_EXPERIMENT_KUPL_ROOT=$task_sdk/kupl/gcc/release
export LQCD_OPT_ALLOCATION=mg-opt-20261103-worker9
export LQCD_OPT_EXPECTED_HOST=cn19483
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
exec "$task_python" -u "$task_root/worker9_entry.py" --root "$task_root" --previous-job 2023152 --source "$task_source" --expected-source-head "$task_source_head"
