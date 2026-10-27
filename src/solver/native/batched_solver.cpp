#include "hierarchy.hpp"
#include <cmath>
#include <iostream>

using namespace lqcd_native::detail;

// Independent MGS for this RHS. Shared operator/preconditioner applications
// happen outside this method; q/z always undergo the same basis transform.
bool NativeMG::Impl::batch_gcr_update(BatchKrylovWorkspace &w) {
    auto &q = w.images[w.active];
    auto &z = w.directions[w.active];
    for (size_t j = 0; j < w.active; ++j) {
        const auto beta = fine_dot(w.images[j], q);
        fine_axpy(q, -beta, w.images[j]);
        fine_axpy(z, -beta, w.directions[j]);
    }
    double qq = 0, re = 0, im = 0;
#pragma omp parallel for reduction(+ : qq, re, im) schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; ++cb)
        for (int a = 0; a < 12; ++a) {
            const size_t base = ((size_t)cb * 24 + 2 * a) * block_sites;
#pragma omp simd reduction(+ : qq, re, im)
            for (int s = 0; s < block_sites; ++s) {
                const size_t k = base + s, l = k + block_sites;
                const double qr = q[k], qi = q[l];
                qq += qr * qr + qi * qi;
                re += qr * w.r[k] + qi * w.r[l];
                im += qr * w.r[l] - qi * w.r[k];
            }
        }
    double sums[3] = {qq, re, im};
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, sums, 3, MPI_DOUBLE, MPI_SUM, native_comm);
    const double den = std::sqrt(sums[0]);
    if (!std::isfinite(den))
        throw std::runtime_error("nonfinite batch GCR direction");
    if (den < 1e-30)
        return false;
    const float ar = sums[1] / den, ai = sums[2] / den;
    double rr = 0;
#pragma omp parallel for reduction(+ : rr) schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; ++cb)
        for (int a = 0; a < 12; ++a) {
            const size_t base = ((size_t)cb * 24 + 2 * a) * block_sites;
#pragma omp simd reduction(+ : rr)
            for (int s = 0; s < block_sites; ++s) {
                const size_t k = base + s, l = k + block_sites;
                q[k] /= den;
                q[l] /= den;
                z[k] /= den;
                z[l] /= den;
                w.x[k] += ar * z[k] - ai * z[l];
                w.x[l] += ar * z[l] + ai * z[k];
                w.r[k] += -ar * q[k] + ai * q[l];
                w.r[l] += -ar * q[l] - ai * q[k];
                rr += (double)w.r[k] * w.r[k] + (double)w.r[l] * w.r[l];
            }
        }
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &rr, 1, MPI_DOUBLE, MPI_SUM, native_comm);
    const double rn = std::sqrt(rr) / w.float_bn;
    if (!std::isfinite(rn))
        throw std::runtime_error("nonfinite batch float residual");
    ++w.active;
    w.correction_done = rn < w.target;
    return true;
}

std::vector<int> NativeMG::solve_batch(const std::vector<Field> &b, std::vector<Field> &x,
                                       double tol, int maxiter, int restart) {
    // API caller validates matching shapes/parameters collectively. Keep this
    // native entry collective-safe as well, including for direct C++ callers.
    int invalid = b.empty() || b.size() > 12 || maxiter <= 0 || restart <= 0 ||
                  !std::isfinite(tol) || tol <= 0 || tol >= 1;
    for (const auto &rhs : b)
        invalid |= rhs.size() != impl->fine_sites * 12 / native_size;
    int any_invalid;
    MPI_Allreduce(&invalid, &any_invalid, 1, MPI_INT, MPI_MAX, native_comm);
    double params[4] = {(double)b.size(), tol, (double)maxiter, (double)restart};
    double minimum[4], maximum[4];
    MPI_Allreduce(params, minimum, 4, MPI_DOUBLE, MPI_MIN, native_comm);
    MPI_Allreduce(params, maximum, 4, MPI_DOUBLE, MPI_MAX, native_comm);
    for (int i = 0; i < 4; ++i)
        any_invalid |= minimum[i] != maximum[i];
    if (any_invalid)
        throw std::runtime_error("invalid or rank-inconsistent native batch solve inputs");
    impl->configure_solve();
    x.resize(b.size());
    std::vector<int> counts(b.size(), 0);
    if (b.size() == 1 || !setting("NATIVE_OUTER_FLOAT", 1) || !setting("LQCD_GCR_FUSED", 1)) {
        for (size_t i = 0; i < b.size(); ++i) {
            solve(b[i], x[i], tol, maxiter, restart);
            counts[i] = iterations;
        }
        return counts;
    }
    impl->restrict_seconds = impl->coarse_seconds = impl->prolong_seconds = impl->sap_seconds = 0;
    impl->begin_halo_profile();
    if (impl->batch_workspace.size() < b.size())
        impl->batch_workspace.resize(b.size());
    auto &work = impl->batch_workspace;
    for (size_t i = 0; i < b.size(); ++i) {
        auto &w = work[i];
        x[i].assign(b[i].size(), 0.);
        w.residual = b[i];
        w.bn = distributed_norm(b[i]);
        if (!std::isfinite(w.bn))
            throw std::runtime_error("nonfinite batch source");
        w.relative = w.bn == 0 ? 0 : 1;
        w.iterations = 0;
        w.converged = w.bn == 0;
    }
    const bool verbose = setting("LQCD_VERBOSE", 0) && native_rank == 0;
    for (int correction = 0; correction < 12; ++correction) {
        bool remaining = false;
        for (size_t i = 0; i < b.size(); ++i) {
            auto &w = work[i];
            w.correction_done = w.converged;
            if (w.converged)
                continue;
            if (w.iterations >= maxiter)
                throw std::runtime_error("native batch iteration budget exhausted");
            remaining = true;
            impl->encode_fine(w.residual, w.b);
            w.x.resize(w.b.size());
            const size_t first = (size_t)impl->first_aggregate * 24 * impl->block_sites;
            const size_t last = (size_t)impl->end_aggregate * 24 * impl->block_sites;
#pragma omp parallel for schedule(static)
            for (size_t k = first; k < last; ++k)
                w.x[k] = 0;
            impl->fine_copy(w.b, w.r);
            w.float_bn = fine_norm(w.b);
            w.active = 0;
            w.target = impl->adaptive_correction ? std::max(impl->correction_base_tol,
                                                            std::min(.1, .5 * tol / w.relative))
                                                 : impl->correction_base_tol;
        }
        if (!remaining)
            break;
        for (;;) {
            std::vector<size_t> active;
            std::vector<const FloatField *> sources;
            std::vector<FloatField *> directions, images;
            for (size_t i = 0; i < b.size(); ++i) {
                auto &w = work[i];
                if (w.correction_done)
                    continue;
                if (w.iterations >= maxiter) {
                    w.correction_done = true;
                    continue;
                }
                if (w.images.size() <= w.active) {
                    w.images.emplace_back();
                    w.directions.emplace_back();
                }
                active.push_back(i);
                sources.push_back(&w.r);
                directions.push_back(&w.directions[w.active]);
                images.push_back(&w.images[w.active]);
            }
            if (active.empty())
                break;
            impl->apply_vcycle_batch(sources, directions);
            sources.assign(directions.begin(), directions.end());
            impl->fine_apply_batch(sources, images);
            std::vector<size_t> refresh;
            sources.clear();
            images.clear();
            for (size_t i : active) {
                auto &w = work[i];
                ++w.iterations; // Every attempted V-cycle consumes the budget.
                if (!impl->batch_gcr_update(w)) {
                    w.correction_done = true;
                    continue;
                }
                if ((w.correction_done && impl->float_correction_verify) ||
                    (!w.correction_done && w.active == (size_t)restart)) {
                    refresh.push_back(i);
                    sources.push_back(&w.x);
                    images.push_back(&w.float_image);
                }
            }
            if (!refresh.empty()) {
                impl->fine_apply_batch(sources, images);
                for (size_t i : refresh) {
                    auto &w = work[i];
                    impl->fine_copy(w.b, w.r);
                    impl->fine_axpy(w.r, -1., w.float_image);
                    const double rn = fine_norm(w.r) / w.float_bn;
                    if (!std::isfinite(rn))
                        throw std::runtime_error("nonfinite batch refreshed residual");
                    w.correction_done = rn < w.target;
                    w.active = 0;
                }
            }
        }
        for (size_t i = 0; i < b.size(); ++i) {
            auto &w = work[i];
            if (w.converged)
                continue;
            impl->decode_fine(w.x, w.delta);
            axpy(x[i], 1., w.delta);
            apply(x[i], w.image);
            w.residual = b[i];
            axpy(w.residual, -1., w.image);
            w.relative = distributed_norm(w.residual) / w.bn;
            if (!std::isfinite(w.relative))
                throw std::runtime_error("nonfinite batch reliable residual");
            w.converged = w.relative < tol;
            if (verbose)
                std::cerr << "native batch rhs " << i << " correction " << correction + 1
                          << " iterations " << w.iterations << " residual " << w.relative << '\n';
        }
    }
    iterations = 0;
    for (size_t i = 0; i < b.size(); ++i) {
        if (!work[i].converged)
            throw std::runtime_error("native batch mixed precision residual gate failed");
        counts[i] = work[i].iterations;
        iterations = std::max(iterations, counts[i]);
    }
    impl->report_halo_profile();
    return counts;
}
