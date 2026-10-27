#pragma once
#include <cstddef>
namespace lqcd_native::arm {
// One complex row-major matrix -> [column][real/imag][row].
inline void pack_coarse_columns(int n, const float *row_major, float *columns) {
    for (int row = 0; row < n; ++row)
        for (int col = 0; col < n; ++col) {
            columns[(size_t)(2*col)*n+row] = row_major[((size_t)row*n+col)*2];
            columns[(size_t)(2*col+1)*n+row] = row_major[((size_t)row*n+col)*2+1];
        }
}
}
#if defined(__ARM_FEATURE_SVE)
#include <arm_sve.h>
#include <cstdint>
namespace lqcd_native::arm {
// SVE lanes are independent output rows, so no horizontal sum is needed.
// Interleaved input/output ABI is unchanged. `add` extends an existing
// stencil sum, preserving direction then column accumulation order.
inline void coarse_gemv_sve(int n, const float *matrix, const float *input,
                            float *output, bool add) {
    for (int row = 0; row < n; row += svcntw()) {
        const auto pg = svwhilelt_b32((uint64_t)row, (uint64_t)n);
        svfloat32_t re = svdup_f32(0), im = svdup_f32(0);
        if (add) {
            const auto previous = svld2_f32(pg, output + 2*row);
            re = svget2_f32(previous, 0);
            im = svget2_f32(previous, 1);
        }
        for (int col = 0; col < n; ++col) {
            const auto mr = svld1_f32(pg, matrix + (size_t)(2*col)*n + row);
            const auto mi = svld1_f32(pg, matrix + (size_t)(2*col+1)*n + row);
            const float xr = input[2*col], xi = input[2*col+1];
            re = svadd_f32_x(pg,re,svsub_f32_x(pg,svmul_n_f32_x(pg,mr,xr),svmul_n_f32_x(pg,mi,xi)));
            im = svadd_f32_x(pg,im,svadd_f32_x(pg,svmul_n_f32_x(pg,mr,xi),svmul_n_f32_x(pg,mi,xr)));
        }
        svst2_f32(pg,output+2*row,svcreate2_f32(re,im));
    }
}
}
#endif
