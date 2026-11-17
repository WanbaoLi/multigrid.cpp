#!/usr/bin/env bash
# Execute in a whole allocated compute node; upstream remains unmodified.
set -eo pipefail
upstream=$1
out=$2
control=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[[ ! -e $out ]] || { echo 'Output exists'; exit 2; }
mkdir -p "$out"
exec > >(tee "$out/run.log") 2>&1
task_sdk=/work_ssd/software/HPCKit/25.2.1
source "$task_sdk/setvars.sh" --use-bisheng --force
export OPAL_PREFIX=$task_sdk/hmpi/bisheng/release/hmpi
export PATH=$OPAL_PREFIX/bin:/work_ssd/software/soft/tool/anaconda3/2023.3/bin:$PATH
task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OMP_NUM_THREADS=2
unset OMP_PLACES OMP_PROC_BIND GOMP_CPU_AFFINITY KMP_AFFINITY
base_python=/work_ssd/software/soft/tool/anaconda3/2023.3/bin/python3
scratch=$(mktemp -d /tmp/pyqcu-review-XXXXXXXX)
printf '%s\n' "$scratch" > "$out/scratch-path.txt"
cp -a "$upstream" "$scratch/upstream"
upstream=$scratch/upstream
wheel=/home/share/nsls_lwb/lqcd-run/pyqcu-mpi4py-4.1.1-cp310-aarch64.whl
"$base_python" -m venv --without-pip --system-site-packages "$scratch/python"
python_bin=$scratch/python/bin/python
"$python_bin" -m zipfile -e "$wheel" "$scratch/python/lib/python3.10/site-packages"
own=/home/share/nsls_lwb/lqcd-run/health-20261113/source
export PYTHONPATH=$upstream:$own/bindings
export PYQCU_KUPL_LIB=$out/build/libqcu.so
lime=/home/share/nsls_lwb/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
git -C "$upstream" rev-parse HEAD > "$out/upstream-commit.txt"
git -C "$upstream" status --short > "$out/upstream-status.txt"
sha256sum "$lime" "$wheel" > "$out/input-and-wheel.sha256"
"$python_bin" -c 'import numpy,h5py; from mpi4py import MPI; print(numpy.__version__,h5py.__version__,MPI.Get_library_version())'
"$python_bin" "$own/tools/probe_host.py" > "$out/host.json"
on_exit() {
  code=$?
  trap - EXIT
  "$python_bin" - "$out" "$code" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1],'status.json').write_text(json.dumps({'complete':int(sys.argv[2])==0,'exit_code':int(sys.argv[2])},indent=2)+'\n')
PY
  exit "$code"
}
trap on_exit EXIT
cmake -S "$upstream/cpp/kupl/qcu" -B "$out/build" -DCMAKE_BUILD_TYPE=Release \
  -DPython3_EXECUTABLE="$python_bin" \
  -DKUPL_ENABLE_NATIVE=ON -DKUPL_ENABLE_LTO=ON -DKUPL_BUILD_TESTS=ON \
  -DCMAKE_CXX_COMPILER="$CXX" -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
  '-DMPIEXEC_PREFLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core' \
  -DCMAKE_EXE_LINKER_FLAGS="-L$task_sdk/compiler/gcc/lib64 -Wl,-rpath,$task_sdk/compiler/gcc/lib64" \
  -DCMAKE_SHARED_LINKER_FLAGS="-L$task_sdk/compiler/gcc/lib64 -Wl,-rpath,$task_sdk/compiler/gcc/lib64"
cmake --build "$out/build" -j16
ctest --test-dir "$out/build" --output-on-failure --parallel 1
sha256sum "$out/build/libqcu.so" > "$out/build.sha256"
export KUPL_NUMA_BIND=1 KUPL_MEMORY_POLICY=preferred KUPL_MEMORY_NODE=local+16
export KUPL_REQUIRE_MEMORY_BIND=1 KUPL_HUGEPAGE=1 KUPL_TOPOLOGY_REPORT=1
export KUPL_PROFILE_OPT=1 KUPL_SKIP_FINAL_RESIDUAL=1 OMP_WAIT_POLICY=ACTIVE OMP_DYNAMIC=FALSE
export KUPL_ENABLE_T2_LANES=1 KUPL_HALO_PACK6=1 KUPL_HALO_DEDUP_PACK=1
export KUPL_T_LOCAL_IN_PART1=1 KUPL_ENABLE_BOUNDARY_LANES=1 KUPL_SHM_HALO=0
export KUPL_OMP_THREADS=18 OMP_NUM_THREADS=18
mkdir -p "$scratch/inputs"
mpirun --host localhost:16 -n 16 --bind-to none --map-by ppr:1:numa \
  "$python_bin" -u "$control/reproduce.py" prepare --upstream "$upstream" \
  --lime "$lime" --out "$scratch/inputs"
cp "$scratch/inputs/inputs.json" "$out/inputs.json"
run_case() {
  label=$1; shift
  mkdir -p "$out/$label"
  set +e
  timeout 1800 mpirun --host localhost:16 -n 16 --bind-to none --map-by ppr:1:numa \
    "$python_bin" -u "$control/reproduce.py" "$@" --upstream "$upstream" \
    --inputs "$scratch/inputs" --out "$scratch/$label" > "$out/$label/run.log" 2>&1
  code=$?
  set -e
  printf '%s\n' "$code" > "$out/$label/exit-code.txt"
  if [[ -d $scratch/$label ]]; then
    find "$scratch/$label" -maxdepth 1 -name '*.json' -type f -exec cp '{}' "$out/$label/" ';'
  fi
  echo "CASE_COMPLETE $label exit=$code"
  if [[ $code == 0 && $1 == full12 ]]; then
    OMP_NUM_THREADS=8 OMP_PLACES=cores OMP_PROC_BIND=spread \
      "$python_bin" -u "$control/reproduce.py" verify --upstream "$upstream" \
      --inputs "$scratch/inputs" --out "$scratch/$label" \
      --reference /home/share/nsls_lwb/lqcd-run/reproduce-efe57de-20261116-1749/build/multigrid \
      > "$out/$label/scalar.log" 2>&1 || true
    cp "$scratch/$label/scalar-verification.json" "$out/$label/"
  fi
}
run_case report-c64-random single --dtype c64 --tol 1e-6 --source random
run_case report-c128-ones single --dtype c128 --tol 1e-9 --source ones
run_case report-c128-mg single --dtype c128 --tol 1e-9 --source ones --solver mg
export KUPL_OMP_THREADS=32 OMP_NUM_THREADS=32
run_case physical-bicg-full12 full12 --dtype c128 --tol 1e-8 --source point
run_case physical-mg-full12 full12 --dtype c128 --tol 1e-8 --source point --solver mg
own_python=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
own_build=/home/share/nsls_lwb/lqcd-run/reproduce-efe57de-20261116-1749/build
mkdir -p "$out/own-mg"
PYTHONPATH=$own/bindings "$own_python" "$own/tools/run_numa.py" \
  --lattice 24 24 24 64 --block 6 6 6 4 --numa-nodes 0-15 --ranks-per-numa 1 --threads 37 -- \
  "$own_python" -u "$own/benchmarks/runtime/check_lime_solver.py" --gauge "$lime" \
  --output "$scratch/own-mg" --backend arm --mass -0.277 --csw 1.160920226 --block 6 6 6 4 \
  --plan "$own/profiles/optimization/lingsheng-shared-uniform.json" \
  --library "$own_build/liblqcd_cpu.so" --repeats 3 --tol 1e-8 \
  --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 > "$out/own-mg/run.log" 2>&1
PYTHONPATH=$own/bindings OMP_NUM_THREADS=8 OMP_PLACES=cores OMP_PROC_BIND=spread \
  "$own_python" "$own/benchmarks/runtime/verify_lime_solver.py" "$scratch/own-mg" \
  --reference "$own_build/multigrid" --extractor "$own_build/extract_columns" \
  --reference-threads 8 --tol 1e-8 > "$out/own-mg/scalar.log" 2>&1
find "$scratch/own-mg" -maxdepth 1 -name '*.json' -type f -exec cp '{}' "$out/own-mg/" ';'
echo "PYQCU_REVIEW_COMPLETE $out"
