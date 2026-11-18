"""Small-volume 2+1 pseudofermion validation with rational MD and exact endpoints."""
from __future__ import annotations

import math

import numpy as np
import torch

from .rational import apply_rational, inverse_power_terms, rational_action_gradient
from .reference import CD, RD, CloverHMC, dagger
from .shifted import solve_shifted
from .spectral import positive_schur_bounds


class PseudofermionHMC(CloverHMC):
    """Cross-check a rational MD force using dense heatbath and Metropolis."""

    def __init__(self, *args, strange_interval=(0.15, 2.0), rational_order=24, **kwargs):
        super().__init__(*args, **kwargs)
        self.strange_interval = tuple(strange_interval)
        self.strange_terms = inverse_power_terms(0.5, *self.strange_interval, order=rational_order)
        dofs = torch.arange(12)
        self.even_dofs = (12 * self.even[:, None] + dofs).flatten()
        self.odd_dofs = (12 * self.odd[:, None] + dofs).flatten()

    def matrix_free_endpoint_energy(self, u, p, fields, strange_terms, interval, tol=1e-12):
        """Evaluate the pseudofermion Hamiltonian using only local Clover and Schur solves."""
        strength = self.field_strength(u)
        energy = float(self.gauge_action(u)) + float(p.square().sum()) / 2
        for mass, strange, multiplicity, phi in (
                (self.ml, False, 2, fields[0]), (self.ms, True, 1, fields[1])):
            clover = self.clover_blocks(strength, mass)
            odd = clover[self.odd]
            if strange:
                lower, upper = positive_schur_bounds(clover[self.even], odd, mass)
                if not (interval[0] <= lower <= upper <= interval[1]):
                    raise ArithmeticError("Certified strange spectrum exceeds the endpoint interval")
            schur = self.prepare_even_schur(u, mass, clover)

            def normal(vec):
                return self.even_normal_from_schur(schur, vec)

            solved = (apply_rational(normal, phi, strange_terms, tol)[0] if strange
                      else solve_shifted(normal, phi, 0., tol)[0])
            energy += float((phi.conj() * solved).real.sum())
            energy -= multiplicity * float(torch.linalg.slogdet(odd)[1].sum())
        if not math.isfinite(energy):
            raise ArithmeticError("Nonfinite matrix-free pseudofermion Hamiltonian")
        return energy

    def _normal_spectrum(self, u, mass, field, strange=False):
        full = self.dirac(u, mass, field)
        e, o = self.even_dofs, self.odd_dofs
        odd_block = full[o][:, o]
        schur = full[e][:, e] - full[e][:, o] @ torch.linalg.solve(odd_block, full[o][:, e])
        if strange:
            sign, logdet = torch.linalg.slogdet(full)
            if abs(complex(sign) - 1) > 1e-9 or not math.isfinite(float(logdet)):
                raise ArithmeticError("Invalid strange determinant at trajectory endpoint")
        values, vectors = torch.linalg.eigh(dagger(schur) @ schur)
        if not torch.isfinite(values).all().item() or values[0].item() <= 0:
            raise ArithmeticError("Nonpositive Schur normal spectrum")
        if strange and not (self.strange_interval[0] <= values[0].item() and
                            values[-1].item() <= self.strange_interval[1]):
            raise ArithmeticError("Strange endpoint spectrum outside the fixed MD interval")
        odd_logdet = float(torch.linalg.slogdet(odd_block)[1])
        return values, vectors, odd_logdet

    def refresh(self, u, rng):
        field = self.field_strength(u)
        result = []
        for mass, strange, power in ((self.ml, False, 0.5), (self.ms, True, 0.25)):
            values, vectors, _ = self._normal_spectrum(u, mass, field, strange)
            # Unitary rotation leaves the complex Gaussian distribution invariant.
            eta = torch.randn(values.shape, dtype=CD, generator=rng)
            result.append(vectors @ (values.pow(power) * eta))
        return tuple(result)

    def endpoint_energy(self, u, p, fields):
        strength = self.field_strength(u)
        energy = float(self.gauge_action(u)) + float(p.square().sum()) / 2
        for mass, strange, power, multiplicity, phi in (
                (self.ml, False, 1., 2, fields[0]), (self.ms, True, 0.5, 1, fields[1])):
            values, vectors, logdet = self._normal_spectrum(u, mass, strength, strange)
            projection = dagger(vectors) @ phi
            energy += float((projection.abs().square() * values.pow(-power)).sum()) - multiplicity * logdet
        if not math.isfinite(energy):
            raise ArithmeticError("Nonfinite pseudofermion Hamiltonian")
        return energy

    def md_force(self, u, fields):
        links = u.detach().requires_grad_(True)
        strength = self.field_strength(links)
        total = 0.
        for mass, multiplicity in ((self.ml, 2), (self.ms, 1)):
            odd_clover = self.clover_blocks(strength, mass)[self.odd]
            total = total - multiplicity * torch.linalg.slogdet(odd_clover)[1].sum()
        gradient, = torch.autograd.grad(total, links)
        gradient = gradient + self.gauge_link_gradient(u)
        for mass, phi, terms in ((self.ml, fields[0], ((0., 1.),)),
                                 (self.ms, fields[1], self.strange_terms)):
            _, sea_gradient = rational_action_gradient(self, u, mass, phi, terms)
            gradient = gradient + sea_gradient
        tangent = 1j * torch.einsum("aij,vmjk->vmaik", self.t, u.detach())
        return (gradient.conj().unsqueeze(-3) * tangent).sum((-1, -2)).real

    def trajectory(self, u, rng, length=0.5, steps=10, integrator="leapfrog"):
        p = torch.randn((self.volume, 4, 8), dtype=RD, generator=rng)
        fields = self.refresh(u, rng)
        h0 = self.endpoint_energy(u, p, fields)
        proposal, final_p = self.integrate(u, p, length, steps, integrator,
                                           force=lambda gauge: self.md_force(gauge, fields))
        h1 = self.endpoint_energy(proposal, final_p, fields)
        delta = h1 - h0
        draw = float(torch.rand((), dtype=RD, generator=rng))
        probability = math.exp(min(0., -delta))
        accepted = draw < probability
        return (proposal if accepted else u.clone()), dict(
            accepted=accepted, delta_h=delta, h_initial=h0, h_final=h1,
            metropolis_probability=probability)


class MatrixFreePseudofermionHMC(PseudofermionHMC):
    """Rational refresh and endpoints with a sufficient positivity check."""

    def __init__(self, *args, strange_interval=(0.004, 4.), endpoint_order=64, **kwargs):
        super().__init__(*args, strange_interval=strange_interval, rational_order=32,
                         dense_reference=False, **kwargs)
        points = np.geomspace(*self.strange_interval, 4097)
        def grid_error(power, terms):
            approximation = sum(weight / (points + shift) for shift, weight in terms)
            return float(np.max(np.abs(approximation * points ** power - 1)))

        def choose_terms(power):
            for order in (*range(8, endpoint_order, 4), endpoint_order):
                terms = inverse_power_terms(power, *self.strange_interval, order=order)
                error = grid_error(power, terms)
                if error <= 1e-12:
                    return terms, error
            raise ArithmeticError("Endpoint or refresh rational approximation exceeds grid tolerance")

        self.endpoint_terms, endpoint_error = choose_terms(0.5)
        self.refresh_terms, refresh_error = choose_terms(0.75)
        self.rational_grid_error = dict(endpoint=endpoint_error, refresh=refresh_error,
                                        md=grid_error(0.5, self.strange_terms))

    def _certify_strange(self, clover):
        lower, upper = positive_schur_bounds(clover[self.even], clover[self.odd], self.ms)
        if not (self.strange_interval[0] <= lower <= upper <= self.strange_interval[1]):
            raise ArithmeticError("Certified strange spectrum exceeds the fixed rational interval")
        return lower, upper

    def refresh(self, u, rng):
        strength = self.field_strength(u)
        shape = (self.volume // 2, 4, 3)
        light = self.prepare_even_schur(u, self.ml, self.clover_blocks(strength, self.ml))
        noise_l = torch.randn(shape, dtype=CD, generator=rng)
        phi_l = self.gamma5 @ light(self.gamma5 @ noise_l)
        clover_s = self.clover_blocks(strength, self.ms)
        self._certify_strange(clover_s)
        strange = self.prepare_even_schur(u, self.ms, clover_s)

        def normal(vec):
            return self.even_normal_from_schur(strange, vec)

        noise_s = torch.randn(shape, dtype=CD, generator=rng)
        fractional, _ = apply_rational(normal, noise_s, self.refresh_terms)
        return phi_l, normal(fractional)

    def endpoint_energy(self, u, p, fields):
        return self.matrix_free_endpoint_energy(u, p, fields, self.endpoint_terms, self.strange_interval)

    def observables(self, u):
        result = self.gauge_observables(u)
        lower, upper = self._certify_strange(self.clover_blocks(self.field_strength(u), self.ms))
        return dict(result, strange_det_phase=1., strange_normal_lower=lower, strange_normal_upper=upper)
