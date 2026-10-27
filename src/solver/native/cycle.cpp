#include "hierarchy.hpp"
#include "kernels.hpp"

using namespace lqcd_native::detail;

void NativeMG::Impl::restrict_to_coarse(const FloatField &fine, FloatField &cr) const {
    cr.resize((size_t)(end_aggregate - first_aggregate) * coarse_dof * 2);
    // Diagnostic candidate: retain the original double-accumulation path by
    // default. The float sum spans all six components of each chirality.
    const bool reduce_float = setting("LQCD_RESTRICT_FLOAT", 0) != 0;
    if (reduce_float) {
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            for (int cs = 0; cs < 2; cs++)
                for (int v = 0; v < 24; v++) {
                    float re = 0, im = 0;
                    for (int j = 0; j < 6; j++) {
                        int a = cs * 6 + j;
                        const float *br = basis_block(cb) + ((a * 24 + v) * 2) * block_sites,
                                    *bi = br + block_sites;
                        const float *fr = fine.data() + ((size_t)cb * 24 + a * 2) * block_sites,
                                    *fi = fr + block_sites;
#pragma omp simd reduction(+ : re, im)
                        for (int s = 0; s < block_sites; s++) {
                            re += br[s] * fr[s] + bi[s] * fi[s];
                            im += br[s] * fi[s] - bi[s] * fr[s];
                        }
                    }
                    cr[((cb - first_aggregate) * coarse_dof + cs * 24 + v) * 2] = re;
                    cr[((cb - first_aggregate) * coarse_dof + cs * 24 + v) * 2 + 1] = im;
                }
        return;
    }
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int cs = 0; cs < 2; cs++)
            for (int v = 0; v < 24; v++) {
                double re = 0, im = 0;
                for (int j = 0; j < 6; j++) {
                    int a = cs * 6 + j;
                    const float *br = basis_block(cb) + ((a * 24 + v) * 2) * block_sites,
                                *bi = br + block_sites;
                    const float *fr = fine.data() + ((size_t)cb * 24 + a * 2) * block_sites,
                                *fi = fr + block_sites;
#pragma omp simd reduction(+ : re, im)
                    for (int s = 0; s < block_sites; s++) {
                        re += (double)br[s] * fr[s] + (double)bi[s] * fi[s];
                        im += (double)br[s] * fi[s] - (double)bi[s] * fr[s];
                    }
                }
                cr[((cb - first_aggregate) * coarse_dof + cs * 24 + v) * 2] = re;
                cr[((cb - first_aggregate) * coarse_dof + cs * 24 + v) * 2 + 1] = im;
            }
}

void NativeMG::Impl::prolongate_add(const FloatField &cr, FloatField &fine) const {
#if defined(LQCD_NATIVE_AVX512_TRANSFER)
    const bool tile = setting("LQCD_TRANSFER_TILE", 1) != 0;
#endif
#if defined(LQCD_NATIVE_SVE_TRANSFER)
    const bool sve_tile = lqcd_native::kernels::sve_transfer_enabled();
#endif
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int a = 0; a < 12; a++) {
            float *fr = fine.data() + ((size_t)cb * 24 + a * 2) * block_sites,
                  *fi = fr + block_sites;
#if defined(LQCD_NATIVE_AVX512_TRANSFER)
            if (tile) {
                const float *vectors = basis_block(cb) + (a * 24 * 2) * block_sites;
                const float *coefficients = cr.data() +
                    ((size_t)(cb - first_aggregate) * coarse_dof + (a / 6) * 24) * 2;
                lqcd_native::kernels::prolongate_component_avx512(
                    block_sites, vectors, coefficients, fr, fi);
                continue;
            }
#endif
#if defined(LQCD_NATIVE_SVE_TRANSFER)
            if (sve_tile) {
                const float *vectors = basis_block(cb) + (a * 24 * 2) * block_sites;
                const float *coefficients = cr.data() +
                    ((size_t)(cb - first_aggregate) * coarse_dof + (a / 6) * 24) * 2;
                lqcd_native::kernels::prolongate_component_sve(
                    block_sites, vectors, coefficients, fr, fi);
                continue;
            }
#endif
            for (int v = 0; v < 24; v++) {
                const float *br = basis_block(cb) + ((a * 24 + v) * 2) * block_sites,
                            *bi = br + block_sites;
                float zr = cr[((cb - first_aggregate) * coarse_dof + (a / 6) * 24 + v) * 2],
                      zi = cr[((cb - first_aggregate) * coarse_dof + (a / 6) * 24 + v) * 2 + 1];
#pragma omp simd
                for (int s = 0; s < block_sites; s++) {
                    fr[s] += br[s] * zr - bi[s] * zi;
                    fi[s] += br[s] * zi + bi[s] * zr;
                }
            }
        }
}

void NativeMG::Impl::precondition(const Field &b, Field &out) {
    encode_fine(b, fine_rhs);
    apply_vcycle(fine_rhs, fine_correction);
    decode_fine(fine_correction, out);
}

void NativeMG::Impl::apply_vcycle(const FloatField &source, FloatField &dest) {
    dest.resize(fine_sites * 24);
#pragma omp parallel for schedule(static)
    for (size_t j = (size_t)first_aggregate * 24 * block_sites;
         j < (size_t)end_aggregate * 24 * block_sites; j++)
        dest[j] = 0;
    // Coarse correction followed by red-black SAP (paper Algorithm 2).
    double t = wall_seconds();
    restrict_to_coarse(source, coarse_rhs);
    restrict_seconds += wall_seconds() - t;
    t = wall_seconds();
    coarse_solve(coarse_rhs, coarse_correction);
    coarse_seconds += wall_seconds() - t;
    t = wall_seconds();
    prolongate_add(coarse_correction, dest);
    prolong_seconds += wall_seconds() - t;
    t = wall_seconds();
    sap(source, dest, sap_cycles);
    sap_seconds += wall_seconds() - t;
}

void NativeMG::apply(const Field &x, Field &y) const {
    impl->apply_double(x, y);
}

void NativeMG::precondition(const Field &b, Field &x) {
    impl->precondition(b, x);
}
