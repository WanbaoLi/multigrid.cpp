"""Check full distributed refresh, force, Metropolis energy and reversibility."""
import argparse
import json
import os
from pathlib import Path
import sys

from mpi4py import MPI
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.distributed_rhmc import DistributedRHMC
from hmc.pseudofermion import MatrixFreePseudofermionHMC, PseudofermionHMC
from hmc.reference import CD, RD


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--direct-clover", action="store_true")
    parser.add_argument("--packed-faces", action="store_true")
    parser.add_argument("--compact-spin", action="store_true")
    parser.add_argument("--zolotarev", action="store_true")
    parser.add_argument("--projected-force-faces", action="store_true")
    parser.add_argument("--light-heatbath-action", action="store_true")
    parser.add_argument("--real-krylov-dot", action="store_true")
    parser.add_argument("--pade-drift", action="store_true")
    parser.add_argument("--shared-clover-spin", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(1)
    comm = MPI.COMM_WORLD.Dup()
    try:
        lattice = (2, 2, 2, comm.size)
        params = (lattice, 5.6, .5, .8, 1.)
        model = DistributedRHMC(*params, comm, os.environ["LQCD_HMC_SCHUR_LIBRARY"],
                                direct_clover=args.direct_clover, packed_faces=args.packed_faces,
                                compact_spin=args.compact_spin, zolotarev=args.zolotarev,
                                projected_force_faces=args.projected_force_faces,
                                light_heatbath_action=args.light_heatbath_action, real_krylov_dot=args.real_krylov_dot,
                                pade_drift=args.pade_drift, shared_clover_spin=args.shared_clover_spin)
        baseline, final, precise_difference = model._hamiltonian_pair([2.**56, 2.], [2.**56, 3.])
        assert final == baseline and precise_difference == comm.size
        serial = MatrixFreePseudofermionHMC(*params)
        dense = PseudofermionHMC(*params)
        rng = torch.Generator().manual_seed(1729)
        p = torch.randn((serial.volume, 4, 8), dtype=RD, generator=rng)
        u = serial.drift(serial.cold(), p, 0.13)
        sites = model.local_volume
        slab = slice(sites * comm.rank, sites * (comm.rank + 1))
        half = slice(slab.start // 2, slab.stop // 2)
        local_u, local_p = u[slab].contiguous(), p[slab].contiguous()
        seed = 2354
        expected = serial.refresh(u, torch.Generator().manual_seed(seed))
        noise_rng = torch.Generator().manual_seed(seed)
        noise = [torch.randn(field.shape, dtype=CD, generator=noise_rng)[half] for field in expected]
        actual = model.refresh(local_u, *noise)
        reused_fields, reused_terms, _ = model._heatbath_and_initial_terms(local_u, local_p, noise)
        assert all(torch.equal(a, b) for a, b in zip(actual, reused_fields))
        explicit_terms = model._local_endpoint_terms(local_u, local_p, actual)
        heatbath_error = 0.
        if args.light_heatbath_action:
            local_clover = model._coefficients(model._gauge_faces(local_u))[0]
            assert reused_terms[2] == model._light_noise_action(local_u, local_clover, noise[0])
            assert model._light_noise_action(local_u, torch.zeros_like(local_clover), noise[0]) is None
            assert reused_terms[:2] == explicit_terms[:2] and reused_terms[3:] == explicit_terms[3:]
            heatbath_error = abs(comm.allreduce(reused_terms[2] - explicit_terms[2]))
        else:
            assert reused_terms == explicit_terms
        refresh_error = max(float((a - e[half]).abs().max()) for a, e in zip(actual, expected))
        hamiltonian = model.endpoint_energy(local_u, local_p, actual)
        dense_fields = tuple(x.flatten() for x in expected)
        dense_initial = dense.endpoint_energy(u, p, dense_fields)
        endpoint_error = abs(hamiltonian - dense_initial)
        force = model.force(local_u, actual)
        split_force = model.force(local_u, actual, include_gauge=False) + model.gauge_force(local_u)
        serial_force = comm.bcast(serial.md_force(u, expected).numpy() if comm.rank == 0 else None, root=0)
        force_error = float((force - torch.from_numpy(serial_force[slab])).abs().max())
        up, pp = model.integrate(local_u, local_p, actual, .04, 1)
        _, _, measured_delta = model._hamiltonian_pair(
            reused_terms, model._local_endpoint_terms(up, pp, actual))
        dense_final = dense.endpoint_energy(torch.cat(comm.allgather(up)), torch.cat(comm.allgather(pp)),
                                            dense_fields)
        ub, pb = model.integrate(up, -pp, actual, .04, 1)
        split_u, split_p = model.integrate(local_u, local_p, actual, .04, 1, gauge_steps=2)
        split_back_u, split_back_p = model.integrate(split_u, -split_p, actual, .04, 1, gauge_steps=2)
        errors = dict(refresh=refresh_error, endpoint=endpoint_error, force=force_error,
                      delta_h=abs(measured_delta - (dense_final - dense_initial)),
                      light_heatbath_action=heatbath_error,
                      split_force=float((split_force - force).abs().max()),
                      split_reversible_links=float((split_back_u - local_u).abs().max()),
                      split_reversible_momenta=float((split_back_p + local_p).abs().max()),
                      reversible_links=float((ub - local_u).abs().max()),
                      reversible_momenta=float((pb + local_p).abs().max()))
        errors = {key: comm.allreduce(value, op=MPI.MAX) for key, value in errors.items()}
        limits = dict(refresh=2e-11, endpoint=1e-9, force=3e-9, delta_h=1e-9, light_heatbath_action=1e-9,
                      reversible_links=2e-12, reversible_momenta=2e-11,
                      split_force=2e-12, split_reversible_links=2e-12, split_reversible_momenta=2e-11)
        if any(errors[key] > tolerance for key, tolerance in limits.items()):
            raise AssertionError(errors)
        if comm.rank == 0:
            args.output.write_text(json.dumps(dict(passed=True, ranks=comm.size, lattice=lattice,
                                                   extensive_difference_check=precise_difference,
                                                   identical_heatbath_fields=True,
                                                   identical_initial_terms=not args.light_heatbath_action,
                                                   max_error=errors), indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
