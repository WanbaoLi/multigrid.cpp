#!/bin/bash
set -eo pipefail
TASK_SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
TASK_SYSROOT=/work_ssd/system/os_jasmine_v01/vroot
source "$TASK_SDK/setvars.sh" --use-bisheng --force
export FAIR_PYTHON=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
export PATH="$(dirname "$FAIR_PYTHON"):$PATH"
export CC=$TASK_SYSROOT/usr/bin/gcc CXX=$TASK_SYSROOT/usr/bin/g++ OMPI_CC=$TASK_SYSROOT/usr/bin/gcc OMPI_CXX=$TASK_SYSROOT/usr/bin/g++
export CPATH=$TASK_SYSROOT/usr/include:$TASK_SYSROOT/usr/local/include
export LIBRARY_PATH=$TASK_SDK/compiler/gcc/lib64:$TASK_SDK/kupl/gcc/release/lib:$TASK_SYSROOT/usr/lib64:$TASK_SYSROOT/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$TASK_SDK/compiler/gcc/lib64:$TASK_SDK/kupl/gcc/release/lib:$TASK_SDK/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT OMP_WAIT_POLICY GOMP_SPINCOUNT
export LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1 LQCD_ARM_SVE_PLANNED=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_ARM_COARSE_SVE=0 LQCD_COARSE_FUSED=0 LQCD_COARSE_SPATIAL_OVERLAP=1
export LQCD_HBM=off LQCD_HBW_ALLOC=off LQCD_RHS_BATCH=2
unset LQCD_MG_SAP_STEPS LQCD_MG_SAP_CYCLES LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL LQCD_COARSE_THREADS

