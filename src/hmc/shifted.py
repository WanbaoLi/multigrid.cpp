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
