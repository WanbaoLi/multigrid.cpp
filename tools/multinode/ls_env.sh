#!/usr/bin/env bash
# Source on the allocated compute node; matches the measured stable ABI.
task_sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
source "$task_sdk/setvars.sh" --use-bisheng --force
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export PATH=$HOME/.cache/multigrid-arm-20261025-env/bin:$PATH
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
unset LD_PRELOAD
