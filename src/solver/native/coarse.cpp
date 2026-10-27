#include "hierarchy.hpp"
#include "kernels.hpp"
#include <cmath>

using namespace lqcd_native::detail;

namespace {
// Two classical Gram-Schmidt passes: each projection has one global vector
// reduction. Transform q and its paired preconditioned direction z together,
// preserving D*z ~= q. Fields contain owned entries only, including zero odd
// rows in the Schur representation; MPI stays outside OpenMP regions.
void coarse_cgs2_project(FloatField &q, FloatField &z,
                         const std::vector<FloatField> &qs,
                         const std::vector<FloatField> &zs) {
    const size_t n = qs.size();
    std::vector<double> h(2 * n);
    std::vector<const float *> qptr(n), zptr(n);
    for (size_t j = 0; j < n; ++j) {
        qptr[j] = qs[j].data();
        zptr[j] = zs[j].data();
    }
    for (int pass = 0; pass < 2; ++pass) {
#pragma omp parallel for schedule(static) if (q.size() > 100000)
        for (size_t j = 0; j < n; ++j) {
            double re = 0, im = 0;
            const float *basis = qs[j].data();
#pragma omp simd reduction(+ : re, im)
            for (size_t k = 0; k < q.size() / 2; ++k) {
                re += (double)basis[2 * k] * q[2 * k] +
                      (double)basis[2 * k + 1] * q[2 * k + 1];
                im += (double)basis[2 * k] * q[2 * k + 1] -
                      (double)basis[2 * k + 1] * q[2 * k];
            }
            h[2 * j] = re;
            h[2 * j + 1] = im;
        }
        if (native_size > 1)
            MPI_Allreduce(MPI_IN_PLACE, h.data(), static_cast<int>(h.size()),
                          MPI_DOUBLE, MPI_SUM, native_comm);
        // Tile independent sites, not the short direction reduction. This
        // makes SIMD explicit while preserving the order and precision of
        // each site's sum over j; q/z are written once after all directions.
#pragma omp parallel for schedule(static) if (q.size() > 100000)
        for (size_t first = 0; first < q.size() / 2; first += 16) {
            const size_t lanes = std::min(size_t(16), q.size() / 2 - first);
            alignas(64) double qr[16] = {}, qi[16] = {}, zr[16] = {}, zi[16] = {};
            for (size_t j = 0; j < n; ++j) {
                const double ar = h[2 * j], ai = h[2 * j + 1];
                const float *qj = qptr[j] + 2 * first, *zj = zptr[j] + 2 * first;
#pragma omp simd
                for (size_t lane = 0; lane < lanes; ++lane) {
                    qr[lane] += ar * qj[2 * lane] - ai * qj[2 * lane + 1];
                    qi[lane] += ar * qj[2 * lane + 1] + ai * qj[2 * lane];
                    zr[lane] += ar * zj[2 * lane] - ai * zj[2 * lane + 1];
                    zi[lane] += ar * zj[2 * lane + 1] + ai * zj[2 * lane];
                }
            }
#pragma omp simd
            for (size_t lane = 0; lane < lanes; ++lane) {
                const size_t k = first + lane;
                q[2 * k] = static_cast<float>((double)q[2 * k] - qr[lane]);
                q[2 * k + 1] = static_cast<float>((double)q[2 * k + 1] - qi[lane]);
                z[2 * k] = static_cast<float>((double)z[2 * k] - zr[lane]);
                z[2 * k + 1] = static_cast<float>((double)z[2 * k + 1] - zi[lane]);
            }
        }
    }
}

// Both coarse representations contain owned complex entries only; the Schur
// representation keeps inactive odd entries zero. MPI runs after OMP joins.
bool coarse_gcr_fused_step(FloatField &q, FloatField &z, FloatField &x,
                           FloatField &r, double &rn) {
    double qq = 0, qr_re = 0, qr_im = 0;
#pragma omp parallel for reduction(+ : qq, qr_re, qr_im) schedule(static) if (q.size() > 100000)
    for (size_t k = 0; k < q.size() / 2; k++) {
        const size_t re = 2 * k, im = re + 1;
        const double a = q[re], b = q[im];
        qq += a * a + b * b;
        qr_re += a * r[re] + b * r[im];
        qr_im += a * r[im] - b * r[re];
    }
    double sums[3] = {qq, qr_re, qr_im};
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, sums, 3, MPI_DOUBLE, MPI_SUM, native_comm);
    const double den = std::sqrt(sums[0]);
    if (den < 1e-30)
        return false;
    const float ar = sums[1] / den, ai = sums[2] / den;
    double rr = 0;
#pragma omp parallel for reduction(+ : rr) schedule(static) if (q.size() > 100000)
    for (size_t k = 0; k < q.size() / 2; k++) {
        const size_t re = 2 * k, im = re + 1;
        q[re] /= den;
        q[im] /= den;
        z[re] /= den;
        z[im] /= den;
        x[re] += ar * z[re] - ai * z[im];
        x[im] += ar * z[im] + ai * z[re];
        r[re] += -ar * q[re] + ai * q[im];
        r[im] += -ar * q[im] - ai * q[re];
        rr += (double)r[re] * r[re] + (double)r[im] * r[im];
    }
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &rr, 1, MPI_DOUBLE, MPI_SUM, native_comm);
    rn = std::sqrt(rr);
    return true;
}
} // namespace

void NativeMG::Impl::prepare_coarse_columns() const {
#if defined(LQCD_NATIVE_SVE_COARSE)
    if (!coarse_sve || coarse_pack_ready) return;
    // Called by the main thread before any parallel matrix applications.
    // Rebuilding Impl for a new hierarchy invalidates these caches naturally.
    const size_t stride = (size_t)coarse_dof * coarse_dof * 2;
    coarse_columns.resize((size_t)(end_aggregate-first_aggregate)*9*stride);
    coarse_inverse_columns.resize((size_t)(end_aggregate-first_aggregate)*stride);
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; ++cb) {
        const size_t local = cb-first_aggregate;
        for (int dir=0; dir<9; ++dir)
            lqcd_native::kernels::pack_coarse_columns(coarse_dof,
                coarse.data()+((size_t)cb*9+dir)*stride,
                coarse_columns.data()+(local*9+dir)*stride);
        lqcd_native::kernels::pack_coarse_columns(coarse_dof,
            coarse_inverse.data()+(size_t)cb*stride,
            coarse_inverse_columns.data()+local*stride);
    }
    coarse_pack_ready = true;
#endif
}

void NativeMG::Impl::coarse_block_apply(int cb, const FloatField &src, FloatField &out,
                                        bool diagonal) const {
#if defined(LQCD_NATIVE_SVE_COARSE)
    if (coarse_sve) {
        const size_t stride = (size_t)coarse_dof * coarse_dof * 2;
        float *dest = out.data() + (size_t)(cb-first_aggregate)*coarse_dof*2;
        bool add = false;
        for (int dir = diagonal ? 0 : 1; dir < 9; ++dir) {
            const int nb = cneighbor[cb*9+dir];
            const float *v;
            if (nb >= first_aggregate && nb < end_aggregate)
                v = src.data() + (size_t)(nb-first_aggregate)*coarse_dof*2;
            else
                v = (dir==7 ? coarse_recv_upper : coarse_recv_lower).data() +
                    (size_t)(nb%aggregates_per_tslice)*coarse_dof*2;
            lqcd_native::kernels::coarse_gemv_sve(coarse_dof,
                coarse_column_block(cb)+(size_t)dir*stride,v,dest,add);
            add = true;
        }
        return;
    }
#endif
    for (int a = 0; a < coarse_dof; a++) {
        float re = 0, im = 0;
        for (int dir = diagonal ? 0 : 1; dir < 9; dir++) {
            const int nb = cneighbor[cb * 9 + dir];
            const float *v;
            if (nb >= first_aggregate && nb < end_aggregate)
                v = src.data() + (size_t)(nb - first_aggregate) * coarse_dof * 2;
            else {
                // Only temporal neighbours leave a t-slab.  Their
                // spatial plane index is unchanged by periodic wrapping.
                const FloatField &ghost = dir == 7 ? coarse_recv_upper : coarse_recv_lower;
                v = ghost.data() + (size_t)(nb % aggregates_per_tslice) * coarse_dof * 2;
            }
            const float *row =
                coarse.data() + ((size_t)(cb * 9 + dir) * coarse_dof + a) * coarse_dof * 2;
#pragma omp simd reduction(+ : re, im)
            for (int j = 0; j < coarse_dof; j++) {
                re += row[2 * j] * v[2 * j] - row[2 * j + 1] * v[2 * j + 1];
                im += row[2 * j] * v[2 * j + 1] + row[2 * j + 1] * v[2 * j];
            }
        }
        out[((cb - first_aggregate) * coarse_dof + a) * 2] = re;
        out[((cb - first_aggregate) * coarse_dof + a) * 2 + 1] = im;
    }
}

void NativeMG::Impl::coarse_apply(const FloatField &src, FloatField &out, int color,
                                  bool diagonal) const {
    prepare_coarse_columns();
    if (color < 0)
        out.resize(src.size());
    else
        out.assign(src.size(), 0.f);
    if (native_size == 1) {
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            if (color < 0 || colors[cb] == color)
                coarse_block_apply(cb, src, out, diagonal);
        return;
    }
    HaloTrace trace(coarse_halo_stats, profile_active);
    const int prev = (native_rank + native_size - 1) % native_size;
    const int next = (native_rank + 1) % native_size;
    const int count = aggregates_per_tslice * coarse_dof * 2;
    coarse_send_lower.assign(src.begin(), src.begin() + count);
    coarse_send_upper.assign(src.end() - count, src.end());
    coarse_recv_lower.resize(count);
    coarse_recv_upper.resize(count);
    MPI_Request requests[4];
    MPI_Irecv(coarse_recv_upper.data(), count, MPI_FLOAT, next, 20, native_comm, &requests[0]);
    MPI_Irecv(coarse_recv_lower.data(), count, MPI_FLOAT, prev, 21, native_comm, &requests[1]);
    MPI_Isend(coarse_send_lower.data(), count, MPI_FLOAT, prev, 20, native_comm, &requests[2]);
    MPI_Isend(coarse_send_upper.data(), count, MPI_FLOAT, next, 21, native_comm, &requests[3]);
    trace.post(count);
    const int interior_first = first_aggregate + aggregates_per_tslice;
    const int interior_last = std::max(interior_first, end_aggregate - aggregates_per_tslice);
    if (!halo_overlap || (coarse_empty_interior && interior_first == interior_last)) {
        const double wait_start = trace.now();
        MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
        trace.wait(wait_start);
        const double compute_start = trace.now();
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            if (color < 0 || colors[cb] == color)
                coarse_block_apply(cb, src, out, diagonal);
        trace.compute_all(compute_start);
        return;
    }
#pragma omp parallel
    {
        const int tid = omp_get_thread_num(), threads = omp_get_num_threads();
        if (tid == 0) {
            const double wait_start = trace.now();
            MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
            trace.wait(wait_start);
            if (threads == 1) {
                const double work_start = trace.now();
                for (int cb = interior_first; cb < interior_last; cb++)
                    if (color < 0 || colors[cb] == color)
                        coarse_block_apply(cb, src, out, diagonal);
                trace.interior(tid, work_start);
            }
        } else {
            const double work_start = trace.now();
            const int n = interior_last - interior_first;
            const int begin = interior_first + n * (tid - 1) / (threads - 1);
            const int end = interior_first + n * tid / (threads - 1);
            for (int cb = begin; cb < end; cb++)
                if (color < 0 || colors[cb] == color)
                    coarse_block_apply(cb, src, out, diagonal);
            trace.interior(tid, work_start);
        }
#pragma omp barrier
        if (tid == 0)
            trace.region();
        const double boundary_start = trace.now();
        // Compact faces balance static scheduling across all workers;
        // scanning the whole slab would leave most threads without work.
#pragma omp for schedule(static)
        for (int i = 0; i < std::min(end_aggregate - first_aggregate, 2 * aggregates_per_tslice);
             i++) {
            const int cb = i < aggregates_per_tslice
                               ? first_aggregate + i
                               : end_aggregate - aggregates_per_tslice + i - aggregates_per_tslice;
            if (color < 0 || colors[cb] == color)
                coarse_block_apply(cb, src, out, diagonal);
        }
        trace.boundary(tid, boundary_start);
    }
}

void NativeMG::Impl::coarse_diagonal(const FloatField &src, FloatField &out, int color,
                                     bool inverse) const {
    prepare_coarse_columns();
    out.assign(src.size(), 0.f);
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        if (colors[cb] == color) {
#if defined(LQCD_NATIVE_SVE_COARSE)
            if (coarse_sve) {
                const size_t stride=(size_t)coarse_dof*coarse_dof*2;
                const size_t local=cb-first_aggregate;
                lqcd_native::kernels::coarse_gemv_sve(coarse_dof,
                    inverse ? coarse_inverse_column_block(cb)
                            : coarse_column_block(cb),
                    src.data()+local*coarse_dof*2,out.data()+local*coarse_dof*2,false);
                continue;
            }
#endif
            for (int a = 0; a < coarse_dof; a++) {
                const float *row =
                    inverse ? coarse_inverse.data() + ((size_t)cb * coarse_dof + a) * coarse_dof * 2
                            : coarse.data() + ((size_t)cb * 9 * coarse_dof + a) * coarse_dof * 2;
                const float *v = src.data() + (size_t)(cb - first_aggregate) * coarse_dof * 2;
                float re = 0, im = 0;
#pragma omp simd reduction(+ : re, im)
                for (int j = 0; j < coarse_dof; j++) {
                    re += row[2 * j] * v[2 * j] - row[2 * j + 1] * v[2 * j + 1];
                    im += row[2 * j] * v[2 * j + 1] + row[2 * j + 1] * v[2 * j];
                }
                out[((cb - first_aggregate) * coarse_dof + a) * 2] = re;
                out[((cb - first_aggregate) * coarse_dof + a) * 2 + 1] = im;
            }
        }
}

void NativeMG::Impl::coarse_copy_color(const FloatField &src, FloatField &out, int color) const {
    out.assign(src.size(), 0.f);
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        if (colors[cb] == color) {
            const size_t begin = (size_t)(cb - first_aggregate) * coarse_dof * 2;
            std::copy_n(src.data() + begin, coarse_dof * 2, out.data() + begin);
        }
}

void NativeMG::Impl::coarse_schur(const FloatField &even, FloatField &out) const {
    if (!coarse_fused) {
        FloatField hop, eliminated, extended;
        coarse_apply(even, hop, 1, false);
        coarse_diagonal(hop, eliminated, 1, true);
        coarse_copy_color(even, extended, 0);
        coarse_axpy(extended, -1., eliminated);
        coarse_apply(extended, out, 0, true);
        return;
    }
    // Keep both halo stages. Between them, inverse application and extended
    // vector construction share one team and overwrite every owned component.
    prepare_coarse_columns();
    coarse_schur_hop.resize(even.size());
    coarse_schur_extended.resize(even.size());
    coarse_apply(even, coarse_schur_hop, 1, false);
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; ++cb) {
        const size_t offset = (size_t)(cb - first_aggregate) * coarse_dof * 2;
        float *dest = coarse_schur_extended.data() + offset;
        if (colors[cb] == 0) {
            std::copy_n(even.data() + offset, coarse_dof * 2, dest);
            continue;
        }
        const float *v = coarse_schur_hop.data() + offset;
#if defined(LQCD_NATIVE_SVE_COARSE)
        if (coarse_sve) {
            lqcd_native::kernels::coarse_gemv_sve(coarse_dof,
                coarse_inverse_column_block(cb),
                v, dest, false);
            for (int a = 0; a < coarse_dof * 2; ++a) dest[a] = -dest[a];
            continue;
        }
#endif
        for (int a = 0; a < coarse_dof; ++a) {
            const float *row = coarse_inverse.data() + ((size_t)cb * coarse_dof + a) * coarse_dof * 2;
            float re = 0, im = 0;
#pragma omp simd reduction(+ : re, im)
            for (int j = 0; j < coarse_dof; ++j) {
                re += row[2*j] * v[2*j] - row[2*j+1] * v[2*j+1];
                im += row[2*j] * v[2*j+1] + row[2*j+1] * v[2*j];
            }
            dest[2*a] = -re;
            dest[2*a+1] = -im;
        }
    }
    coarse_apply(coarse_schur_extended, out, 0, true);
}

void NativeMG::Impl::coarse_reduced_rhs(const FloatField &b, FloatField &reduced) const {
    FloatField odd, hop;
    coarse_diagonal(b, odd, 1, true);
    coarse_apply(odd, hop, 0, false);
    coarse_copy_color(b, reduced, 0);
    coarse_axpy(reduced, -1., hop);
}

void NativeMG::Impl::coarse_reconstruct(const FloatField &b, const FloatField &even,
                                        FloatField &out) const {
    FloatField hop, rhs, odd;
    coarse_apply(even, hop, 1, false);
    coarse_copy_color(b, rhs, 1);
    coarse_axpy(rhs, -1., hop);
    coarse_diagonal(rhs, odd, 1, true);
    coarse_copy_color(even, out, 0);
    coarse_axpy(out, 1., odd);
}

void NativeMG::Impl::coarse_solve_eo(const FloatField &b, FloatField &out) const {
    const double bn = coarse_norm(b);
    out.assign(b.size(), 0.f);
    if (bn == 0)
        return;
    FloatField reduced, r, x(b.size(), 0.f);
    coarse_reduced_rhs(b, reduced);
    r = reduced;
    double rn = coarse_norm(r);
    std::vector<FloatField> zs, qs;
    for (int it = 0; it < coarse_it && rn >= coarse_tolerance * bn; it++) {
        FloatField z, q;
        coarse_diagonal(r, z, 0, true);
        coarse_schur(z, q);
        if (coarse_cgs2 && qs.size() > 2) {
            coarse_cgs2_project(q, z, qs, zs);
        } else {
            for (size_t j = 0; j < qs.size(); j++) {
                const Complex beta = coarse_dot(qs[j], q);
                coarse_axpy(q, -beta, qs[j]);
                coarse_axpy(z, -beta, zs[j]);
            }
        }
        if (setting("LQCD_GCR_FUSED", 1)) {
            if (!coarse_gcr_fused_step(q, z, x, r, rn))
                break;
        } else {
            const double den = coarse_norm(q);
            if (den < 1e-30)
                break;
            for (float &v : q)
                v /= den;
            for (float &v : z)
                v /= den;
            const Complex alpha = coarse_dot(q, r);
            coarse_axpy(x, alpha, z);
            coarse_axpy(r, -alpha, q);
            rn = coarse_norm(r);
        }
        zs.push_back(std::move(z));
        qs.push_back(std::move(q));
        if (rn < coarse_tolerance * bn || qs.size() == 16) {
            FloatField actual;
            coarse_schur(x, actual);
            r = reduced;
            coarse_axpy(r, -1., actual);
            rn = coarse_norm(r);
            zs.clear();
            qs.clear();
        }
    }
    // A capped approximate coarse solve remains a valid flexible MG
    // preconditioner; only the outer double full residual accepts a solve.
    coarse_reconstruct(b, x, out);
}

void NativeMG::Impl::coarse_solve(const FloatField &b, FloatField &x) const {
    if (coarse_eo) {
        coarse_solve_eo(b, x);
        return;
    }
    x.assign(b.size(), 0);
    FloatField r = b;
    double bn = coarse_norm(b);
    if (bn == 0)
        return;
    std::vector<FloatField> zs, qs;
    for (int it = 0; it < coarse_it; it++) {
        FloatField z(r.size()), q;
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            for (int a = 0; a < coarse_dof; a++) {
                const float *row = coarse_inverse.data() +
                                   ((size_t)cb * coarse_dof + a) * coarse_dof * 2,
                            *v = r.data() + (size_t)(cb - first_aggregate) * coarse_dof * 2;
                float re = 0, im = 0;
#pragma omp simd reduction(+ : re, im)
                for (int j = 0; j < coarse_dof; j++) {
                    re += row[2 * j] * v[2 * j] - row[2 * j + 1] * v[2 * j + 1];
                    im += row[2 * j] * v[2 * j + 1] + row[2 * j + 1] * v[2 * j];
                }
                z[((cb - first_aggregate) * coarse_dof + a) * 2] = re;
                z[((cb - first_aggregate) * coarse_dof + a) * 2 + 1] = im;
            }
        coarse_apply(z, q);
        if (coarse_cgs2 && qs.size() > 2) {
            coarse_cgs2_project(q, z, qs, zs);
        } else {
            for (size_t j = 0; j < qs.size(); j++) {
                Complex beta = coarse_dot(qs[j], q);
                coarse_axpy(q, -beta, qs[j]);
                coarse_axpy(z, -beta, zs[j]);
            }
        }
        double rn;
        if (setting("LQCD_GCR_FUSED", 1)) {
            if (!coarse_gcr_fused_step(q, z, x, r, rn))
                break;
        } else {
            double den = coarse_norm(q);
            if (den < 1e-30)
                break;
            for (float &v : q)
                v /= den;
            for (float &v : z)
                v /= den;
            Complex alpha = coarse_dot(q, r);
            coarse_axpy(x, alpha, z);
            coarse_axpy(r, -alpha, q);
            rn = coarse_norm(r);
        }
        zs.push_back(std::move(z));
        qs.push_back(std::move(q));
        if (rn < coarse_tolerance * bn)
            break;
        if (qs.size() == 16) {
            zs.clear();
            qs.clear();
            coarse_apply(x, q);
            r = b;
            coarse_axpy(r, -1., q);
        }
    }
}
