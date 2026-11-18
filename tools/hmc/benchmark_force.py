"""Compare two reference implementations on identical fields and momenta."""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.reference import CloverHMC, RD


def benchmark(first, second, momenta, gauge, repeats):
    errors = {}
    for mass in (first.ml, first.ms):
        old = first.dirac(gauge, mass)
        new = second.dirac(gauge, mass)
        torch.testing.assert_close(new, old, atol=2e-14, rtol=2e-14)
        errors[f"dirac_{mass}"] = float((new - old).abs().max())
    old_force, new_force = first.force(gauge), second.force(gauge)
    torch.testing.assert_close(new_force, old_force, atol=2e-12, rtol=2e-12)
    errors["force"] = float((new_force - old_force).abs().max())
    old_links, old_p = first.integrate(gauge, momenta, 0.2, 4)
    new_links, new_p = second.integrate(gauge, momenta, 0.2, 4)
    torch.testing.assert_close(new_links, old_links, atol=2e-12, rtol=2e-12)
    torch.testing.assert_close(new_p, old_p, atol=2e-12, rtol=2e-12)
    errors["links_after_md"] = float((new_links - old_links).abs().max())
    errors["momenta_after_md"] = float((new_p - old_p).abs().max())
    timings = {"baseline": [], "candidate": []}
    models = (("baseline", first), ("candidate", second))
    for trial in range(repeats):
        for label, model in (models if trial % 2 == 0 else reversed(models)):
            start = perf_counter()
            model.integrate(gauge, momenta, 0.2, 4)
            timings[label].append(perf_counter() - start)
    medians = {label: statistics.median(values) for label, values in timings.items()}
    return dict(max_errors=errors, md_samples_seconds=timings, md_median_seconds=medians,
                speedup=medians["baseline"] / medians["candidate"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    if args.repeats < 1 or args.threads < 1:
        parser.error("Positive thread and repeat counts required")
    spec = importlib.util.spec_from_file_location("baseline_reference", args.baseline)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    torch.set_num_threads(args.threads)
    rng = torch.Generator().manual_seed(1729)
    results = []
    for lattice in ((2, 2, 2, 2), (2, 2, 2, 4)):
        first, second = baseline.CloverHMC(lattice), CloverHMC(lattice)
        p = torch.randn((first.volume, 4, 8), dtype=RD, generator=rng)
        gauge = first.drift(first.cold(), p, 0.2)
        results.append(dict(lattice=lattice, **benchmark(first, second, p, gauge, args.repeats)))
    print(json.dumps(dict(torch=torch.__version__, threads=args.threads, results=results), indent=2))


if __name__ == "__main__":
    main()
