#pragma once
#if defined(__ARM_FEATURE_SVE)
#include <arm_sve.h>
#include <cstddef>
#include <cstdint>
#include <cstdlib>

namespace lqcd_native::arm {
inline bool sve_transfer_enabled() {
    // Process-wide opt-in, independent of the Wilson addressing experiment.
    static const bool enabled = [] {
        const char *value = std::getenv("LQCD_ARM_SVE_TRANSFER");
        return value && value[0] == '1' && value[1] == '\0';
    }();
    return enabled;
}

// One fine spin/color component: basis[24][real/imag][sites], interleaved
// coarse[24][real/imag]. Initial output is part of the sum (fine += P*coarse).
// Inputs and outputs must not alias. Preserve vector order and FP32 arithmetic
// of the portable path; no horizontal reductions or approximate arithmetic.
inline void prolongate_component_sve(int sites, const float *basis,
                                     const float *coarse, float *real, float *imag) {
    for (int first = 0; first < sites; first += svcntw()) {
        const svbool_t pg = svwhilelt_b32((uint64_t)first, (uint64_t)sites);
        svfloat32_t re = svld1_f32(pg, real + first);
        svfloat32_t im = svld1_f32(pg, imag + first);
        for (int vector = 0; vector < 24; ++vector) {
            const float *row = basis + (size_t)vector * 2 * sites + first;
            const svfloat32_t br = svld1_f32(pg, row);
            const svfloat32_t bi = svld1_f32(pg, row + sites);
            const float zr = coarse[2 * vector], zi = coarse[2 * vector + 1];
            const svfloat32_t dr = svsub_f32_x(
                pg, svmul_n_f32_x(pg, br, zr), svmul_n_f32_x(pg, bi, zi));
            const svfloat32_t di = svadd_f32_x(
                pg, svmul_n_f32_x(pg, br, zi), svmul_n_f32_x(pg, bi, zr));
            re = svadd_f32_x(pg, re, dr);
            im = svadd_f32_x(pg, im, di);
        }
        svst1_f32(pg, real + first, re);
        svst1_f32(pg, imag + first, im);
    }
}
} // namespace lqcd_native::arm
#endif
