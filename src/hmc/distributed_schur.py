"""Time-slab MPI exchange for the two native Wilson–Clover Schur phases."""
import ctypes
from functools import lru_cache
import math
from pathlib import Path

import torch


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
