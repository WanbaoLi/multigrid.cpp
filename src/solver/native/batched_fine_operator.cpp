#include "hierarchy.hpp"
#include "kernels.hpp"
#include <climits>
using namespace lqcd_native::detail;

void NativeMG::Impl::fine_apply_batch(const std::vector<const FloatField *> &sources,
                                      const std::vector<FloatField *> &outputs, int color) const {
    const int nrhs = sources.size();
    if (nrhs < 1 || nrhs > 12 || outputs.size() != sources.size())
        throw std::runtime_error("fine batch requires one to twelve matching fields");
    if (nrhs == 1) {
        fine_apply(*sources[0], *outputs[0], color);
        return;
    }
    for (int r = 0; r < nrhs; r++)
        outputs[r]->resize(sources[r]->size());
    auto whole = [&](int cb) {
        for (int r = 0; r < nrhs; r++)
            block_apply(cb, sources[r]->data(), outputs[r]->data() + (size_t)cb * 24 * block_sites,
                        false);
    };
    if (native_size == 1) {
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++)
            if (color < 0 || colors[cb] == color)
                whole(cb);
        return;
    }
    const int bt = hierarchy.o.bt, face = block_sites / bt;
    const size_t per_face = (size_t)aggregates_per_tslice * 24 * face;
    if (per_face > (size_t)INT_MAX / nrhs)
        throw std::runtime_error("fine batch halo exceeds MPI int count");
    const int count = (int)(per_face * nrhs);
    send_lower.resize(count);
    send_upper.resize(count);
    recv_lower.resize(count);
    recv_upper.resize(count);
    HaloTrace trace(fine_halo_stats, profile_active);
    const int prev = (native_rank + native_size - 1) % native_size,
              next = (native_rank + 1) % native_size;
    MPI_Request requests[4];
    auto pack = [&](int j) {
        const int cb = j / 24, component = j % 24;
        const size_t lo = ((size_t)(first_aggregate + cb) * 24 + component) * block_sites;
        const size_t hi =
            ((size_t)(end_aggregate - aggregates_per_tslice + cb) * 24 + component) * block_sites;
        for (int r = 0; r < nrhs; r++) {
            const float *src = sources[r]->data();
            const size_t dst = r * per_face + (size_t)j * face;
            if (sap_eo)
                for (int p = 0; p < 2; p++) {
                    const size_t slot = p * (block_sites / 2), off = dst + p * (face / 2);
                    std::copy_n(src + lo + slot, face / 2, send_lower.data() + off);
                    std::copy_n(src + hi + slot + (block_sites - face) / 2, face / 2,
                                send_upper.data() + off);
                }
            else {
                std::copy_n(src + lo, face, send_lower.data() + dst);
                std::copy_n(src + hi + block_sites - face, face, send_upper.data() + dst);
            }
        }
    };
    auto exchange = [&] {
        MPI_Irecv(recv_upper.data(), count, MPI_FLOAT, next, 10, native_comm, &requests[0]);
        MPI_Irecv(recv_lower.data(), count, MPI_FLOAT, prev, 11, native_comm, &requests[1]);
        MPI_Isend(send_lower.data(), count, MPI_FLOAT, prev, 10, native_comm, &requests[2]);
        MPI_Isend(send_upper.data(), count, MPI_FLOAT, next, 11, native_comm, &requests[3]);
        trace.post(count);
        const double start = trace.now();
        MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
        trace.wait(start);
        // Main-thread sequential unpack is necessary for coincident periodic
        // ghost faces (two ranks, one aggregate and bt=1).
        for (int j = 0; j < aggregates_per_tslice * 24; j++) {
            const int cb = j / 24, component = j % 24;
            const size_t lo =
                ((size_t)((first_aggregate - aggregates_per_tslice + aggregate_count) %
                              aggregate_count +
                          cb) *
                     24 +
                 component) *
                block_sites;
            const size_t hi =
                ((size_t)(end_aggregate % aggregate_count + cb) * 24 + component) * block_sites;
            for (int r = 0; r < nrhs; r++) {
                float *src = const_cast<float *>(sources[r]->data());
                const size_t from = r * per_face + (size_t)j * face;
                if (sap_eo)
                    for (int p = 0; p < 2; p++) {
                        const size_t slot = p * (block_sites / 2), off = from + p * (face / 2);
                        std::copy_n(recv_lower.data() + off, face / 2,
                                    src + lo + slot + (block_sites - face) / 2);
                        std::copy_n(recv_upper.data() + off, face / 2, src + hi + slot);
                    }
                else {
                    std::copy_n(recv_lower.data() + from, face, src + lo + block_sites - face);
                    std::copy_n(recv_upper.data() + from, face, src + hi);
                }
            }
        }
    };
    auto range = [&](int cb, int begin_t, int end_t) {
        if (begin_t >= end_t)
            return;
        if (begin_t == 0 && end_t == bt) {
            whole(cb);
            return;
        }
        const int parities = sap_eo ? 2 : 1, ps = block_sites / parities, pf = face / parities;
        for (int r = 0; r < nrhs; r++)
            for (int p = 0; p < parities; p++) {
                const float *src = sources[r]->data();
                float *dst = outputs[r]->data() + (size_t)cb * 24 * block_sites;
                const int begin = p * ps + begin_t * pf, end = p * ps + end_t * pf;
#if defined(LQCD_NATIVE_PACKED_WILSON)
                if (use_packed_coefficients && fine_sites <= (size_t)INT_MAX / 24) {
                    const size_t off = (size_t)(cb - first_aggregate) * packed_block_stride;
                    lqcd_native::kernels::wilson_avx512<true, int, true>(
                        block_sites, packed_diag.data() + off, packed_links.data() + off,
                        neighbor32.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, dst,
                        begin, end, (size_t)cb * 24 * block_sites);
                    continue;
                }
#endif
                lqcd_native::kernels::wilson_clover_global_range(
                    cb, block_sites, diag_block(cb),
                    links_block(cb),
                    neighbor.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, dst, begin,
                    end, fine_sites * 24
#if defined(LQCD_NATIVE_ARM_WILSON)
                    , neighbor32.empty() ? nullptr : neighbor32.data() + (size_t)cb * 8 * block_sites
#endif
                );
            }
    };
    const auto &interior = fine_interior_work[color < 0 ? 0 : color + 1];
    const auto &boundary = fine_boundary_work[color < 0 ? 0 : color + 1];
#pragma omp parallel
    {
        const int tid = omp_get_thread_num();
#pragma omp for schedule(static)
        for (int j = 0; j < aggregates_per_tslice * 24; j++)
            pack(j);
        if (tid == 0)
            exchange();
        if (halo_overlap) {
            const double start = trace.now();
#pragma omp for schedule(static) nowait
            for (int i = 0; i < (int)interior.size(); i++) {
                const int cb = interior[i];
                range(cb, cb < first_aggregate + aggregates_per_tslice ? 1 : 0,
                      bt - (cb >= end_aggregate - aggregates_per_tslice ? 1 : 0));
            }
            trace.interior(tid, start);
#pragma omp barrier
            if (tid == 0)
                trace.region();
            const double boundary_start = trace.now();
#pragma omp for schedule(static)
            for (int i = 0; i < (int)boundary.size(); i++) {
                const int cb = boundary[i];
                const bool lo = cb < first_aggregate + aggregates_per_tslice,
                           hi = cb >= end_aggregate - aggregates_per_tslice;
                if (lo && hi && bt <= 2)
                    whole(cb);
                else {
                    if (lo)
                        range(cb, 0, 1);
                    if (hi)
                        range(cb, bt - 1, bt);
                }
            }
            trace.boundary(tid, boundary_start);
        } else {
#pragma omp barrier
#pragma omp for schedule(static)
            for (int cb = first_aggregate; cb < end_aggregate; cb++)
                if (color < 0 || colors[cb] == color)
                    whole(cb);
        }
    }
}
