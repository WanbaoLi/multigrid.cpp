"""Optional native CPU Schur stencil for the non-differentiated Krylov path."""
import ctypes
from functools import lru_cache
import os
from pathlib import Path

import torch


@lru_cache(maxsize=None)
def _apply_function(path):
    apply = ctypes.CDLL(str(Path(path).resolve())).lqcd_hmc_schur_apply
    apply.argtypes = [ctypes.c_int64, ctypes.c_double, ctypes.c_int] + [ctypes.c_void_p] * 7
    apply.restype = None
    return apply


def prepare_native_schur(hopping, even_clover, odd_inverse, kappa):
    path = os.environ.get("LQCD_HMC_SCHUR_LIBRARY")
    if not path or even_clover.device.type != "cpu" or even_clover.dtype != torch.complex128:
        return None
    apply = _apply_function(path)
    with torch.no_grad():
        neighbors = torch.stack([index for terms in hopping for index, _, _ in terms]).contiguous()
        links = torch.stack([link for terms in hopping for _, link, _ in terms]).contiguous()
        even = even_clover.detach().contiguous()
        inverse = odd_inverse.detach().contiguous()
    half = even.shape[0]
    threads = torch.get_num_threads()
    def run(spinor):
        field = spinor.resolve_conj().contiguous()
        output = torch.empty_like(field)
        scratch = torch.empty_like(field)
        apply(half, kappa, threads, neighbors.data_ptr(), links.data_ptr(), even.data_ptr(),
              inverse.data_ptr(), field.data_ptr(), scratch.data_ptr(), output.data_ptr())
        return output

    return run
