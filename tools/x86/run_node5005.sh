#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
work=$1
cd "$work"
mpi="$HOME/miniconda3/envs/pyquda"
hmc="$HOME/miniconda3/envs/sglang"
cmake="$HOME/miniconda3/bin/cmake"
export PATH="$mpi/bin:$PATH"
export LD_LIBRARY_PATH="$mpi/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_WAIT_POLICY=PASSIVE
test "$(hostname -s)" = node5005
test "${SLURM_CPUS_PER_TASK:?}" -eq 256
test "$(nproc)" -eq 256
build="$work/build"
git -C "$root" rev-parse HEAD > source-commit.txt
"$cmake" -S "$root" -B "$build" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
    -DLQCD_BUILD_RUNTIME=ON -DLQCD_BUILD_HMC_KERNELS=ON -DLQCD_DD_REFERENCE=OFF \
    -DMPI_C_COMPILER="$mpi/bin/mpicc" -DMPI_CXX_COMPILER="$mpi/bin/mpicxx" \
    -DLQCD_TEST_PYTHON="$mpi/bin/python" -DLQCD_CPU_BACKEND_TEST_TIMEOUT=720 \
    '-DLQCD_MPI_FLAGS=-bind-to;core:2;-launcher;fork;-rmk;user'
"$cmake" --build "$build" -j 24
gate='core|compact_basis|halo_storage'
if [[ ${LQCD_ITP_MPI_REGRESSION:-1} == 1 ]]; then
    gate+='|cpu_backend_mpi2|distributed_cpu_backend_mpi2|reused_halo_mpi2'
fi
OMP_NUM_THREADS=2 OMP_PROC_BIND=close OMP_PLACES=cores OMP_WAIT_POLICY=ACTIVE \
    "$HOME/miniconda3/bin/ctest" --test-dir "$build" --output-on-failure \
    -R "^($gate)$" | tee ctest.log
sha256sum "$build/"{liblqcd_cpu.so,verify_slab,multigrid,liblqcd_hmc_kernels.so} > build.sha256

solve() {
    local l=$1 b=$2 csw=$3 gauge=$4 digest=$5
    local out="$work/c$l"
    printf '%s  %s\n' "$digest" "$gauge" | sha256sum -c
    mkdir "$out"
    local run=("$mpi/bin/python" "$root/tools/run_numa.py" --lattice "$l" "$l" "$l" 64 \
        --block "$b" "$b" "$b" 4 --threads 16 --ranks-per-numa 2 --mpirun "$mpi/bin/mpiexec" --)
    LQCD_DISTRIBUTED_STORAGE=1 LQCD_HBW_ALLOC=off LQCD_COARSE_THREADS=8 \
      "${run[@]}" "$mpi/bin/python" -u "$root/benchmarks/runtime/benchmark_multinode.py" \
        --backend x86 --threads 16 --ranks-per-node 16 --library "$build/liblqcd_cpu.so" \
        --lattice "$l" "$l" "$l" 64 --block "$b" "$b" "$b" 4 --mass -.279 --csw "$csw" \
        --tol 1e-8 --source wall --single-only --gauge "$gauge" \
        --output "$out/measurements" --scratch "$out/slabs" | tee "$out/solver.log"
    "${run[@]}" "$build/verify_slab" "$out/slabs" "$l" 64 -.279 "$csw" 1e-8 0 1 wall \
        | tee "$out/independent.log"
    grep -qx SCALAR_ALL_PASSED "$out/independent.log"
    "$mpi/bin/python" - "$out" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
data = json.loads((out / "measurements/result.json").read_text())
line = next(s for s in (out / "independent.log").read_text().splitlines() if s.startswith("SCALAR_COLUMN 0 "))
residual = float(line.split()[2])
assert 0 <= residual <= 1e-8 and data["measurements_complete"]
data.update(complete=True, independent_full_residual=residual)
(out / "result.json").write_text(json.dumps(data, indent=2) + "\n")
PY
}

generate() (
printf '%s  %s\n' f59477552f281812cc703f83c3c9f95415a3ed87dfb4fdc5b2bb9176e7dc579c "$work/hmc_initial.lime" | sha256sum -c
mkdir -p "$work/hmc-deps"
ln -s "$mpi/lib/python3.12/site-packages/mpi4py" "$work/hmc-deps/mpi4py"
export PYTHONPATH="$work/hmc-deps:$root/bindings"
export LQCD_HMC_SCHUR_LIBRARY="$build/liblqcd_hmc_kernels.so"
"$hmc/bin/python" -c 'import numpy, scipy, torch; from mpi4py import MPI; print(MPI.Get_library_version().splitlines()[0])'
"$hmc/bin/python" "$root/tools/run_numa.py" --lattice 24 24 24 64 --time-slab \
    --threads 4 --ranks-per-numa 8 --mpirun "$mpi/bin/mpiexec" -- "$hmc/bin/python" -u "$root/tools/hmc/generate_mpi.py" \
    --output "$work/hmc" --initial-lime "$work/hmc_initial.lime" --lattice 24 24 24 64 \
    --beta 5.6 --mass-light 0.5 --mass-strange 0.8 --csw 1 --trajectories 8 --warmup 2 \
    --length 0.036 --steps 2 --gauge-steps 2 --save-every 2 --threads 4 --md-order 16 --seed 6452 \
    --packed-faces --direct-clover --compact-spin --zolotarev --force-pole-batch 11 --projected-force-faces \
    | tee "$work/hmc.log"
OMP_NUM_THREADS=2 "$hmc/bin/python" "$root/tools/hmc/verify_configs.py" "$work/hmc" \
    --reference "$build/multigrid"
)

gauge24="$HOME/.cache/quda-wall-20261122/inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
set +e
(set -e; solve 24 6 1.160678675188 "$gauge24" f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326)
status=$?
pending32=1
pending_hmc=1
deadline=$((SECONDS + 14400))
while (( pending32 || pending_hmc )); do
    if (( pending32 )) && [[ -s $work/c32.lime ]]; then
        (set -e; solve 32 8 1.1606789224 "$work/c32.lime" bc2918403eee5d1e10a409fc0e69ac03b22cc7f0cf71be760b44a593ff0d0828)
        if (( $? != 0 )); then status=1; fi
        pending32=0
    elif (( pending_hmc )) && [[ -s $work/hmc_initial.lime ]]; then
        (set -e; generate)
        if (( $? != 0 )); then status=1; fi
        pending_hmc=0
    elif (( SECONDS >= deadline )); then
        echo "Timed out waiting for inputs: C32=$pending32 RHMC=$pending_hmc" >&2
        exit 1
    else
        sleep 30
    fi
done
exit "$status"
