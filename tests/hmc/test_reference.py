"""Physics gates for the small-volume 2+1 Wilson-Clover HMC reference."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from hmc.reference import CloverHMC, CD, RD, dagger, generators, write_lime

REFERENCE = None
REQUIRE_LIME = False
METRICS = {}


class HMCPhysicsTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.m = CloverHMC()
        self.rng = torch.Generator().manual_seed(1234)
        self.p = torch.randn((16, 4, 8), dtype=RD, generator=self.rng)
        self.u = self.m.drift(self.m.cold(), self.p, 0.2)

    def test_generators_and_gamma5(self):
        t = generators()
        torch.testing.assert_close(torch.einsum('aij,bji->ab', t, t),
                                   torch.eye(8, dtype=CD) / 2)
        g = self.m.gamma
        g5 = g[0] @ g[1] @ g[2] @ g[3]
        full = torch.kron(torch.eye(16, dtype=CD), torch.kron(g5, torch.eye(3, dtype=CD)))
        for mass in (self.m.ml, self.m.ms):
            d = self.m.dirac(self.u, mass)
            torch.testing.assert_close(dagger(d), full @ d @ full, atol=2e-14, rtol=2e-14)

    def test_force_finite_difference_gauge_and_sea(self):
        direction = torch.randn((16, 4, 8), dtype=RD, generator=self.rng)
        direction /= torch.linalg.vector_norm(direction)
        for part in ('gauge', 'fermion', 'total'):
            analytic = float((self.m.force(self.u, part) * direction).sum())
            eps = 2e-5
            finite = float((self.m.action(self.m.drift(self.u, direction, eps), part) -
                            self.m.action(self.m.drift(self.u, direction, -eps), part)) / (2 * eps))
            self.assertAlmostEqual(analytic, finite, delta=2e-7)
            METRICS['force_' + part + '_absolute_error'] = abs(analytic - finite)
        no_clover = CloverHMC(csw=0)
        self.assertGreater(float((self.m.force(self.u, 'fermion') -
                                 no_clover.force(self.u, 'fermion')).abs().max()), 1e-5)

    def test_flavor_weights(self):
        m = CloverHMC(mass_light=0.5, mass_strange=0.5)
        expected = -3 * torch.linalg.slogdet(m.dirac(self.u, 0.5))[1]
        torch.testing.assert_close(m.fermion_action(self.u), expected)

    def test_gauge_covariance(self):
        p = torch.randn((16, 1, 8), dtype=RD, generator=self.rng)
        gauge_rotation = self.m.drift(torch.eye(3, dtype=CD).repeat(16, 1, 1, 1), p, 0.3)[:, 0]
        transformed = torch.stack([gauge_rotation @ self.u[:, mu] @
                                   dagger(gauge_rotation[self.m.plus[mu]]) for mu in range(4)], dim=1)
        self.assertAlmostEqual(float(self.m.action(self.u)), float(self.m.action(transformed)), delta=2e-11)

    def test_reversibility_and_su3(self):
        u1, p1 = self.m.integrate(self.u, self.p, 0.2, 4)
        u2, p2 = self.m.integrate(u1, -p1, 0.2, 4)
        METRICS['reversibility_links_max'] = float((u2 - self.u).abs().max())
        METRICS['reversibility_momenta_max'] = float((p2 + self.p).abs().max())
        self.assertLess(float((u2 - self.u).abs().max()), 2e-12)
        self.assertLess(float((p2 + self.p).abs().max()), 2e-11)
        self.assertLess(self.m.observables(u1)['max_unitarity_error'], 2e-12)
        self.assertLess(self.m.observables(u1)['max_det_su3_error'], 2e-12)

    def test_step_size_scaling(self):
        h0 = self.m.hamiltonian(self.u, self.p)
        errors = []
        for steps in (4, 8):
            u, p = self.m.integrate(self.u, self.p, 0.2, steps)
            errors.append(abs(self.m.hamiltonian(u, p) - h0))
        self.assertGreater(errors[0], 1e-8)
        self.assertLess(errors[1], 0.35 * errors[0])
        METRICS['energy_errors_steps_4_8'] = errors
        METRICS['energy_error_ratio'] = errors[1] / errors[0]

    def test_omelyan_reversibility_and_equal_force_budget(self):
        h0 = self.m.hamiltonian(self.u, self.p)
        errors = {}
        # Both trajectories use nine force evaluations.
        for integrator, steps in (("leapfrog", 8), ("omelyan", 4)):
            u, p = self.m.integrate(self.u, self.p, 0.2, steps, integrator)
            errors[integrator] = abs(self.m.hamiltonian(u, p) - h0)
            u_back, p_back = self.m.integrate(u, -p, 0.2, steps, integrator)
            torch.testing.assert_close(u_back, self.u, atol=2e-12, rtol=0)
            torch.testing.assert_close(p_back, -self.p, atol=2e-11, rtol=0)
        METRICS['equal_force_energy_errors'] = errors

    def test_native_independent_operator(self):
        if REFERENCE is None:
            self.skipTest('Pass --reference to check the independent native operator')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.u.numpy().tofile(out / 'gauge.bin')
            vector = torch.randn((192,), dtype=CD, generator=self.rng)
            vector.numpy().tofile(out / 'source.bin')
            for mass in (self.m.ml, self.m.ms):
                subprocess.run([str(REFERENCE), '--dims', '2', '2', '2', '2',
                                '--gauge', str(out / 'gauge.bin'), '--source', str(out / 'source.bin'),
                                '--mass', str(mass), '--csw', str(self.m.csw), '--operator',
                                '--out', str(out / 'applied.bin')], check=True, capture_output=True)
                actual = np.fromfile(out / 'applied.bin', dtype=np.complex128)
                expected = (self.m.dirac(self.u, mass) @ vector).numpy()
                self.assertLess(np.linalg.norm(actual - expected) / np.linalg.norm(actual), 3e-14)
                METRICS['native_operator_relative_error_mass_' + str(mass)] = float(
                    np.linalg.norm(actual - expected) / np.linalg.norm(actual))

    def test_lime_independent_reader(self):
        try:
            from mpi4py import MPI
        except (ImportError, RuntimeError):
            if REQUIRE_LIME:
                self.fail('Required independent LIME reader is unavailable')
            self.skipTest('mpi4py required by the existing LIME reader')
        spec = importlib.util.spec_from_file_location('existing_lime_io', ROOT / 'bindings/lqcd_cpu/io.py')
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'field.lime'
            write_lime(path, self.u.numpy(), (2, 2, 2, 2), dict(nf='2+1', csw=1))
            read = reader.read_lime_gauge(path, comm=MPI.COMM_SELF)
            np.testing.assert_array_equal(read, self.u.numpy().reshape(2, 2, 2, 2, 4, 3, 3))

    def test_size_guard(self):
        with self.assertRaises(ValueError):
            CloverHMC((24, 24, 24, 64))

    def test_matrix_free_dirac_and_link_gradient(self):
        model = CloverHMC((2, 2, 2, 4))
        p = torch.randn((model.volume, 4, 8), dtype=RD, generator=self.rng)
        gauge = model.drift(model.cold(), p, 0.2).requires_grad_(True)
        x = torch.randn((model.volume * 12,), dtype=CD, generator=self.rng)
        y = torch.randn(x.shape, dtype=CD, generator=self.rng)
        for mass in (model.ml, model.ms):
            dense = model.dirac(gauge, mass) @ x
            sparse = model.apply_dirac(gauge, mass, x)
            torch.testing.assert_close(sparse, dense, atol=3e-14, rtol=3e-14)
            grad_dense, = torch.autograd.grad(torch.vdot(y, dense).real, gauge)
            grad_sparse, = torch.autograd.grad(torch.vdot(y, sparse).real, gauge)
            torch.testing.assert_close(grad_sparse, grad_dense, atol=3e-14, rtol=3e-14)

    def test_even_schur_and_clover_determinant(self):
        spin_color = torch.arange(12)
        even = (12 * self.m.even[:, None] + spin_color).flatten()
        odd = (12 * self.m.odd[:, None] + spin_color).flatten()
        x = torch.randn(even.shape, dtype=CD, generator=self.rng)
        u = self.u.detach().requires_grad_(True)
        for mass in (self.m.ml, self.m.ms):
            full = self.m.dirac(u, mass)
            c = self.m.clover(self.m.field_strength(u), mass)
            schur = (full[even][:, even] - full[even][:, odd] @
                     torch.linalg.solve(full[odd][:, odd], full[odd][:, even]))
            torch.testing.assert_close(self.m.apply_even_schur(u, mass, x, c),
                                       schur @ x, atol=3e-14, rtol=3e-14)
            sign, logdet = torch.linalg.slogdet(full)
            schur_sign, schur_logdet = torch.linalg.slogdet(schur)
            clover_signs, clover_logdets = torch.linalg.slogdet(c[self.m.odd])
            reduced_logdet = schur_logdet + clover_logdets.sum()
            torch.testing.assert_close(schur_sign * clover_signs.prod(), sign,
                                       atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(reduced_logdet, logdet, atol=3e-14, rtol=3e-14)
            full_grad, = torch.autograd.grad(logdet, u)
            reduced_grad, = torch.autograd.grad(reduced_logdet, u)
            torch.testing.assert_close(reduced_grad, full_grad, atol=3e-14, rtol=3e-14)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--reference', type=Path)
    p.add_argument('--report', type=Path)
    p.add_argument('--require-lime', action='store_true')
    args, rest = p.parse_known_args()
    REFERENCE = args.reference.resolve() if args.reference else None
    REQUIRE_LIME = args.require_lime
    program = unittest.main(argv=[sys.argv[0], *rest], verbosity=2, exit=False)
    if args.report:
        args.report.write_text(json.dumps(dict(passed=program.result.wasSuccessful(),
            tests_run=program.result.testsRun, failures=len(program.result.failures),
            errors=len(program.result.errors), skipped=len(program.result.skipped),
            metrics=METRICS), indent=2) + '\n')
    sys.exit(0 if program.result.wasSuccessful() else 1)
