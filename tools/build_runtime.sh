#!/usr/bin/env bash
# Build the production runtime; external reference code is explicitly opt-in.
set -euo pipefail
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
build_dir=${BUILD_DIR:-$project_dir/build/runtime}
mpi_c=${MPICC:-${MPI_PREFIX:+$MPI_PREFIX/bin/}mpicc}
mpi_cxx=${MPICXX:-${MPI_PREFIX:+$MPI_PREFIX/bin/}mpicxx}

cmake_options=(
  -DCMAKE_BUILD_TYPE=Release
  -DLQCD_BUILD_RUNTIME=ON
  -DMULTIGRID_NATIVE="${LQCD_CPU_NATIVE:-ON}"
  -DLQCD_DD_REFERENCE="${LQCD_DD_REFERENCE:-OFF}"
  -DMPI_C_COMPILER="$mpi_c"
  -DMPI_CXX_COMPILER="$mpi_cxx"
  -DLQCD_TEST_PYTHON="${LQCD_TEST_PYTHON:-}"
)

if [[ ${LQCD_DD_REFERENCE:-OFF} == ON ]]; then
  reference_source=${DDALPHAAMG_SOURCE:-$project_dir/../.cache/cpu_libraries/DDalphaAMG}
  if [[ ! -f "$reference_source/src/DDalphaAMG.h" ]]; then
    reference_source="$project_dir/.cache/third_party/DDalphaAMG"
    mkdir -p "$reference_source"
    git -C "$reference_source" init
    if ! git -C "$reference_source" remote get-url origin >/dev/null 2>&1; then
      git -C "$reference_source" remote add origin https://github.com/etmc/DDalphaAMG.git
    fi
    git -C "$reference_source" fetch --depth 1 origin 9c723a818b4b1d69b7547d33087ab0c520eba38c
    git -C "$reference_source" checkout --detach FETCH_HEAD
  fi
  cmake_options+=(
    -DLQCD_DDALPHAAMG_SOURCE="$reference_source"
    -DLQCD_DD_SIMD="${LQCD_DD_SIMD:-SSE}"
    -DLQCD_CPU_NATIVE="${LQCD_CPU_NATIVE:-ON}"
  )
fi

cmake -S "$project_dir" -B "$build_dir" "${cmake_options[@]}"
cmake --build "$build_dir" -j "${BUILD_JOBS:-8}"
