#!/usr/bin/env bash
set -euo pipefail

work=$(realpath "${1:?pass the source and build directory}")
conda_root=${CONDA_ROOT:-"$HOME/miniconda3"}
toolchain="$work/toolchain"
cuda=${CUDA_HOME:-/usr/local/cuda-12.8}
cmake="$conda_root/bin/cmake"
prefix="$work/quda-install"
export PATH="$toolchain/bin:$conda_root/bin:$PATH"

git -C "$work/quda-src" rev-parse HEAD
git -C "$work/pyquda-src" rev-parse HEAD
git -C "$work/pyquda-src" submodule status
git -C "$work/cccl" rev-parse HEAD
"$cmake" -S "$work/quda-src" -B "$work/quda-build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DCMAKE_C_COMPILER="$toolchain/bin/x86_64-conda-linux-gnu-gcc" \
    -DCMAKE_CXX_COMPILER="$toolchain/bin/x86_64-conda-linux-gnu-g++" \
    -DCMAKE_CUDA_COMPILER="$cuda/bin/nvcc" \
    -DQUDA_GPU_ARCH=sm_90 -DQUDA_GPU_ARCH_SUFFIX=real \
    -DQUDA_DIRAC_DEFAULT_OFF=ON -DQUDA_DIRAC_WILSON=ON -DQUDA_DIRAC_CLOVER=ON \
    -DQUDA_MULTIGRID=ON -DQUDA_MULTIGRID_NVEC_LIST=24 \
    -DQUDA_MULTIGRID_MRHS_LIST=16 -DQUDA_MAX_MULTI_RHS=16 \
    -DQUDA_PRECISION=14 -DQUDA_RECONSTRUCT=6 \
    -DQUDA_BUILD_ALL_TESTS=OFF -DQUDA_INSTALL_ALL_TESTS=OFF \
    -DQUDA_MPI=OFF -DQUDA_QMP=OFF -DQUDA_INTERFACE_MILC=OFF \
    -DQUDA_DOWNLOAD_EIGEN=OFF -DEIGEN_INCLUDE_DIR="$toolchain/include/eigen3" \
    -DCPM_CCCL_SOURCE="$work/cccl"

"$cmake" --build "$work/quda-build" --target quda --parallel "${BUILD_JOBS:-32}"
"$cmake" --install "$work/quda-build"
python="$conda_root/envs/pyquda/bin/python"
export QUDA_PATH="$prefix"
export CC="$toolchain/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$toolchain/bin/x86_64-conda-linux-gnu-g++"
"$python" -m pip install --no-build-isolation --no-deps "$work/pyquda-src/pyquda_core"
"$python" -m pip install --no-build-isolation --no-deps "$work/pyquda-src"
"$python" -m pip check
"$python" -c 'from pyquda import quda; from pyquda_utils import core; print(quda.__file__, core.__file__)'
sha256sum "$prefix/lib/libquda.so"
