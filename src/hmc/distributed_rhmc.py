"""Time-slab 2+1 Wilson–Clover RHMC with native shifted solves."""
import math
from time import perf_counter

import numpy as np
import torch

from .distributed_gauge import owned_clover_strength, owned_gauge_action, owned_gauge_gradient, time_faces
from .distributed_schur import prepare_local_slab_schur
from .rational import apply_rational, checked_rational_terms
from .reference import CD, RD, clover_chiral_blocks, dagger, drift_links, generators, integrate_links
from .shifted import solve_multi_shift, solve_shifted
from .spectral import cold_wilson_gap, positive_schur_bounds


def _finite_sum(terms):
    return math.fsum(terms) if all(map(math.isfinite, terms)) else math.nan


class DistributedRHMC:
    def __init__(self, lattice, beta, ml, ms, csw, comm, library, interval=(.004, 4.), *,
                 md_order=32, md_tolerance=1e-12, direct_clover=False, packed_faces=False, compact_spin=False,
                 zolotarev=False, force_pole_batch=8, projected_force_faces=False,
                 light_heatbath_action=False, real_krylov_dot=False, pade_drift=False):
        self.lattice = tuple(lattice)
        if (len(self.lattice) != 4 or any(n <= 0 or n % 2 for n in self.lattice) or
                self.lattice[3] % comm.size != 0):
            raise ValueError("Use even global extents and an equal decomposition in time")
        if not all(math.isfinite(x) for x in (beta, ml, ms, csw)) or beta <= 0 or min(ml, ms) <= -4:
            raise ValueError("Invalid Wilson–Clover parameters")
        if not 0 < md_tolerance < 1:
            raise ValueError("The MD relative residual tolerance must be between zero and one")
        if type(force_pole_batch) is not int or force_pole_batch < 1:
            raise ValueError("Use a positive integer for the force pole batch size")
        if projected_force_faces and not compact_spin:
            raise ValueError("Projected force faces require compact spin contractions")
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
        self.direct_clover = direct_clover
        self.packed_faces = packed_faces
        self.compact_spin = compact_spin
        self.zolotarev = zolotarev
        self.force_pole_batch = force_pole_batch
        self.projected_force_faces = projected_force_faces
        self.light_heatbath_action = light_heatbath_action
        self.real_krylov_dot = real_krylov_dot
        self.pade_drift = pade_drift
        self.md_terms, self.endpoint_terms, self.refresh_terms, self.grid_errors = checked_rational_terms(
            self.interval, md_order=md_order, zolotarev=zolotarev)

    def cold(self):
        return self.eye.repeat(self.local_volume, 4, 1, 1)

    def _gauge_faces(self, u):
        return time_faces(u.reshape(*self.site_shape, 4, 3, 3), self.comm)

    def _coefficients(self, extended):
        field = [value.reshape(-1, 3, 3)
                 for value in owned_clover_strength(extended, direct=self.direct_clover)]
        return tuple(clover_chiral_blocks(field, mass, self.csw) for mass in (self.ml, self.ms))

    def _certify(self, strange_clover, gauge):
        lower, upper = positive_schur_bounds(strange_clover[~self.odd], strange_clover[self.odd],
                                              self.ms, comm=self.comm,
                                              cold_gap=self.strange_cold_gap, links=gauge)
        if not self.interval[0] <= lower <= upper <= self.interval[1]:
            raise ArithmeticError("Certified strange spectrum exceeds the fixed rational interval")
        return lower, upper

    def _schur(self, extended, clover, mass):
        return prepare_local_slab_schur(extended, clover, mass, self.comm, self.library,
                                        packed_faces=self.packed_faces, compact_spin=self.compact_spin,
                                        projected_force_faces=self.projected_force_faces)

    def _normal(self, schur, field):
        return self.gamma5 * schur(self.gamma5 * schur(field))

    def _endpoint_geometry(self, u):
        extended = self._gauge_faces(u)
        coefficients = self._coefficients(extended)
        self._certify(coefficients[1], u)
        return extended, coefficients

    def _refresh_fields(self, schur_l, schur_s, noise_l, noise_s):
        def normal(vec):
            return self._normal(schur_s, vec)

        fraction, _ = apply_rational(normal, noise_s, self.refresh_terms, comm=self.comm, real_dot=self.real_krylov_dot)
        return self.gamma5 * schur_l(self.gamma5 * noise_l), normal(fraction)

    @torch.no_grad()
    def refresh(self, u, noise_l, noise_s):
        extended, (light, strange) = self._endpoint_geometry(u)
        schur_l = self._schur(extended, light, self.ml)
        schur_s = self._schur(extended, strange, self.ms)
        return self._refresh_fields(schur_l, schur_s, noise_l, noise_s)

    @torch.no_grad()
    def _local_endpoint_terms(self, u, p, fields):
        extended, coefficients = self._endpoint_geometry(u)
        return self._endpoint_terms(extended, coefficients, p, fields)

    def _endpoint_terms(self, extended, coefficients, p, fields, operators=None, light_action=None):
        terms = [float(owned_gauge_action(extended, self.beta)), float(p.square().sum()) / 2]
        for i, (mass, phi, clover) in enumerate(zip((self.ml, self.ms), fields, coefficients)):
            if i == 0 and light_action is not None:
                action = light_action
            else:
                schur = self._schur(extended, clover, mass) if operators is None else operators[i]

                def normal(vec):
                    return self._normal(schur, vec)

                if i == 0:
                    solved, _, _ = solve_shifted(normal, phi, 0., comm=self.comm, real_dot=self.real_krylov_dot)
                else:
                    solved, _ = apply_rational(normal, phi, self.endpoint_terms, comm=self.comm,
                                               real_dot=self.real_krylov_dot)
                action = float((phi.conj() * solved).real.sum())
            terms.extend((action, -(2 - i) * float(torch.linalg.slogdet(clover[self.odd])[1].sum())))
        return terms

    def _light_noise_action(self, gauge, clover, noise):
        # With phi = S† eta and nonsingular S, phi† (S†S)⁻¹ phi = ||eta||².
        # Certify invertibility using local Gershgorin bounds and the same
        # Wilson hopping norm bound used for the strange Schur operator.
        entries = clover.abs()
        diagonal = clover.diagonal(dim1=-2, dim2=-1).real
        bound = float((diagonal + diagonal.abs() - entries.sum(dim=-1)).amin())
        scale = float(entries.amax())
        deviation = float((dagger(gauge) @ gauge - self.eye).abs().square().sum(dim=(-2, -1)).amax().sqrt())
        # Each time hop may use another rank's gauge link.
        extrema = self.comm.allgather((bound, scale, deviation))
        if not all(math.isfinite(value) for row in extrema for value in row):
            return None
        bounds, scales, deviations = zip(*extrema)
        hopping = 4 * math.sqrt(1 + max(deviations)) / (self.ml + 4)
        bound, scale = min(bounds), max(scales)
        margin = 64 * torch.finfo(diagonal.dtype).eps * max(1., scale, hopping)
        if bound > hopping + margin:
            return float((noise.real.square() + noise.imag.square()).sum())
        return None

    @torch.no_grad()
    def _heatbath_and_initial_terms(self, u, p, noises):
        # The freshly drawn fields and H at the initial configuration use
        # the same halo, Clover factors, and native Schur workspaces.
        extended, coefficients = self._endpoint_geometry(u)
        operators = tuple(self._schur(extended, clover, mass)
                          for clover, mass in zip(coefficients, (self.ml, self.ms)))
        fields = self._refresh_fields(*operators, *noises)
        refreshed = perf_counter()
        light_action = self._light_noise_action(u, coefficients[0], noises[0]) if self.light_heatbath_action else None
        return fields, self._endpoint_terms(extended, coefficients, p, fields, operators, light_action), refreshed

    def endpoint_energy(self, u, p, fields):
        energy = self.comm.allreduce(_finite_sum(self._local_endpoint_terms(u, p, fields)))
        if not math.isfinite(energy):
            raise ArithmeticError("Nonfinite distributed Hamiltonian")
        return energy

    def _hamiltonian_pair(self, initial, final):
        # Subtract corresponding terms before the collective. This avoids
        # subtracting two extensive, already rounded global Hamiltonians.
        differences = [b - a for a, b in zip(initial, final)]
        local = np.array([_finite_sum(initial), _finite_sum(final), _finite_sum(differences)], dtype=np.float64)
        total = np.empty_like(local)
        self.comm.Allreduce(local, total)
        if not np.isfinite(total).all():
            raise ArithmeticError("Nonfinite distributed Hamiltonian")
        return tuple(total.tolist())

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
                solutions = [solve_shifted(normal, phi, shifts[0], self.md_tolerance, comm=self.comm,
                                           real_dot=self.real_krylov_dot)[0]]
            else:
                solutions, _ = solve_multi_shift(normal, phi, shifts, self.md_tolerance, comm=self.comm,
                                                 real_dot=self.real_krylov_dot)
            finished_solve = perf_counter()
            solves += finished_solve - start
            # Release spinor intermediates after each block. Accumulate the
            # coefficient cotangents before differentiating the gauge geometry.
            for first in range(0, len(weights), self.force_pole_batch):
                end = min(first + self.force_pole_batch, len(weights))
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
        return drift_links(u, p, length, self.basis, pade=self.pade_drift)

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
        fields, initial_terms, refreshed = self._heatbath_and_initial_terms(u, p, noises)
        force_timing = dict(coefficient_build=0., prepare_and_solve=0.,
                            spinor_differentiation=0., gauge_differentiation=0.)
        started_md = perf_counter()
        proposed, final_p = self.integrate(u, p, fields, length, steps, integrator,
                                           force_timing=force_timing, gauge_steps=gauge_steps)
        finished_md = perf_counter()
        final_terms = self._local_endpoint_terms(proposed, final_p, fields)
        initial, final, delta = self._hamiltonian_pair(initial_terms, final_terms)
        finished_endpoint = perf_counter()
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
