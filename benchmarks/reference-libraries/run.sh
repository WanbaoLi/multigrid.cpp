#!/usr/bin/env bash
# Run serially: no overlapping compiles, setups or timed CPU solves.
set -euo pipefail
PROJECT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
WORKSPACE=$(cd "$PROJECT/.." && pwd)
cd "$WORKSPACE"
LIB="$WORKSPACE/.cache/cpu_libraries"
RUN=${RUN_DIR:-$(mktemp -d "$LIB/run-XXXXXXXX")}
mkdir -p "$RUN"
echo "$RUN" > "$LIB/last_run.txt"
echo "RESULTS=$RUN"
CONDA_BASE=/public2/home/lwb_720/miniconda3
MPI="$CONDA_BASE/envs/pyquda/bin/mpirun"
INPUT="$LIB/input"
echo 'DDalphaAMG 8 ranks x 11 threads'
OMP_NUM_THREADS=11 OMP_PROC_BIND=close OMP_PLACES=cores "$MPI" -n 8 \
  --map-by ppr:4:socket:PE=11 --bind-to core \
  "$LIB/dd_bench" "$INPUT" "$RUN/dd" 3 > "$RUN/dd.log" 2>&1
echo 'openQCD 4 ranks x 18 threads (geometry requires 72 cores)'
OMP_NUM_THREADS=18 OMP_PROC_BIND=close OMP_PLACES=cores "$MPI" -n 4 \
  --map-by ppr:2:socket:PE=18 --bind-to core \
  "$LIB/openqcd-build/openqcd_bench" "$INPUT" "$RUN/openqcd" > "$RUN/openqcd.log" 2>&1
echo 'Grid AVX512 mixed precision 8 ranks x 11 threads'
LD_LIBRARY_PATH="$LIB/deps/lib:$CONDA_BASE/lib" \
OMP_NUM_THREADS=11 OMP_PROC_BIND=close OMP_PLACES=cores "$CONDA_BASE/bin/mpirun" -n 8 \
  --map-by ppr:4:socket:PE=11 --bind-to core "$LIB/grid_bench" "$INPUT" "$RUN/grid" \
  --grid 24.24.24.64 --mpi 1.1.1.8 --threads 11 --dslash-asm --mixed > "$RUN/grid.log" 2>&1
echo 'PyQCU real/imag + torch.compile BiCGStab, 88 threads'
bash PyQCU/pyqcu/testing/cpu/run_compile_lime.sh --real-split --solve \
  --output "$RUN/pyqcu.json" > "$RUN/pyqcu.log" 2>&1
echo 'multigrid.cpp MG/GCR, 88 threads'
OMP_NUM_THREADS=88 OMP_PROC_BIND=spread OMP_PLACES=cores multigrid.cpp/build/runtime/multigrid \
  --gauge "$INPUT/gauge.bin" --source "$INPUT/b.bin" \
  --basis-file "$WORKSPACE/.cache/runs/run-Kc1cnYeU/quda/quda_near_null_canonical.bin" \
  --solver mg --tol 1e-8 --maxiter 2000 --restart 8 --repeat 2 --out "$RUN/cpp.bin" \
  > "$RUN/cpp.log" 2>&1
echo 'Convert and independently validate all three library solutions'
OPENBLAS_NUM_THREADS=1 "$CONDA_BASE/envs/pytorch/bin/python" \
  multigrid.cpp/benchmarks/reference-libraries/verify.py "$RUN" > "$RUN/solution_checks.log"
for code in dd openqcd grid; do
  OMP_NUM_THREADS=88 OMP_PROC_BIND=spread OMP_PLACES=cores multigrid.cpp/build/runtime/multigrid \
    --gauge "$INPUT/gauge.bin" --source "$INPUT/b.bin" --tol 1e-8 \
    --validate-solution "$RUN/${code}_canonical.bin" --out "$RUN/${code}_verified.bin" \
    > "$RUN/${code}_independent_residual.log" 2>&1
done
OPENBLAS_NUM_THREADS=1 "$CONDA_BASE/envs/pytorch/bin/python" \
  multigrid.cpp/benchmarks/reference-libraries/collect.py "$RUN" > "$RUN/summary.log"
echo 'ALL FIVE SOLVERS COMPLETED; INDEPENDENT RESIDUAL GATES PASSED'
