#pragma once
#if defined(__AVX512F__)
#include <immintrin.h>
#include <algorithm>
#include <cstddef>
#include <climits>
namespace lqcd_native::x86 {
// Packed coefficients: [ceil(B/16) tiles][144 scalar planes][16 lanes].
// Packed callers align the site origin to a tile; masks select both ends.
template <bool Packed>
inline const float *wilson_coefficient_tile(const float *base, int B, int plane, int site) {
    if constexpr (Packed)
        return base + ((size_t)(site / 16) * 144 + plane) * 16;
    else
        return base + (size_t)plane * B + site;
}
inline __mmask16 wilson_range_mask(int site, int begin, int end) {
    const unsigned high = (1u << std::min(16, end - site)) - 1;
    const unsigned low = (1u << std::max(0, begin - site)) - 1;
    return (__mmask16)(high & ~low);
}

// Source and output must be distinct: each output row consumes all six
// input rows of its chirality. Inactive site lanes are left untouched.
template <bool Packed = false>
inline void clover_tile_avx512(int B, const float *diag, const float *src,
                              float *out, int site, __mmask16 mask) {
    const __m512 zero = _mm512_setzero_ps();
    for (int a = 0; a < 12; a++) {
        __m512 yr = zero, yi = zero;
        for (int j = 0; j < 6; j++) {
            const int component = (a / 6) * 6 + j;
            const __m512 xr = _mm512_maskz_loadu_ps(mask, src + component * 2 * B + site);
            const __m512 xi = _mm512_maskz_loadu_ps(mask, src + (component * 2 + 1) * B + site);
            const __m512 ar = _mm512_maskz_loadu_ps(mask, wilson_coefficient_tile<Packed>(diag, B, (a * 6 + j) * 2, site));
            const __m512 ai = _mm512_maskz_loadu_ps(mask, wilson_coefficient_tile<Packed>(diag, B, (a * 6 + j) * 2 + 1, site));
            yr = _mm512_add_ps(yr, _mm512_sub_ps(_mm512_mul_ps(ar, xr), _mm512_mul_ps(ai, xi)));
            yi = _mm512_add_ps(yi, _mm512_add_ps(_mm512_mul_ps(ar, xi), _mm512_mul_ps(ai, xr)));
        }
        _mm512_mask_storeu_ps(out + a * 2 * B + site, mask, yr);
        _mm512_mask_storeu_ps(out + (a * 2 + 1) * B + site, mask, yi);
    }
}
template <bool Packed = false>
inline void clover_range_avx512(int B, const float *matrix, const float *src,
                                float *out, int begin, int end) {
    for (int site = Packed ? (begin / 16) * 16 : begin; site < end; site += 16)
        clover_tile_avx512<Packed>(B, matrix, src, out, site, wilson_range_mask(site, begin, end));
}

// Index metadata stays pointer-width on the global lattice. Narrow on load
// only after the caller has established that the complete float field fits
// signed int32 element indices. Masked tails do not form an invalid high pointer.
template <class Offset>
inline __m512i wilson_indices_avx512(const Offset *indices, __mmask16 mask, int lanes) {
    static_assert(sizeof(Offset) == 4 || sizeof(Offset) == 8, "unsupported site offset");
    if constexpr (sizeof(Offset) == 4)
        return _mm512_maskz_loadu_epi32(mask, indices);
    else {
        const __m512i low = _mm512_maskz_loadu_epi64((__mmask8)(mask & 255), indices);
        __m512i high = _mm512_setzero_si512();
        if (lanes > 8)
            high = _mm512_maskz_loadu_epi64((__mmask8)(mask >> 8), indices + 8);
        return _mm512_inserti64x4(_mm512_castsi256_si512(_mm512_cvtepi64_epi32(low)),
                                  _mm512_cvtepi64_epi32(high), 1);
    }
}

// Common local/global arithmetic. Clover reads the current block at
// center_offset; hopping offsets already contain the appropriate site base.
// Source/output must be distinct except for opposite-parity hopping-only calls.
template <bool Clover, class Offset, bool Packed, bool Planned>
inline void wilson_avx512_impl(int B, const float *diag, const float *links,
                         const Offset *neighbor, const int gp[4][4],
                         const float gr[4][4], const float gi[4][4],
                         const float *src, float *out, int begin, int end,
                         size_t center_offset, const int *local_load_offsets) {
    const __m512 zero = _mm512_setzero_ps();
    for (int site = Packed ? (begin / 16) * 16 : begin; site < end; site += 16) {
        const int lanes = std::min(16, end - site);
        const __mmask16 mask = wilson_range_mask(site, begin, end);
        if constexpr (Clover)
            clover_tile_avx512<Packed>(B, diag, src + center_offset, out, site, mask);
        else
            for (int a = 0; a < 24; a++)
                _mm512_mask_storeu_ps(out + a * B + site, mask, zero);
        for (int dir = 0; dir < 8; dir++) {
            const __m512i indices = wilson_indices_avx512(neighbor + dir * B + site, mask, lanes);
            const __mmask16 valid = mask & _mm512_cmp_epi32_mask(indices, _mm512_setzero_si512(), _MM_CMPINT_GE);
            // Optional local plan is certified by the caller: every valid
            // neighbor in a half block equals target_site + delta. A tile
            // crossing halves, or an unrepresentable base, keeps the gather.
            bool contiguous = false;
            std::ptrdiff_t base = 0;
            if constexpr (Planned) {
                const int first_active = std::max(site, begin);
                const int last_active = std::min(site + 16, end) - 1;
                if (B >= 2 && (first_active < B / 2) == (last_active < B / 2)) {
                    const int half = first_active < B / 2 ? 0 : 1;
                    const int delta = local_load_offsets[half * 8 + dir];
                    if (delta != INT_MIN) {
                        base = (std::ptrdiff_t)site + delta;
                        contiguous = base >= 0 && base < B;
                    }
                }
            }
            auto load_component = [&](int component) {
                if constexpr (Planned) {
                    if (!valid)
                        return zero;
                    if (contiguous)
                        return _mm512_maskz_loadu_ps(valid, src + (size_t)component * B + base);
                }
                return _mm512_mask_i32gather_ps(
                    zero, valid, indices, src + (size_t)component * B, 4);
            };
            const float sign = dir % 2 ? 1.f : -1.f;
            for (int spin = 0; spin < 2; spin++) {
                const int paired = gp[dir / 2][spin];
                const __m512 pr = _mm512_set1_ps(sign * gr[dir / 2][spin]);
                const __m512 pi = _mm512_set1_ps(sign * gi[dir / 2][spin]);
                __m512 zr[3], zi[3];
                // Each projected input colour serves all three output colours.
                for (int j = 0; j < 3; j++) {
                    const __m512 vr = load_component((spin * 3 + j) * 2);
                    const __m512 vi = load_component(((spin * 3 + j) * 2 + 1));
                    const __m512 wr = load_component((paired * 3 + j) * 2);
                    const __m512 wi = load_component(((paired * 3 + j) * 2 + 1));
                    zr[j] = _mm512_sub_ps(_mm512_add_ps(vr, _mm512_mul_ps(pr, wr)), _mm512_mul_ps(pi, wi));
                    zi[j] = _mm512_add_ps(_mm512_add_ps(vi, _mm512_mul_ps(pr, wi)), _mm512_mul_ps(pi, wr));
                }
                const __m512 rr = _mm512_set1_ps(sign * gr[dir / 2][paired]);
                const __m512 ri = _mm512_set1_ps(sign * gi[dir / 2][paired]);
                for (int color = 0; color < 3; color++) {
                    __m512 hr = zero, hi = zero;
                    for (int j = 0; j < 3; j++) {
                        const int plane = (dir * 9 + color * 3 + j) * 2;
                        const __m512 ar = _mm512_maskz_loadu_ps(mask,
                            wilson_coefficient_tile<Packed>(links, B, plane, site));
                        const __m512 ai = _mm512_maskz_loadu_ps(mask,
                            wilson_coefficient_tile<Packed>(links, B, plane + 1, site));
                        hr = _mm512_add_ps(hr, _mm512_sub_ps(_mm512_mul_ps(ar, zr[j]), _mm512_mul_ps(ai, zi[j])));
                        hi = _mm512_add_ps(hi, _mm512_add_ps(_mm512_mul_ps(ar, zi[j]), _mm512_mul_ps(ai, zr[j])));
                    }
                    float *yr = out + (spin * 3 + color) * 2 * B + site, *yi = yr + B;
                    float *lr = out + (paired * 3 + color) * 2 * B + site, *li = lr + B;
                    _mm512_mask_storeu_ps(yr, mask, _mm512_add_ps(_mm512_maskz_loadu_ps(mask, yr), hr));
                    _mm512_mask_storeu_ps(yi, mask, _mm512_add_ps(_mm512_maskz_loadu_ps(mask, yi), hi));
                    _mm512_mask_storeu_ps(lr, mask, _mm512_add_ps(_mm512_maskz_loadu_ps(mask, lr),
                        _mm512_sub_ps(_mm512_mul_ps(rr, hr), _mm512_mul_ps(ri, hi))));
                    _mm512_mask_storeu_ps(li, mask, _mm512_add_ps(_mm512_maskz_loadu_ps(mask, li),
                        _mm512_add_ps(_mm512_mul_ps(rr, hi), _mm512_mul_ps(ri, hr))));
                }
            }
        }
    }
}
// Dispatch once per call: the null-plan specialization contains only the
// original gathers, with no plan/valid/contiguous branches in component loops.
template <bool Clover, class Offset, bool Packed = false>
inline void wilson_avx512(int B, const float *diag, const float *links,
                         const Offset *neighbor, const int gp[4][4],
                         const float gr[4][4], const float gi[4][4],
                         const float *src, float *out, int begin, int end,
                         size_t center_offset, const int *local_load_offsets = nullptr) {
    if (local_load_offsets)
        wilson_avx512_impl<Clover, Offset, Packed, true>(
            B, diag, links, neighbor, gp, gr, gi, src, out, begin, end,
            center_offset, local_load_offsets);
    else
        wilson_avx512_impl<Clover, Offset, Packed, false>(
            B, diag, links, neighbor, gp, gr, gi, src, out, begin, end,
            center_offset, nullptr);
}
// Preserve the local entry point for SAP callers and component tests.
template <bool Clover>
inline void wilson_local_avx512(int B, const float *diag, const float *links,
                               const int *neighbor, const int gp[4][4],
                               const float gr[4][4], const float gi[4][4],
                               const float *src, float *out, int begin, int end) {
    wilson_avx512<Clover>(B, diag, links, neighbor, gp, gr, gi, src, out, begin, end, 0);
}
} // namespace lqcd_native::x86
#endif
