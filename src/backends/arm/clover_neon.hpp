#pragma once
#include "wilson_sve.hpp"
#if defined(__aarch64__)
#include <arm_neon.h>
namespace lqcd_native::arm {
// Raw SoA clover/inverse matrices, four physical sites per NEON vector.
// Source and output are separate (as required by the existing clover caller).
inline void clover_range_neon(int B, const float *matrix, const float *src,
                              float *out, int begin, int end) {
#if defined(__ARM_FEATURE_SVE)
    if (sve_enabled()) {
        clover_range_sve(B,matrix,src,out,begin,end);
        return;
    }
#endif
    for (int a = 0; a < 12; ++a) {
        int s = begin;
        for (; s + 4 <= end; s += 4) {
            float32x4_t yr = vdupq_n_f32(0), yi = yr;
            for (int j = 0; j < 6; ++j) {
                const float *m = matrix + (a * 6 + j) * 2 * B + s;
                const float *x = src + 2 * ((a / 6) * 6 + j) * B + s;
                const auto mr = vld1q_f32(m), mi = vld1q_f32(m + B);
                const auto xr = vld1q_f32(x), xi = vld1q_f32(x + B);
                yr = vaddq_f32(yr, vsubq_f32(vmulq_f32(mr, xr), vmulq_f32(mi, xi)));
                yi = vaddq_f32(yi, vaddq_f32(vmulq_f32(mr, xi), vmulq_f32(mi, xr)));
            }
            vst1q_f32(out + 2 * a * B + s, yr);
            vst1q_f32(out + (2 * a + 1) * B + s, yi);
        }
        for (; s < end; ++s) {
            float yr = 0, yi = 0;
            for (int j = 0; j < 6; ++j) {
                const float *m = matrix + (a * 6 + j) * 2 * B + s;
                const float *x = src + 2 * ((a / 6) * 6 + j) * B + s;
                yr += m[0] * x[0] - m[B] * x[B];
                yi += m[0] * x[B] + m[B] * x[0];
            }
            out[2 * a * B + s] = yr;
            out[(2 * a + 1) * B + s] = yi;
        }
    }
}
} // namespace lqcd_native::arm
#endif
