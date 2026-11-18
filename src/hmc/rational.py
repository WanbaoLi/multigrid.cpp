"""Positive-pole quadrature reference for fractional normal-operator powers."""
from __future__ import annotations

import math

import numpy as np
import torch

from .shifted import solve_multi_shift, solve_shifted


def inverse_power_terms(power, lower, upper, order=16):
    """Return (shift, weight) pairs for x**(-power) over a spectral interval.

    Split the Stieltjes integral at the geometric center of the interval.
    Fourth-power changes of variables regularize both tails in the three
    fractional powers used for action and pseudofermion refresh.
    """
    if power not in (0.25, 0.5, 0.75) or not 0 < lower <= upper < math.inf or order < 1:
        raise ValueError("Invalid fractional power, spectral interval or quadrature order")
    split = math.sqrt(lower) * math.sqrt(upper)
    nodes, weights = np.polynomial.legendre.leggauss(order)
    t = (1 + nodes) / 2
    prefactor = (2 * math.sin(math.pi * power) / math.pi) * split ** (1 - power)
    low_weights = prefactor * weights * t ** (3 - 4 * power)
    high_weights = prefactor * weights * t ** (4 * power - 5)
    shifts = np.concatenate((split * t ** 4, split / t ** 4))
    return tuple(zip(shifts.tolist(), np.concatenate((low_weights, high_weights)).tolist()))


def apply_rational(apply, rhs, terms, tol=1e-12, *, comm=None):
    """Apply the partial fraction and return the largest shifted residual."""
    shifts, weights = zip(*terms)
    solutions, residuals = solve_multi_shift(apply, rhs, shifts, tol, comm=comm)
    result = torch.zeros_like(rhs)
    for solution, weight in zip(solutions, weights):
        result.add_(solution, alpha=weight)
    return result, max(residuals)


def zolotarev_inverse_sqrt(lower, upper, tol, max_poles=64):
    """Find positive (n-1,n) partial fractions for the inverse square root."""
    from scipy.special import ellipj, ellipk

    if not 0 < lower < upper < math.inf or not 0 < tol < 1:
        raise ValueError("Invalid Zolotarev spectral interval or tolerance")
    parameter = 1. - lower / upper
    if parameter >= 1.:
        raise ValueError("Spectral ratio is too large for FP64 elliptic coefficients")
    period = ellipk(parameter)
    points = np.geomspace(lower, upper, 32769)
    root = np.sqrt(points)
    for n in range(1, max_poles + 1):
        # Chiu, Physics Letters B 744 (2015), Appendix A, (n-1,n).
        sn, cn, _, _ = ellipj(np.arange(1, 2 * n) * (period / (2 * n)), parameter)
        offsets = np.square(sn / cn)
        poles, zeros = offsets[::2], offsets[1::2]
        residues = []
        for i, pole in enumerate(poles):
            # The interlacing zeros and poles give positive residues.
            rest = np.concatenate((poles[:i], poles[i + 1:]))
            log_residue = np.log(np.abs(zeros - pole)).sum() - np.log(np.abs(rest - pole)).sum()
            residues.append(math.exp(log_residue) * math.sqrt(lower))
        shifts = poles * lower
        relative = root * sum(weight / (points + shift) for shift, weight in zip(shifts, residues))
        scale = 2. / (relative.min() + relative.max())
        coefficients = tuple((float(shift), float(scale * weight)) for shift, weight in zip(shifts, residues))
        error = float(np.max(np.abs(root * sum(weight / (points + shift)
                                                for shift, weight in coefficients) - 1.)))
        if error <= tol:
            return coefficients, error
    raise ArithmeticError("Zolotarev inverse square root missed the checked error target")


def checked_rational_terms(interval, endpoint_order=64, *, md_order=32, zolotarev=False):
    """Choose fixed refresh, endpoint and MD expansions on a tested scalar grid."""
    points = np.geomspace(*interval, 4097)

    def grid_error(power, terms):
        approximation = sum(weight / (points + shift) for shift, weight in terms)
        return float(np.max(np.abs(approximation * points ** power - 1)))

    def choose(power):
        for order in (*range(8, endpoint_order, 4), endpoint_order):
            terms = inverse_power_terms(power, *interval, order=order)
            error = grid_error(power, terms)
            if error <= 1e-12:
                return terms, error
        raise ArithmeticError("Endpoint or refresh rational approximation exceeds grid tolerance")

    refresh, err_refresh = choose(0.75)
    md = inverse_power_terms(0.5, *interval, order=md_order)
    err_md = grid_error(0.5, md)
    if zolotarev:
        endpoint, err_endpoint = zolotarev_inverse_sqrt(*interval, 2.5e-13, endpoint_order)
        md, err_md = zolotarev_inverse_sqrt(*interval, max(5e-14, .5 * err_md), endpoint_order)
    else:
        endpoint, err_endpoint = choose(0.5)
    return md, endpoint, refresh, dict(endpoint=err_endpoint, refresh=err_refresh, md=err_md)


def rational_action_gradient(model, gauge, mass, rhs, terms, tol=1e-12):
    """Return the fixed-pseudofermion quadratic action and its link gradient."""
    links = gauge.detach().requires_grad_(True)
    clover = model.clover_blocks(model.field_strength(links), mass)
    schur = model.prepare_even_schur(links, mass, clover)

    def normal(vec):
        return model.even_normal_from_schur(schur, vec)

    shifts, weights = zip(*terms)
    if len(shifts) == 1:
        solutions = [solve_shifted(normal, rhs, shifts[0], tol)[0]]
    else:
        solutions, _ = solve_multi_shift(normal, rhs, shifts, tol)
    action = sum(weight * (rhs.conj() * solution).real.sum().item()
                 for weight, solution in zip(weights, solutions))
    surrogate = 0.
    batch_size = 8
    for first in range(0, len(weights), batch_size):
        last = min(first + batch_size, len(weights))
        # The derivative of the inverse contributes -x† (dA) x at fixed x.
        image = schur(torch.stack(solutions[first:last])).reshape(last - first, -1)
        quadratic = (image.real.square() + image.imag.square()).sum(dim=1)
        coefficients = torch.tensor(weights[first:last], dtype=quadratic.dtype, device=quadratic.device)
        surrogate = surrogate - (coefficients * quadratic).sum()
    gradient, = torch.autograd.grad(surrogate, links)
    return action, gradient
