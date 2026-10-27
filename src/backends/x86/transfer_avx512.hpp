#pragma once

#if defined(__AVX512F__)
#include <immintrin.h>
#include <cstddef>

namespace lqcd_native::x86 {

// One fine spin/color component, 24 coarse basis vectors. A site tile stays
// in registers across all vectors, instead of loading/storing the fine field
// 24 times. Unaligned masked accesses also cover odd aggregate extents.
inline void prolongate_component_avx512(int sites, const float *basis,
                                       const float *coarse, float *real, float *imag) {
    for (int first = 0; first < sites; first += 16) {
        const int remaining = sites - first;
        const __mmask16 mask = remaining >= 16 ? (__mmask16)0xffff
                                              : (__mmask16)((1u << remaining) - 1);
        __m512 re = _mm512_maskz_loadu_ps(mask, real + first);
        __m512 im = _mm512_maskz_loadu_ps(mask, imag + first);
        for (int vector = 0; vector < 24; vector++) {
            const float *row = basis + (size_t)vector * 2 * sites + first;
            const __m512 br = _mm512_maskz_loadu_ps(mask, row);
            const __m512 bi = _mm512_maskz_loadu_ps(mask, row + sites);
            const __m512 zr = _mm512_set1_ps(coarse[2 * vector]);
            const __m512 zi = _mm512_set1_ps(coarse[2 * vector + 1]);
            re = _mm512_add_ps(re, _mm512_fmsub_ps(br, zr, _mm512_mul_ps(bi, zi)));
            im = _mm512_add_ps(im, _mm512_fmadd_ps(br, zi, _mm512_mul_ps(bi, zr)));
        }
        _mm512_mask_storeu_ps(real + first, mask, re);
        _mm512_mask_storeu_ps(imag + first, mask, im);
    }
}

} // namespace lqcd_native::x86
#endif
