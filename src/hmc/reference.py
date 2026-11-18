"""Small-volume SU(3), Nf=2+1 Wilson-Clover determinant HMC reference.

CPU complex128 only. Fermions are integrated out using dense log determinants,
not quenched, not pseudofermion/RHMC, and not a scalable production generator.
The single-flavor strange determinant must be positive at every evaluation;
a sign/phase violation raises instead of silently sampling an absolute weight.
Conventions match src/core/{clover,dslash}.cpp (normalized Dirac M, DR basis).
"""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import torch

CD = torch.complex128
RD = torch.float64


def dagger(a):
    return a.conj().transpose(-1, -2)


def generators():
    result = []
    for i, j in ((0, 1), (0, 2), (1, 2)):
        a = torch.zeros((3, 3), dtype=CD)
        a[i, j] = a[j, i] = 0.5
        result.append(a)
        a = torch.zeros((3, 3), dtype=CD)
        a[i, j], a[j, i] = -0.5j, 0.5j
        result.append(a)
    result += [torch.diag(torch.tensor([0.5, -0.5, 0], dtype=CD)),
               torch.diag(torch.tensor([1, 1, -2], dtype=CD)) / math.sqrt(12)]
    return torch.stack(result)


def gamma_matrices():
    return torch.tensor([
        [[0, 0, 0, 1j], [0, 0, 1j, 0], [0, -1j, 0, 0], [-1j, 0, 0, 0]],
        [[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]],
        [[0, 0, 1j, 0], [0, 0, 0, -1j], [-1j, 0, 0, 0], [0, 1j, 0, 0]],
        [[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]]], dtype=CD)


class CloverHMC:
    def __init__(self, lattice=(2, 2, 2, 2), beta=5.6,
                 mass_light=0.5, mass_strange=0.8, csw=1.0):
        self.lattice = tuple(int(n) for n in lattice)
        if len(self.lattice) != 4 or any(n < 2 or n % 2 for n in self.lattice):
            raise ValueError("Use four positive even extents, each at least two")
        self.volume = math.prod(self.lattice)
        if self.volume > 32:
            raise ValueError("Dense reference capped at 32 sites; production requires sparse RHMC")
        if not all(math.isfinite(x) for x in (beta, mass_light, mass_strange, csw)):
            raise ValueError("Nonfinite parameters")
        if beta <= 0 or min(mass_light, mass_strange) <= -4:
            raise ValueError("beta must be positive and mass must exceed -4")
        self.beta, self.ml, self.ms, self.csw = beta, mass_light, mass_strange, csw
        grid = torch.arange(self.volume).reshape(tuple(reversed(self.lattice)))
        self.plus = [torch.roll(grid, -1, 3 - mu).flatten() for mu in range(4)]
        self.minus = [torch.roll(grid, 1, 3 - mu).flatten() for mu in range(4)]
        self.eye3 = torch.eye(3, dtype=CD)
        self.eye4 = torch.eye(4, dtype=CD)
        self.gamma = gamma_matrices()
        self.t = generators()
        sites = torch.arange(self.volume)
        self.block_indices = torch.cat(
            [sites * self.volume + sites]
            + [sites * self.volume + neighbors
               for pair in zip(self.plus, self.minus) for neighbors in pair])
        times = torch.div(torch.arange(self.volume), math.prod(self.lattice[:3]), rounding_mode='floor')
        self.forward_sign = torch.where(times == self.lattice[3] - 1, -1., 1.)
        self.backward_sign = torch.where(times == 0, -1., 1.)

    def cold(self):
        return self.eye3.repeat(self.volume, 4, 1, 1)

    def drift(self, u, p, step):
        algebra = torch.einsum("vma,aij->vmij", p.to(CD), self.t)
        # Momentum is Hermitian. A spectral exponential preserves unitarity
        # accurately even on the site's old PyTorch 1.12 batch-exp backend.
        # MD does not differentiate through the drift/eigenvectors.
        eigenvalues, vectors = torch.linalg.eigh(algebra)
        rotation = (vectors * torch.exp(1j * step * eigenvalues).unsqueeze(-2)) @ dagger(vectors)
        return (rotation @ u).detach()

    def loop(self, u, directions):
        index = torch.arange(self.volume)
        value = self.eye3.repeat(self.volume, 1, 1)
        for signed in directions:
            mu = abs(signed) - 1
            if signed > 0:
                value = value @ u[index, mu]
                index = self.plus[mu][index]
            else:
                index = self.minus[mu][index]
                value = value @ dagger(u[index, mu])
        return value

    def gauge_action(self, u):
        total = torch.zeros((), dtype=RD)
        for mu in range(4):
            for nu in range(mu):
                plaq = self.loop(u, (mu + 1, nu + 1, -mu - 1, -nu - 1))
                total = total + (1 - plaq.diagonal(dim1=-2, dim2=-1).sum(-1).real / 3).sum()
        return self.beta * total

    def field_strength(self, u):
        field = []
        for mu in range(4):
            for nu in range(mu):
                m, n = mu + 1, nu + 1
                q = sum((self.loop(u, path) for path in
                         ((m, n, -m, -n), (n, -m, -n, m),
                          (-n, m, n, -m), (-m, -n, m, n))))
                field.append((q - dagger(q)) / 8)
        return field

    def clover(self, field, mass):
        coeff = self.csw / (2 * (mass + 4))
        blocks = []
        for ch in (0, 1):
            sign = 1 if ch else -1
            b10 = 1j * coeff * (field[0] + sign * field[5])
            b20 = coeff * (field[1] - sign * field[4] - 1j * (field[2] + sign * field[3]))
            blocks.append(torch.cat((torch.cat((self.eye3 - b10, dagger(b20)), -1),
                                     torch.cat((b20, self.eye3 + b10), -1)), -2))
        zero = torch.zeros_like(blocks[0])
        return torch.cat((torch.cat((blocks[0], zero), -1),
                          torch.cat((zero, blocks[1]), -1)), -2)

    def dirac(self, u, mass, field=None):
        c = self.clover(self.field_strength(u) if field is None else field, mass)
        hopping = []
        for mu in range(4):
            forward = u[:, mu]
            backward = dagger(u[self.minus[mu], mu])
            if mu == 3:
                forward = forward * self.forward_sign[:, None, None]
                backward = backward * self.backward_sign[:, None, None]
            hf = torch.einsum("ab,vcd->vacbd", self.eye4 - self.gamma[mu], forward).reshape(-1, 12, 12)
            hb = torch.einsum("ab,vcd->vacbd", self.eye4 + self.gamma[mu], backward).reshape(-1, 12, 12)
            hopping.extend((hf, hb))
        blocks = torch.cat((c, -torch.cat(hopping) / (2 * (mass + 4))))
        # On an extent of two the forward and backward blocks share an index.
        assembled = blocks.new_zeros((self.volume ** 2, 12, 12))
        assembled.index_add_(0, self.block_indices, blocks)
        return assembled.view(self.volume, self.volume, 12, 12).transpose(1, 2).reshape(
            12 * self.volume, 12 * self.volume)

    def apply_dirac(self, u, mass, spinor, field=None):
        """Apply the normalized operator to one site-major spin/color field."""
        c = self.clover(self.field_strength(u) if field is None else field, mass)
        sites = spinor.reshape(self.volume, 4, 3)
        result = (c @ sites.reshape(self.volume, 12, 1)).reshape_as(sites)
        kappa = 1 / (2 * (mass + 4))
        for mu, (plus, minus) in enumerate(zip(self.plus, self.minus)):
            forward = torch.einsum("vab,vsb->vsa", u[:, mu], sites[plus])
            backward = torch.einsum("vab,vsb->vsa", dagger(u[minus, mu]), sites[minus])
            if mu == 3:
                forward = forward * self.forward_sign[:, None, None]
                backward = backward * self.backward_sign[:, None, None]
            projected = (torch.einsum("st,vta->vsa", self.eye4 - self.gamma[mu], forward) +
                         torch.einsum("st,vta->vsa", self.eye4 + self.gamma[mu], backward))
            result = result - kappa * projected
        return result.reshape_as(spinor)

    def fermion_action(self, u):
        field = self.field_strength(u)
        sign_l, log_l = torch.linalg.slogdet(self.dirac(u, self.ml, field))
        sign_s, log_s = torch.linalg.slogdet(self.dirac(u, self.ms, field))
        if (not torch.isfinite(log_l).item() or not torch.isfinite(log_s).item() or
                abs(complex(sign_s.detach()) - 1) > 1e-9 or
                abs(abs(complex(sign_l.detach())) - 1) > 1e-9):
            raise ArithmeticError("Non-positive strange determinant or singular light operator; no silent sign quenching")
        return -2 * log_l - log_s

    def action(self, u, part="total"):
        if part == "gauge":
            return self.gauge_action(u)
        if part == "fermion":
            return self.fermion_action(u)
        return self.gauge_action(u) + self.fermion_action(u)

    def force(self, u, part="total"):
        leaf = u.detach().requires_grad_(True)
        action = self.action(leaf, part)
        grad, = torch.autograd.grad(action, leaf)
        tangent = 1j * torch.einsum("aij,vmjk->vmaik", self.t, leaf.detach())
        return (grad.conj().unsqueeze(-3) * tangent).sum((-1, -2)).real.detach()

    def integrate(self, u, p, length, steps, integrator="leapfrog"):
        if steps < 1 or not math.isfinite(length) or integrator not in ("leapfrog", "omelyan"):
            raise ValueError("Invalid integration parameters")
        step = length / steps
        u, p = u.clone(), p.clone()
        if integrator == "omelyan":
            edge = 0.1931833275037836 * step
            p = p - edge * self.force(u)
            for i in range(steps):
                u = self.drift(u, p, step / 2)
                p = p - (step - 2 * edge) * self.force(u)
                u = self.drift(u, p, step / 2)
                p = p - (edge if i == steps - 1 else 2 * edge) * self.force(u)
            return u, p
        p = p - step / 2 * self.force(u)
        for i in range(steps):
            u = self.drift(u, p, step)
            p = p - (step / 2 if i == steps - 1 else step) * self.force(u)
        return u, p

    def hamiltonian(self, u, p):
        return float(self.action(u)) + float(p.square().sum()) / 2

    def trajectory(self, u, rng, length=0.5, steps=10, integrator="leapfrog"):
        p = torch.randn((self.volume, 4, 8), dtype=RD, generator=rng)
        h0 = self.hamiltonian(u, p)
        proposal, pend = self.integrate(u, p, length, steps, integrator)
        h1 = self.hamiltonian(proposal, -pend)
        delta = h1 - h0
        log_uniform = math.log(max(float(torch.rand((), generator=rng, dtype=RD)), 1e-300))
        if not math.isfinite(delta):
            raise ArithmeticError("Nonfinite Hamiltonian")
        accepted = log_uniform < -delta
        return (proposal if accepted else u.clone()), dict(
            accepted=accepted, delta_h=delta, h_initial=h0, h_final=h1,
            metropolis_probability=math.exp(min(0, -delta)))

    def observables(self, u):
        eye = dagger(u) @ u - self.eye3
        return dict(plaquette=1 - float(self.gauge_action(u)) / (6 * self.volume * self.beta),
                    max_unitarity_error=float(eye.abs().max()),
                    max_det_su3_error=float((torch.linalg.det(u) - 1).abs().max()),
                    strange_det_phase=complex(torch.linalg.slogdet(self.dirac(u, self.ms))[0]).real)


def write_lime(path, gauge, lattice, metadata):
    """Write untwisted SU(3) links, QIO site-major complex128 + SciDAC CRCs."""
    array = np.asarray(gauge, dtype=np.complex128).reshape(*reversed(lattice), 4, 3, 3)
    raw = np.ascontiguousarray(array, dtype=">c16")
    sums = [0, 0]
    for site, row in enumerate(raw.reshape(-1, 36).view(np.uint8).reshape(-1, 576)):
        crc = zlib.crc32(row)
        for i, modulo in enumerate((29, 31)):
            shift = site % modulo
            sums[i] ^= ((crc << shift) | (crc >> (32 - shift))) & 0xffffffff
    xml = ET.Element("hmc")
    for key, value in metadata.items():
        ET.SubElement(xml, key).text = str(value)
    records = [
        ("scidac-private-file-xml", ("<scidacFile><version>1.1</version><spacetime>4</spacetime><dims>" +
          " ".join(map(str, lattice)) + "</dims><volfmt>0</volfmt></scidacFile>").encode()),
        ("scidac-file-xml", ET.tostring(xml)),
        ("scidac-private-record-xml", b"<scidacRecord><version>1.1</version><recordtype>0</recordtype><datatype>QDP_D3_ColorMatrix</datatype><precision>D</precision><colors>3</colors><spins>1</spins><typesize>144</typesize><datacount>4</datacount></scidacRecord>"),
        ("scidac-record-xml", ET.tostring(xml)),
        ("ildg-binary-data", raw.tobytes()),
        ("scidac-checksum", ("<scidacChecksum><version>1.0</version><suma>%08x</suma><sumb>%08x</sumb></scidacChecksum>" % tuple(sums)).encode())]
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as f:
        for i, (name, data) in enumerate(records):
            flags = (0x8000 if i == 0 else 0) | (0x4000 if i == len(records) - 1 else 0)
            f.write(struct.pack(">IHHQ128s", 0x456789ab, 1, flags, len(data), name.encode()))
            f.write(data)
            f.write(b"\0" * ((-len(data)) % 8))
        f.flush()
        __import__("os").fsync(f.fileno())
    temporary.replace(path)
