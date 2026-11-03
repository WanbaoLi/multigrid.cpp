#include "hierarchy.hpp"
#include "kernels.hpp"
#include <climits>

using namespace lqcd_native::detail;

// This copy deliberately keeps the scalar row/direction/column accumulation
// order, including the SVE kernel's add contract. Only ghost ownership differs.
// The old scalar helper and its scratch buffers remain unchanged.
void NativeMG::Impl::coarse_block_apply_ghosts(int cb, const FloatField &src, FloatField &out,
                                               const float *lower, const float *upper,
                                               int dir_begin, int dir_end, bool add) const {
#if defined(LQCD_NATIVE_SVE_COARSE)
    if (coarse_sve) {
        const size_t stride = (size_t)coarse_dof * coarse_dof * 2;
        float *dest = out.data() + (size_t)(cb-first_aggregate)*coarse_dof*2;
        for (int dir = dir_begin; dir < dir_end; ++dir) {
            const int nb = cneighbor[cb*9+dir];
            const float *v;
            if (nb >= first_aggregate && nb < end_aggregate)
                v = src.data() + (size_t)(nb-first_aggregate)*coarse_dof*2;
            else
                v = (dir == 7 ? upper : lower) +
                    (size_t)(nb%aggregates_per_tslice)*coarse_dof*2;
            lqcd_native::kernels::coarse_gemv_sve(coarse_dof,
                coarse_column_block(cb)+(size_t)dir*stride, v, dest, add);
            add = true;
        }
        return;
    }
#endif
    for (int a = 0; a < coarse_dof; a++) {
        const size_t output = ((size_t)(cb-first_aggregate)*coarse_dof+a)*2;
        float re = add ? out[output] : 0.f, im = add ? out[output+1] : 0.f;
        for (int dir = dir_begin; dir < dir_end; dir++) {
            const int nb = cneighbor[cb*9+dir];
            const float *v;
            if (nb >= first_aggregate && nb < end_aggregate)
                v = src.data() + (size_t)(nb-first_aggregate)*coarse_dof*2;
            else
                v = (dir == 7 ? upper : lower) +
                    (size_t)(nb%aggregates_per_tslice)*coarse_dof*2;
            const float *row =
                coarse.data() + ((size_t)(cb*9+dir)*coarse_dof+a)*coarse_dof*2;
#pragma omp simd reduction(+ : re, im)
            for (int j = 0; j < coarse_dof; j++) {
                re += row[2*j]*v[2*j] - row[2*j+1]*v[2*j+1];
                im += row[2*j]*v[2*j+1] + row[2*j+1]*v[2*j];
            }
        }
        out[output] = re;
        out[output+1] = im;
    }
}

void NativeMG::Impl::coarse_apply_batch(const std::vector<const FloatField *> &sources,
                                        const std::vector<FloatField *> &outputs,
                                        int color, bool diagonal) const {
    const size_t nrhs = sources.size();
    if (nrhs < 1 || nrhs > 12 || outputs.size() != nrhs)
        throw std::runtime_error("coarse halo batch requires one to twelve matching fields");
    // Keep the established scalar behavior whenever there is no MPI message
    // to combine. A single remaining active RHS is a normal, supported tail.
    if (!coarse_batch_halo || nrhs == 1 || native_size == 1) {
        for (size_t r = 0; r < nrhs; ++r)
            coarse_apply(*sources[r], *outputs[r], color, diagonal);
        return;
    }
    prepare_coarse_columns();
    const size_t owned = (size_t)(end_aggregate-first_aggregate)*coarse_dof*2;
    const size_t face = (size_t)aggregates_per_tslice*coarse_dof*2;
    if (face > (size_t)INT_MAX/nrhs)
        throw std::runtime_error("coarse batch halo exceeds MPI int count");
    for (size_t r = 0; r < nrhs; ++r) {
        if (sources[r]->size() != owned || sources[r] == outputs[r])
            throw std::runtime_error("coarse batch halo needs distinct owned input/output fields");
        if (color < 0)
            outputs[r]->resize(owned);
        else
            outputs[r]->assign(owned, 0.f);
    }
    HaloTrace trace(coarse_halo_stats, profile_active);
    const int count = (int)(face*nrhs);
    coarse_batch_send_lower.resize(count);
    coarse_batch_send_upper.resize(count);
    coarse_batch_recv_lower.resize(count);
    coarse_batch_recv_upper.resize(count);
    for (size_t r = 0; r < nrhs; ++r) {
        std::copy_n(sources[r]->data(), face, coarse_batch_send_lower.data()+r*face);
        std::copy_n(sources[r]->data()+owned-face, face,
                    coarse_batch_send_upper.data()+r*face);
    }
    // Every rank receives the same globally determined active RHS order.
    // Tags40/41 are distinct from scalar coarse20/21 and double30/31. All
    // requests finish within this call, including coincident periodic peers.
    const int prev = (native_rank+native_size-1)%native_size;
    const int next = (native_rank+1)%native_size;
    MPI_Request requests[4];
    MPI_Irecv(coarse_batch_recv_upper.data(), count, MPI_FLOAT, next, 40, native_comm, &requests[0]);
    MPI_Irecv(coarse_batch_recv_lower.data(), count, MPI_FLOAT, prev, 41, native_comm, &requests[1]);
    MPI_Isend(coarse_batch_send_lower.data(), count, MPI_FLOAT, prev, 40, native_comm, &requests[2]);
    MPI_Isend(coarse_batch_send_upper.data(), count, MPI_FLOAT, next, 41, native_comm, &requests[3]);
    trace.post(count);
    ++coarse_batch_halo_stats.calls;
    coarse_batch_halo_stats.send_bytes += 2ULL*count*sizeof(float);
    coarse_batch_halo_stats.rhs_slots += nrhs;
    coarse_batch_halo_stats.max_width = std::max(coarse_batch_halo_stats.max_width, (int)nrhs);
    auto apply_range = [&](int cb, int first, int last, bool add) {
        // Block outer, RHS inner reuses the coefficient block. No cross-RHS
        // arithmetic or change to each RHS's direction/column summation order.
        for (size_t r = 0; r < nrhs; ++r)
            coarse_block_apply_ghosts(cb, *sources[r], *outputs[r],
                coarse_batch_recv_lower.data()+r*face,
                coarse_batch_recv_upper.data()+r*face, first, last, add);
    };
    auto whole = [&](int cb) { apply_range(cb, diagonal ? 0 : 1, 9, false); };
    auto selected = [&](int cb) { return color < 0 || colors[cb] == color; };
    const int interior_first = first_aggregate+aggregates_per_tslice;
    const int interior_last = std::max(interior_first, end_aggregate-aggregates_per_tslice);
    if (halo_overlap && coarse_spatial_overlap && interior_first == interior_last &&
        omp_get_max_threads() > 1) {
#pragma omp parallel
        {
            const int tid = omp_get_thread_num(), threads = omp_get_num_threads();
            if (threads == 1) {
                // OMP_THREAD_LIMIT/dynamic teams may shrink the actual team.
                const double start = trace.now();
                MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
                trace.wait(start);
                const double work = trace.now();
                for (int cb = first_aggregate; cb < end_aggregate; ++cb)
                    if (selected(cb)) whole(cb);
                trace.compute_all(work);
            } else {
                if (tid == 0) {
                    const double start = trace.now();
                    MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
                    trace.wait(start);
                } else {
                    const double work = trace.now();
                    const int n = end_aggregate-first_aggregate;
                    const int begin = first_aggregate+n*(tid-1)/(threads-1);
                    const int end = first_aggregate+n*tid/(threads-1);
                    for (int cb = begin; cb < end; ++cb)
                        if (selected(cb)) apply_range(cb, diagonal ? 0 : 1, 7, false);
                    trace.interior(tid, work);
                }
                // Receives and every local prefix are complete before use.
#pragma omp barrier
                if (tid == 0) trace.region();
                const double work = trace.now();
#pragma omp for schedule(static)
                for (int cb = first_aggregate; cb < end_aggregate; ++cb)
                    if (selected(cb)) apply_range(cb, 7, 9, true);
                trace.boundary(tid, work);
            }
        }
        return;
    }
    if (!halo_overlap || (coarse_empty_interior && interior_first == interior_last)) {
        const double start = trace.now();
        MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
        trace.wait(start);
        const double work = trace.now();
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; ++cb)
            if (selected(cb)) whole(cb);
        trace.compute_all(work);
        return;
    }
#pragma omp parallel
    {
        const int tid = omp_get_thread_num(), threads = omp_get_num_threads();
        if (tid == 0) {
            const double start = trace.now();
            MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
            trace.wait(start);
            if (threads == 1) {
                const double work = trace.now();
                for (int cb = interior_first; cb < interior_last; ++cb)
                    if (selected(cb)) whole(cb);
                trace.interior(tid, work);
            }
        } else {
            const double work = trace.now();
            const int n = interior_last-interior_first;
            const int begin = interior_first+n*(tid-1)/(threads-1);
            const int end = interior_first+n*tid/(threads-1);
            for (int cb = begin; cb < end; ++cb)
                if (selected(cb)) whole(cb);
            trace.interior(tid, work);
        }
#pragma omp barrier
        if (tid == 0) trace.region();
        const double work = trace.now();
#pragma omp for schedule(static)
        for (int i = 0; i < std::min(end_aggregate-first_aggregate, 2*aggregates_per_tslice); ++i) {
            const int cb = i < aggregates_per_tslice ? first_aggregate+i :
                end_aggregate-aggregates_per_tslice+i-aggregates_per_tslice;
            if (selected(cb)) whole(cb);
        }
        trace.boundary(tid, work);
    }
}

void NativeMG::Impl::coarse_schur_batch(const std::vector<const FloatField *> &sources,
                                        const std::vector<FloatField *> &outputs) const {
    const size_t nrhs = sources.size();
    std::vector<FloatField> hop(nrhs), extended(nrhs);
    std::vector<const FloatField *> inputs(nrhs);
    std::vector<FloatField *> targets(nrhs);
    for (size_t r = 0; r < nrhs; ++r) targets[r] = &hop[r];
    coarse_apply_batch(sources, targets, 1, false);
    if (!coarse_fused) {
        for (size_t r = 0; r < nrhs; ++r) {
            FloatField eliminated;
            coarse_diagonal(hop[r], eliminated, 1, true);
            coarse_copy_color(*sources[r], extended[r], 0);
            coarse_axpy(extended[r], -1., eliminated);
        }
    } else {
        // Same inverse/negation arithmetic as the established fused Schur.
        prepare_coarse_columns();
        for (size_t r = 0; r < nrhs; ++r) extended[r].resize(sources[r]->size());
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; ++cb) {
            const size_t offset = (size_t)(cb-first_aggregate)*coarse_dof*2;
            for (size_t r = 0; r < nrhs; ++r) {
                float *dest = extended[r].data()+offset;
                if (colors[cb] == 0) {
                    std::copy_n(sources[r]->data()+offset, coarse_dof*2, dest);
                    continue;
                }
                const float *v = hop[r].data()+offset;
#if defined(LQCD_NATIVE_SVE_COARSE)
                if (coarse_sve) {
                    lqcd_native::kernels::coarse_gemv_sve(coarse_dof,
                        coarse_inverse_column_block(cb), v, dest, false);
                    for (int a = 0; a < coarse_dof*2; ++a) dest[a] = -dest[a];
                    continue;
                }
#endif
                for (int a = 0; a < coarse_dof; ++a) {
                    const float *row = coarse_inverse.data()+((size_t)cb*coarse_dof+a)*coarse_dof*2;
                    float re = 0, im = 0;
#pragma omp simd reduction(+ : re, im)
                    for (int j = 0; j < coarse_dof; ++j) {
                        re += row[2*j]*v[2*j]-row[2*j+1]*v[2*j+1];
                        im += row[2*j]*v[2*j+1]+row[2*j+1]*v[2*j];
                    }
                    dest[2*a] = -re;
                    dest[2*a+1] = -im;
                }
            }
        }
    }
    for (size_t r = 0; r < nrhs; ++r) inputs[r] = &extended[r];
    coarse_apply_batch(inputs, outputs, 0, true);
}

void NativeMG::Impl::coarse_reduced_rhs_batch(const std::vector<const FloatField *> &sources,
                                              const std::vector<FloatField *> &outputs) const {
    const size_t nrhs = sources.size();
    std::vector<FloatField> odd(nrhs), hop(nrhs);
    std::vector<const FloatField *> inputs(nrhs);
    std::vector<FloatField *> targets(nrhs);
    for (size_t r = 0; r < nrhs; ++r) {
        coarse_diagonal(*sources[r], odd[r], 1, true);
        inputs[r] = &odd[r];
        targets[r] = &hop[r];
    }
    coarse_apply_batch(inputs, targets, 0, false);
    for (size_t r = 0; r < nrhs; ++r) {
        coarse_copy_color(*sources[r], *outputs[r], 0);
        coarse_axpy(*outputs[r], -1., hop[r]);
    }
}

void NativeMG::Impl::coarse_reconstruct_batch(const std::vector<const FloatField *> &sources,
                                              const std::vector<const FloatField *> &solutions,
                                              const std::vector<FloatField *> &outputs) const {
    const size_t nrhs = sources.size();
    std::vector<FloatField> hop(nrhs);
    std::vector<FloatField *> targets(nrhs);
    for (size_t r = 0; r < nrhs; ++r) targets[r] = &hop[r];
    coarse_apply_batch(solutions, targets, 1, false);
    for (size_t r = 0; r < nrhs; ++r) {
        FloatField rhs, odd;
        coarse_copy_color(*sources[r], rhs, 1);
        coarse_axpy(rhs, -1., hop[r]);
        coarse_diagonal(rhs, odd, 1, true);
        coarse_copy_color(*solutions[r], *outputs[r], 0);
        coarse_axpy(*outputs[r], 1., odd);
    }
}
