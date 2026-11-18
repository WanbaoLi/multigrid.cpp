"""Pair native and Torch normal-operator timings on identical gauge fields."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter
from unittest.mock import patch

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.reference import CD, RD, CloverHMC


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--applications", type=int, default=24)
    args = parser.parse_args()
    if args.applications < 1 or args.threads < 1:
        parser.error("Positive thread and application counts required")
    torch.set_num_threads(args.threads)
    rng = torch.Generator().manual_seed(1729)
    results = []
    with torch.no_grad():
        for extent in (4, 8):
            model = CloverHMC((extent,) * 4, dense_reference=False)
            p = torch.randn((model.volume, 4, 8), dtype=RD, generator=rng)
            gauge = model.drift(model.cold(), p, 0.2)
            clover = model.clover_blocks(model.field_strength(gauge), model.ms)
            x = torch.randn((model.volume // 2, 4, 3), dtype=CD, generator=rng)
            ops = {}
            lib = str(args.library.resolve())
            for name, path, split in (("torch", "", "0"), ("split_native", lib, "1"), ("native", lib, "0")):
                with patch.dict(os.environ, {"LQCD_HMC_SCHUR_LIBRARY": path,
                                             "LQCD_HMC_SPLIT_NORMAL": split}):
                    ops[name] = model.prepare_even_schur(gauge, model.ms, clover)
            baseline = model.even_normal_from_schur(ops["torch"], x)
            actual = model.even_normal_from_schur(ops["native"], x)
            torch.testing.assert_close(actual, baseline, rtol=3e-14, atol=3e-14)
            torch.testing.assert_close(model.even_normal_from_schur(ops["split_native"], x),
                                       baseline, rtol=3e-14, atol=3e-14)
            times = {name: [] for name in ops}
            for repeat in range(4):
                for name in (ops if repeat % 2 == 0 else reversed(ops)):
                    start = perf_counter()
                    for _ in range(args.applications):
                        model.even_normal_from_schur(ops[name], x)
                    times[name].append((perf_counter() - start) / args.applications)
            medians = {name: statistics.median(values) for name, values in times.items()}
            results.append(dict(lattice=model.lattice, seconds=times, median_seconds=medians,
                speedup=medians["torch"] / medians["native"],
                fusion_speedup=medians["split_native"] / medians["native"],
                max_absolute_error=(actual - baseline).abs().max().item()))
    print(json.dumps(dict(threads=args.threads, applications_per_sample=args.applications,
                          torch=torch.__version__, results=results), indent=2))


if __name__ == "__main__":
    main()
