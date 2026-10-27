#!/usr/bin/env bash
# Run only: no builds, GPUs, MPI or mutation of the reference dataset.
set -euo pipefail
[[ $# == 3 ]] || { echo 'Usage: bash tests/oracle/run_oracle.sh BINARY REFERENCE_RUN NEW_OUTPUT_DIR' >&2; exit 2; }
BIN=$(realpath "$1")
REF=$(realpath "$2")
OUT=$(realpath -m "$3")
TESTS=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-python3}
[[ ! -e "$OUT" ]] || { echo "Output already exists: $OUT" >&2; exit 1; }
mkdir -p "$OUT"/{logs,fine,gcr,mg/trace,gates}
ln -s "$REF/quda" "$OUT/quda"
ln -s "$REF/common" "$OUT/common"
ln -s "$REF/logs/quda.log" "$OUT/logs/quda.log"
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-128} OMP_PLACES=cores OMP_PROC_BIND=spread
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export LQCD_ARTIFACT_DIR="$OUT/quda"
CPU=("$BIN")
if command -v numactl >/dev/null; then CPU=(numactl --interleave=all "$BIN"); fi
COMMON=(--gauge "$OUT/common/smeared_gauge_tzyx_mu_rc.bin" --source "$OUT/quda/source.bin")
SOLVE=(--tol 1e-10 --maxiter 2000 --restart 8)
"$PY" "$TESTS/prepare_oracle.py" "$OUT"
echo '[test] fine operator'
"${CPU[@]}" --gauge "$OUT/common/smeared_gauge_tzyx_mu_rc.bin" --source "$OUT/quda/probe_source.bin" --operator --out "$OUT/fine/cpu_M_source_global.bin" > "$OUT/logs/cpu-fine.log" 2>&1
for name in M dslash clover; do ln -s "$OUT/quda/quda_${name}_source_global.npy" "$OUT/fine/quda_${name}_source_global.npy"; done
LQCD_ARTIFACT_DIR="$OUT/fine" "$PY" "$TESTS/compare_cpu_quda.py" > "$OUT/logs/fine-compare.log" 2>&1
touch "$OUT/gates/Fine_operator"
echo '[test] P/R and Ac=RAP'
"${CPU[@]}" "${COMMON[@]}" --basis-file "$OUT/quda/quda_near_null_canonical.bin" --trace "$OUT/mg/trace" --coarse-source "$OUT/mg/quda_ec.bin" --check-ac --check-only > "$OUT/logs/ac.log" 2>&1
touch "$OUT/gates/Ac_=_RAP"
LQCD_CPU_TRANSFER_DIR="$OUT/mg/trace" "$PY" "$TESTS/compare_quda_p_probe.py" > "$OUT/logs/pr.log" 2>&1
touch "$OUT/gates/P_R"
echo '[test] plain GCR'
"${CPU[@]}" "${COMMON[@]}" "${SOLVE[@]}" --solver gcr --out "$OUT/gcr/x.bin" > "$OUT/logs/cpu-plain.log" 2>&1
echo '[test] MG-GCR'
"${CPU[@]}" "${COMMON[@]}" "${SOLVE[@]}" --solver mg --basis-file "$OUT/quda/quda_near_null_canonical.bin" --trace "$OUT/mg/trace" --out "$OUT/mg/x.bin" > "$OUT/logs/cpu-mg.log" 2>&1
for stage in gcr mg; do
    "${CPU[@]}" "${COMMON[@]}" "${SOLVE[@]}" --validate-solution "$OUT/$stage/quda_x.bin" --out "$OUT/$stage/quda_verified.bin" > "$OUT/logs/verify-$stage.log" 2>&1
done
"$PY" "$TESTS/compare_all.py" "$OUT" | tee "$OUT/logs/compare.log"
"$PY" "$TESTS/compare_baseline.py" "$REF" "$OUT" | tee "$OUT/logs/baseline-compare.log"
