"""Optional native CPU kernels for the Schur stencil and gauge drift."""
import ctypes
from functools import lru_cache
import os
from pathlib import Path

import torch


@lru_cache(maxsize=None)
def _apply_functions(path):
    library = ctypes.CDLL(str(Path(path).resolve()))
    apply = library.lqcd_hmc_schur_apply
    apply.argtypes = [ctypes.c_int64, ctypes.c_double, ctypes.c_int] + [ctypes.c_void_p] * 7
    apply.restype = None
    normal = getattr(library, "lqcd_hmc_normal_apply", None)
    if normal is not None:
        normal.argtypes = apply.argtypes + [ctypes.c_void_p]
        normal.restype = None
    return apply, normal


@lru_cache(maxsize=None)
def _pade_drift_function(path):
    function = ctypes.CDLL(str(Path(path).resolve())).lqcd_hmc_pade_drift
    function.argtypes = [ctypes.c_int64, ctypes.c_double, ctypes.c_int] + [ctypes.c_void_p] * 3
    function.restype = ctypes.c_int
    return function


def native_pade_drift(gauge, momenta, step, library):
    if (gauge.device.type != "cpu" or gauge.dtype != torch.complex128 or gauge.shape[-2:] != (3, 3) or
            momenta.device.type != "cpu" or momenta.dtype != torch.float64 or
            momenta.shape != gauge.shape[:-2] + (8,)):
        raise ValueError("Native gauge drift requires CPU complex128 links and matching float64 momenta")
    field = gauge.detach().resolve_conj().contiguous()
    momenta = momenta.detach().contiguous()
    result = torch.empty_like(field)
    kernel = _pade_drift_function(str(library))
    outside = kernel(field.numel() // 9, step, torch.get_num_threads(), field.data_ptr(),
                     momenta.data_ptr(), result.data_ptr())
    return None if outside else result


def prepare_native_schur(hopping, even_clover, odd_inverse, kappa):
    path = os.environ.get("LQCD_HMC_SCHUR_LIBRARY")
    if not path or even_clover.device.type != "cpu" or even_clover.dtype != torch.complex128:
        return None, None
    apply, normal_apply = _apply_functions(path)
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

    def normal(spinor):
        field = spinor.resolve_conj().contiguous()
        output = torch.empty_like(field)
        scratch = torch.empty_like(field)
        intermediate = torch.empty_like(field)
        normal_apply(half, kappa, threads, neighbors.data_ptr(), links.data_ptr(), even.data_ptr(),
                     inverse.data_ptr(), field.data_ptr(), scratch.data_ptr(),
                     intermediate.data_ptr(), output.data_ptr())
        return output

    enabled = normal_apply is not None and os.environ.get("LQCD_HMC_SPLIT_NORMAL") != "1"
    return run, normal if enabled else None
