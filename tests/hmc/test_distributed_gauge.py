"""Check link halo adjoints and distributed plaquette and Clover derivatives."""
import argparse
import json
from pathlib import Path
import sys

from mpi4py import MPI
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.distributed_gauge import owned_clover_strength, owned_gauge_action, time_faces
from hmc.reference import CD, RD, CloverHMC


def compare(comm, lattice):
    model = CloverHMC(lattice, dense_reference=False)
    rng = torch.Generator().manual_seed(15269)
    p = torch.randn((model.volume, 4, 8), dtype=RD, generator=rng)
    full = model.drift(model.cold(), p, 0.3).requires_grad_(True)
    nt = lattice[3] // comm.size
    ti = slice(comm.rank * nt, (comm.rank + 1) * nt)
    local = full.reshape(*reversed(lattice), 4, 3, 3)[ti].detach().clone().requires_grad_(True)
    extended = time_faces(local, comm)
    action = owned_gauge_action(extended, model.beta)
    local_strength = owned_clover_strength(extended)
    whole_strength = model.field_strength(full)
    whole_action = model.gauge_action(full)
    probes = [torch.randn(v.shape, dtype=CD, generator=rng) for v in whole_strength]
    site_shape = tuple(reversed(lattice)) + (3, 3)
    local_probe = [p.reshape(site_shape)[ti] for p in probes]
    strength_error = max(float((a - b.reshape(site_shape)[ti]).abs().max())
                         for a, b in zip(local_strength, whole_strength))
    action_error = abs(comm.allreduce(float(action.detach())) - float(whole_action.detach()))
    local_loss = action + sum((p.conj() * f).real.sum() for p, f in zip(local_probe, local_strength))
    whole_loss = whole_action + sum((p.conj() * f).real.sum() for p, f in zip(probes, whole_strength))
    local_grad, = torch.autograd.grad(local_loss, local)
    whole_grad, = torch.autograd.grad(whole_loss, full)
    grad_error = float((local_grad - whole_grad.reshape(*reversed(lattice), 4, 3, 3)[ti]).abs().max())
    strength_error = comm.allreduce(strength_error, op=MPI.MAX)
    grad_error = comm.allreduce(grad_error, op=MPI.MAX)
    if action_error > 1e-10 or strength_error > 3e-14 or grad_error > 5e-14:
        raise AssertionError((lattice, action_error, strength_error, grad_error))
    return dict(lattice=lattice, gauge_action_error=action_error,
                field_strength_error=strength_error, link_gradient_error=grad_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    comm = MPI.COMM_WORLD.Dup()
    try:
        results = [compare(comm, lattice) for lattice in
                   ((2, 4, 2, comm.size), (4, 4, 4, 2 * comm.size))]
        if comm.rank == 0:
            args.output.write_text(json.dumps(dict(ranks=comm.size, cases=results, passed=True),
                                              indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
