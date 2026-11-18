"""Time-slab MPI exchange for the two native Wilson–Clover Schur phases."""
import ctypes
from functools import lru_cache
import math
from pathlib import Path

import torch

from .distributed_gauge import time_faces
from .reference import dagger, gamma_matrices


@lru_cache(maxsize=None)
def _kernels(path):
    library = ctypes.CDLL(str(Path(path).resolve()))
    odd = library.lqcd_hmc_schur_odd
    even = library.lqcd_hmc_schur_even
    prefix = [ctypes.c_int64, ctypes.c_double, ctypes.c_int]
    odd.argtypes = prefix + [ctypes.c_void_p] * 5
    even.argtypes = prefix + [ctypes.c_void_p] * 6
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


def prepare_local_slab_schur(extended_gauge, clover, mass, comm, library):
    """Prepare Schur from only an owned Clover slab and its gauge faces.

    The returned operator differentiates through link and spinor halo adjoints
    when autograd is enabled. Under no_grad it uses the native half-spin phases.
    """
    if extended_gauge.ndim != 7 or extended_gauge.shape[0] < 3:
        raise ValueError("Expected t,z,y,x,mu,row,column gauge with time faces")
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
    odd_kernel, even_kernel = _kernels(str(library))
    threads = torch.get_num_threads()
    with torch.no_grad():
        neighbors_e, neighbors_o = [torch.stack([i for i, _, _ in terms]) for terms in hopping]
        links_e, links_o = [torch.stack([u for _, u, _ in terms]) for terms in hopping]
        blocks_e, blocks_o = even_clover.detach().contiguous(), odd_inverse.detach().contiguous()

    def halo(spinor):
        return time_faces(spinor.reshape(nt, face, 4, 3), comm)

    def torch_hop(spinor, terms):
        neighbors = halo(spinor).reshape(-1, 4, 3)
        result = spinor.new_zeros((local_sites, 4, 3))
        for indices, link, projector in terms:
            result = result + projector @ (neighbors[indices] @ link.transpose(-2, -1))
        return (-kappa * result).reshape(local_sites, 2, 6, 1)

    def apply(spinor):
        if torch.is_grad_enabled():
            odd = odd_inverse @ torch_hop(spinor, hopping[1])
            even = even_clover @ spinor.reshape(local_sites, 2, 6, 1)
            return (even - torch_hop(odd, hopping[0])).reshape_as(spinor)
        even = spinor.resolve_conj().contiguous()
        odd = torch.empty_like(even)
        output = torch.empty_like(even)
        extended_even = halo(even)
        odd_kernel(local_sites, kappa, threads, neighbors_o.data_ptr(), links_o.data_ptr(),
                   blocks_o.data_ptr(), extended_even.data_ptr(), odd.data_ptr())
        extended_odd = halo(odd)
        even_kernel(local_sites, kappa, threads, neighbors_e.data_ptr(), links_e.data_ptr(),
                    blocks_e.data_ptr(), even.data_ptr(), extended_odd.data_ptr(), output.data_ptr())
        return output

    return apply
