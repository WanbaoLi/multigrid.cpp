#include "hierarchy.hpp"
#include "distributed_storage.hpp"
#include "core/clover.h"
#include "core/dirac.h"
#include <cmath>
#include <iostream>
#include <random>

using namespace lqcd_native::detail;

void NativeMG::Impl::verify_eo(const FloatField &probe) const {
    if (!sap_eo)
        return;
    double inverse_error = 0, schur_error = 0, reference_norm = 0;
#pragma omp parallel reduction(+ : inverse_error, schur_error, reference_norm)
    {
        FloatField b(24 * block_sites), rr(24 * block_sites), ar(24 * block_sites),
            dx(24 * block_sites), tmp(24 * block_sites);
#pragma omp for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++) {
            std::copy_n(probe.data() + (size_t)cb * 24 * block_sites, 24 * block_sites, b.data());
            for (int p = 0; p < 2; p++) {
                clover_range(cb, b.data(), tmp.data(), p, true);
                clover_range(cb, tmp.data(), ar.data(), p, false);
            }
            for (int j = 0; j < 24 * block_sites; j++) {
                const double d = (double)ar[j] - b[j];
                inverse_error += d * d;
                reference_norm += (double)b[j] * b[j];
            }
            rr = b;
            std::fill(dx.begin(), dx.end(), 0.f);
            solve_sap_block_eo(cb, rr, ar, dx, b.data(), nullptr);
            // Check reconstruction against the complete local operator:
            // odd residual vanishes, even residual equals Schur MR's
            // recursively updated residual (not just a self-comparison
            // of the same Schur matrix-vector implementation).
            block_apply(cb, dx.data(), ar.data(), true);
            for (int j = 0; j < 24; j++)
                for (int t = 0; t < block_sites; t++) {
                    const size_t k = (size_t)j * block_sites + t;
                    const double expected = t < block_sites / 2 ? rr[k] : 0.;
                    const double d = ((double)b[k] - ar[k]) - expected;
                    schur_error += d * d;
                }
        }
    }
    double sums[3] = {inverse_error, schur_error, reference_norm};
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, sums, 3, MPI_DOUBLE, MPI_SUM, native_comm);
    const double inverse_rel = std::sqrt(sums[0] / sums[2]);
    const double schur_rel = std::sqrt(sums[1] / sums[2]);
    if (native_rank == 0)
        std::cout << "native EO gates clover_inverse=" << inverse_rel
                  << " Schur_reconstruction=" << schur_rel << std::endl;
    if (!std::isfinite(inverse_rel + schur_rel) || inverse_rel > 2e-6 || schur_rel > 3e-6)
        throw std::runtime_error("native EO clover/Schur component gate failed");
}

void NativeMG::Impl::verify_coarse_eo(const FloatField &probe) const {
    if (!coarse_eo)
        return;
    FloatField even, full, image, schur, reduced, actual;
    coarse_copy_color(probe, even, 0);
    coarse_reconstruct(probe, even, full);
    coarse_apply(full, image); // original full operator, not Schur
    actual = probe;
    coarse_axpy(actual, -1., image);
    coarse_reduced_rhs(probe, reduced);
    coarse_schur(even, schur);
    coarse_axpy(reduced, -1., schur);
    coarse_axpy(actual, -1., reduced);
    // Both equations checked: odd residual = 0; even = b_e' - S_e x_e.
    const double error = coarse_norm(actual) / coarse_norm(probe);
    if (native_rank == 0)
        std::cout << "native coarse EO gate Schur_reconstruction=" << error << std::endl;
    if (!std::isfinite(error) || error > 5e-6)
        throw std::runtime_error("native coarse EO Schur reconstruction gate failed");
}

void NativeMG::verify() const {
    std::mt19937 gen(1234);
    std::normal_distribution<float> normal;
    // Setup-only scalar oracle remains independent of the production halo and
    // SIMD implementations. Every decomposition sees the same global probe.
    Field probe, expected, actual;
    if (distributed_storage()) {
        const auto &o = impl->gauge.o;
        const size_t spatial = (size_t)o.nx*o.ny*o.nz;
        const int lt = o.nt/native_size;
        const size_t count = spatial*lt*12;
        probe.resize(count);
        for (size_t i = 0; i < count; ++i)
            probe[i] = {setup_probe(2*(i+count*native_rank),1234),
                        setup_probe(2*(i+count*native_rank)+1,1234)};
        // Scalar oracle on a padded local lattice. Twist only the physical
        // global wrap link; the scalar local wrap is outside the tested rows.
        Gauge padded;
        padded.o = o; padded.o.nt = lt+2;
        padded.u.resize(spatial*(lt+2)*36);
        Field input(spatial*(lt+2)*12), output;
        for (int t = 0; t < lt+2; ++t) {
            int gt = (native_rank*lt+t-1+o.nt)%o.nt;
            for (size_t j = 0; j < spatial*36; ++j) {
                auto z = impl->gauge.u[(size_t)gt*spatial*36+j];
                if (gt == o.nt-1 && (j%36)/9 == 3) z = -z;
                padded.u[(size_t)t*spatial*36+j] = z;
            }
            for (size_t j = 0; j < spatial*12; ++j) {
                size_t i = (size_t)gt*spatial*12+j;
                input[(size_t)t*spatial*12+j] = {setup_probe(2*i,1234),setup_probe(2*i+1,1234)};
            }
        }
        build_clover(padded,padded.clover);
        apply_dirac(padded,input,output,1,o.mass);
        expected.assign(output.begin()+spatial*12,output.begin()+(lt+1)*spatial*12);
    } else {
        Field global_probe(impl->fine_sites*12), global_expected;
        for (auto &z : global_probe) z = {normal(gen),normal(gen)};
        apply_dirac(impl->gauge,global_probe,global_expected,1,impl->gauge.o.mass);
        const size_t size = global_probe.size()/native_size, first = size*native_rank;
        probe.assign(global_probe.begin()+first,global_probe.begin()+first+size);
        expected.assign(global_expected.begin()+first,global_expected.begin()+first+size);
    }
    apply(probe, actual);
    axpy(actual, -1., expected);
    const double double_error = distributed_norm(actual) / distributed_norm(expected);
    if (!std::isfinite(double_error) || double_error > 2e-13)
        throw std::runtime_error("native distributed double/scalar operator gate failed");
    FloatField fp, fy;
    impl->encode_fine(probe, fp);
    impl->fine_apply(fp, fy);
    impl->decode_fine(fy, actual);
    axpy(actual, -1., expected);
    double fine_error = distributed_norm(actual) / distributed_norm(expected);
    impl->verify_eo(fp);
    FloatField cr((size_t)(impl->end_aggregate - impl->first_aggregate) * impl->coarse_dof * 2),
        pr(impl->fine_sites * 24), back, coarse_image;
    std::fill(pr.begin()+(size_t)impl->first_aggregate*24*impl->block_sites,
              pr.begin()+(size_t)impl->end_aggregate*24*impl->block_sites,0.f);
    // Same global random probe for every decomposition, stored locally.
    const size_t begin = (size_t)impl->first_aggregate * impl->coarse_dof * 2;
    const size_t end = (size_t)impl->end_aggregate * impl->coarse_dof * 2;
    for (size_t i = 0; i < (size_t)impl->aggregate_count * impl->coarse_dof * 2; i++) {
        const float value = normal(gen);
        if (i >= begin && i < end)
            cr[i - begin] = value;
    }
    impl->verify_coarse_eo(cr);
    impl->prolongate_add(cr, pr);
    impl->restrict_to_coarse(pr, back);
    for (size_t i = 0; i < cr.size(); i++)
        back[i] -= cr[i];
    double ortho = coarse_norm(back) / coarse_norm(cr);
    impl->fine_apply(pr, fy);
    impl->restrict_to_coarse(fy, back);
    impl->coarse_apply(cr, coarse_image);
    for (size_t i = 0; i < cr.size(); i++)
        back[i] -= coarse_image[i];
    double galerkin = coarse_norm(back) / coarse_norm(coarse_image);
    std::cout << "native gates double=" << double_error << " fine=" << fine_error << " R*P=" << ortho << " RAP=" << galerkin
              << std::endl;
    if (!std::isfinite(fine_error + ortho + galerkin) || fine_error > 1e-6 || ortho > 2e-6 ||
        galerkin > 2e-6)
        throw std::runtime_error("native component gate failed");
}
