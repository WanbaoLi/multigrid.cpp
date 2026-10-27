#pragma once
#include "../../support/aligned_workspace.hpp"
#include <cstddef>
#include <vector>
#include <cstdlib>
#include <climits>
#include <limits>
#include "../portable/wilson_kernel.hpp"
#include "wilson_sve.hpp"
namespace lqcd_native::arm {
using portable::wilson_clover_block_impl;

// Read once per process; changing this environment variable after the first
// kernel application is intentionally unsupported (diagnostic A/B switch).
inline bool wilson_simd_enabled() {
    static const bool enabled = [] {
        const char *value = std::getenv("LQCD_WILSON_SIMD");
        return !value || std::atoi(value) != 0;
    }();
    return enabled;
}
// The generic kernel above is retained as portable fallback and test oracle.
template <bool Clover>
inline void wilson_local_dispatch(int cb, int B, const float *diag, const float *links,
                                 const int *inner, const int gp[4][4], const float gr[4][4],
                                 const float gi[4][4], const float *src, float *out,
                                 int begin, int end, const int *local_plan = nullptr) {
#if defined(__ARM_FEATURE_SVE)
    if (wilson_simd_enabled() && sve_enabled()) {
        wilson_sve<true,int,Clover>(cb,B,diag,links,inner,gp,gr,gi,src,out,begin,end,
                                    sve_planned_enabled() ? local_plan : nullptr);
        return;
    }
#endif
    wilson_clover_block_impl<true, int, Clover>(cb, B, diag, links, inner, gp, gr, gi,
                                               src, out, begin, end);
}
// False means the caller must retain pointer-width generic indexing. Check
// geometry before touching any data, including for dummy-pointer guard tests.
template <bool Clover>
inline bool try_wilson_global_simd(int cb, int B, const float *diag, const float *links,
                                  const std::ptrdiff_t *neighbor, const int gp[4][4],
                                  const float gr[4][4], const float gi[4][4],
                                  const float *src, float *out, int begin, int end,
                                  size_t full_float_count, const int *compact_neighbors = nullptr) {
#if defined(__ARM_FEATURE_SVE)
    if (full_float_count <= (size_t)INT_MAX && wilson_simd_enabled() && sve_enabled()) {
        // The compact table is the hierarchy's checked copy of neighbor.
        // Keep this size guard before inspecting either pointer (including
        // oversized-geometry tests that deliberately pass dummy pointers).
        if (sve_planned_enabled() && compact_neighbors)
            wilson_sve<false,int,Clover>(cb,B,diag,links,compact_neighbors,gp,gr,gi,src,out,begin,end);
        else
            wilson_sve<false,std::ptrdiff_t,Clover>(cb,B,diag,links,neighbor,gp,gr,gi,src,out,begin,end);
        return true;
    }
#endif
    return false;
}
template <bool Clover>
inline void wilson_global_dispatch(int cb, int B, const float *diag, const float *links,
                                   const std::ptrdiff_t *neighbor, const int gp[4][4],
                                   const float gr[4][4], const float gi[4][4],
                                   const float *src, float *out, int begin, int end,
                                   size_t full_float_count, const int *compact_neighbors = nullptr) {
    if (!try_wilson_global_simd<Clover>(cb, B, diag, links, neighbor, gp, gr, gi,
                                      src, out, begin, end, full_float_count, compact_neighbors))
        wilson_clover_block_impl<false, std::ptrdiff_t, Clover>(
            cb, B, diag, links, neighbor, gp, gr, gi, src, out, begin, end);
}
inline void wilson_clover_block(int cb, int B, const float *diag, const float *links,
                                const int *inner, const std::ptrdiff_t *neighbor,
                                const int gp[4][4], const float gr[4][4], const float gi[4][4],
                                const float *src, float *out, bool local,
                                size_t full_float_count = std::numeric_limits<size_t>::max(),
                                const int *local_plan = nullptr,
                                const int *compact_neighbors = nullptr) {
    // Dispatch outside the SIMD loops: SAP retains 32-bit local gathers,
    // while the full lattice uses pointer-width precomputed addresses.
    if (local)
        wilson_local_dispatch<true>(cb, B, diag, links, inner, gp, gr, gi, src, out, 0, B, local_plan);
    else
        wilson_global_dispatch<true>(cb, B, diag, links, neighbor, gp, gr, gi, src, out, 0, B, full_float_count, compact_neighbors);
}
// A full-field hop with a restricted output range. Source indexing remains
// global/blocked, so this also handles owned sites adjacent to an MPI face.
inline void wilson_clover_global_range(int cb, int B, const float *diag, const float *links,
                                       const std::ptrdiff_t *neighbor, const int gp[4][4],
                                       const float gr[4][4], const float gi[4][4],
                                       const float *src, float *out, int begin, int end,
                                       size_t full_float_count = std::numeric_limits<size_t>::max(),
                                       const int *compact_neighbors = nullptr) {
    wilson_global_dispatch<true>(cb, B, diag, links, neighbor, gp, gr, gi, src, out, begin, end, full_float_count, compact_neighbors);
}
// EO-local block ranges are contiguous halves; hopping-only skips all
// diagonal reads, so an uninitialized same-parity input is never accessed.
inline void wilson_clover_local_range(int cb, int B, const float *diag, const float *links,
                                      const int *inner, const int gp[4][4], const float gr[4][4],
                                      const float gi[4][4], const float *src, float *out,
                                      int parity, bool clover, const int *local_plan = nullptr) {
    const int begin = parity * (B / 2), end = begin + B / 2;
    if (clover)
        wilson_local_dispatch<true>(cb, B, diag, links, inner, gp, gr, gi, src, out,
                                                  begin, end, local_plan);
    else
        wilson_local_dispatch<false>(cb, B, diag, links, inner, gp, gr, gi, src, out,
                                                   begin, end, local_plan);
}
} // namespace lqcd_native::arm
