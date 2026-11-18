"""FP64 reference for the shifted normal solves needed by a rational action."""
from __future__ import annotations

import math

import numpy as np
import torch


def _scalar_sum(comm):
    if comm is None:
        return float
    send = np.empty(1, dtype=np.float64)
    receive = np.empty_like(send)

    def reduce(value):
        send[0] = value
        comm.Allreduce(send, receive)
        return float(receive[0])

    return reduce


def _norm2(vector):
    return (vector.real.square() + vector.imag.square()).sum().item()


def _inner(left, right):
    return (left.real * right.real + left.imag * right.imag).sum().item()


def _real_buffer_dot(left, right):
    # Use a real dot over the interleaved components. This avoids allocating
    # separate real and imaginary products, and does not use a complex BLAS dot.
    lhs = torch.view_as_real(left.resolve_conj()).reshape(-1)
    rhs = lhs if right is left else torch.view_as_real(right.resolve_conj()).reshape(-1)
    return torch.dot(lhs, rhs).item()


def _dot_norm2(vector):
    return _real_buffer_dot(vector, vector)


@torch.no_grad()
def solve_shifted(apply, rhs, shift, tol=1e-12, maxiter=1000, *, comm=None, real_dot=False):
    """Solve (A + shift I)x=b for one shift and check the true residual."""
    if not math.isfinite(shift) or shift < 0 or not 0 < tol < 1 or maxiter < 1:
        raise ValueError("Invalid shifted solve parameters")
    x = torch.zeros_like(rhs)
    r = rhs.clone()
    p = r.clone()
    reduce = _scalar_sum(comm)
    inner = _real_buffer_dot if real_dot else _inner
    norm2 = _dot_norm2 if real_dot else _norm2
    rho = reduce(norm2(r))
    if not math.isfinite(rho):
        raise ArithmeticError("Nonfinite right-hand side norm")
    if rho == 0:
        return x, 0, 0.0
    b_norm = math.sqrt(rho)
    threshold = tol * b_norm
    for iteration in range(1, maxiter + 1):
        image = apply(p) + shift * p
        curvature = reduce(inner(p, image))
        if not math.isfinite(curvature) or curvature <= 0:
            raise ArithmeticError("Nonpositive shifted CG curvature")
        alpha = rho / curvature
        x.add_(p, alpha=alpha)
        r.add_(image, alpha=-alpha)
        new_rho = reduce(norm2(r))
        if not math.isfinite(new_rho):
            raise ArithmeticError("Nonfinite shifted CG residual")
        if math.sqrt(new_rho) <= threshold:
            r = rhs - apply(x) - shift * x
            # Use the same explicit FP64 residual norm for both paths.
            norm = math.sqrt(reduce(_norm2(r)))
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
def solve_multi_shift(apply, rhs, shifts, tol=1e-12, maxiter=1000, *, comm=None, real_dot=False):
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
    reduce = _scalar_sum(comm)
    inner = _real_buffer_dot if real_dot else _inner
    norm2 = _dot_norm2 if real_dot else _norm2
    rho = reduce(norm2(r))
    if not math.isfinite(rho):
        raise ArithmeticError("Nonfinite right-hand side norm")
    if rho == 0:
        return solutions, [0.] * len(shifts)
    b_norm = math.sqrt(rho)
    threshold = tol * b_norm
    for _ in range(maxiter):
        image = apply(p) + base_shift * p
        curvature = reduce(inner(p, image))
        if not math.isfinite(curvature) or curvature <= 0:
            break
        alpha = rho / curvature
        r.add_(image, alpha=-alpha)
        new_rho = reduce(norm2(r))
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

    local_norms = [_norm2(rhs - apply(x) - shift * x) for x, shift in zip(solutions, shifts)]
    if comm is not None:
        # Verify every pole but reduce all squared norms in one collective.
        packed = np.asarray(local_norms, dtype=np.float64)
        norms = np.empty_like(packed)
        comm.Allreduce(packed, norms)
    else:
        norms = local_norms
    residuals = []
    for i, (norm2, shift) in enumerate(zip(norms, shifts)):
        norm = math.sqrt(norm2)
        if not math.isfinite(norm) or norm > threshold:
            solutions[i], _, relative = solve_shifted(apply, rhs, shift, tol, maxiter, comm=comm, real_dot=real_dot)
        else:
            relative = norm / b_norm
        residuals.append(relative)
    return solutions, residuals
