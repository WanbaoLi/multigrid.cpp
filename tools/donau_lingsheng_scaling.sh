#!/usr/bin/env bash
# Run with dsub -q <queue> -A <account> -nn 1 -N 1 -x job \
#   -R 'cpu=<allocated cores>,mem=<MB>MB' -T 3600 --cwd <source directory> \
#   /bin/bash tools/donau_lingsheng_scaling.sh
set -e
source "${LQCD_TOOLCHAIN_ENV:?set the installed HPCKit setvars.sh path}" --use-bisheng --force
set -u
project_dir=${LQCD_SOURCE_DIR:-$PWD}
if [[ ! -f "$project_dir/tools/run_numa.py" ]]; then
    echo 'Set LQCD_SOURCE_DIR to the multigrid.cpp source directory.' >&2
    exit 2
fi
task_root=${LQCD_SCALING_ROOT:-"$HOME/.cache/multigrid-lingsheng-scaling"}/${LQCD_RUN_ID:-"donau-$(date +%Y%m%dT%H%M%S)"}
mkdir -p "$task_root"
exec > >(tee "$task_root/job.log") 2>&1
hostname
date -Is
lscpu
numactl --hardware
numactl --show
python_bin=${LQCD_PYTHON:-"$HOME/.cache/multigrid-arm-20261025-env/bin/python"}
if [[ ${LQCD_COMPILER:-gcc} == gcc ]]; then
    task_sysroot=${LQCD_SYSROOT:-/work_ssd/system/os_jasmine_v01/vroot}
    export CC="$task_sysroot/usr/bin/gcc" CXX="$task_sysroot/usr/bin/g++"
    export OMPI_CC="$CC" OMPI_CXX="$CXX"
    export CPATH="$task_sysroot/usr/include:$task_sysroot/usr/local/include"
    export LIBRARY_PATH="$task_sysroot/usr/lib64:$task_sysroot/usr/lib"
    export LD_LIBRARY_PATH="$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LD_LIBRARY_PATH:-}"
else
    export CC=clang CXX=clang++
fi
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=2
export OMP_PROC_BIND=spread OMP_PLACES=cores
# One Donau replica reserves this node's cores, while this single-host tool
# launches its own NUMA ranks. Bypass Donau's one-slot MPI replica description.
export OMPI_MCA_ras='^donau' OMPI_MCA_plm=isolated
"$python_bin" "$HOME/.codex/skills/kunpeng-lingsheng-cpu/scripts/probe_cpu.py" > "$task_root/cpu-probe.json"
"$python_bin" -c 'from mpi4py import MPI; print(MPI.Get_library_version())'
cmake -S "$project_dir" -B "$task_root/build" \
    -DCMAKE_BUILD_TYPE=Release -DLQCD_BUILD_RUNTIME=ON -DMULTIGRID_NATIVE=ON \
    -DMPI_C_COMPILER="$(command -v mpicc)" -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
    -DLQCD_TEST_PYTHON="$python_bin" \
    '-DLQCD_MPI_FLAGS=--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
cmake --build "$task_root/build" -j "${LQCD_BUILD_JOBS:-24}"
ctest --test-dir "$task_root/build" \
    -R '^(core|arm_kernel|numa_launcher|cpu_backend_serial|cpu_backend_mpi2|mg_tuning)$' \
    --output-on-failure
# run_numa discovers the permitted physical cores; system-reserved cores are
# excluded by the job cpuset (37 of 38 per NUMA on the observed cn05131).
unset OMP_PLACES OMP_PROC_BIND
"$python_bin" "$project_dir/tools/benchmark_numa_scaling.py" \
    --gauge "${LQCD_GAUGE:?set the raw LIME file}" \
    --library "$task_root/build/liblqcd_cpu.so" --mpirun "$(command -v mpirun)" \
    --numa-counts 8 16 --repeats 3 --backend arm --output "$task_root/results"
date -Is
