#!/bin/bash
set -eo pipefail
R=/public2/home/lwb_720/.cache/mg-x86-20261110
P=/public2/home/lwb_720/miniconda3/envs/pyquda/bin
export PATH=$P:/public2/home/lwb_720/miniconda3/bin:$PATH
git clone --shared --no-checkout /public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/source "$R/source"
git -C "$R/source" fetch "$R/source.bundle" HEAD
git -C "$R/source" checkout --detach FETCH_HEAD
cmake -S "$R/source" -B "$R/build" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON -DLQCD_BUILD_RUNTIME=ON \
 -DCMAKE_C_COMPILER=/public2/home/lwb_720/miniconda3/bin/gcc -DCMAKE_CXX_COMPILER=/public2/home/lwb_720/miniconda3/bin/g++ \
 -DMPI_C_COMPILER=$P/mpicc -DMPI_CXX_COMPILER=$P/mpicxx -DLQCD_TEST_PYTHON=$P/python \
 '-DLQCD_MPI_FLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
cmake --build "$R/build" -j16
export OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close OPENBLAS_NUM_THREADS=1
for mode in 0 1 2; do
 LQCD_X86_CLOVER_REGISTERS=$mode ctest --test-dir "$R/build" --output-on-failure --parallel 1 \
  -R '^(core|wilson_.*|cpu_backend_mpi2|batch12_mpi2|runtime_batch|mg_tuning)$' > "$R/tests-$mode.log" 2>&1
done
touch "$R/build-passed"
