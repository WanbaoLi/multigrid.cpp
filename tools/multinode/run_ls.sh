#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
gauge=$2
build=$3
case ${4:-64} in
  64) lattice=64; time_extent=128; block=8; block_t=4; mass=-.2334; csw=1.140825606017;;
  24) lattice=24; time_extent=64; block=6; block_t=2; mass=-.277; csw=1.160920226;;
  *) echo 'Supported real-input gates: C24 or F64P14' >&2; exit 2;;
esac
mkdir -p "$out"
exec > >(tee "$out/run.log") 2>&1
source "$root/tools/multinode/ls_env.sh"
export PYTHONPATH=$root/bindings
export LQCD_DISTRIBUTED_STORAGE=1 LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1
export LQCD_ARM_COARSE_SVE=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_COARSE_FUSED=0 LQCD_COARSE_SPATIAL_OVERLAP=1 LQCD_COARSE_BATCH_REDUCE=1
export LQCD_HBW_ALLOC=prefer LQCD_HBM=off
export OMP_NUM_THREADS=32
cd "$root"
test -z "$(git status --porcelain --untracked-files=no)"
if [[ "$lattice" == 64 && ! -f "$(dirname "$out")/c24/result.json" ]]; then
  bash "$root/tools/multinode/run_ls.sh" "$(dirname "$out")/c24" \
    "$HOME/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime" "$build" 24
  export LQCD_MULTINODE_SKIP_GATES=1
fi
git rev-parse HEAD > "$out/source-commit.txt"
if [[ ${LQCD_MULTINODE_SKIP_GATES:-0} != 1 ]]; then
  cmake --build "$build" -j 24
  OMP_NUM_THREADS=2 ctest --test-dir "$build" --output-on-failure \
    -R '^(compact_basis|distributed_cpu_backend_mpi2|distributed_batch12_mpi2)$'
fi
sha256sum "$build/liblqcd_cpu.so" "$build/verify_slab" > "$out/build.sha256"
unset OMPI_MCA_ras OMPI_MCA_plm OMPI_MCA_btl OMPI_MCA_pml
scratch=/tmp/lqcd-C64-$(basename "$out")
mpirun -n 32 --oversubscribe --map-by ppr:16:node --bind-to none \
  python tools/multinode/rank_exec.py python -u benchmarks/runtime/benchmark_multinode.py \
  --gauge "$gauge" --library "$build/liblqcd_cpu.so" --output "$out/measurements" --scratch "$scratch" \
  --lattice "$lattice" "$lattice" "$lattice" "$time_extent" --block "$block" "$block" "$block" "$block_t" \
  --mass "$mass" --csw "$csw"
mpirun -n 32 --oversubscribe --map-by ppr:16:node --bind-to none \
  python tools/multinode/rank_exec.py "$build/verify_slab" "$scratch" "$lattice" "$time_extent" "$mass" "$csw" 1e-8 0 13 \
  | tee "$out/scalar-verification.log"
python - "$out" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);text=(p/'scalar-verification.log').read_text()
assert 'SCALAR_ALL_PASSED' in text
rows=[dict(column=int(s[1]),residual=float(s[2])) for l in text.splitlines() if (s:=l.split()) and s[0]=='SCALAR_COLUMN']
assert len(rows)==13 and max(r['residual'] for r in rows)<=1e-8
d=json.loads((p/'measurements/result.json').read_text())
d.update(complete=True,independent_verification=dict(passed=True,columns=rows,method='independent scalar full-spin padded slabs'))
(p/'result.json').write_text(json.dumps(d,indent=2)+'\n')
print('COMPLETE',d['single_pure_summary'],d['twelve_pure_summary'])
PY
# The per-host path is deterministic and unique to this output directory.
mpirun -n 2 --map-by ppr:1:node --bind-to none python -c \
  'import pathlib,sys; p=pathlib.Path(sys.argv[1]); assert p.parent==pathlib.Path("/tmp") and p.name.startswith("lqcd-C64-"); [f.unlink() for f in p.glob("*.bin")]; p.rmdir()' "$scratch"
