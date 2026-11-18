"""Positive-pole quadrature reference for fractional normal-operator powers."""
from __future__ import annotations

import math

import numpy as np
import torch

from .shifted import solve_shifted


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


def apply_rational(apply, rhs, terms, tol=1e-12):
    """Apply the partial fraction and return the largest shifted residual."""
    result = torch.zeros_like(rhs)
    worst_residual = 0.
    for shift, weight in terms:
        solution, _, residual = solve_shifted(apply, rhs, shift, tol)
        result.add_(solution, alpha=weight)
        worst_residual = max(worst_residual, residual)
    return result, worst_residual
