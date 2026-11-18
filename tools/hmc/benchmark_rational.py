"""Pair timings for the reference and shared-Krylov strange action and force."""
import argparse
import importlib.util
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.pseudofermion import PseudofermionHMC
from hmc.rational import rational_action_gradient
from hmc.reference import RD


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.threads < 1 or args.repeats < 1:
        parser.error("Positive thread and repeat counts required")
    spec = importlib.util.spec_from_file_location("hmc.baseline_rational", args.baseline)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    torch.set_num_threads(args.threads)
    rng = torch.Generator().manual_seed(1729)
    model = PseudofermionHMC()
    p = torch.randn((model.volume, 4, 8), dtype=RD, generator=rng)
    gauge = model.drift(model.cold(), p, 0.2)
    _, phi = model.refresh(gauge, rng)
    parameters = (model, gauge, model.ms, phi, model.strange_terms)
    old = baseline.rational_action_gradient(*parameters)
    new = rational_action_gradient(*parameters)
    if abs(old[0] - new[0]) > 1e-10:
        raise ArithmeticError("Strange actions disagree")
    torch.testing.assert_close(old[1], new[1], atol=1e-10, rtol=1e-10)
    cases = (("independent", baseline.rational_action_gradient),
             ("shared", rational_action_gradient))
    samples = {label: [] for label, _ in cases}
    for trial in range(args.repeats):
        for label, run in (cases if trial % 2 == 0 else reversed(cases)):
            start = perf_counter()
            run(*parameters)
            samples[label].append(perf_counter() - start)
    medians = {label: median(values) for label, values in samples.items()}
    print(json.dumps(dict(lattice=model.lattice, poles=len(model.strange_terms),
        threads=args.threads, samples_seconds=samples, median_seconds=medians,
        speedup=medians["independent"] / medians["shared"],
        action_absolute_difference=abs(old[0] - new[0]),
        link_gradient_max_difference=(old[1] - new[1]).abs().max().item()), indent=2))


if __name__ == "__main__":
    main()
