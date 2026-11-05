#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v2
source "$TASK/ours_env.sh"
SOURCE=/home/share/nsls_lwb/.cache/mg-opt-20261103/source-delivery-297
mkdir "$TASK/build-login"
cmake -S "$SOURCE" -B "$TASK/build-login" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
 -DLQCD_BUILD_RUNTIME=ON -DLQCD_KUPL_HBW=OFF -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
 -DMPI_C_COMPILER="$(command -v mpicc)" -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
 -DLQCD_TEST_PYTHON="$FAIR_PYTHON" \
 -DCMAKE_CXX_COMPILER_LAUNCHER="$FAIR_PYTHON;$SOURCE/tools/pin_build.py" \
 -DCMAKE_C_COMPILER_LAUNCHER="$FAIR_PYTHON;$SOURCE/tools/pin_build.py" \
 -DCMAKE_SHARED_LINKER_FLAGS="-L$TASK_SDK/compiler/gcc/lib64 -Wl,-rpath,$TASK_SDK/compiler/gcc/lib64" \
 -DCMAKE_EXE_LINKER_FLAGS="-L$TASK_SDK/compiler/gcc/lib64 -Wl,-rpath,$TASK_SDK/compiler/gcc/lib64"
cmake --build "$TASK/build-login" -j8
OMP_NUM_THREADS=2 OMP_PLACES=cores ctest --test-dir "$TASK/build-login" --output-on-failure -R '^(core|wilson_.*|coarse_kernel)$'
touch "$TASK/login-build-passed"

