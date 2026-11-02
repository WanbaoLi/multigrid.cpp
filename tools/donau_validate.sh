#!/usr/bin/env bash
# Site-specific single-node Donau validation; see docs/validation-20261102.md.
set -eo pipefail
source "${LQCD_TOOLCHAIN_ENV:-/home/share/test_mpi/my_software/hpckit/HPCKit/latest/setvars.sh}" --use-bisheng --force
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
task_sysroot=${LQCD_SYSROOT:-/work_ssd/system/os_jasmine_v01/vroot}
export CC="$task_sysroot/usr/bin/gcc" CXX="$task_sysroot/usr/bin/g++"
export OMPI_CC="$CC" OMPI_CXX="$CXX"
export CPATH="$task_sysroot/usr/include:$task_sysroot/usr/local/include${CPATH:+:$CPATH}"
export LIBRARY_PATH="$task_sysroot/usr/lib64:$task_sysroot/usr/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LD_LIBRARY_PATH:-}"
export LQCD_TEST_PYTHON=${LQCD_TEST_PYTHON:-$HOME/.cache/multigrid-arm-20261025-env/bin/python}
export PATH="$(dirname "$LQCD_TEST_PYTHON"):$PATH"
export CMAKE_CXX_COMPILER_LAUNCHER="$LQCD_TEST_PYTHON;$project_dir/tools/pin_build.py"
export CMAKE_C_COMPILER_LAUNCHER="$CMAKE_CXX_COMPILER_LAUNCHER"
# One Donau replica, several local MPI ranks within its allocated cpuset.
export OMPI_MCA_ras='^donau' OMPI_MCA_plm=isolated
export OMPI_MCA_pml=${OMPI_MCA_pml:-ob1} OMPI_MCA_btl=${OMPI_MCA_btl:-self,vader,tcp}
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
export BUILD_JOBS=${BUILD_JOBS:-16}
bash "$project_dir/tools/validate_host.sh"
