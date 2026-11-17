#!/usr/bin/env bash
# One shared compute task: four physical CPUs, no performance scaling claim.
set -eo pipefail
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
out=$1
[[ ! -e $out ]] || { echo 'Output exists'; exit 2; }
mkdir -p "$out"
exec > >(tee "$out/run.log") 2>&1
[[ -z $(git -C "$project" status --porcelain --untracked-files=no) ]]
sdk=/work_ssd/software/HPCKit/25.2.1
export OPAL_PREFIX=$sdk/hmpi/bisheng/release/hmpi
export PATH=$OPAL_PREFIX/bin:/work_ssd/software/soft/tool/anaconda3/2023.3/bin:$PATH
export LD_LIBRARY_PATH=$sdk/compiler/gcc/lib64:$OPAL_PREFIX/lib:${LD_LIBRARY_PATH:-}
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export PYTHONPATH=/home/share/nsls_lwb/lqcd-run/pyqcu-review-deps-cp310:${PYTHONPATH:-}
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=2
python_bin=/work_ssd/software/soft/tool/anaconda3/2023.3/bin/python3
on_exit() {
  code=$?; trap - EXIT
  printf '{"complete":%s,"exit_code":%s}\n' "$([[ $code == 0 ]] && echo true || echo false)" "$code" > "$out/status.json"
  exit "$code"
}
trap on_exit EXIT
"$python_bin" -c 'import torch,numpy; from mpi4py import MPI; print(torch.__version__,numpy.__version__,MPI.Get_library_version())'
"$python_bin" "$project/tools/probe_host.py" > "$out/host.json"
git -C "$project" rev-parse HEAD > "$out/source-commit.txt"
cmake -S "$project" -B "$out/build" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_OPENMP=OFF \
  -DCMAKE_CXX_COMPILER=/work_ssd/system/os_jasmine_v01/vroot/usr/bin/g++ \
  -DCMAKE_C_COMPILER=/work_ssd/system/os_jasmine_v01/vroot/usr/bin/gcc \
  -DLQCD_TEST_HMC_REFERENCE=ON -DLQCD_HMC_REQUIRE_LIME_READER=ON \
  -DPython3_EXECUTABLE="$python_bin"
cmake --build "$out/build" -j4
ctest --test-dir "$out/build" --output-on-failure --parallel 1
cp "$out/build/hmc-validation.json" "$out/hmc-validation.json"
sha256sum "$out/build/multigrid" > "$out/build.sha256"
"$python_bin" -u "$project/tools/hmc/generate.py" --output "$out/chain" \
  --lattice 2 2 2 2 --beta 5.6 --mass-light 0.5 --mass-strange 0.8 --csw 1 \
  --trajectories 80 --warmup 40 --length 0.5 --steps 10 --save-every 10 --seed 1729 --threads 2
"$python_bin" "$project/tools/hmc/verify_configs.py" "$out/chain" --reference "$out/build/multigrid"
echo "HMC_COMPLETE $out"
