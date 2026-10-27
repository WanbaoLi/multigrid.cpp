#include "hierarchy.hpp"

using namespace lqcd_native::detail;

void NativeMG::Impl::solve_sap_block_eo(int cb, FloatField &rr, FloatField &ar, FloatField &dx,
                                        const float *source, const float *image) const {
    const int half = block_sites / 2;
    // H_eo only reads ar_o and writes ar_e, so this parity-disjoint alias
    // is safe. Clover inversions never alias their input and output.
    clover_range(cb, rr.data(), ar.data(), 1, true);
    local_range(cb, ar.data(), ar.data(), 0, false);
    for (int j = 0; j < 24; j++) {
#pragma omp simd
        for (int s = 0; s < half; s++)
            rr[j * block_sites + s] -= ar[j * block_sites + s];
    }
    for (int it = 0; it < sap_steps; it++) {
        // S r_e = (C_e - H_eo C_o^{-1} H_oe) r_e. H already
        // includes the signed -kappa links of the full Wilson operator.
        local_range(cb, rr.data(), ar.data(), 1, false);
        clover_range(cb, ar.data(), rr.data(), 1, true);
        for (int j = 0; j < 24; j++) {
#pragma omp simd
            for (int s = half; s < block_sites; s++)
                rr[j * block_sites + s] = -rr[j * block_sites + s];
        }
        local_range(cb, rr.data(), ar.data(), 0, true);
        double re = 0, im = 0, den = 0;
        for (int a = 0; a < 12; a++) {
            const float *tr = ar.data() + 2 * a * block_sites, *ti = tr + block_sites;
            const float *vr = rr.data() + 2 * a * block_sites, *vi = vr + block_sites;
#pragma omp simd reduction(+ : re, im, den)
            for (int s = 0; s < half; s++) {
                re += (double)tr[s] * vr[s] + (double)ti[s] * vi[s];
                im += (double)tr[s] * vi[s] - (double)ti[s] * vr[s];
                den += (double)tr[s] * tr[s] + (double)ti[s] * ti[s];
            }
        }
        if (den < 1e-30)
            break;
        const float alr = re / den, ali = im / den;
        for (int a = 0; a < 12; a++) {
            float *xr = dx.data() + 2 * a * block_sites, *xi = xr + block_sites;
            float *vr = rr.data() + 2 * a * block_sites, *vi = vr + block_sites;
            const float *tr = ar.data() + 2 * a * block_sites, *ti = tr + block_sites;
#pragma omp simd
            for (int s = 0; s < half; s++) {
                xr[s] += alr * vr[s] - ali * vi[s];
                xi[s] += alr * vi[s] + ali * vr[s];
                vr[s] -= alr * tr[s] - ali * ti[s];
                vi[s] -= alr * ti[s] + ali * tr[s];
            }
        }
    }
    // Recover the untouched original r_o from source-image, avoiding
    // another full block workspace. Only x_e is read by H_oe here.
    local_range(cb, dx.data(), ar.data(), 1, false);
    for (int j = 0; j < 24; j++) {
#pragma omp simd
        for (int s = half; s < block_sites; s++) {
            const size_t k = (size_t)j * block_sites + s;
            rr[k] = source[k] - (image ? image[k] : 0.f) - ar[k];
        }
    }
    clover_range(cb, rr.data(), dx.data(), 1, true);
}

void NativeMG::Impl::sap(const FloatField &b, FloatField &solution, int cycles) {
    // Reuse the global-index workspace. Releasing it every V-cycle would
    // fault the same owned pages back in on the next application.
    FloatField &image = sap_image;
    image.resize(b.size());
    for (int cycle = 0; cycle < cycles; cycle++)
        for (int color = 0; color < 2; color++) {
            fine_apply(solution, image, color);
#pragma omp parallel
            {
                // A worker reuses its block buffers across colors, V-cycles and
                // RHS columns. Only owned block entries are read below.
                static thread_local FloatField rr, ar, dx;
                rr.resize(24 * block_sites);
                ar.resize(24 * block_sites);
                dx.resize(24 * block_sites);
#pragma omp for schedule(static)
                for (int cb = first_aggregate; cb < end_aggregate; cb++)
                    if (colors[cb] == color) {
                        size_t offset = (size_t)cb * 24 * block_sites;
                        for (int j = 0; j < 24 * block_sites; j++) {
                            rr[j] = b[offset + j] - image[offset + j];
                            dx[j] = 0;
                        }
                        if (sap_eo)
                            solve_sap_block_eo(cb, rr, ar, dx, b.data() + offset,
                                               image.data() + offset);
                        else
                            for (int it = 0; it < sap_steps; it++) {
                                block_apply(cb, rr.data(), ar.data(), true);
                                double re = 0, im = 0, den = 0;
                                for (int a = 0; a < 12; a++) {
                                    const float *tr = ar.data() + 2 * a * block_sites,
                                                *ti = tr + block_sites,
                                                *vr = rr.data() + 2 * a * block_sites,
                                                *vi = vr + block_sites;
#pragma omp simd reduction(+ : re, im, den)
                                    for (int s = 0; s < block_sites; s++) {
                                        re += (double)tr[s] * vr[s] + (double)ti[s] * vi[s];
                                        im += (double)tr[s] * vi[s] - (double)ti[s] * vr[s];
                                        den += (double)tr[s] * tr[s] + (double)ti[s] * ti[s];
                                    }
                                }
                                if (den < 1e-30)
                                    break;
                                float alr = re / den, ali = im / den;
                                for (int a = 0; a < 12; a++) {
                                    float *xr = dx.data() + 2 * a * block_sites,
                                          *xi = xr + block_sites,
                                          *vr = rr.data() + 2 * a * block_sites,
                                          *vi = vr + block_sites;
                                    const float *tr = ar.data() + 2 * a * block_sites,
                                                *ti = tr + block_sites;
#pragma omp simd
                                    for (int s = 0; s < block_sites; s++) {
                                        xr[s] += alr * vr[s] - ali * vi[s];
                                        xi[s] += alr * vi[s] + ali * vr[s];
                                        vr[s] -= alr * tr[s] - ali * ti[s];
                                        vi[s] -= alr * ti[s] + ali * tr[s];
                                    }
                                }
                            }
                        for (int j = 0; j < 24 * block_sites; j++)
                            solution[offset + j] += dx[j];
                    }
            }
        }
}
