#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
SOURCE=$TASK/source-reliable
test "$(git -C "$SOURCE" rev-parse HEAD)" = 797ac9c9b5b09050d71251899f42201da2ac1266
unset NATIVE_OUTER_FLOAT
cmake -S "$SOURCE" -B "$TASK/build-reliable" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
 -DLQCD_BUILD_RUNTIME=ON -DLQCD_KUPL_HBW=ON -DLQCD_KUPL_ROOT="$TASK_SDK/kupl/gcc/release" \
 -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
 -DMPI_C_COMPILER="$(command -v mpicc)" -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
 -DLQCD_TEST_PYTHON="$FAIR_PYTHON" \
 -DCMAKE_CXX_COMPILER_LAUNCHER="$FAIR_PYTHON;$SOURCE/tools/pin_build.py" \
 -DCMAKE_C_COMPILER_LAUNCHER="$FAIR_PYTHON;$SOURCE/tools/pin_build.py" \
 -DLQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core' \
 -DCMAKE_SHARED_LINKER_FLAGS="-L$TASK_SDK/compiler/gcc/lib64 -Wl,-rpath,$TASK_SDK/compiler/gcc/lib64" \
 -DCMAKE_EXE_LINKER_FLAGS="-L$TASK_SDK/compiler/gcc/lib64 -Wl,-rpath,$TASK_SDK/compiler/gcc/lib64"
cmake --build "$TASK/build-reliable" -j16
OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close ctest --test-dir "$TASK/build-reliable" \
 --parallel 1 --output-on-failure -R '^(core|mg_tuning|cpu_backend_mpi2|runtime_batch|batch12_mpi2)$'
touch "$TASK/reliable-build-passed"
