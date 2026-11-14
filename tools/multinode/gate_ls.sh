#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
mkdir -p "$out"
exec > >(tee "$out/gates.log") 2>&1
source "$root/tools/multinode/ls_env.sh"
cd "$root"
git rev-parse HEAD > "$out/source-commit.txt"
cmake -S . -B "$out/build" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
  -DLQCD_BUILD_RUNTIME=ON -DLQCD_DD_REFERENCE=OFF -DLQCD_KUPL_HBW=ON \
  -DLQCD_KUPL_ROOT="$task_sdk/kupl/gcc/release" \
  -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
  -DMPI_C_COMPILER="$(command -v mpicc)" -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
  -DLQCD_TEST_PYTHON="$(command -v python)" \
  '-DLQCD_MPI_FLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core' \
  "-DCMAKE_EXE_LINKER_FLAGS=-L$task_sdk/compiler/gcc/lib64 -Wl,-rpath,$task_sdk/compiler/gcc/lib64" \
  "-DCMAKE_SHARED_LINKER_FLAGS=-L$task_sdk/compiler/gcc/lib64 -Wl,-rpath,$task_sdk/compiler/gcc/lib64"
cmake --build "$out/build" -j 24
ctest --test-dir "$out/build" --output-on-failure -R '^(core|halo_storage|compact_basis|native_allocator|cpu_backend_mpi2|shared_cpu_backend_mpi2|shared_batch12_mpi2|reused_halo_mpi2|distributed_.*)$' \
  | tee "$out/ctest.log"
