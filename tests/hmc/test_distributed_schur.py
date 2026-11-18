"""Compare native MPI Schur phases with the full-volume Torch stencil."""
import argparse
import json
import os
from pathlib import Path
import sys

from mpi4py import MPI
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hmc.distributed_gauge import owned_clover_strength, time_faces
from hmc.distributed_schur import prepare_local_slab_schur, prepare_slab_schur
from hmc.reference import CloverHMC, CD, RD
from hmc.shifted import solve_multi_shift, solve_shifted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--real-krylov-dot", action="store_true")
    parser.add_argument("--overlap-schur-faces", action="store_true")
    parser.add_argument("--fused-schur-gamma5", action="store_true")
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
                    distributed_normal, field[slab], shifts, comm=comm, real_dot=args.real_krylov_dot)
                plain, _, plain_residual = solve_shifted(
                    distributed_normal, field[slab], shifts[0], comm=comm, real_dot=args.real_krylov_dot)
                torch.testing.assert_close(plain, solutions[0], rtol=2e-11, atol=2e-11)
                independent = []
                for shift, solution in zip(shifts, solutions):
                    whole = torch.cat(comm.allgather(solution), dim=0)
                    delta = model.apply_even_normal(gauge, mass, whole, clover) + shift * whole - field
                    independent.append(float(torch.linalg.vector_norm(delta) /
                                             torch.linalg.vector_norm(field)))
                if max((*independent, *residuals, plain_residual)) > 1.01e-12:
                    raise AssertionError((lattice, mass, independent, residuals, plain_residual))
                # Prepare strictly local gauge/Clover coefficients, then check
                # both the native solve path and the adjoint through each halo.
                nt = lattice[3] // comm.size
                ti = slice(comm.rank * nt, (comm.rank + 1) * nt)
                full = gauge.clone().requires_grad_(True)
                local = full.reshape(*reversed(lattice), 4, 3, 3)[ti].detach().clone().requires_grad_(True)
                extended = time_faces(local, comm)
                local_clover = model.clover_blocks(
                    [x.reshape(-1, 3, 3) for x in owned_clover_strength(extended)], mass)
                local_apply = prepare_local_slab_schur(extended, local_clover, mass, comm, library,
                                                      fused_gamma5=args.fused_schur_gamma5)
                local_image = local_apply(field[slab])
                global_image = model.apply_even_schur(full, mass, field)
                with torch.no_grad():
                    native_image = local_apply(field[slab])
                    full_halo = prepare_local_slab_schur(
                        extended, local_clover, mass, comm, library, projected=False)
                    native_full_halo = full_halo(field[slab])
                    packed_apply = prepare_local_slab_schur(
                        extended, local_clover, mass, comm, library, packed_faces=True,
                        overlap_faces=args.overlap_schur_faces, fused_gamma5=args.fused_schur_gamma5)
                    native_packed = packed_apply(field[slab])

                    def packed_normal(x):
                        return model.gamma5 @ packed_apply(model.gamma5 @ packed_apply(x))

                    if args.fused_schur_gamma5:
                        for operator in (local_apply, packed_apply):
                            reflected = operator(field[slab], reflect=True)
                            torch.testing.assert_close(reflected, model.gamma5 @ operator(field[slab]),
                                                       rtol=0., atol=0.)
                            fused_normal = operator(reflected, reflect=True)
                            torch.testing.assert_close(fused_normal, packed_normal(field[slab]),
                                                       rtol=0., atol=0.)
                    packed_solution, _, packed_residual = solve_shifted(
                        packed_normal, field[slab], shifts[1], comm=comm, real_dot=args.real_krylov_dot)
                    torch.testing.assert_close(packed_solution, solutions[1], rtol=2e-11, atol=2e-11)
                local_error = max(float((x - global_image[slab]).abs().max())
                                  for x in (local_image, native_image, native_full_halo, native_packed))
                halo_error = comm.allreduce(float((native_image - native_full_halo).abs().max()),
                                            op=MPI.MAX)
                packed_error = comm.allreduce(float((native_image - native_packed).abs().max()), op=MPI.MAX)
                local_grad, = torch.autograd.grad(local_image.abs().square().sum(), local)
                full_grad, = torch.autograd.grad(global_image.abs().square().sum(), full)
                grad_error = float((local_grad - full_grad.reshape(*reversed(lattice), 4, 3, 3)[ti]).abs().max())
                local_error = comm.allreduce(local_error, op=MPI.MAX)
                grad_error = comm.allreduce(grad_error, op=MPI.MAX)
                if local_error > 3e-14 or grad_error > 5e-14:
                    raise AssertionError((lattice, mass, local_error, grad_error))
                results.append(dict(lattice=lattice, mass=mass, schur_error=max_schur,
                                    normal_error=max_normal, independent_shifted_residuals=independent,
                                    distributed_shifted_residuals=residuals,
                                    local_schur_error=local_error, projected_halo_error=halo_error,
                                    packed_halo_error=packed_error, packed_shifted_true_residual=packed_residual,
                                    schur_link_gradient_error=grad_error))
        if comm.rank == 0:
            args.output.write_text(json.dumps(dict(ranks=comm.size, cases=results, passed=True,
                                                fused_schur_gamma5=args.fused_schur_gamma5),
                                              indent=2) + "\n")
    finally:
        comm.Free()


if __name__ == "__main__":
    main()
