#include "hierarchy.hpp"
#include "kernels.hpp"

using namespace lqcd_native::detail;

void NativeMG::Impl::local_range(int cb, const float *src, float *out, int parity,
                                 bool clover) const {
#if defined(LQCD_NATIVE_PACKED_WILSON)
    if (use_packed_coefficients) {
        const size_t off = (size_t)(cb - first_aggregate) * packed_block_stride;
        const int begin = parity * (block_sites / 2), end = begin + block_sites / 2;
        if (clover)
            lqcd_native::kernels::wilson_avx512<true, int, true>(
                block_sites, packed_diag.data() + off, packed_links.data() + off,
                inner.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, out, begin, end, 0,
                local_contiguous ? local_load_offsets.data() + (size_t)(cb - first_aggregate) * 16
                                 : nullptr);
        else
            lqcd_native::kernels::wilson_avx512<false, int, true>(
                block_sites, packed_diag.data() + off, packed_links.data() + off,
                inner.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, out, begin, end, 0,
                local_contiguous ? local_load_offsets.data() + (size_t)(cb - first_aggregate) * 16
                                 : nullptr);
        return;
    }
#endif
    lqcd_native::kernels::wilson_clover_local_range(
        cb, block_sites, diag_block(cb),
        links_block(cb), inner.data() + (size_t)cb * 8 * block_sites,
        gp, gr, gi, src, out, parity, clover
#if defined(LQCD_NATIVE_ARM_WILSON)
        , local_contiguous ? local_load_offsets.data() + (size_t)(cb - first_aggregate) * 16
                           : nullptr
#endif
    );
}

void NativeMG::Impl::clover_range(int cb, const float *src, float *out, int parity,
                                  bool inverse) const {
    const float *matrix =
        (inverse ? inverse_block(cb) : diag_block(cb));
    const int begin = parity * (block_sites / 2), end = begin + block_sites / 2;
#if defined(LQCD_NATIVE_PACKED_WILSON)
    if (lqcd_native::kernels::wilson_simd_enabled()) {
        if (use_packed_coefficients) {
            const size_t off = (size_t)(cb - first_aggregate) * packed_block_stride;
            matrix = (inverse ? packed_inverse.data() : packed_diag.data()) + off;
            lqcd_native::kernels::clover_range_avx512<true>(block_sites, matrix, src, out, begin, end);
        } else
            lqcd_native::kernels::clover_range_avx512(block_sites, matrix, src, out, begin, end);
        return;
    }
#endif
#if defined(LQCD_NATIVE_NEON_CLOVER)
    lqcd_native::kernels::clover_range_neon(block_sites, matrix, src, out, begin, end);
    return;
#endif
    for (int a = 0; a < 12; a++) {
        float *yr = out + 2 * a * block_sites, *yi = yr + block_sites;
#pragma omp simd
        for (int s = begin; s < end; s++) {
            yr[s] = 0;
            yi[s] = 0;
        }
        for (int j = 0; j < 6; j++) {
            const float *xr = src + 2 * ((a / 6) * 6 + j) * block_sites, *xi = xr + block_sites;
            const float *mr = matrix + (a * 6 + j) * 2 * block_sites, *mi = mr + block_sites;
#pragma omp simd
            for (int s = begin; s < end; s++) {
                yr[s] += mr[s] * xr[s] - mi[s] * xi[s];
                yi[s] += mr[s] * xi[s] + mi[s] * xr[s];
            }
        }
    }
}

void NativeMG::Impl::block_apply(int cb, const float *src, float *out, bool local) const {
#if defined(LQCD_NATIVE_PACKED_WILSON)
    if (use_packed_coefficients && (local || fine_sites <= (size_t)INT_MAX / 24)) {
        const size_t off = (size_t)(cb - first_aggregate) * packed_block_stride;
        if (local)
            lqcd_native::kernels::wilson_avx512<true, int, true>(
                block_sites, packed_diag.data() + off, packed_links.data() + off,
                inner.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, out, 0, block_sites, 0,
                local_contiguous ? local_load_offsets.data() + (size_t)(cb - first_aggregate) * 16
                                 : nullptr);
        else
            lqcd_native::kernels::wilson_avx512<true, int, true>(
                block_sites, packed_diag.data() + off, packed_links.data() + off,
                neighbor32.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, out, 0,
                block_sites, (size_t)cb * 24 * block_sites);
        return;
    }
#endif
    lqcd_native::kernels::wilson_clover_block(
        cb, block_sites, diag_block(cb),
        links_block(cb), inner.data() + (size_t)cb * 8 * block_sites,
        neighbor.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src, out, local,
        fine_sites * 24
#if defined(LQCD_NATIVE_ARM_WILSON)
        , local_contiguous ? local_load_offsets.data() + (size_t)(cb - first_aggregate) * 16
                           : nullptr,
        neighbor32.empty() ? nullptr : neighbor32.data() + (size_t)cb * 8 * block_sites
#endif
    );
}

void NativeMG::Impl::fine_apply(const FloatField &src, FloatField &out, int color) const {
    out.resize(src.size());
    const int work_slot = color < 0 ? 0 : color + 1;
    auto apply_sites = [&](int cb, int begin, int end) {
        float *dst = out.data() + (size_t)cb * 24 * block_sites;
#if defined(LQCD_NATIVE_PACKED_WILSON)
        if (use_packed_coefficients && fine_sites <= (size_t)INT_MAX / 24) {
            const size_t off = (size_t)(cb - first_aggregate) * packed_block_stride;
            lqcd_native::kernels::wilson_avx512<true, int, true>(
                block_sites, packed_diag.data() + off, packed_links.data() + off,
                neighbor32.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src.data(), dst,
                begin, end, (size_t)cb * 24 * block_sites);
            return;
        }
#endif
        lqcd_native::kernels::wilson_clover_global_range(
            cb, block_sites, diag_block(cb), links_block(cb),
            neighbor.data() + (size_t)cb * 8 * block_sites, gp, gr, gi, src.data(), dst, begin, end,
            fine_sites * 24
#if defined(LQCD_NATIVE_ARM_WILSON)
            ,
            neighbor32.empty() ? nullptr : neighbor32.data() + (size_t)cb * 8 * block_sites
#endif
        );
    };
    auto apply_all = [&] {
        fine_sites_all[work_slot].run(omp_get_thread_num(), omp_get_num_threads(), apply_sites);
    };
    if (native_size == 1) {
#pragma omp parallel
        {
            apply_all();
        }
        return;
    }
    HaloTrace trace(fine_halo_stats, profile_active);
    const int prev = (native_rank + native_size - 1) % native_size;
    const int next = (native_rank + 1) % native_size;
    // Block-local x,y,z are contiguous, t slowest.  A Wilson hop needs
    // only one physical t face, not the complete neighbouring aggregate.
    const int face = block_sites / hierarchy.o.bt, count = aggregates_per_tslice * 24 * face;
    send_lower.resize(count);
    send_upper.resize(count);
    recv_lower.resize(count);
    recv_upper.resize(count);
    auto pack_face = [&](int j) {
        const int cb = j / 24, component = j % 24;
        const size_t lo = ((size_t)(first_aggregate + cb) * 24 + component) * block_sites;
        const size_t hi =
            ((size_t)(end_aggregate - aggregates_per_tslice + cb) * 24 + component) * block_sites;
        if (sap_eo) {
            for (int p = 0; p < 2; p++) {
                const size_t slot = p * (block_sites / 2), dst = (size_t)j * face + p * (face / 2);
                std::copy_n(src.data() + lo + slot, face / 2, send_lower.data() + dst);
                std::copy_n(src.data() + hi + slot + (block_sites - face) / 2, face / 2,
                            send_upper.data() + dst);
            }
        } else {
            std::copy_n(src.data() + lo, face, send_lower.data() + (size_t)j * face);
            std::copy_n(src.data() + hi + block_sites - face, face,
                        send_upper.data() + (size_t)j * face);
        }
    };
    MPI_Request requests[4];
    auto post_halo = [&] {
        MPI_Irecv(recv_upper.data(), count, MPI_FLOAT, next, 10, native_comm, &requests[0]);
        MPI_Irecv(recv_lower.data(), count, MPI_FLOAT, prev, 11, native_comm, &requests[1]);
        MPI_Isend(send_lower.data(), count, MPI_FLOAT, prev, 10, native_comm, &requests[2]);
        MPI_Isend(send_upper.data(), count, MPI_FLOAT, next, 11, native_comm, &requests[3]);
        trace.post(count);
    };
    const bool fused_team = fine_team_fused && halo_overlap;
    if (!fused_team) {
        // Retain the separate packing team and main-thread post for the
        // diagnostic reference and for the non-overlapped path.
#pragma omp parallel for schedule(static)
        for (int j = 0; j < aggregates_per_tslice * 24; j++)
            pack_face(j);
        post_halo();
    }
    auto unpack = [&] {
        // Ghost slots are outside the owned slice.  Unpack sequentially
        // here: for two ranks with one t aggregate each and bt=1 both
        // faces name the same ghost slots (and have identical values).
        float *data = const_cast<float *>(src.data());
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
            if (sap_eo) {
                for (int p = 0; p < 2; p++) {
                    const size_t slot = p * (block_sites / 2),
                                 from = (size_t)j * face + p * (face / 2);
                    std::copy_n(recv_lower.data() + from, face / 2,
                                data + lo + slot + (block_sites - face) / 2);
                    std::copy_n(recv_upper.data() + from, face / 2, data + hi + slot);
                }
            } else {
                std::copy_n(recv_lower.data() + (size_t)j * face, face,
                            data + lo + block_sites - face);
                std::copy_n(recv_upper.data() + (size_t)j * face, face, data + hi);
            }
        }
    };
    if (!halo_overlap) {
        // Same messages and packing as the overlapped path: isolates
        // overlap effects without changing the numerical calculation.
        const double wait_start = trace.now();
        MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
        trace.wait(wait_start);
        unpack();
        const double compute_start = trace.now();
#pragma omp parallel
        {
            apply_all();
        }
        trace.compute_all(compute_start);
        return;
    }
#pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        if (fused_team) {
            // All workers finish packing before the main thread exposes the
            // send buffers to MPI. This worksharing barrier is required.
#pragma omp for schedule(static)
            for (int j = 0; j < aggregates_per_tslice * 24; j++)
                pack_face(j);
        }
        if (tid == 0) {
            if (fused_team)
                post_halo();
            // The MPI main thread drives progress while workers compute.
            // No MPI_THREAD_MULTIPLE or background progress is required.
            const double wait_start = trace.now();
            MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
            trace.wait(wait_start);
            unpack();
        }
        // Each thread owns a balanced contiguous interval of valid sites.
        // Thread zero joins after MPI progress, retaining FUNNELED semantics.
        const double work_start = trace.now();
        fine_sites_interior[work_slot].run(tid, omp_get_num_threads(), apply_sites);
        trace.interior(tid, work_start);
        // Interior workers do not read ghost slots; unpack may safely run
        // concurrently.  Boundaries require completion of both phases.
#pragma omp barrier
        if (tid == 0)
            trace.region();
        const double boundary_start = trace.now();
        fine_sites_boundary[work_slot].run(tid, omp_get_num_threads(), apply_sites);
        trace.boundary(tid, boundary_start);
    }
}

// The outer double solver stores lexical sites locally; aggregate-major float
// workspaces retain global offsets so the SIMD/SAP kernels can share indexing.
void NativeMG::Impl::encode_fine(const Field &b, FloatField &out) const {
    if (b.size() != fine_sites * 12 / native_size)
        throw std::runtime_error("native double input must contain the owned t slab");
    out.resize(fine_sites * 24);
    const size_t first_site = fine_sites * native_rank / native_size;
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int a = 0; a < 12; a++)
            for (int s = 0; s < block_sites; s++) {
                Complex z = b[(lex[(size_t)cb * block_sites + s] - first_site) * 12 + a];
                out[((size_t)cb * 24 + a * 2) * block_sites + s] = z.real();
                out[((size_t)cb * 24 + a * 2 + 1) * block_sites + s] = z.imag();
            }
}

void NativeMG::Impl::decode_fine(const FloatField &in, Field &out) const {
    out.resize(fine_sites * 12 / native_size);
    const size_t first_site = fine_sites * native_rank / native_size;
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int a = 0; a < 12; a++)
            for (int s = 0; s < block_sites; s++)
                out[(lex[(size_t)cb * block_sites + s] - first_site) * 12 + a] =
                    Complex(in[((size_t)cb * 24 + a * 2) * block_sites + s],
                            in[((size_t)cb * 24 + a * 2 + 1) * block_sites + s]);
}

Complex NativeMG::Impl::fine_dot(const FloatField &a, const FloatField &b) const {
    double re = 0, im = 0;
#pragma omp parallel for reduction(+ : re, im) schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int j = 0; j < 12; j++) {
            auto ar = a.data() + ((size_t)cb * 24 + 2 * j) * block_sites, ai = ar + block_sites,
                 br = b.data() + ((size_t)cb * 24 + 2 * j) * block_sites, bi = br + block_sites;
#pragma omp simd reduction(+ : re, im)
            for (int s = 0; s < block_sites; s++) {
                re += (double)ar[s] * br[s] + (double)ai[s] * bi[s];
                im += (double)ar[s] * bi[s] - (double)ai[s] * br[s];
            }
        }
    if (native_size > 1) {
        double sums[2] = {re, im};
        MPI_Allreduce(MPI_IN_PLACE, sums, 2, MPI_DOUBLE, MPI_SUM, native_comm);
        re = sums[0];
        im = sums[1];
    }
    return {re, im};
}

void NativeMG::Impl::fine_axpy(FloatField &y, Complex v, const FloatField &x) const {
    float vr = v.real(), vi = v.imag();
#pragma omp parallel for schedule(static)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int j = 0; j < 12; j++) {
            auto yr = y.data() + ((size_t)cb * 24 + 2 * j) * block_sites, yi = yr + block_sites;
            auto xr = x.data() + ((size_t)cb * 24 + 2 * j) * block_sites, xi = xr + block_sites;
#pragma omp simd
            for (int s = 0; s < block_sites; s++) {
                yr[s] += vr * xr[s] - vi * xi[s];
                yi[s] += vr * xi[s] + vi * xr[s];
            }
        }
}

void NativeMG::Impl::fine_copy(const FloatField &source, FloatField &dest) const {
    // Off-rank storage is a halo workspace, not a readable replicated field.
    // Copy only initialized owned entries; fine_apply fills required ghosts.
    dest.resize(source.size());
#pragma omp parallel for schedule(static)
    for (size_t k = (size_t)first_aggregate * 24 * block_sites;
         k < (size_t)end_aggregate * 24 * block_sites; k++)
        dest[k] = source[k];
}
