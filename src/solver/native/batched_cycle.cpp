#include "hierarchy.hpp"
#include "kernels.hpp"
using namespace lqcd_native::detail;

void NativeMG::Impl::apply_vcycle_batch(const std::vector<const FloatField *> &sources,
                                        const std::vector<FloatField *> &destinations) {
    const int nrhs = sources.size();
    if (nrhs < 1 || nrhs > 12 || destinations.size() != sources.size())
        throw std::runtime_error("V-cycle batch requires one to twelve matching fields");
    if (nrhs == 1) {
        apply_vcycle(*sources[0], *destinations[0]);
        return;
    }
    if (batch_coarse_rhs.size() < (size_t)nrhs)
        batch_coarse_rhs.resize(nrhs);
    if (batch_coarse_correction.size() < (size_t)nrhs)
        batch_coarse_correction.resize(nrhs);
    for (int r = 0; r < nrhs; r++) {
        destinations[r]->resize(fine_sites * 24);
        batch_coarse_rhs[r].resize((size_t)(end_aggregate - first_aggregate) * coarse_dof * 2);
    }
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int r = 0; r < nrhs; r++)
            std::fill_n(destinations[r]->data() + (size_t)cb * 24 * block_sites, 24 * block_sites,
                        0.f);
    double t = wall_seconds();
    if (setting("LQCD_RESTRICT_FLOAT", 0)) {
        for (int r = 0; r < nrhs; r++)
            restrict_to_coarse(*sources[r], batch_coarse_rhs[r]);
    } else {
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            for (int r = 0; r < nrhs; r++)
                for (int cs = 0; cs < 2; cs++)
                    for (int v = 0; v < 24; v++) {
                        double re = 0, im = 0;
                        for (int j = 0; j < 6; j++) {
                            int a = cs * 6 + j;
                            const float *br = basis_block(cb) + (a * 24 + v) * 2 * block_sites,
                                        *bi = br + block_sites;
                            const float *fr = sources[r]->data() +
                                              ((size_t)cb * 24 + a * 2) * block_sites,
                                        *fi = fr + block_sites;
#pragma omp simd reduction(+ : re, im)
                            for (int s = 0; s < block_sites; s++) {
                                re += (double)br[s] * fr[s] + (double)bi[s] * fi[s];
                                im += (double)br[s] * fi[s] - (double)bi[s] * fr[s];
                            }
                        }
                        batch_coarse_rhs[r][((cb - first_aggregate) * coarse_dof + cs * 24 + v) *
                                            2] = re;
                        batch_coarse_rhs[r]
                                        [((cb - first_aggregate) * coarse_dof + cs * 24 + v) * 2 +
                                         1] = im;
                    }
    }
    restrict_seconds += wall_seconds() - t;
    t = wall_seconds();
    for (int r = 0; r < nrhs; r++)
        coarse_solve(batch_coarse_rhs[r], batch_coarse_correction[r]);
    coarse_seconds += wall_seconds() - t;
    t = wall_seconds();
#if defined(LQCD_NATIVE_AVX512_TRANSFER)
    const bool tile = setting("LQCD_TRANSFER_TILE", 1) != 0;
#endif
#if defined(LQCD_NATIVE_SVE_TRANSFER)
    const bool sve_tile = lqcd_native::kernels::sve_transfer_enabled();
#endif
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int r = 0; r < nrhs; r++)
            for (int a = 0; a < 12; a++) {
                float *fr = destinations[r]->data() + ((size_t)cb * 24 + a * 2) * block_sites,
                      *fi = fr + block_sites;
#if defined(LQCD_NATIVE_AVX512_TRANSFER)
                if (tile) {
                    const float *vectors =
                        basis_block(cb) + (a * 24 * 2) * block_sites;
                    const float *coefficients =
                        batch_coarse_correction[r].data() +
                        ((size_t)(cb - first_aggregate) * coarse_dof + (a / 6) * 24) * 2;
                    lqcd_native::kernels::prolongate_component_avx512(block_sites, vectors,
                                                                  coefficients, fr, fi);
                    continue;
                }
#endif
#if defined(LQCD_NATIVE_SVE_TRANSFER)
                if (sve_tile) {
                    const float *vectors = basis_block(cb) + (a * 24 * 2) * block_sites;
                    const float *coefficients = batch_coarse_correction[r].data() +
                        ((size_t)(cb - first_aggregate) * coarse_dof + (a / 6) * 24) * 2;
                    lqcd_native::kernels::prolongate_component_sve(
                        block_sites, vectors, coefficients, fr, fi);
                    continue;
                }
#endif
                for (int v = 0; v < 24; v++) {
                    const float *br = basis_block(cb) + ((a * 24 + v) * 2) * block_sites,
                                *bi = br + block_sites;
                    float zr = batch_coarse_correction[r][((cb - first_aggregate) * coarse_dof +
                                                           (a / 6) * 24 + v) *
                                                          2],
                          zi = batch_coarse_correction
                              [r][((cb - first_aggregate) * coarse_dof + (a / 6) * 24 + v) * 2 + 1];
#pragma omp simd
                    for (int s = 0; s < block_sites; s++) {
                        fr[s] += br[s] * zr - bi[s] * zi;
                        fi[s] += br[s] * zi + bi[s] * zr;
                    }
                }
            }
    prolong_seconds += wall_seconds() - t;
    t = wall_seconds();
    sap_batch(sources, destinations, sap_cycles);
    sap_seconds += wall_seconds() - t;
}
