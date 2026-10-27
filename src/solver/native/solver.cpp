#include "hierarchy.hpp"
#include <cmath>
#include <iostream>

using namespace lqcd_native::detail;

int NativeMG::Impl::solve_float_gcr(const FloatField &b, FloatField &solution, double tol,
                                    int budget, int restart) {
    // Ghost storage is initialized by fine_apply; only owned values enter BLAS.
    solution.resize(b.size());
#pragma omp parallel for schedule(static)
    for (size_t k = (size_t)first_aggregate * 24 * block_sites;
         k < (size_t)end_aggregate * 24 * block_sites; k++)
        solution[k] = 0;
    FloatField &residual = outer_residual;
    fine_copy(b, residual);
    double bn = fine_norm(b);
    auto &qs = outer_images;
    auto &zs = outer_directions;
    size_t active = 0;
    int it = 0;
    for (; it < budget; it++) {
        if (qs.size() <= active) {
            qs.emplace_back();
            zs.emplace_back();
        }
        FloatField &z = zs[active], &q = qs[active];
        apply_vcycle(residual, z);
        fine_apply(z, q);
        for (size_t j = 0; j < active; j++) {
            auto beta = fine_dot(qs[j], q);
            fine_axpy(q, -beta, qs[j]);
            fine_axpy(z, -beta, zs[j]);
        }
        double rn;
        if (setting("LQCD_GCR_FUSED", 1)) {
            double qq = 0, qr_re = 0, qr_im = 0;
#pragma omp parallel for reduction(+ : qq, qr_re, qr_im) schedule(static)
            for (int cb = first_aggregate; cb < end_aggregate; cb++)
                for (int j = 0; j < 12; j++) {
                    const size_t base = ((size_t)cb * 24 + 2 * j) * block_sites;
#pragma omp simd reduction(+ : qq, qr_re, qr_im)
                    for (int k = 0; k < block_sites; k++) {
                        const size_t re = base + k, im = re + block_sites;
                        const double a = q[re], b = q[im];
                        qq += a * a + b * b;
                        qr_re += a * residual[re] + b * residual[im];
                        qr_im += a * residual[im] - b * residual[re];
                    }
                }
            double sums[3] = {qq, qr_re, qr_im};
            if (native_size > 1)
                MPI_Allreduce(MPI_IN_PLACE, sums, 3, MPI_DOUBLE, MPI_SUM, native_comm);
            const double den = std::sqrt(sums[0]);
            if (den < 1e-30)
                break;
            const float ar = sums[1] / den, ai = sums[2] / den;
            double rr = 0;
#pragma omp parallel for reduction(+ : rr) schedule(static)
            for (int cb = first_aggregate; cb < end_aggregate; cb++)
                for (int j = 0; j < 12; j++) {
                    const size_t base = ((size_t)cb * 24 + 2 * j) * block_sites;
#pragma omp simd reduction(+ : rr)
                    for (int k = 0; k < block_sites; k++) {
                        const size_t re = base + k, im = re + block_sites;
                        // Store the normalized float basis, then measure the
                        // actually rounded residual (never a norm downdate).
                        q[re] /= den;
                        q[im] /= den;
                        z[re] /= den;
                        z[im] /= den;
                        solution[re] += ar * z[re] - ai * z[im];
                        solution[im] += ar * z[im] + ai * z[re];
                        residual[re] += -ar * q[re] + ai * q[im];
                        residual[im] += -ar * q[im] - ai * q[re];
                        rr += (double)residual[re] * residual[re] +
                              (double)residual[im] * residual[im];
                    }
                }
            if (native_size > 1)
                MPI_Allreduce(MPI_IN_PLACE, &rr, 1, MPI_DOUBLE, MPI_SUM, native_comm);
            rn = std::sqrt(rr) / bn;
        } else {
            double den = fine_norm(q);
            if (den < 1e-30)
                break;
#pragma omp parallel for schedule(static)
            for (size_t k = (size_t)first_aggregate * 24 * block_sites;
                 k < (size_t)end_aggregate * 24 * block_sites; k++) {
                q[k] /= den;
                z[k] /= den;
            }
            auto alpha = fine_dot(q, residual);
            fine_axpy(solution, alpha, z);
            fine_axpy(residual, -alpha, q);
            rn = fine_norm(residual) / bn;
        }
        if (!std::isfinite(rn))
            throw std::runtime_error("nonfinite float residual");
        ++active;
        // A correction is always followed by the outer double b-Dx gate.
        // Avoid a duplicate float operator application at this exit only;
        // a continuing restart still refreshes the float residual below.
        if (rn < tol && !float_correction_verify)
            return it + 1;
        if (rn < tol || active == (size_t)restart) {
            FloatField &image = outer_image;
            fine_apply(solution, image);
            fine_copy(b, residual);
            fine_axpy(residual, -1., image);
            if (fine_norm(residual) / bn < tol)
                return it + 1;
            active = 0;
        }
    }
    return it;
}

void NativeMG::solve(const Field &b, Field &x, double tol, int maxiter, int restart) {
    impl->configure_solve();
    impl->restrict_seconds = impl->coarse_seconds = impl->prolong_seconds = impl->sap_seconds = 0;
    impl->begin_halo_profile();
    const bool verbose = setting("LQCD_VERBOSE", 0) && native_rank == 0;
    x.assign(b.size(), 0.);
    Field &r = impl->reliable_residual;
    Field &ax = impl->reliable_image;
    r = b;
    double bn = distributed_norm(b);
    iterations = 0;
    if (bn == 0) {
        impl->report_halo_profile();
        return;
    }
    if (setting("NATIVE_OUTER_FLOAT", 1)) {
        double current_relative = 1.;
        for (int correction = 0; correction < 12 && iterations < maxiter; correction++) {
            auto &fb = impl->outer_rhs;
            auto &fx = impl->outer_solution;
            impl->encode_fine(r, fb);
            // Avoid oversolving the last float correction. The double full
            // residual remains the sole acceptance gate; the safety factor
            // leaves headroom for float arithmetic and operator differences.
            const double correction_tol =
                impl->adaptive_correction
                    ? std::max(impl->correction_base_tol,
                               std::min(.1, .5 * (tol / current_relative)))
                    : impl->correction_base_tol;
            iterations +=
                impl->solve_float_gcr(fb, fx, correction_tol, maxiter - iterations, restart);
            Field &dx = impl->reliable_delta;
            impl->decode_fine(fx, dx);
            axpy(x, 1., dx);
            apply(x, ax);
            r = b;
            axpy(r, -1., ax);
            current_relative = distributed_norm(r) / bn;
            if (!std::isfinite(current_relative))
                throw std::runtime_error("native reliable residual nonfinite");
            if (verbose)
                std::cerr << "native reliable update " << correction + 1 << " iterations " << iterations
                      << " correction_target " << correction_tol << " residual " << current_relative
                      << std::endl;
            if (current_relative < tol) {
                if (verbose)
                    std::cerr << "native profile R " << impl->restrict_seconds << " coarse "
                          << impl->coarse_seconds << " P " << impl->prolong_seconds << " SAP "
                          << impl->sap_seconds << std::endl;
                impl->report_halo_profile();
                return;
            }
        }
        throw std::runtime_error("native mixed precision residual gate failed");
    }
    std::vector<Field> zs, qs;
    for (int it = 0; it < maxiter; it++) {
        Field z, q;
        precondition(r, z);
        apply(z, q);
        for (size_t j = 0; j < qs.size(); j++) {
            auto beta = distributed_dot(qs[j], q);
            axpy(q, -beta, qs[j]);
            axpy(z, -beta, zs[j]);
        }
        double den = distributed_norm(q);
        if (den < 1e-30)
            break;
#pragma omp parallel for schedule(static)
        for (size_t k = 0; k < q.size(); k++) {
            q[k] /= den;
            z[k] /= den;
        }
        auto alpha = distributed_dot(q, r);
        axpy(x, alpha, z);
        axpy(r, -alpha, q);
        iterations = it + 1;
        double rn = distributed_norm(r) / bn;
        if (!std::isfinite(rn))
            throw std::runtime_error("native residual nonfinite");
        if (verbose)
            std::cerr << "native iteration " << iterations << " residual " << rn << std::endl;
        zs.push_back(std::move(z));
        qs.push_back(std::move(q));
        if (rn < tol || qs.size() == (size_t)restart) {
            apply(x, ax);
            r = b;
            axpy(r, -1., ax);
            if (distributed_norm(r) / bn < tol) {
                if (verbose)
                    std::cerr << "native profile R " << impl->restrict_seconds << " coarse "
                          << impl->coarse_seconds << " P " << impl->prolong_seconds << " SAP "
                          << impl->sap_seconds << std::endl;
                impl->report_halo_profile();
                return;
            }
            zs.clear();
            qs.clear();
        }
    }
    throw std::runtime_error("native MG did not converge");
}
