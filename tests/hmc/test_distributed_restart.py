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
                        save_every=1, direct_clover=False, packed_faces=False, compact_spin=False, zolotarev=False,
                        force_pole_batch=8, projected_force_faces=False, initial_lime=None,
                        light_heatbath_action=False, real_krylov_dot=False, pade_drift=False,
                        shared_clover_spin=False, native_pade_drift=False, reuse_odd_inverse=False,
                        overlap_schur_faces=False, gershgorin_strange=False, fused_schur_gamma5=False,
                        compress_refresh=False,
                        library=Path(os.environ["LQCD_HMC_SCHUR_LIBRARY"]))
        whole = run(SimpleNamespace(**settings, output=args.output / "whole",
                                    trajectories=3, resume_from=None), comm)
        head = run(SimpleNamespace(**settings, output=args.output / "head",
                                   trajectories=1, resume_from=None), comm)
        checkpoint = args.output / "head" / "result.json"
        tail = run(SimpleNamespace(**settings, output=args.output / "tail",
                                   trajectories=2, resume_from=checkpoint), comm)
        assert tail["resumed_from"]["trajectory"] == 1
        field_path = args.output / "head" / head["saved_configurations"][0]["file"]
        initial_settings = dict(settings, initial_lime=field_path, seed=9831)
        new_chain = run(SimpleNamespace(**initial_settings, output=args.output / "initial-lime",
                                        trajectories=1, resume_from=None), comm)
        assert new_chain["initial_lime"]["sha256"] == head["saved_configurations"][0]["sha256"]
        assert new_chain["samples"][0]["trajectory"] == 1 and new_chain["seed"] == 9831
        mismatch = dict(initial_settings, lattice=(4, 2, 2, 2 * comm.size))
        try:
            run(SimpleNamespace(**mismatch, output=args.output / "invalid-lime",
                                trajectories=1, resume_from=None), comm)
        except RuntimeError as error:
            assert "Initial LIME lattice dimensions differ" in str(error)
        else:
            raise AssertionError("An initial LIME file with different lattice dimensions was accepted")
        saved = head["saved_configurations"] + tail["saved_configurations"]
        assert len(whole["saved_configurations"]) == len(saved) == 3
        for left, right in zip(whole["saved_configurations"], saved):
            assert left["trajectory"] == right["trajectory"]
            assert left["sha256"] == right["sha256"]
            assert left["rng_state"]["sha256"] == right["rng_state"]["sha256"]
        samples = head["samples"] + tail["samples"]
        assert len(whole["samples"]) == len(samples) == 3
        for left, right in zip(whole["samples"], samples):
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
                initial_lime_starts_new_chain=True,
                invalid_parameters_rejected=True), indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
