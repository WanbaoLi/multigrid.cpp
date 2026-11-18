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
    args = parser.parse_args()
    torch.set_num_threads(1)
    comm = MPI.COMM_WORLD.Dup()
    try:
        lattice = (2, 2, 2, comm.size)
        params = (lattice, 5.6, .5, .8, 1.)
        model = DistributedRHMC(*params, comm, os.environ["LQCD_HMC_SCHUR_LIBRARY"],
                                direct_clover=args.direct_clover, packed_faces=args.packed_faces)
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
        refresh_error = max(float((a - e[half]).abs().max()) for a, e in zip(actual, expected))
        hamiltonian = model.endpoint_energy(local_u, local_p, actual)
        endpoint_error = abs(hamiltonian - dense.endpoint_energy(u, p, tuple(x.flatten() for x in expected)))
        force = model.force(local_u, actual)
        split_force = model.force(local_u, actual, include_gauge=False) + model.gauge_force(local_u)
        serial_force = comm.bcast(serial.md_force(u, expected).numpy() if comm.rank == 0 else None, root=0)
        force_error = float((force - torch.from_numpy(serial_force[slab])).abs().max())
        up, pp = model.integrate(local_u, local_p, actual, .04, 1)
        ub, pb = model.integrate(up, -pp, actual, .04, 1)
        split_u, split_p = model.integrate(local_u, local_p, actual, .04, 1, gauge_steps=2)
        split_back_u, split_back_p = model.integrate(split_u, -split_p, actual, .04, 1, gauge_steps=2)
        errors = dict(refresh=refresh_error, endpoint=endpoint_error, force=force_error,
                      split_force=float((split_force - force).abs().max()),
                      split_reversible_links=float((split_back_u - local_u).abs().max()),
                      split_reversible_momenta=float((split_back_p + local_p).abs().max()),
                      reversible_links=float((ub - local_u).abs().max()),
                      reversible_momenta=float((pb + local_p).abs().max()))
        errors = {key: comm.allreduce(value, op=MPI.MAX) for key, value in errors.items()}
        limits = dict(refresh=2e-11, endpoint=1e-9, force=3e-9,
                      reversible_links=2e-12, reversible_momenta=2e-11,
                      split_force=2e-12, split_reversible_links=2e-12, split_reversible_momenta=2e-11)
        if any(errors[key] > tolerance for key, tolerance in limits.items()):
            raise AssertionError(errors)
        if comm.rank == 0:
            args.output.write_text(json.dumps(dict(passed=True, ranks=comm.size, lattice=lattice,
                                                   max_error=errors), indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
