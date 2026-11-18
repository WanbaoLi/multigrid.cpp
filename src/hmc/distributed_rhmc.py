"""Time-slab 2+1 Wilson–Clover RHMC with native shifted solves."""
import math
from time import perf_counter

import torch

from .distributed_gauge import owned_clover_strength, owned_gauge_action, owned_gauge_gradient, time_faces
from .distributed_schur import prepare_local_slab_schur
from .rational import apply_rational, checked_rational_terms
from .reference import CD, RD, clover_chiral_blocks, dagger, drift_links, generators, integrate_links
from .shifted import solve_multi_shift, solve_shifted
from .spectral import cold_wilson_gap, positive_schur_bounds


class DistributedRHMC:
    def __init__(self, lattice, beta, ml, ms, csw, comm, library, interval=(.004, 4.), *,
                 md_order=32, md_tolerance=1e-12):
        self.lattice = tuple(lattice)
        if (len(self.lattice) != 4 or any(n <= 0 or n % 2 for n in self.lattice) or
                self.lattice[3] % comm.size != 0):
            raise ValueError("Use even global extents and an equal decomposition in time")
        if not all(math.isfinite(x) for x in (beta, ml, ms, csw)) or beta <= 0 or min(ml, ms) <= -4:
            raise ValueError("Invalid Wilson–Clover parameters")
        if not 0 < md_tolerance < 1:
            raise ValueError("The MD relative residual tolerance must be between zero and one")
        self.beta, self.ml, self.ms, self.csw = beta, ml, ms, csw
        self.comm, self.library = comm, library
        nx, ny, nz, lt = self.lattice
        nt = lt // comm.size
        self.site_shape = (nt, nz, ny, nx)
        self.volume = math.prod(self.lattice)
        self.local_volume = math.prod(self.site_shape)
        self.spinor_shape = (self.local_volume // 2, 4, 3)
        parity = (torch.arange(nt) + comm.rank * nt)[:, None, None, None]
        parity = parity + torch.arange(nz)[None, :, None, None]
        parity = parity + torch.arange(ny)[None, None, :, None]
        parity = parity + torch.arange(nx)[None, None, None, :]
        self.odd = parity.flatten() % 2 == 1
        self.strange_cold_gap = cold_wilson_gap(lt, ms) if ms <= 0 else None
        self.basis = generators()
        self.eye = torch.eye(3, dtype=CD)
        self.gamma5 = torch.tensor([1., 1., -1., -1.], dtype=RD)[:, None]
        self.interval = tuple(interval)
        self.md_tolerance = md_tolerance
        self.md_terms, self.endpoint_terms, self.refresh_terms, self.grid_errors = checked_rational_terms(
            self.interval, md_order=md_order)

    def cold(self):
        return self.eye.repeat(self.local_volume, 4, 1, 1)

    def _gauge_faces(self, u):
        return time_faces(u.reshape(*self.site_shape, 4, 3, 3), self.comm)

    def _coefficients(self, extended):
        field = [value.reshape(-1, 3, 3) for value in owned_clover_strength(extended)]
        return tuple(clover_chiral_blocks(field, mass, self.csw) for mass in (self.ml, self.ms))

    def _certify(self, strange_clover, gauge):
        lower, upper = positive_schur_bounds(strange_clover[~self.odd], strange_clover[self.odd],
                                              self.ms, comm=self.comm,
                                              cold_gap=self.strange_cold_gap, links=gauge)
        if not self.interval[0] <= lower <= upper <= self.interval[1]:
            raise ArithmeticError("Certified strange spectrum exceeds the fixed rational interval")
        return lower, upper

    def _schur(self, extended, clover, mass):
        return prepare_local_slab_schur(extended, clover, mass, self.comm, self.library)

    def _normal(self, schur, field):
        return self.gamma5 * schur(self.gamma5 * schur(field))

    @torch.no_grad()
    def refresh(self, u, noise_l, noise_s):
        extended = self._gauge_faces(u)
        light, strange = self._coefficients(extended)
        self._certify(strange, u)
        schur_l = self._schur(extended, light, self.ml)
        schur_s = self._schur(extended, strange, self.ms)

        def normal(vec):
            return self._normal(schur_s, vec)

        fraction, _ = apply_rational(normal, noise_s, self.refresh_terms, comm=self.comm)
        return self.gamma5 * schur_l(self.gamma5 * noise_l), normal(fraction)

    @torch.no_grad()
    def endpoint_energy(self, u, p, fields):
        extended = self._gauge_faces(u)
        coefficients = self._coefficients(extended)
        self._certify(coefficients[1], u)
        local = float(owned_gauge_action(extended, self.beta)) + float(p.square().sum()) / 2
        for i, (mass, phi, clover) in enumerate(zip((self.ml, self.ms), fields, coefficients)):
            schur = self._schur(extended, clover, mass)

            def normal(vec):
                return self._normal(schur, vec)

            if i == 0:
                solved, _, _ = solve_shifted(normal, phi, 0., comm=self.comm)
            else:
                solved, _ = apply_rational(normal, phi, self.endpoint_terms, comm=self.comm)
            local += float((phi.conj() * solved).real.sum())
            local -= (2 - i) * float(torch.linalg.slogdet(clover[self.odd])[1].sum())
        energy = self.comm.allreduce(local)
        if not math.isfinite(energy):
            raise ArithmeticError("Nonfinite distributed Hamiltonian")
        return energy

    def force(self, u, fields, timing=None, *, include_gauge=True):
        start = perf_counter()
        links = u.detach().requires_grad_(True)
        extended = self._gauge_faces(links)
        coefficients = self._coefficients(extended)
        local = -sum((2 - i) * torch.linalg.slogdet(clover[self.odd])[1].sum()
                     for i, clover in enumerate(coefficients))
        schur_links = extended.detach().requires_grad_(True)
        link_gradient = torch.zeros_like(extended)
        clover_gradients = []
        geometry = perf_counter() - start
        solves = 0.
        spinor_grad = 0.
        for i, (mass, phi, clover, terms) in enumerate(zip(
                (self.ml, self.ms), fields, coefficients, (((0., 1.),), self.md_terms))):
            start = perf_counter()
            schur_clover = clover.detach().requires_grad_(True)
            clover_gradient = torch.zeros_like(clover)
            schur = self._schur(schur_links, schur_clover, mass)

            def normal(vec):
                return self._normal(schur, vec)

            shifts, weights = zip(*terms)
            if len(shifts) == 1:
                solutions = [solve_shifted(normal, phi, shifts[0], self.md_tolerance, comm=self.comm)[0]]
            else:
                solutions, _ = solve_multi_shift(normal, phi, shifts, self.md_tolerance, comm=self.comm)
            finished_solve = perf_counter()
            solves += finished_solve - start
            # Release spinor intermediates after each block. Accumulate the
            # coefficient cotangents before differentiating the gauge geometry.
            for first in range(0, len(weights), 8):
                end = min(first + 8, len(weights))
                image = schur(torch.stack(solutions[first:end])).reshape(end - first, -1)
                norm = (image.real.square() + image.imag.square()).sum(dim=1)
                weight = torch.tensor(weights[first:end], dtype=RD)
                gauge_grad, clover_grad = torch.autograd.grad(
                    -(weight * norm).sum(), (schur_links, schur_clover), retain_graph=end < len(weights))
                link_gradient.add_(gauge_grad)
                clover_gradient.add_(clover_grad)
            clover_gradients.append(clover_gradient)
            spinor_grad += perf_counter() - finished_solve
        start = perf_counter()
        gradient, = torch.autograd.grad(
            (local, extended, *coefficients), links,
            grad_outputs=(torch.ones_like(local), link_gradient, *clover_gradients))
        if include_gauge:
            gradient.add_(owned_gauge_gradient(extended, self.beta).reshape_as(gradient))
        force = self._project_force(u, gradient)
        if timing is not None:
            timing["coefficient_build"] += geometry
            timing["prepare_and_solve"] += solves
            timing["spinor_differentiation"] += spinor_grad
            timing["gauge_differentiation"] += perf_counter() - start
        return force

    def drift(self, u, p, length):
        return drift_links(u, p, length, self.basis)

    def _project_force(self, u, link_gradient):
        return torch.einsum("vmij,aji->vma", u @ dagger(link_gradient), 1j * self.basis).real

    @torch.no_grad()
    def gauge_force(self, u):
        gradient = owned_gauge_gradient(self._gauge_faces(u), self.beta).reshape_as(u)
        return self._project_force(u, gradient)

    def integrate(self, u, p, fields, length, steps, integrator="omelyan", *, force_timing=None, gauge_steps=0):
        def fermion_step(gauge):
            return self.force(gauge, fields, force_timing, include_gauge=gauge_steps == 0)

        return integrate_links(u, p, length, steps, integrator,
                               fermion_step, self.drift, fast_force=self.gauge_force if gauge_steps else None,
                               fast_steps=gauge_steps)

    def trajectory(self, u, rng, length, steps, integrator="omelyan", *, gauge_steps=0):
        p = torch.randn((self.local_volume, 4, 8), dtype=RD, generator=rng)
        noises = [torch.randn(self.spinor_shape, dtype=CD, generator=rng) for _ in range(2)]
        start = perf_counter()
        fields = self.refresh(u, *noises)
        refreshed = perf_counter()
        initial = self.endpoint_energy(u, p, fields)
        force_timing = dict(coefficient_build=0., prepare_and_solve=0.,
                            spinor_differentiation=0., gauge_differentiation=0.)
        started_md = perf_counter()
        proposed, final_p = self.integrate(u, p, fields, length, steps, integrator,
                                           force_timing=force_timing, gauge_steps=gauge_steps)
        finished_md = perf_counter()
        final = self.endpoint_energy(proposed, final_p, fields)
        finished_endpoint = perf_counter()
        delta = final - initial
        probability = math.exp(min(0., -delta))
        draw = float(torch.rand((), dtype=RD, generator=rng)) if self.comm.rank == 0 else None
        accepted = self.comm.bcast(draw, root=0) < probability
        return (proposed if accepted else u.clone()), dict(
            accepted=accepted, delta_h=delta, h_initial=initial, h_final=final,
            metropolis_probability=probability, force_seconds=force_timing,
            phase_seconds=dict(refresh=refreshed - start, md=finished_md - started_md,
                               endpoint=(started_md - refreshed) + (finished_endpoint - finished_md)))

    @torch.no_grad()
    def observables(self, u):
        extended = self._gauge_faces(u)
        action = self.comm.allreduce(float(owned_gauge_action(extended, self.beta)))
        errors = self.comm.allgather((float((dagger(u) @ u - self.eye).abs().max()),
                                      float((torch.linalg.det(u) - 1).abs().max())))
        lower, upper = self._certify(self._coefficients(extended)[1], u)
        return dict(plaquette=1 - action / (6 * self.volume * self.beta),
                    max_unitarity_error=max(x[0] for x in errors),
                    max_det_su3_error=max(x[1] for x in errors),
                    strange_det_phase=1., strange_normal_lower=lower, strange_normal_upper=upper)
