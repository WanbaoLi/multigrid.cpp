#pragma once
#include "../../support/aligned_workspace.hpp"
#include <cstddef>
#include <vector>
namespace lqcd_native::portable {
// Split-complex block fields; OpenMP SIMD over sites. Half-spin projection
// computes two spin components and reconstructs the other two exactly.
template <bool Local, class Offset, bool Clover = true>
inline void wilson_clover_block_impl(int cb, int B, const float *diag, const float *links,
                                     const Offset *neighbor, const int gp[4][4],
                                     const float gr[4][4], const float gi[4][4], const float *src,
                                     float *out, int site_begin, int site_end) {
    const float *cl = diag, *u = links;
    for (int a = 0; a < 12; a++) {
        float *yr = out + (a * 2) * B, *yi = yr + B;
#pragma omp simd
        for (int s = site_begin; s < site_end; s++) {
            yr[s] = 0;
            yi[s] = 0;
        }
        if constexpr (Clover)
            for (int j = 0; j < 6; j++) {
                int c = (a / 6) * 6 + j;
                const float *xr = src + (Local ? 0 : (size_t)cb * 24 * B) + c * 2 * B, *xi = xr + B;
                const float *ar = cl + (a * 6 + j) * 2 * B, *ai = ar + B;
#pragma omp simd
                for (int s = site_begin; s < site_end; s++) {
                    yr[s] += ar[s] * xr[s] - ai[s] * xi[s];
                    yi[s] += ar[s] * xi[s] + ai[s] * xr[s];
                }
            }
    }
    // Each OpenMP worker reuses its scratch storage. Every element is
    // overwritten below; no per-block allocation/zero initialization.
    static thread_local std::vector<float, lqcd_native::WorkspaceAllocator<float>> half;
    half.resize((size_t)2 * B);
    for (int dir = 0; dir < 8; dir++)
        for (int sp = 0; sp < 2; sp++)
            for (int color = 0; color < 3; color++) {
                int gs = gp[dir / 2][sp];
                float sign = dir % 2 ? 1.f : -1.f;
                float pr = sign * gr[dir / 2][sp], pi = sign * gi[dir / 2][sp];
                const Offset *nb = neighbor + dir * B;
                float *hr = half.data(), *hi = hr + B;
#pragma omp simd
                for (int s = site_begin; s < site_end; s++) {
                    hr[s] = 0;
                    hi[s] = 0;
                }
                for (int j = 0; j < 3; j++) {
                    const float *ar = u + (dir * 9 + color * 3 + j) * 2 * B, *ai = ar + B;
                    const float *vrp = src + (sp * 3 + j) * 2 * B, *vip = vrp + B;
                    const float *wrp = src + (gs * 3 + j) * 2 * B, *wip = wrp + B;
#pragma omp simd
                    for (int s = site_begin; s < site_end; s++) {
                        // Full neighbours already include the blocked site base;
                        // local neighbours are site offsets with -1 at the face.
                        const Offset n = nb[s];
                        if (n < 0)
                            continue;
                        float vr = vrp[n], vi = vip[n];
                        float wr = wrp[n], wi = wip[n];
                        float zr = vr + pr * wr - pi * wi, zi = vi + pr * wi + pi * wr;
                        hr[s] += ar[s] * zr - ai[s] * zi;
                        hi[s] += ar[s] * zi + ai[s] * zr;
                    }
                }
                float *yr = out + (sp * 3 + color) * 2 * B, *yi = yr + B;
                float *lr = out + (gs * 3 + color) * 2 * B, *li = lr + B;
                float rr = sign * gr[dir / 2][gs], ri = sign * gi[dir / 2][gs];
#pragma omp simd
                for (int s = site_begin; s < site_end; s++) {
                    yr[s] += hr[s];
                    yi[s] += hi[s];
                    lr[s] += rr * hr[s] - ri * hi[s];
                    li[s] += rr * hi[s] + ri * hr[s];
                }
            }
}
} // namespace lqcd_native::portable
