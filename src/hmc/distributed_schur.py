"""Time-slab MPI exchange for the two native Wilson–Clover Schur phases."""
import ctypes
from functools import lru_cache
import math
from pathlib import Path

import torch
from torch.autograd.function import once_differentiable

from .distributed_gauge import time_faces
from .reference import dagger, gamma_matrices


class _ProjectedTimeFaces(torch.autograd.Function):
    """Exchange half-spinor time faces and return each cotangent to its owner."""

    @staticmethod
    def forward(ctx, first, last, comm):
        ctx.comm = comm
        first, last = (field.detach().resolve_conj().contiguous() for field in (first, last))
        lower, upper = torch.empty_like(last), torch.empty_like(first)
        prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
        comm.Sendrecv(first.numpy(), prev, 22, upper.numpy(), nxt, 22)
        comm.Sendrecv(last.numpy(), nxt, 23, lower.numpy(), prev, 23)
        return lower, upper

    @staticmethod
    @once_differentiable
    def backward(ctx, lower, upper):
        comm = ctx.comm
        lower, upper = (field.detach().resolve_conj().contiguous() for field in (lower, upper))
        first, last = torch.empty_like(upper), torch.empty_like(lower)
        prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
        comm.Sendrecv(upper.numpy(), nxt, 24, first.numpy(), prev, 24)
        comm.Sendrecv(lower.numpy(), prev, 25, last.numpy(), nxt, 25)
        return first, last, None


@lru_cache(maxsize=None)
def _kernels(path, packed_faces=False):
    library = ctypes.CDLL(str(Path(path).resolve()))
    suffix = "_faces" if packed_faces else ""
    odd = getattr(library, "lqcd_hmc_schur_odd" + suffix)
    even = getattr(library, "lqcd_hmc_schur_even" + suffix)
    prefix = [ctypes.c_int64, ctypes.c_double, ctypes.c_int]
    extra = 2 if packed_faces else 0
    odd.argtypes = prefix + [ctypes.c_void_p] * (5 + extra)
    even.argtypes = prefix + [ctypes.c_void_p] * (6 + extra)
    odd.restype = even.restype = None
    return odd, even


def prepare_slab_schur(model, gauge, mass, clover, comm, library):
    """Prepare an MPI Schur apply on owned even fields in lexicographic order.

    Setup takes a global gauge and Clover field as an oracle fixture.
    The returned apply keeps only local coefficients and two spinor faces.
    Use a dedicated communicator and call the operator in the same order on
    every rank. The halo contains complete spinors for this initial transport.
    """
    if comm.size < 2 or model.lattice[3] % comm.size != 0:
        raise ValueError("Use at least two equal time slabs")
    face = math.prod(model.lattice[:3]) // 2
    local_sites = model.volume // (2 * comm.size)
    first = comm.rank * local_sites
    end = first + local_sites
    total = model.volume // 2
    lower, upper = (first - face) % total, end % total
    prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
    odd_kernel, even_kernel = _kernels(str(library))
    threads = torch.get_num_threads()

    def pack(terms):
        global_indices = torch.stack([index for index, _, _ in terms])
        local = (global_indices >= first) & (global_indices < end)
        left = (global_indices >= lower) & (global_indices < lower + face)
        right = (global_indices >= upper) & (global_indices < upper + face)
        if not (local | left | right).all().item():
            raise RuntimeError("Stencil references a site outside the local time slab and halo")
        indices = torch.where(local, global_indices - first,
                              torch.where(left, local_sites + global_indices - lower,
                                          local_sites + face + global_indices - upper))
        links = torch.stack([link for _, link, _ in terms])
        return indices.contiguous(), links.contiguous()

    with torch.no_grad():
        terms, even_blocks, odd_inverse, kappa = model.prepare_schur_coefficients(
            gauge, mass, clover, slice(first, end))
        neighbors_e, links_e = pack(terms[0])
        neighbors_o, links_o = pack(terms[1])
        even_blocks = even_blocks.contiguous()
        odd_inverse = odd_inverse.contiguous()

    def exchange(field, target, tag):
        target[:local_sites].copy_(field)
        comm.Sendrecv(field[:face].numpy(), dest=prev, sendtag=tag,
                      recvbuf=target[local_sites+face:].numpy(), source=nxt, recvtag=tag)
        comm.Sendrecv(field[-face:].numpy(), dest=nxt, sendtag=tag + 1,
                      recvbuf=target[local_sites:local_sites+face].numpy(), source=prev, recvtag=tag + 1)

    def apply(spinor):
        if spinor.numel() != 12 * local_sites or spinor.dtype != torch.complex128 or spinor.device.type != "cpu":
            raise ValueError("Incorrect owned Schur field")
        even = spinor.detach().resolve_conj().reshape(local_sites, 12).contiguous()
        odd = torch.empty_like(even)
        halo = torch.empty((local_sites + 2 * face, 12), dtype=even.dtype)
        out = torch.empty_like(even)
        exchange(even, halo, 0)
        odd_kernel(local_sites, kappa, threads, neighbors_o.data_ptr(), links_o.data_ptr(),
                   odd_inverse.data_ptr(), halo.data_ptr(), odd.data_ptr())
        exchange(odd, halo, 2)
        even_kernel(local_sites, kappa, threads, neighbors_e.data_ptr(), links_e.data_ptr(),
                    even_blocks.data_ptr(), even.data_ptr(), halo.data_ptr(), out.data_ptr())
        return out.reshape_as(spinor)

    return apply


def prepare_local_slab_schur(extended_gauge, clover, mass, comm, library, *, projected=True,
                             packed_faces=False, compact_spin=False, projected_force_faces=False):
    """Prepare Schur from only an owned Clover slab and its gauge faces.

    The returned operator differentiates through link and spinor halo adjoints
    when autograd is enabled. Under no_grad it uses the native half-spin phases.
    """
    if extended_gauge.ndim != 7 or extended_gauge.shape[0] < 3:
        raise ValueError("Expected t,z,y,x,mu,row,column gauge with time faces")
    if packed_faces and not projected:
        raise ValueError("Packed faces require the temporal Wilson projector")
    if projected_force_faces and not compact_spin:
        raise ValueError("Projected force faces require compact spin contractions")
    nt = extended_gauge.shape[0] - 2
    spatial = tuple(extended_gauge.shape[1:4])
    if any(n % 2 for n in spatial) or nt * comm.size % 2:
        raise ValueError("Even global Wilson–Clover extents required")
    grid = torch.arange((nt + 2) * math.prod(spatial)).reshape(nt + 2, *spatial)
    area = math.prod(spatial)
    face = area // 2
    local_sites = nt * face
    t = (torch.arange(nt + 2) + comm.rank * nt - 1) % (nt * comm.size)
    parity = t[:, None, None, None]
    for axis, extent in enumerate(spatial, start=1):
        shape = [1, 1, 1, 1]
        shape[axis] = extent
        parity = parity + torch.arange(extent).reshape(shape)
    parity = parity % 2
    # Opposite-parity spinor indices follow the [lower halo, owned, upper halo]
    # field order. Each parity has exactly half of every spatial time slice.
    parity_indices = torch.empty_like(grid)
    targets = []
    for p in (0, 1):
        mask = parity == p
        parity_indices[mask] = torch.arange((nt + 2) * face)
        targets.append(grid[mask][face:-face])
    links = extended_gauge.reshape(-1, 4, 3, 3)
    owned_grid = grid[1:-1]
    gamma = gamma_matrices()
    eye4 = torch.eye(4, dtype=links.dtype)
    if compact_spin:
        # In the DeGrand–Rossi basis the upper-lower block is a signed
        # permutation. X and Y exchange the two lower spin components.
        spins = torch.arange(2)
        half_projectors = []
        for mu in range(4):
            swap = mu < 2
            partner = 3 - spins if swap else 2 + spins
            for sign in (-1, 1):
                phase = (sign * gamma[mu, spins, partner]).reshape(2, 1)
                half_projectors.append((phase, swap))
    hopping = []
    for target in targets:
        terms = []
        offset = target - area
        for mu in range(4):
            if mu == 3:
                plus = (owned_grid + area).flatten()[offset]
                minus = (owned_grid - area).flatten()[offset]
            else:
                plus = torch.roll(owned_grid, -1, 3 - mu).flatten()[offset]
                minus = torch.roll(owned_grid, 1, 3 - mu).flatten()[offset]
            forward, backward = links[target, mu], dagger(links[minus, mu])
            if mu == 3:
                times = t[torch.div(target, area, rounding_mode="floor")]
                sf = torch.where(times == nt * comm.size - 1, -1., 1.)
                sb = torch.where(times == 0, -1., 1.)
                forward = forward * sf[:, None, None]
                backward = backward * sb[:, None, None]
            terms.extend(((parity_indices.flatten()[plus], forward, eye4 - gamma[mu]),
                          (parity_indices.flatten()[minus], backward, eye4 + gamma[mu])))
        hopping.append(terms)
    clover = clover.reshape(nt * area, 2, 6, 6)
    even_clover = clover[targets[0] - area]
    odd_inverse = torch.linalg.inv(clover[targets[1] - area])
    kappa = 1 / (2 * (mass + 4))
    odd_kernel, even_kernel = _kernels(str(library), packed_faces)
    threads = torch.get_num_threads()
    with torch.no_grad():
        neighbors_e, neighbors_o = [torch.stack([i for i, _, _ in terms]) for terms in hopping]
        if packed_faces:
            for indices in (neighbors_e, neighbors_o):
                indices.copy_(torch.where(indices < face, -indices - 1,
                    torch.where(indices >= face + local_sites, face + local_sites - indices - 1,
                                indices - face)))
        links_e, links_o = [torch.stack([u for _, u, _ in terms]) for terms in hopping]
        blocks_e, blocks_o = even_clover.detach().contiguous(), odd_inverse.detach().contiguous()
    scratch_odd = links.new_empty((local_sites, 4, 3))
    prev, nxt = (comm.rank - 1) % comm.size, (comm.rank + 1) % comm.size
    if packed_faces:
        from mpi4py import MPI
        sends = links.new_empty((2, face, 2, 3))
        lower, upper = torch.empty_like(sends[0]), torch.empty_like(sends[0])
        to_prev, to_next = sends[0].numpy(), sends[1].numpy()
        receive_lower, receive_upper = lower.numpy(), upper.numpy()
    elif projected:
        extended = links.new_zeros((nt + 2, face, 4, 3))
        send = links.new_empty((face, 2, 3))
        received = torch.empty_like(send)
        send_buffer, receive_buffer = send.numpy(), received.numpy()

    def halo(spinor):
        owned = spinor.reshape(nt, face, 4, 3)
        if packed_faces:
            torch.sub(owned[0, :, :2], owned[0, :, 2:], out=sends[0])
            torch.add(owned[-1, :, :2], owned[-1, :, 2:], out=sends[1])
            requests = (comm.Irecv(receive_upper, nxt, 20), comm.Irecv(receive_lower, prev, 21),
                        comm.Isend(to_prev, prev, 20), comm.Isend(to_next, nxt, 21))
            MPI.Request.Waitall(requests)
            return spinor, lower, upper
        if not projected:
            return time_faces(owned, comm),
        # The time gamma swaps the upper and lower spin pairs. Carry only
        # the pair consumed by the projector. The lower halo spins stay zero.
        extended[1:-1].copy_(owned)
        torch.sub(owned[0, :, :2], owned[0, :, 2:], out=send)
        comm.Sendrecv(send_buffer, prev, 20, receive_buffer, nxt, 20)
        extended[-1, :, :2].copy_(received)
        torch.add(owned[-1, :, :2], owned[-1, :, 2:], out=send)
        comm.Sendrecv(send_buffer, nxt, 21, receive_buffer, prev, 21)
        extended[0, :, :2].copy_(received)
        return extended,

    def torch_hop(spinor, terms):
        fields = spinor.reshape(-1, nt, face, 4, 3)
        batches = fields.shape[0]
        if projected_force_faces:
            neighbors = fields.reshape(batches, local_sites, 4, 3)
            first, second = fields.split(2, dim=-2)
            forward, backward = first - second, first + second
            lower, upper = _ProjectedTimeFaces.apply(forward[:, 0], backward[:, -1], comm)
            # A time hop preserves the lexicographic index within each
            # checkerboard slice because the spatial x extent is even.
            temporal = (torch.cat((forward[:, 1:], upper.unsqueeze(1)), dim=1),
                        torch.cat((lower.unsqueeze(1), backward[:, :-1]), dim=1))
        else:
            neighbors = time_faces(fields.transpose(0, 1), comm).transpose(0, 1).reshape(
                batches, (nt + 2) * face, 4, 3)
        if compact_spin:
            upper = spinor.new_zeros((batches, local_sites, 2, 3))
            lower = torch.zeros_like(upper)
            for direction, ((indices, link, _), (phase, swap)) in enumerate(zip(terms, half_projectors)):
                if projected_force_faces and direction >= 6:
                    half = temporal[direction - 6].reshape(batches, local_sites, 2, 3)
                else:
                    owned_indices = indices - face if projected_force_faces else indices
                    source_upper, source_lower = neighbors[:, owned_indices].split(2, dim=-2)
                    source_lower = source_lower.flip(-2) if swap else source_lower
                    half = source_upper + phase * source_lower
                projected = half @ link.transpose(-2, -1)
                reconstructed = phase.conj() * projected
                upper = upper + projected
                lower = lower + (reconstructed.flip(-2) if swap else reconstructed)
            result = torch.cat((upper, lower), dim=-2)
        else:
            result = spinor.new_zeros((batches, local_sites, 4, 3))
            for indices, link, projector in terms:
                result = result + projector @ (neighbors[:, indices] @ link.transpose(-2, -1))
        return (-kappa * result).reshape(-1, local_sites, 2, 6, 1)

    def apply(spinor):
        if torch.is_grad_enabled() or spinor.numel() != local_sites * 12:
            odd = odd_inverse @ torch_hop(spinor, hopping[1])
            even = even_clover @ spinor.reshape(-1, local_sites, 2, 6, 1)
            return (even - torch_hop(odd, hopping[0])).reshape_as(spinor)
        even = spinor.resolve_conj().contiguous()
        output = torch.empty_like(even)
        # The two blocking phases consume shared scratch in order. Return a
        # separate field because Krylov callers can retain previous results.
        extended_even = halo(even)
        odd_kernel(local_sites, kappa, threads, neighbors_o.data_ptr(), links_o.data_ptr(),
                   blocks_o.data_ptr(), *(part.data_ptr() for part in extended_even), scratch_odd.data_ptr())
        extended_odd = halo(scratch_odd)
        even_kernel(local_sites, kappa, threads, neighbors_e.data_ptr(), links_e.data_ptr(),
                    blocks_e.data_ptr(), even.data_ptr(), *(part.data_ptr() for part in extended_odd), output.data_ptr())
        return output

    return apply
