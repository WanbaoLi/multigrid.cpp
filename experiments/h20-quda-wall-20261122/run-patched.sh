#!/usr/bin/env bash
set -euo pipefail

driver=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
work=$(realpath "${1:?pass the original H20 benchmark directory}")
variant="$work/h20-product-precision"
patch="$driver/quda-h20-af7e150.patch"
base=af7e15080e247795ef076b6d9284478755a9a683
python="${CONDA_ROOT:-"$HOME/miniconda3"}/envs/pyquda/bin/python"

mkdir -p "$variant"
source_dir="$variant/quda-src"
if [[ ! -d "$source_dir/.git" ]]; then
    git clone --no-hardlinks "$work/quda-src" "$source_dir"
fi
test "$(git -C "$source_dir" rev-parse HEAD)" = "$base"
if ! git -C "$source_dir" apply --reverse --check "$patch"; then
    test -z "$(git -C "$source_dir" status --porcelain)"
    git -C "$source_dir" apply --check "$patch"
    git -C "$source_dir" apply "$patch"
fi
git -C "$source_dir" diff --check
sha256sum "$patch"

export QUDA_SOURCE_DIR="$source_dir"
export QUDA_BUILD_DIR="$variant/quda-build"
export QUDA_INSTALL_DIR="$variant/quda-install"
export QUDA_ONLY=1
bash "$driver/build.sh" "$work"

export LD_LIBRARY_PATH="$QUDA_INSTALL_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
expected="$QUDA_INSTALL_DIR/lib/libquda.so"
# The existing PyQUDA extension embeds the baseline path in DT_RPATH.
export LD_PRELOAD="$expected${LD_PRELOAD:+:$LD_PRELOAD}"
"$python" - "$expected" <<'PY'
from pathlib import Path
import sys
from pyquda import quda

expected = Path(sys.argv[1]).resolve()
mapped = {
    Path(line.split()[-1]).resolve()
    for line in Path("/proc/self/maps").read_text().splitlines()
    if "libquda.so" in line and line.split()[-1].startswith("/")
}
if mapped != {expected}:
    raise RuntimeError(f"Expected {expected}, loaded {mapped}")
print(f"Loaded QUDA library {expected}", flush=True)
PY

export CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
nvidia-smi --id=0 --query-gpu=name,memory.used,utilization.gpu --format=csv
gauge="$work/verified-inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
printf '%s  %s\n' f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326 "$gauge" | sha256sum -c
"$python" -u "$driver/benchmark.py" "$gauge" "$variant/run/result.json"
