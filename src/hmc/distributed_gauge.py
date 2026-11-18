"""Periodic time-slab link halos and local Wilson–Clover loop derivatives."""
import torch


class _TimeFaces(torch.autograd.Function):
    @staticmethod
    def forward(ctx, slab, comm):
        ctx.comm = comm
        slab = slab.detach().resolve_conj().contiguous()
        result = slab.new_empty((slab.shape[0] + 2, *slab.shape[1:]))
        result[1:-1].copy_(slab)
        prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
        comm.Sendrecv(slab[0].numpy(), prev, 10, result[-1].numpy(), nxt, 10)
        comm.Sendrecv(slab[-1].numpy(), nxt, 11, result[0].numpy(), prev, 11)
        return result

    @staticmethod
    def backward(ctx, extended_gradient):
        comm = ctx.comm
        prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
        extended_gradient = extended_gradient.detach().resolve_conj().contiguous()
        owned = extended_gradient[1:-1].clone()
        face = torch.empty_like(owned[0])
        comm.Sendrecv(extended_gradient[-1].numpy(), nxt, 12, face.numpy(), prev, 12)
        owned[0].add_(face)
        comm.Sendrecv(extended_gradient[0].numpy(), prev, 13, face.numpy(), nxt, 13)
        owned[-1].add_(face)
        return owned, None


def time_faces(slab, comm):
    """Append periodic time faces, returning their gradients to their owners."""
    if slab.device.type != "cpu" or slab.ndim < 2 or slab.shape[0] < 1:
        raise ValueError("Use a nonempty CPU time slab with time as the leading axis")
    return _TimeFaces.apply(slab, comm)


def _dagger(matrix):
    return matrix.conj().transpose(-1, -2)


def _loop(extended, directions, origin=(0, 0, 0, 0)):
    offset = list(origin)
    nt = extended.shape[0] - 2
    result = None
    for direction in directions:
        mu = abs(direction) - 1
        if direction < 0:
            offset[mu] -= 1
        t = 1 + offset[3]
        link = extended[t:t+nt, ..., mu, :, :]
        for axis in range(3):
            if offset[axis]:
                link = torch.roll(link, -offset[axis], 3 - axis)
        if direction < 0:
            link = _dagger(link)
        else:
            offset[mu] += 1
        result = link if result is None else result @ link
    return result


def owned_gauge_action(extended, beta):
    """Local summand of the plaquette action, including links in the halos."""
    total = 0.
    for m in range(1, 5):
        for n in range(1, m):
            loop = _loop(extended, (m, n, -m, -n))
            total = total + (1 - loop.diagonal(dim1=-2, dim2=-1).sum(-1).real / 3).sum()
    return beta * total


@torch.no_grad()
def owned_gauge_gradient(extended, beta):
    """Link derivative of the global plaquette action on owned sites."""
    gradient = []
    for mu in range(1, 5):
        origin = tuple(int(axis == mu) for axis in range(1, 5))
        staple = torch.zeros_like(extended[1:-1, ..., mu - 1, :, :])
        for nu in range(1, 5):
            if nu == mu:
                continue
            staple.add_(_loop(extended, (nu, -mu, -nu), origin))
            staple.add_(_loop(extended, (-nu, -mu, nu), origin))
        gradient.append((-beta / 3) * _dagger(staple))
    return torch.stack(gradient, dim=-3)


def owned_clover_strength(extended):
    """Return the six anti-Hermitian field strengths on owned sites."""
    field = []
    for m in range(1, 5):
        for n in range(1, m):
            paths = ((m, n, -m, -n), (n, -m, -n, m),
                     (-n, m, n, -m), (-m, -n, m, n))
            four_leaf = sum(_loop(extended, path) for path in paths)
            field.append((four_leaf - _dagger(four_leaf)) / 8)
    return field
