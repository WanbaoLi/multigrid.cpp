#!/bin/bash
# Single-node, bounded queue worker. Tasks are atomically renamed *.ready.json.
# A task executes through campaign.run_stage when registered; raw argv is also
# accepted for initial acquisition. Ordinary benchmarks never overlap workers.
set -eo pipefail
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source /home/share/test_mpi/my_software/hpckit/HPCKit/latest/setvars.sh --use-bisheng --force
task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++ OMPI_CC=$task_sysroot/usr/bin/gcc OMPI_CXX=$task_sysroot/usr/bin/g++
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
export LIBRARY_PATH=$task_sysroot/usr/lib64:$task_sysroot/usr/lib
export LD_LIBRARY_PATH=$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LD_LIBRARY_PATH:-}
export PATH=$HOME/.cache/multigrid-arm-20261025-env/bin:$PATH
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export OMP_PROC_BIND=close
export LQCD_TEST_PYTHON=$HOME/.cache/multigrid-arm-20261025-env/bin/python
export CMAKE_CXX_COMPILER_LAUNCHER="$LQCD_TEST_PYTHON;$project_dir/tools/pin_build.py"
export CMAKE_C_COMPILER_LAUNCHER="$CMAKE_CXX_COMPILER_LAUNCHER"
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
exec python -u "$project_dir/tools/optimization/worker.py" "$@"
