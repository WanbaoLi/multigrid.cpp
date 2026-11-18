"""Compare native MPI Schur phases with the full-volume Torch stencil."""
import argparse
import json
import os
from pathlib import Path
import sys

from mpi4py import MPI
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.distributed_schur import prepare_slab_schur
from hmc.reference import CloverHMC, CD, RD
from hmc.shifted import solve_multi_shift, solve_shifted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    library = os.environ["LQCD_HMC_SCHUR_LIBRARY"]
    comm = MPI.COMM_WORLD.Dup()
    results = []
    try:
        for lattice in ((2, 4, 2, comm.size), (4, 4, 4, 2 * comm.size)):
            model = CloverHMC(lattice, dense_reference=False)
            rng = torch.Generator().manual_seed(7933)
            momentum = torch.randn((model.volume, 4, 8), dtype=RD, generator=rng)
            gauge = model.drift(model.cold(), momentum, 0.25)
            strength = model.field_strength(gauge)
            field = torch.randn((model.volume // 2, 4, 3), dtype=CD, generator=rng)
            owned = field.shape[0] // comm.size
            slab = slice(owned * comm.rank, owned * (comm.rank + 1))
            for mass in (model.ml, model.ms):
                clover = model.clover(strength, mass)
                distributed = prepare_slab_schur(model, gauge, mass, clover, comm, library)
                image = distributed(field[slab])
                normal = model.gamma5 @ distributed(model.gamma5 @ image)
                serial_image = model.apply_even_schur(gauge, mass, field, clover)
                serial_normal = model.apply_even_normal(gauge, mass, field, clover)
                errors = [
                    float((image - serial_image[slab]).abs().max()),
                    float((normal - serial_normal[slab]).abs().max()),
                ]
                max_schur, max_normal = (comm.allreduce(error, op=MPI.MAX) for error in errors)
                if max(max_schur, max_normal) > 3e-14:
                    raise AssertionError((lattice, mass, max_schur, max_normal))
                # Recompute all true residuals against the global Torch stencil.
                def distributed_normal(x):
                    return model.gamma5 @ distributed(model.gamma5 @ distributed(x))

                shifts = (0., .01, 1., 1000.)
                solutions, residuals = solve_multi_shift(
                    distributed_normal, field[slab], shifts, comm=comm)
                plain, _, plain_residual = solve_shifted(
                    distributed_normal, field[slab], shifts[0], comm=comm)
                torch.testing.assert_close(plain, solutions[0], rtol=2e-11, atol=2e-11)
                independent = []
                for shift, solution in zip(shifts, solutions):
                    whole = torch.cat(comm.allgather(solution), dim=0)
                    delta = model.apply_even_normal(gauge, mass, whole, clover) + shift * whole - field
                    independent.append(float(torch.linalg.vector_norm(delta) /
                                             torch.linalg.vector_norm(field)))
                if max((*independent, *residuals, plain_residual)) > 1.01e-12:
                    raise AssertionError((lattice, mass, independent, residuals, plain_residual))
                results.append(dict(lattice=lattice, mass=mass, schur_error=max_schur,
                                    normal_error=max_normal, independent_shifted_residuals=independent,
                                    distributed_shifted_residuals=residuals))
        if comm.rank == 0:
            args.output.write_text(json.dumps(dict(ranks=comm.size, cases=results, passed=True),
                                              indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
