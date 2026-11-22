"""Run the H20 three-level wall-source benchmark using one GPU."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "gpu", nargs="?", default=os.environ.get("CUDA_VISIBLE_DEVICES") or "0",
        help="physical GPU index (default: CUDA_VISIBLE_DEVICES or 0)",
    )
    gpu = parser.parse_args().gpu
    if not gpu.isascii() or not gpu.isdecimal():
        parser.error("specify exactly one GPU index, for example: python test.py 2")

    work = Path.home() / ".cache/quda-wall-20261122"
    variant = work / "h20-pure-mg"
    library = variant / "quda-install/lib/libquda.so"
    benchmark = work / "driver-pure-mg/experiments/h20-quda-wall-20261122/benchmark.py"
    gauge = work / "verified-inputs/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
    for path in (library, benchmark, gauge):
        if not path.is_file():
            parser.error(f"required file missing on h20: {path}")

    check = subprocess.run(
        ["nvidia-smi", f"--id={gpu}", "--query-compute-apps=pid", "--format=csv,noheader"],
        capture_output=True, text=True,
    )
    if check.returncode:
        parser.error(check.stderr.strip() or check.stdout.strip() or f"GPU {gpu} is unavailable")
    if check.stdout.strip():
        parser.error(f"GPU {gpu} is busy; choose another GPU")

    results = variant / "test-runs"
    results.mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="wall-", dir=results))
    output = run / "result.json"
    existing_cache = variant / "run/quda-cache/tunecache.tsv"
    if existing_cache.is_file():
        cache = run / "quda-cache"
        cache.mkdir()
        shutil.copyfile(existing_cache, cache / existing_cache.name)

    env = os.environ.copy()
    preload = env.get("LD_PRELOAD")
    env.update(
        CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=gpu,
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
        LD_PRELOAD=f"{library}:{preload}" if preload else str(library),
    )
    print(f"GPU {gpu} | 24³×64 | 1 and 12 RHS | result: {output}", flush=True)
    os.execve(sys.executable, [
        sys.executable, "-u", str(benchmark), str(gauge), str(output),
        "--compute-only", "--solve-tol", "1e-8", "--mg-profile", "ensemble",
    ], env)


if __name__ == "__main__":
    main()
