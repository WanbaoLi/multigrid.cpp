"""Small-volume 2+1 pseudofermion validation with rational MD and exact endpoints."""
from __future__ import annotations

import math

import torch

from .rational import inverse_power_terms, rational_action_gradient
from .reference import CD, RD, CloverHMC, dagger


class PseudofermionHMC(CloverHMC):
    """Cross-check a rational MD force using dense heatbath and Metropolis."""

    def __init__(self, *args, strange_interval=(0.15, 2.0), rational_order=24, **kwargs):
        super().__init__(*args, **kwargs)
        self.strange_interval = tuple(strange_interval)
        self.strange_terms = inverse_power_terms(0.5, *self.strange_interval, order=rational_order)
        dofs = torch.arange(12)
        self.even_dofs = (12 * self.even[:, None] + dofs).flatten()
        self.odd_dofs = (12 * self.odd[:, None] + dofs).flatten()

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
        total = self.gauge_action(links)
        for mass, multiplicity in ((self.ml, 2), (self.ms, 1)):
            odd_clover = self.clover(strength, mass)[self.odd]
            total = total - multiplicity * torch.linalg.slogdet(odd_clover)[1].sum()
        gradient, = torch.autograd.grad(total, links)
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
