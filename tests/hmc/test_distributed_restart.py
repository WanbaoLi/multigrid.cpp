"""Check that an MPI run resumed from LIME continues the same Markov chain."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from mpi4py import MPI
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "hmc"))
from generate_mpi import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    comm = MPI.COMM_WORLD.Dup()
    try:
        settings = dict(lattice=(2, 2, 2, 2 * comm.size), beta=5.6, mass_light=.5, mass_strange=.8,
                        csw=1., strange_interval=(.004, 4.), md_order=16, md_tolerance=1e-12,
                        length=.025, steps=1, gauge_steps=2, threads=1, seed=1729, warmup=0,
                        save_every=1, direct_clover=False, packed_faces=False,
                        library=Path(os.environ["LQCD_HMC_SCHUR_LIBRARY"]))
        whole = run(SimpleNamespace(**settings, output=args.output / "whole",
                                    trajectories=3, resume_from=None), comm)
        head = run(SimpleNamespace(**settings, output=args.output / "head",
                                   trajectories=1, resume_from=None), comm)
        checkpoint = args.output / "head" / "result.json"
        tail = run(SimpleNamespace(**settings, output=args.output / "tail",
                                   trajectories=2, resume_from=checkpoint), comm)
        for left, right in zip(whole["saved_configurations"],
                               head["saved_configurations"] + tail["saved_configurations"]):
            assert left["trajectory"] == right["trajectory"]
            assert left["sha256"] == right["sha256"]
            assert left["rng_state"]["sha256"] == right["rng_state"]["sha256"]
        for left, right in zip(whole["samples"], head["samples"] + tail["samples"]):
            for key in ("accepted", "h_initial", "h_final", "delta_h", "plaquette"):
                assert left[key] == right[key], key
        invalid = dict(settings, mass_strange=1.0)
        try:
            run(SimpleNamespace(**invalid, output=args.output / "invalid",
                                trajectories=2, resume_from=checkpoint), comm)
        except RuntimeError as error:
            assert "Checkpoint parameters differ: mass_strange" in str(error)
        else:
            raise AssertionError("Incompatible checkpoint parameters were accepted")
        if comm.rank == 0:
            (args.output / "restart-verification.json").write_text(json.dumps(dict(
                passed=True, ranks=comm.size, checkpoint=tail["resumed_from"],
                matched_trajectories=3, matched_lime_and_rng_digests=True,
                invalid_parameters_rejected=True), indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
