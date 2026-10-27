#!/usr/bin/env bash
# Submit on the target cluster; partition/account belong to sbatch arguments.
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=608
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --time=01:00:00
#SBATCH --job-name=lqcd-numa-scaling

set -euo pipefail
if [[ -z ${SLURM_JOB_ID:-} ]]; then
    echo 'Submit this script with sbatch on the compute cluster.' >&2
    exit 2
fi
# Slurm executes a spool copy of this file, so BASH_SOURCE is not the repo path.
project_dir=${LQCD_SOURCE_DIR:-${SLURM_SUBMIT_DIR:?}}
if [[ ! -f "$project_dir/CMakeLists.txt" || ! -f "$project_dir/tools/run_numa.py" ]]; then
    echo 'Submit from multigrid.cpp/ or export LQCD_SOURCE_DIR to that directory.' >&2
    exit 2
fi
task_root=${LQCD_SCALING_ROOT:-"$HOME/.cache/multigrid-lingsheng-scaling"}/"$SLURM_JOB_ID"
mkdir -p "$task_root"
exec > >(tee "$task_root/job.log") 2>&1
printf 'job=%s host=%s source=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$project_dir"
date -Is
env | sort | sed -n '/^SLURM_/p'
lscpu
lscpu -e=CPU,NODE,SOCKET,CORE
if command -v numactl >/dev/null; then
    numactl --hardware
    numactl --show || true
fi

# A site compiler/MPI module can be loaded before submission and exported.
python_bin=${LQCD_PYTHON:-"$HOME/.cache/multigrid-arm-20261025-env/bin/python"}
cmake_bin=${LQCD_CMAKE:-"$HOME/.cache/multigrid-arm-20261025-env/bin/cmake"}
ctest_bin=${LQCD_CTEST:-"$(dirname -- "$cmake_bin")/ctest"}
mpirun_bin=${LQCD_MPIRUN:-mpirun}
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
if [[ -n ${LQCD_MPI_LIBRARY_PATH:-} ]]; then
    export LD_LIBRARY_PATH="$LQCD_MPI_LIBRARY_PATH:${LD_LIBRARY_PATH:-}"
fi
"$python_bin" -c 'from mpi4py import MPI; import numpy; print(MPI.Get_library_version()); print("NumPy", numpy.__version__)'
"$python_bin" "${LQCD_CPU_PROBE:-$HOME/.codex/skills/kunpeng-lingsheng-cpu/scripts/probe_cpu.py}" > "$task_root/cpu-probe.json"

# Build on this allocation. Native ISA must be recognized by its compiler;
# failures remain visible instead of silently falling back to login-host code.
"$cmake_bin" -S "$project_dir" -B "$task_root/build" \
    -DCMAKE_BUILD_TYPE=Release -DLQCD_BUILD_RUNTIME=ON -DMULTIGRID_NATIVE=ON \
    -DLQCD_TEST_PYTHON="$python_bin"
"$cmake_bin" --build "$task_root/build" -j "${LQCD_BUILD_JOBS:-16}"
"$ctest_bin" --test-dir "$task_root/build" \
    -R '^(core|arm_kernel|numa_launcher)$' --output-on-failure

"$python_bin" "$project_dir/tools/benchmark_numa_scaling.py" \
    --gauge "${LQCD_GAUGE:?set LQCD_GAUGE to the raw LIME file}" \
    --library "$task_root/build/liblqcd_cpu.so" --mpirun "$mpirun_bin" \
    --numa-counts 8 16 --threads 38 --repeats 3 --backend arm \
    --output "$task_root/results"
date -Is
