"""Sufficient positivity and Schur spectral bounds for heavy Wilson–Clover."""
from __future__ import annotations

import math

import torch


def positive_schur_bounds(even_clover, odd_clover, mass, *, comm=None):
    """Enclose the Schur normal spectrum, assuming unitary gauge links.

    Orthogonal spin projectors bound each directional hopping term by
    1/(mass+4). If the local Clover minimum exceeds their sum, the full
    operator is strictly accretive. Gamma-five Hermiticity then implies
    a positive determinant. The even-even block of the full inverse
    is the Schur inverse, so its norm shares the full inverse bound.
    """
    if not math.isfinite(mass) or mass <= -4:
        raise ValueError("Invalid Wilson mass")
    even = torch.linalg.eigvalsh(even_clover)
    odd = torch.linalg.eigvalsh(odd_clover)
    even_min, even_max = float(even.min()), float(even.max())
    odd_min, odd_max = float(odd.min()), float(odd.max())
    if comm is not None:
        extrema = comm.allgather((even_min, even_max, odd_min, odd_max))
        even_min = min(row[0] for row in extrema)
        even_max = max(row[1] for row in extrema)
        odd_min = min(row[2] for row in extrema)
        odd_max = max(row[3] for row in extrema)
    hopping = 4 / (mass + 4)
    padding = 64 * torch.finfo(even.dtype).eps * max(1., abs(even_max), abs(odd_max), hopping)
    gap = min(even_min, odd_min) - hopping - padding
    if not math.isfinite(gap) or gap <= 0:
        raise ArithmeticError("Local Clover bound cannot certify a positive strange determinant")
    upper = even_max + padding + hopping ** 2 / (odd_min - padding)
    return gap ** 2, upper ** 2
