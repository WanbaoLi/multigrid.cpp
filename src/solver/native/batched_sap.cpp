#include "hierarchy.hpp"
using namespace lqcd_native::detail;

void NativeMG::Impl::sap_batch(const std::vector<const FloatField *> &sources,
                               const std::vector<FloatField *> &solutions, int cycles) {
    const int nrhs = sources.size();
    if (nrhs < 1 || nrhs > 12 || solutions.size() != sources.size())
        throw std::runtime_error("SAP batch requires one to twelve matching fields");
    if (nrhs == 1 || !sap_eo) {
        for (int r = 0; r < nrhs; r++)
            sap(*sources[r], *solutions[r], cycles);
        return;
    }
    if (batch_sap_image.size() < (size_t)nrhs)
        batch_sap_image.resize(nrhs);
    std::vector<const FloatField *> src(nrhs);
    std::vector<FloatField *> image(nrhs);
    for (int r = 0; r < nrhs; r++) {
        batch_sap_image[r].resize(sources[r]->size());
        src[r] = solutions[r];
        image[r] = &batch_sap_image[r];
    }
    for (int cycle = 0; cycle < cycles; cycle++)
        for (int color = 0; color < 2; color++) {
            fine_apply_batch(src, image, color);
#pragma omp parallel
            {
                static thread_local FloatField rr, ar, dx;
                rr.resize(24 * block_sites);
                ar.resize(24 * block_sites);
                dx.resize(24 * block_sites);
#pragma omp for schedule(static)
                for (int cb = first_aggregate; cb < end_aggregate; cb++)
                    if (colors[cb] == color) {
                        const size_t offset = (size_t)cb * 24 * block_sites;
                        for (int r = 0; r < nrhs; r++) {
                            const float *source = sources[r]->data() + offset;
                            const float *im = batch_sap_image[r].data() + offset;
                            for (int j = 0; j < 24 * block_sites; j++) {
                                rr[j] = source[j] - im[j];
                                dx[j] = 0.f;
                            }
                            solve_sap_block_eo(cb, rr, ar, dx, source, im);
                            float *dest = solutions[r]->data() + offset;
                            for (int j = 0; j < 24 * block_sites; j++)
                                dest[j] += dx[j];
                        }
                    }
            }
        }
}
