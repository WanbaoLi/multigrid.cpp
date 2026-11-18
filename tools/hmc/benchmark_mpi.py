"""Pair distributed RHMC trajectories on one independently verified LIME checkpoint."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
from time import perf_counter

from mpi4py import MPI
import torch

from generate_mpi import ROOT, initial_gauge, on_root
from generate import atomic_json
from hmc.distributed_rhmc import DistributedRHMC
from hmc.reference import lime_sha256


OPTIMIZATIONS = {
    "overlap-schur-faces": "overlap_schur_faces",
    "fused-schur-gamma5": "fused_schur_gamma5",
    "compress-refresh": "compress_refresh",
    "native-pade": "native_pade",
    "md-tolerance": "md_tolerance",
    "native-library": None,
}


class TimedRHMC(DistributedRHMC):
    def integrate(self, *args, **kwargs):
        self.proposal, self.momentum = super().integrate(*args, **kwargs)
        return self.proposal, self.momentum

    def drift(self, *args):
        started = perf_counter()
        result = super().drift(*args)
        self.drift_seconds += perf_counter() - started
        return result


def checkpoint(chain, trajectory):
    report = json.loads((chain / "result.json").read_text())
    verification = json.loads((chain / "verification.json").read_text())
    if not report["complete"] or not verification["passed"]:
        raise ValueError("A complete independently verified RHMC chain is required")
    candidates = [row for row in report["saved_configurations"]
                  if trajectory is None or row["trajectory"] == trajectory]
    if not candidates:
        raise ValueError("The requested checkpoint was not saved")
    item = candidates[-1]
    name = item["file"]
    if Path(name).name != name or not name.endswith(".lime"):
        raise ValueError("Invalid checkpoint filename")
    if not any(row["file"] == name and row["sha256"] == item["sha256"] and row["scidac_crc_passed"]
               for row in verification["configurations"]):
        raise ValueError("The selected checkpoint has no matching independent readback")
    return report, item


def pair(args, comm):
    on_root(comm, lambda: args.output.open("x").close())
    chain, item = on_root(comm, lambda: checkpoint(args.chain, args.trajectory))
    gauge, source = initial_gauge(args.chain / item["file"], chain["lattice_xyzt"], comm)
    if source["sha256"] != item["sha256"]:
        raise ValueError("Checkpoint SHA256 differs from the verified result")
    commit = on_root(comm, lambda: subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip())
    torch.set_num_threads(args.threads)
    placement = comm.gather(dict(host=socket.gethostname(), cpus=sorted(os.sched_getaffinity(0))), root=0)

    settings = dict(interval=tuple(chain["strange_md_interval"]), md_order=args.md_order,
                    packed_faces=True, direct_clover=True, compact_spin=True, zolotarev=True,
                    projected_force_faces=True, force_pole_batch=11, real_krylov_dot=True,
                    light_heatbath_action=True, reuse_odd_inverse=True, gershgorin_strange=True,
                    native_pade=True, fused_schur_gamma5=True,
                    overlap_schur_faces=False, compress_refresh=False)
    flag = OPTIMIZATIONS[args.optimization]
    if flag is None:
        specifications = dict(control=settings, candidate=settings.copy())
    else:
        tolerance_pair = args.optimization == "md-tolerance"
        settings[flag] = 1e-12 if tolerance_pair else False
        candidate_value = args.candidate_md_tolerance if tolerance_pair else True
        specifications = dict(control=settings, candidate={**settings, flag: candidate_value})
    libraries = dict(control=args.library, candidate=args.candidate_library or args.library)
    models = {key: TimedRHMC(chain["lattice_xyzt"], chain["beta"], chain["mass_light"],
                             chain["mass_strange"], chain["csw"], comm, libraries[key], **settings)
              for key, settings in specifications.items()}
    rational_digests = {key: hashlib.sha256(json.dumps(
        (model.md_terms, model.endpoint_terms, model.refresh_terms)).encode()).hexdigest()
        for key, model in models.items()}
    if any(digests != rational_digests for digests in comm.allgather(rational_digests)):
        raise RuntimeError("Benchmark coefficients differ across MPI ranks")
    if args.optimization == "compress-refresh" and len(models["candidate"].refresh_terms) >= len(models["control"].refresh_terms):
        raise ArithmeticError("The selected interval did not yield a compressed heatbath")
    limits = dict(links=2e-12, momenta=2e-11, delta_h=2e-8)
    report = dict(complete=False, gauge=source, trajectory=item["trajectory"], ranks=comm.size,
                  threads=args.threads, placement=placement, optimization=args.optimization,
                  settings=specifications, rational_sha256=rational_digests,
                  source_commit=commit, torch_version=str(torch.__version__),
                  native_schur_sha256=on_root(comm, lambda: lime_sha256(args.library)),
                  candidate_native_schur_sha256=on_root(comm, lambda: lime_sha256(libraries["candidate"])),
                  length=args.length, steps=args.steps, gauge_steps=args.gauge_steps,
                  lattice_xyzt=chain["lattice_xyzt"], beta=chain["beta"], csw=chain["csw"],
                  mass_light=chain["mass_light"], mass_strange=chain["mass_strange"],
                  seed=args.seed, repeats=args.repeats, proposal_limits=limits, samples=[])
    on_root(comm, lambda: atomic_json(args.output, report))

    for trial in range(args.repeats):
        timings = {}
        order = tuple(models) if trial % 2 == 0 else tuple(reversed(models))
        for name in order:
            model = models[name]
            model.drift_seconds = 0.
            rng = torch.Generator().manual_seed(args.seed + 997 * trial + comm.rank)
            comm.Barrier()
            started = perf_counter()
            _, sample = model.trajectory(gauge, rng, args.length, args.steps, gauge_steps=args.gauge_steps)
            sample["seconds"] = comm.allreduce(perf_counter() - started, op=MPI.MAX)
            sample["drift_seconds"] = comm.allreduce(model.drift_seconds, op=MPI.MAX)
            for section in ("phase_seconds", "force_seconds"):
                sample[section] = {key: comm.allreduce(value, op=MPI.MAX)
                                   for key, value in sample[section].items()}
            timings[name] = sample
        baseline, candidate = models["control"], models["candidate"]

        def difference(left, right):
            return comm.allreduce(float((left - right).abs().max()), op=MPI.MAX)

        errors = dict(links=difference(baseline.proposal, candidate.proposal),
                      momenta=difference(baseline.momentum, candidate.momentum),
                      delta_h=abs(timings["control"]["delta_h"] - timings["candidate"]["delta_h"]))
        passed = (timings["control"]["accepted"] == timings["candidate"]["accepted"]
                  and all(0 <= errors[key] <= limit for key, limit in limits.items()))
        report["samples"].append(dict(trial=trial, order=order, maximum_error=errors,
                                      passed=passed, **timings))
        report["complete"] = passed and len(report["samples"]) == args.repeats
        on_root(comm, lambda: atomic_json(args.output, report))
        if not passed:
            raise ArithmeticError(f"Matched proposals failed agreement checks: {errors}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chain", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--candidate-library", type=Path)
    parser.add_argument("--optimization", choices=OPTIMIZATIONS, required=True)
    parser.add_argument("--trajectory", type=int)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--length", type=float, default=.018)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--gauge-steps", type=int, default=2)
    parser.add_argument("--md-order", type=int, default=16)
    parser.add_argument("--candidate-md-tolerance", type=float, default=1e-10)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    if (min(args.repeats, args.threads, args.steps, args.md_order) < 1 or args.gauge_steps < 0
            or not math.isfinite(args.length) or args.length <= 0 or args.seed < 0):
        parser.error("Invalid trajectory or benchmark parameters")
    if args.optimization == "md-tolerance" and not 0 < args.candidate_md_tolerance < 1:
        parser.error("The candidate MD relative tolerance must be between zero and one")
    if (args.candidate_library is not None) != (args.optimization == "native-library"):
        parser.error("--candidate-library is required with --optimization native-library")
    pair(args, MPI.COMM_WORLD)


if __name__ == "__main__":
    main()
