#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
gauge=$2
build=$3
mkdir -p "$out"
exec > >(tee "$out/run.log") 2>&1
source "$root/tools/multinode/ls_env.sh"
unset OMPI_MCA_ras OMPI_MCA_plm OMPI_MCA_btl OMPI_MCA_pml
export PYTHONPATH=$root/bindings
export LQCD_DISTRIBUTED_STORAGE=1 LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=1
export LQCD_ARM_COARSE_SVE=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_COARSE_FUSED=0 LQCD_COARSE_SPATIAL_OVERLAP=1 LQCD_COARSE_BATCH_REDUCE=1
export LQCD_HBW_ALLOC=prefer LQCD_HBM=off
export OMP_NUM_THREADS=32
cd "$root"
test -z "$(git status --porcelain --untracked-files=no)"
git rev-parse HEAD > "$out/source-commit.txt"
sha256sum "$build/liblqcd_cpu.so" "$build/verify_slab" > "$out/build.sha256"
scratch=/tmp/lqcd-C64-$(basename "$out")
mpirun -n 32 --oversubscribe --map-by ppr:16:node --bind-to none \
  python tools/multinode/rank_exec.py python -u benchmarks/runtime/benchmark_multinode.py \
  --gauge "$gauge" --library "$build/liblqcd_cpu.so" --output "$out/measurements" --scratch "$scratch"
mpirun -n 32 --oversubscribe --map-by ppr:16:node --bind-to none \
  python tools/multinode/rank_exec.py "$build/verify_slab" "$scratch" 64 128 -.2334 1.140825606017 1e-8 0 13 \
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
