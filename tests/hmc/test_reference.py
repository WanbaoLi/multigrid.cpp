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
from unittest.mock import patch

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from hmc.reference import CloverHMC, CD, RD, dagger, generators, write_lime
from hmc.shifted import solve_multi_shift, solve_shifted
from hmc.rational import (apply_rational, checked_rational_terms, inverse_power_terms,
                          rational_action_gradient, zolotarev_inverse_sqrt)
from hmc.pseudofermion import MatrixFreePseudofermionHMC, PseudofermionHMC
from hmc.spectral import cold_wilson_gap, positive_schur_bounds

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

    def test_gauge_staple_gradient_matches_loop_gradient(self):
        for lattice in ((2, 2, 2, 2), (2, 2, 2, 4), (4, 4, 4, 4)):
            model = CloverHMC(lattice, dense_reference=False)
            p = torch.randn((model.volume, 4, 8), dtype=RD, generator=self.rng)
            gauge = model.drift(model.cold(), p, 0.24).requires_grad_(True)
            expected, = torch.autograd.grad(model.gauge_action(gauge), gauge)
            actual = model.gauge_link_gradient(gauge.detach())
            torch.testing.assert_close(actual, expected, rtol=2e-14, atol=2e-14)
            METRICS[f"gauge_staple_gradient_max_error_{lattice}"] = (actual - expected).abs().max().item()

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
            for lattice, copies in (((2, 2, 2, 2), 1), ((2, 2, 18, 32), 144)):
                expected = np.tile(self.u.numpy(), (copies, 1, 1, 1))
                expected = expected.reshape(*reversed(lattice), 4, 3, 3)
                write_lime(path, expected, lattice, dict(nf='2+1', csw=1))
                read = reader.read_lime_gauge(path, comm=MPI.COMM_SELF)
                np.testing.assert_array_equal(read, expected)

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
            grad_dense, = torch.autograd.grad((y.conj() * dense).real.sum(), gauge)
            grad_sparse, = torch.autograd.grad((y.conj() * sparse).real.sum(), gauge)
            self.assertGreater(grad_dense.abs().max().item(), 1e-4)
            torch.testing.assert_close(grad_sparse, grad_dense, atol=3e-14, rtol=3e-14)

    def test_native_prepared_schur_matches_torch(self):
        if not os.environ.get("LQCD_HMC_SCHUR_LIBRARY"):
            self.skipTest("Native HMC Schur library not configured")
        torch.set_num_threads(2)
        for lattice in ((2, 2, 2, 2), (2, 2, 4, 4), (4, 4, 4, 4)):
            model = CloverHMC(lattice, dense_reference=False)
            p = torch.randn((model.volume, 4, 8), dtype=RD, generator=self.rng)
            gauge = model.drift(model.cold(), p, 0.25)
            strength = model.field_strength(gauge)
            x = torch.randn((model.volume // 2, 4, 3), dtype=CD, generator=self.rng).conj()
            for mass in (model.ml, model.ms):
                blocks = model.clover_blocks(strength, mass)
                native = model.prepare_even_schur(gauge, mass, blocks)
                with patch.dict(os.environ, {"LQCD_HMC_SCHUR_LIBRARY": ""}):
                    reference = model.prepare_even_schur(gauge, mass, blocks)
                with torch.no_grad():
                    actual = model.even_normal_from_schur(native, x)
                    expected = model.even_normal_from_schur(reference, x)
                torch.testing.assert_close(actual, expected, atol=3e-14, rtol=3e-14)
                METRICS[f"native_schur_normal_error_{lattice}_{mass}"] = (actual - expected).abs().max().item()

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
            direct = self.m.apply_even_schur(u, mass, x, c)
            prepared_schur = self.m.prepare_even_schur(u, mass, c)
            prepared = prepared_schur(x)
            expected = schur @ x
            batch = torch.stack((x, x.conj(), x * 2j))
            torch.testing.assert_close(prepared_schur(batch), batch @ schur.transpose(-2, -1),
                                       atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(direct, expected, atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(prepared, expected, atol=3e-14, rtol=3e-14)
            direct_grad, = torch.autograd.grad((x.conj() * direct).real.sum(), u, retain_graph=True)
            expected_grad, = torch.autograd.grad((x.conj() * expected).real.sum(), u, retain_graph=True)
            prepared_grad, = torch.autograd.grad((x.conj() * prepared).real.sum(), u, retain_graph=True)
            self.assertGreater(expected_grad.abs().max().item(), 1e-4)
            torch.testing.assert_close(direct_grad, expected_grad, atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(prepared_grad, expected_grad, atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(self.m.even_normal_from_schur(prepared_schur, x),
                                       dagger(schur) @ expected, atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(self.m.apply_even_normal(u, mass, x, c),
                                       dagger(schur) @ expected, atol=3e-14, rtol=3e-14)
            sign, logdet = torch.linalg.slogdet(full)
            schur_sign, schur_logdet = torch.linalg.slogdet(schur)
            clover_signs, clover_logdets = torch.linalg.slogdet(c[self.m.odd])
            reduced_logdet = schur_logdet + clover_logdets.sum()
            torch.testing.assert_close(schur_sign * clover_signs.prod(), sign,
                                       atol=3e-14, rtol=3e-14)
            torch.testing.assert_close(reduced_logdet, logdet, atol=3e-14, rtol=3e-14)
            full_grad, = torch.autograd.grad(logdet, u, retain_graph=True)
            reduced_grad, = torch.autograd.grad(reduced_logdet, u)
            torch.testing.assert_close(reduced_grad, full_grad, atol=3e-14, rtol=3e-14)

    def test_shifted_normal_against_dense_solve(self):
        spin_color = torch.arange(12)
        even = (12 * self.m.even[:, None] + spin_color).flatten()
        odd = (12 * self.m.odd[:, None] + spin_color).flatten()
        rhs = torch.randn(even.shape, dtype=CD, generator=self.rng)
        for mass in (self.m.ml, self.m.ms):
            full = self.m.dirac(self.u, mass)
            c = self.m.clover(self.m.field_strength(self.u), mass)
            schur = (full[even][:, even] - full[even][:, odd] @
                     torch.linalg.solve(full[odd][:, odd], full[odd][:, even]))
            normal = dagger(schur) @ schur
            for shift in (0.0, 0.01, 1.0):
                def apply(vec):
                    return self.m.apply_even_normal(self.u, mass, vec, c)
                actual, iterations, residual = solve_shifted(apply, rhs, shift)
                expected = torch.linalg.solve(normal + shift * torch.eye(even.numel(), dtype=CD), rhs)
                torch.testing.assert_close(actual, expected, atol=2e-11, rtol=2e-11)
                self.assertGreater(iterations, 0)
                self.assertLessEqual(residual, 1e-12)
                METRICS[f"shifted_cg_{mass}_{shift}"] = dict(
                    iterations=iterations, residual=residual)

    def test_negative_mass_cold_certificate_against_dense_spectrum(self):
        mass = -.277
        cold = self.m.cold()
        gap = cold_wilson_gap(self.m.lattice[3], mass)
        dense_gap = float(torch.linalg.svdvals(self.m.dirac(cold, mass)).min())
        self.assertAlmostEqual(gap, dense_gap, places=13)
        near_cold = self.m.drift(cold, self.p, .02)
        strength = self.m.field_strength(near_cold)
        clover = self.m.clover_blocks(strength, mass)
        lower, upper = positive_schur_bounds(clover[self.m.even], clover[self.m.odd], mass,
                                             cold_gap=gap, links=near_cold)
        dense = PseudofermionHMC(mass_strange=mass, strange_interval=(.0005, 6.))
        eigenvalues, _, _ = dense._normal_spectrum(near_cold, mass, strength, True)
        self.assertLessEqual(lower, float(eigenvalues.min()))
        self.assertGreaterEqual(upper, float(eigenvalues.max()))
        far_links = torch.diag(torch.tensor([-1., -1., 1.], dtype=CD)).expand_as(cold)
        cold_clover = self.m.clover_blocks(self.m.field_strength(cold), mass)
        with self.assertRaises(ArithmeticError):
            positive_schur_bounds(cold_clover[self.m.even], cold_clover[self.m.odd], mass,
                                  cold_gap=gap, links=far_links)
        METRICS["negative_mass_cold_certificate"] = dict(
            free_gap=gap, dense_free_gap=dense_gap, certified_bounds=[lower, upper],
            exact_bounds=[float(eigenvalues.min()), float(eigenvalues.max())])

    def test_strange_fractional_power_against_dense_spectrum(self):
        mass = self.m.ms
        spin_color = torch.arange(12)
        even = (12 * self.m.even[:, None] + spin_color).flatten()
        odd = (12 * self.m.odd[:, None] + spin_color).flatten()
        rhs = torch.randn(even.shape, dtype=CD, generator=self.rng)
        full = self.m.dirac(self.u, mass)
        c = self.m.clover(self.m.field_strength(self.u), mass)
        schur = (full[even][:, even] - full[even][:, odd] @
                 torch.linalg.solve(full[odd][:, odd], full[odd][:, even]))
        eigenvalues, vectors = torch.linalg.eigh(dagger(schur) @ schur)
        certified = positive_schur_bounds(c[self.m.even], c[self.m.odd], mass)
        self.assertLessEqual(certified[0], eigenvalues[0].item())
        self.assertGreaterEqual(certified[1], eigenvalues[-1].item())
        row_sum = positive_schur_bounds(c[self.m.even], c[self.m.odd], mass, gershgorin=True)
        self.assertLessEqual(row_sum[0], certified[0])
        self.assertGreaterEqual(row_sum[1], certified[1])
        with self.assertRaises(ArithmeticError):
            positive_schur_bounds(c[self.m.even], c[self.m.odd], -0.277)
        METRICS["positive_strange_schur_bounds"] = certified
        METRICS["gershgorin_strange_schur_bounds"] = row_sum
        lower, upper = eigenvalues[0].item() * 0.9, eigenvalues[-1].item() * 1.1
        projection = dagger(vectors) @ rhs
        for power in (0.25, 0.5, 0.75):
            terms = inverse_power_terms(power, lower, upper, order=24)
            points = np.geomspace(lower, upper, 257)
            scalar = sum(weight / (points + shift) for shift, weight in terms)
            self.assertLess(np.max(np.abs(scalar * points ** power - 1)), 1e-11)
            def apply(vec):
                return self.m.apply_even_normal(self.u, mass, vec, c)
            actual, residual = apply_rational(apply, rhs, terms)
            expected = vectors @ (eigenvalues.pow(-power) * projection)
            error = (torch.linalg.vector_norm(actual - expected) /
                     torch.linalg.vector_norm(expected)).item()
            self.assertLess(error, 2e-11)
            METRICS[f"strange_inverse_power_{power}"] = dict(
                spectral_bounds=[lower, upper], poles=len(terms), relative_error=error,
                max_shifted_residual=residual)

    def test_shared_shifted_krylov_basis(self):
        mass = self.m.ms
        clover = self.m.clover(self.m.field_strength(self.u), mass)
        rhs = torch.randn((self.m.volume * 6,), dtype=CD, generator=self.rng)
        calls = 0
        def apply(x):
            nonlocal calls
            calls += 1
            return self.m.apply_even_normal(self.u, mass, x, clover)
        shifts = (0.01, 25., 0., 1., 10000.)
        expected = [solve_shifted(apply, rhs, shift)[0] for shift in shifts]
        independent_calls, calls = calls, 0
        actual, residuals = solve_multi_shift(apply, rhs, shifts)
        for result, reference in zip(actual, expected):
            torch.testing.assert_close(result, reference, atol=2e-11, rtol=2e-11)
        self.assertLessEqual(max(residuals), 1e-12)
        self.assertLess(calls, independent_calls)
        METRICS["multi_shift"] = dict(shared_operator_calls=calls,
            independent_operator_calls=independent_calls, max_residual=max(residuals))

    def test_compressed_strange_refresh(self):
        interval = (.004, 4.)
        baseline = checked_rational_terms(interval, md_order=16)
        candidate = checked_rational_terms(interval, md_order=16, compress_refresh=True)
        self.assertEqual(candidate[:2], baseline[:2])
        self.assertLess(len(candidate[2]), len(baseline[2]) // 2)
        self.assertTrue(all(shift > 0 and weight > 0 for shift, weight in candidate[2]))
        points = np.geomspace(*interval, 65535)
        approximation = points ** .75 * sum(weight / (points + shift) for shift, weight in candidate[2])
        scalar_error = float(np.max(np.abs(approximation - 1)))
        self.assertLessEqual(scalar_error, 1e-12)

        eigenvalues = torch.from_numpy(np.geomspace(*interval, 24))
        noise = torch.randn(eigenvalues.shape, dtype=CD, generator=self.rng)
        expected = eigenvalues.pow(.25) * noise
        counts = []
        for terms in (baseline[2], candidate[2]):
            calls = 0

            def normal(field):
                nonlocal calls
                calls += 1
                return eigenvalues * field

            field, residual = apply_rational(normal, noise, terms)
            torch.testing.assert_close(normal(field), expected, atol=2e-11, rtol=2e-11)
            self.assertLessEqual(residual, 1e-12)
            counts.append(calls)
        self.assertLess(counts[1], counts[0])
        METRICS["compressed_refresh"] = dict(baseline_poles=len(baseline[2]),
            candidate_poles=len(candidate[2]), baseline_normal_calls=counts[0],
            candidate_normal_calls=counts[1], scalar_error=scalar_error)

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional elliptic coefficients require SciPy")
    def test_zolotarev_inverse_square_root(self):
        summaries = []
        for lower, upper in ((.004, 4.), (.0005, 6.)):
            terms, error = zolotarev_inverse_sqrt(lower, upper, 2.5e-13)
            self.assertLess(len(terms), 48)
            self.assertTrue(all(shift > 0 and weight > 0 for shift, weight in terms))
            points = np.geomspace(lower, upper, 65539)
            approximation = sum(weight / (points + shift) for shift, weight in terms)
            measured = float(np.max(np.abs(np.sqrt(points) * approximation - 1.)))
            self.assertLess(measured, 3e-13)
            summaries.append(dict(interval=[lower, upper], poles=len(terms),
                                  generation_error=error, independent_grid_error=measured))
        METRICS["zolotarev_inverse_square_root"] = summaries

    def test_strange_rational_force_against_dense_variation(self):
        mass = self.m.ms
        offsets = torch.arange(12)
        even = (12 * self.m.even[:, None] + offsets).flatten()
        odd = (12 * self.m.odd[:, None] + offsets).flatten()
        rhs = torch.randn(even.shape, dtype=CD, generator=self.rng)
        rhs /= torch.linalg.vector_norm(rhs)

        def exact(gauge):
            full = self.m.dirac(gauge, mass)
            schur = (full[even][:, even] - full[even][:, odd] @
                     torch.linalg.solve(full[odd][:, odd], full[odd][:, even]))
            eigenvalues, vectors = torch.linalg.eigh(dagger(schur) @ schur)
            projected = dagger(vectors) @ rhs
            return (projected.abs().square() * eigenvalues.rsqrt()).sum().item(), eigenvalues

        expected, eigs = exact(self.u)
        terms = inverse_power_terms(0.5, eigs[0].item() * 0.9, eigs[-1].item() * 1.1, order=24)
        action, gradient = rational_action_gradient(self.m, self.u, mass, rhs, terms)
        self.assertAlmostEqual(action, expected, delta=1e-11)
        direction = torch.randn(self.p.shape, dtype=RD, generator=self.rng)
        direction /= torch.linalg.vector_norm(direction)
        eps = 1e-5
        plus = exact(self.m.drift(self.u, direction, eps))[0]
        minus = exact(self.m.drift(self.u, direction, -eps))[0]
        finite = (plus - minus) / (2 * eps)
        algebra = torch.einsum("vma,aij->vmij", direction.to(CD), self.m.t)
        analytic = (gradient.conj() * (1j * algebra @ self.u)).real.sum().item()
        self.assertGreater(abs(finite), 1e-5)
        self.assertAlmostEqual(analytic, finite, delta=1e-8)
        METRICS["strange_rational_force_absolute_error"] = abs(analytic - finite)

    def test_two_plus_one_pseudofermion_trajectory(self):
        model = PseudofermionHMC()
        fields = model.refresh(self.u, self.rng)
        interval = (0.004, 4.)
        terms = inverse_power_terms(0.5, *interval, order=64)
        dense_energy = model.endpoint_energy(self.u, self.p, fields)
        sparse_energy = model.matrix_free_endpoint_energy(self.u, self.p, fields, terms, interval)
        self.assertAlmostEqual(sparse_energy, dense_energy, delta=1e-9)
        METRICS["matrix_free_endpoint_absolute_error"] = abs(sparse_energy - dense_energy)
        def force(links):
            return model.md_force(links, fields)
        direction = torch.randn(self.p.shape, dtype=RD, generator=self.rng)
        direction /= torch.linalg.vector_norm(direction)
        eps = 2e-5
        plus = model.endpoint_energy(model.drift(self.u, direction, eps), self.p, fields)
        minus = model.endpoint_energy(model.drift(self.u, direction, -eps), self.p, fields)
        finite = (plus - minus) / (2 * eps)
        analytic = float((force(self.u) * direction).sum())
        self.assertAlmostEqual(analytic, finite, delta=2e-7)
        u1, p1 = model.integrate(self.u, self.p, 0.04, 1, "omelyan", force)
        u2, p2 = model.integrate(u1, -p1, 0.04, 1, "omelyan", force)
        torch.testing.assert_close(u2, self.u, atol=2e-12, rtol=0)
        torch.testing.assert_close(p2, -self.p, atol=2e-11, rtol=0)
        u_new, item = model.trajectory(self.u, self.rng, 0.04, 1, "omelyan")
        self.assertTrue(item["accepted"])
        self.assertGreater(float((u_new - self.u).abs().max()), 1e-3)
        METRICS["pseudofermion_force_absolute_error"] = abs(analytic - finite)
        METRICS["pseudofermion_trajectory_delta_h"] = item["delta_h"]

    def test_matrix_free_refresh_and_endpoint(self):
        sparse = MatrixFreePseudofermionHMC()
        dense = PseudofermionHMC()
        seed = 831
        actual_l, actual_s = sparse.refresh(self.u, torch.Generator().manual_seed(seed))
        rng = torch.Generator().manual_seed(seed)
        full_l = dense.dirac(self.u, dense.ml)
        e, o = dense.even_dofs, dense.odd_dofs
        schur_l = full_l[e][:, e] - full_l[e][:, o] @ torch.linalg.solve(
            full_l[o][:, o], full_l[o][:, e])
        eta_l = torch.randn(actual_l.shape, dtype=CD, generator=rng).flatten()
        eta_s = torch.randn(actual_s.shape, dtype=CD, generator=rng).flatten()
        values, vectors, _ = dense._normal_spectrum(
            self.u, dense.ms, dense.field_strength(self.u), True)
        exact_l = dagger(schur_l) @ eta_l
        exact_s = vectors @ (values.pow(0.25) * (dagger(vectors) @ eta_s))
        torch.testing.assert_close(actual_l.flatten(), exact_l, atol=2e-11, rtol=2e-11)
        torch.testing.assert_close(actual_s.flatten(), exact_s, atol=2e-11, rtol=2e-11)
        error = abs(sparse.endpoint_energy(self.u, self.p, (actual_l, actual_s)) -
                    dense.endpoint_energy(self.u, self.p, (exact_l, exact_s)))
        self.assertLess(error, 1e-9)
        METRICS["matrix_free_refresh_endpoint_error"] = error
        METRICS["matrix_free_rational_poles"] = dict(endpoint=len(sparse.endpoint_terms),
                                                     refresh=len(sparse.refresh_terms))
        self.assertLess(len(sparse.endpoint_terms), 128)
        self.assertLess(len(sparse.refresh_terms), 128)


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
