"""FP64 reference for the shifted normal solves needed by a rational action."""
from __future__ import annotations

import math

import torch


@torch.no_grad()
def solve_shifted(apply, rhs, shift, tol=1e-12, maxiter=1000):
    """Solve (A + shift I)x=b for one shift and check the true residual."""
    if not math.isfinite(shift) or shift < 0 or not 0 < tol < 1 or maxiter < 1:
        raise ValueError("Invalid shifted solve parameters")
    x = torch.zeros_like(rhs)
    r = rhs.clone()
    p = r.clone()
    rho = (r.real.square() + r.imag.square()).sum().item()
    if not math.isfinite(rho):
        raise ArithmeticError("Nonfinite right-hand side norm")
    if rho == 0:
        return x, 0, 0.0
    b_norm = math.sqrt(rho)
    threshold = tol * b_norm
    for iteration in range(1, maxiter + 1):
        image = apply(p) + shift * p
        curvature = (p.real * image.real + p.imag * image.imag).sum().item()
        if not math.isfinite(curvature) or curvature <= 0:
            raise ArithmeticError("Nonpositive shifted CG curvature")
        alpha = rho / curvature
        x.add_(p, alpha=alpha)
        r.add_(image, alpha=-alpha)
        new_rho = (r.real.square() + r.imag.square()).sum().item()
        if not math.isfinite(new_rho):
            raise ArithmeticError("Nonfinite shifted CG residual")
        if math.sqrt(new_rho) <= threshold:
            r = rhs - apply(x) - shift * x
            norm = math.sqrt((r.real.square() + r.imag.square()).sum().item())
            if not math.isfinite(norm):
                raise ArithmeticError("Nonfinite true shifted CG residual")
            if norm <= threshold:
                return x, iteration, norm / b_norm
            p = r.clone()
            rho = norm ** 2
        else:
            p.mul_(new_rho / rho).add_(r)
            rho = new_rho
    raise ArithmeticError(f"Shifted CG failed to reach relative residual {tol:g} in {maxiter} iterations")


@torch.no_grad()
def solve_multi_shift(apply, rhs, shifts, tol=1e-12, maxiter=1000):
    """Solve all positive shifts with a shared CG recurrence and true-residual checks."""
    shifts = tuple(shifts)
    if (not shifts or not all(math.isfinite(s) and s >= 0 for s in shifts) or
            not 0 < tol < 1 or maxiter < 1):
        raise ValueError("Invalid multi-shift solve parameters")
    solutions = [torch.zeros_like(rhs) for _ in shifts]
    directions = [rhs.clone() for _ in shifts]
    active = list(range(len(shifts)))
    zeta = [1.] * len(shifts)
    previous_zeta = zeta.copy()
    previous_alpha, previous_beta = 1., 0.
    base_shift = min(shifts)
    r = rhs.clone()
    p = r.clone()
    rho = (r.real.square() + r.imag.square()).sum().item()
    if not math.isfinite(rho):
        raise ArithmeticError("Nonfinite right-hand side norm")
    if rho == 0:
        return solutions, [0.] * len(shifts)
    b_norm = math.sqrt(rho)
    threshold = tol * b_norm
    for _ in range(maxiter):
        image = apply(p) + base_shift * p
        curvature = (p.real * image.real + p.imag * image.imag).sum().item()
        if not math.isfinite(curvature) or curvature <= 0:
            break
        alpha = rho / curvature
        r.add_(image, alpha=-alpha)
        new_rho = (r.real.square() + r.imag.square()).sum().item()
        if not math.isfinite(new_rho):
            break
        beta = new_rho / rho
        norm = math.sqrt(new_rho)
        remaining = []
        for i in active:
            old, current = previous_zeta[i], zeta[i]
            denominator = (old * previous_alpha * (1 + (shifts[i] - base_shift) * alpha) +
                           alpha * previous_beta * (old - current))
            if not math.isfinite(denominator) or denominator == 0 or current == 0:
                continue
            next_zeta = current * old * previous_alpha / denominator
            ratio = next_zeta / current
            solutions[i].add_(directions[i], alpha=alpha * ratio)
            if abs(next_zeta) * norm > threshold:
                directions[i].mul_(beta * ratio ** 2).add_(r, alpha=next_zeta)
                previous_zeta[i], zeta[i] = current, next_zeta
                remaining.append(i)
        if not remaining or norm <= threshold:
            break
        active = remaining
        p.mul_(beta).add_(r)
        rho = new_rho
        previous_alpha, previous_beta = alpha, beta

    residuals = []
    for i, (x, shift) in enumerate(zip(solutions, shifts)):
        residual = rhs - apply(x) - shift * x
        norm = math.sqrt((residual.real.square() + residual.imag.square()).sum().item())
        if not math.isfinite(norm) or norm > threshold:
            solutions[i], _, relative = solve_shifted(apply, rhs, shift, tol, maxiter)
        else:
            relative = norm / b_norm
        residuals.append(relative)
    return solutions, residuals
