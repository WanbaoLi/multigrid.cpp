"""Compare integration cost and energy error on identical saved fields and momenta."""
import argparse
import json
import math
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import numpy as np
from mpi4py import MPI
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "bindings")]
from hmc.reference import CloverHMC, RD
from lqcd_cpu.io import read_lime_gauge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chain", type=Path)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.threads < 1 or args.repeats < 1:
        parser.error("Positive thread and repeat counts required")
    chain = json.loads((args.chain / "result.json").read_text())
    if not chain["complete"] or not chain["saved_configurations"]:
        raise ValueError("The input chain must contain saved configurations")
    torch.set_num_threads(args.threads)
    model = CloverHMC(chain["lattice_xyzt"], chain["beta"], chain["mass_light"],
                      chain["mass_strange"], chain["csw"])
    length = chain["trajectory_length"]
    rng = torch.Generator().manual_seed(1829)
    cases = (("leapfrog", 10), ("omelyan", 5), ("omelyan", 3))
    samples = {f"{name}-{steps}": [] for name, steps in cases}
    for config in chain["saved_configurations"]:
        path = args.chain / config["file"]
        array = read_lime_gauge(path, comm=MPI.COMM_SELF)
        gauge = torch.from_numpy(np.ascontiguousarray(array).reshape(model.volume, 4, 3, 3))
        momenta_shape = (model.volume, 4, 8)
        for trial in range(args.repeats):
            p = torch.randn(momenta_shape, dtype=RD, generator=rng)
            h0 = model.hamiltonian(gauge, p)
            # Rotate the measurement order across cases to distribute warm-up and drift.
            start_case = (trial + config["trajectory"] // 10) % len(cases)
            for name, steps in cases[start_case:] + cases[:start_case]:
                started = perf_counter()
                links, momentum = model.integrate(gauge, p, length, steps, name)
                delta_h = model.hamiltonian(links, momentum) - h0
                elapsed = perf_counter() - started
                samples[f"{name}-{steps}"].append(dict(file=path.name, trial=trial,
                    delta_h=delta_h, seconds=elapsed))
    results = {}
    for name, steps in cases:
        rows = samples[f"{name}-{steps}"]
        rms_energy = math.sqrt(sum(row["delta_h"] ** 2 for row in rows) / len(rows))
        metropolis = sum(math.exp(min(0, -row["delta_h"])) for row in rows) / len(rows)
        results[f"{name}-{steps}"] = dict(force_evaluations=(1 if name == "leapfrog" else 2) * steps + 1,
            rms_delta_h=rms_energy, mean_acceptance_probability=metropolis,
            median_seconds=median(row["seconds"] for row in rows), samples=rows)
    print(json.dumps(dict(lattice=chain["lattice_xyzt"], trajectory_length=length,
                          threads=args.threads, results=results), allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
