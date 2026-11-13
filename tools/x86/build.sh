#!/usr/bin/env bash
# Build the project-owned x86 CPU runtime on an AMD node.
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
build_dir=${BUILD_DIR:-$project_dir/build/amd9755}
python_bin=${PYTHON:-${LQCD_TEST_PYTHON:-python3}}
build_jobs=${BUILD_JOBS:-16}

if [[ -n ${MPI_PREFIX:-} ]]; then
    mpi_c=${MPICC:-$MPI_PREFIX/bin/mpicc}
    mpi_cxx=${MPICXX:-$MPI_PREFIX/bin/mpicxx}
else
    mpi_c=${MPICC:-mpicc}
    mpi_cxx=${MPICXX:-mpicxx}
fi

mpi_c=$(command -v "$mpi_c")
mpi_cxx=$(command -v "$mpi_cxx")
command -v cmake >/dev/null
command -v "$python_bin" >/dev/null

mkdir -p "$build_dir"
cmake -S "$project_dir" -B "$build_dir" \
    -DCMAKE_BUILD_TYPE=Release \
    -DMULTIGRID_NATIVE=ON \
    -DLQCD_BUILD_RUNTIME=ON \
    -DLQCD_DD_REFERENCE=OFF \
    -DLQCD_KUPL_HBW=OFF \
    -DMPI_C_COMPILER="$mpi_c" \
    -DMPI_CXX_COMPILER="$mpi_cxx" \
    -DLQCD_TEST_PYTHON="$python_bin" \
    "-DLQCD_MPI_FLAGS=${LQCD_MPI_FLAGS:---map-by;slot:PE=2;--bind-to;core}"
cmake --build "$build_dir" -j "$build_jobs"

echo "Built x86 runtime: $build_dir/liblqcd_cpu.so"
