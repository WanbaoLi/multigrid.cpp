"""Sufficient positivity and Schur spectral bounds for Wilson–Clover."""
from __future__ import annotations

import math

import torch


def cold_wilson_gap(temporal_extent, mass):
    """Smallest singular value with even extents and antiperiodic time."""
    angle = math.pi / temporal_extent
    c, s = math.cos(angle), math.sin(angle)
    # The squared free dispersion is affine in each cos(p_mu) with the
    # other cosines fixed. All extrema of the discrete cosine sets occur
    # at +/-1 in space and +/-cos(pi/T) in time.
    return min(math.hypot(mass + 4 - spatial_sum - temporal_cosine, s)
               for spatial_sum in (-3, -1, 1, 3) for temporal_cosine in (-c, c)) / (mass + 4)


def positive_schur_bounds(even_clover, odd_clover, mass, *, comm=None, cold_gap=None, links=None):
    """Enclose the Schur normal spectrum, assuming unitary gauge links.

    Orthogonal spin projectors bound each directional hopping term by
    1/(mass+4). If the local Clover minimum exceeds their sum, the full
    operator is strictly accretive. Gamma-five Hermiticity then implies
    a positive determinant. The even-even block of the full inverse
    is the Schur inverse, so its norm shares the full inverse bound.

    For a field near the free operator, the optional cold gap and
    Frobenius link deviations also bound its perturbation. The entire
    straight line between the two Dirac matrices is then nonsingular
    and gamma-five Hermitian, preserving the free determinant sign.
    """
    if not math.isfinite(mass) or mass <= -4:
        raise ValueError("Invalid Wilson mass")
    even = torch.linalg.eigvalsh(even_clover)
    odd = torch.linalg.eigvalsh(odd_clover)
    even_min, even_max = float(even.min()), float(even.max())
    odd_min, odd_max = float(odd.min()), float(odd.max())
    deviations = ()
    if cold_gap is not None:
        identity = torch.eye(3, dtype=links.dtype, device=links.device)
        link_delta = links - identity
        deviations = tuple(link_delta.abs().square().sum(dim=(-2, -1)).amax(dim=0).sqrt().tolist())
    local = (even_min, even_max, odd_min, odd_max, *deviations)
    extrema = [local] if comm is None else comm.allgather(local)
    if not all(math.isfinite(value) for row in extrema for value in row):
        raise ArithmeticError("Nonfinite input to the strange determinant certificate")
    if comm is not None:
        even_min = min(row[0] for row in extrema)
        even_max = max(row[1] for row in extrema)
        odd_min = min(row[2] for row in extrema)
        odd_max = max(row[3] for row in extrema)
        deviations = tuple(max(row[i] for row in extrema) for i in range(4, len(extrema[0])))
    hopping = 4 / (mass + 4)
    padding = 64 * torch.finfo(even.dtype).eps * max(1., abs(even_max), abs(odd_max), hopping)
    gap = min(even_min, odd_min) - hopping - padding
    if cold_gap is not None:
        clover_delta = max(abs(value - 1.) for value in (even_min, even_max, odd_min, odd_max))
        # Forward and backward Wilson projectors have orthogonal spin
        # ranges, hence one directional norm bound, not their sum.
        cold_bound = cold_gap - clover_delta - sum(deviations) / (mass + 4) - padding
        gap = max(gap, cold_bound)
    if not math.isfinite(gap) or gap <= 0 or odd_min <= padding:
        raise ArithmeticError("Local Clover bound cannot certify a positive strange determinant")
    upper = max(abs(even_min), abs(even_max)) + padding + hopping ** 2 / (odd_min - padding)
    return gap ** 2, upper ** 2
