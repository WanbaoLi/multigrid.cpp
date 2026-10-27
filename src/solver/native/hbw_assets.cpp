#include "hierarchy.hpp"
#include <iostream>
#include <limits>

using namespace lqcd_native::detail;

void NativeMG::Impl::prepare_hbw_assets() {
    // Root owns collective policy validation. Never replace FloatField's
    // allocator: raw global setup replicas and Krylov capacity remain ordinary.
    if (hbw_policy == hbm::Policy::Off)
        return;
    constexpr size_t cap = size_t(1) << 30;
    size_t used = hbw_links.allocation_bytes() + hbw_diag.allocation_bytes() +
                  hbw_inverse.allocation_bytes() + hbw_basis.allocation_bytes() +
                  hbw_coarse_columns.allocation_bytes() + hbw_coarse_inverse_columns.allocation_bytes();
    int failed = 0;
    try {
        prepare_coarse_columns();
        const size_t owned = end_aggregate - first_aggregate;
        auto copy = [&](const char *name, const float *source, size_t elements,
                        hbm::HbwBuffer &buffer) {
            if (buffer || !elements)
                return;
            if (elements > std::numeric_limits<size_t>::max() / sizeof(float)) {
                failed = 1;
                return;
            }
            const size_t bytes = elements * sizeof(float);
            if (used > cap || bytes > cap - used || cap - used - bytes < 63) {
                std::cerr << "HBW rank=" << native_rank << " asset=" << name
                          << " bytes=" << bytes << " fallback=raw_DDR reason=rank_cap\n";
                failed |= hbw_policy == hbm::Policy::Require;
                return;
            }
            hbm::HbwBuffer candidate(bytes, 64, hbw_policy, cap - used);
            if (!candidate) {
                std::cerr << "HBW rank=" << native_rank << " asset=" << name
                          << " fallback=raw_DDR error=" << candidate.error() << '\n';
                failed |= hbw_policy == hbm::Policy::Require;
                return;
            }
            used += candidate.allocation_bytes();
            float *dest = static_cast<float *>(candidate.data());
            // Parallel first touch uses the rank's already configured CPU team.
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < elements; ++i)
                dest[i] = source[i];
            const int verified = candidate.verify_hbw();
            const auto sample = candidate.sample_pages();
            std::cerr << "HBW rank=" << native_rank << " asset=" << name
                      << " bytes=" << bytes << " provider="
                      << (candidate.backend() == hbm::Backend::KUPL ? "KUPL" : "POSIX")
                      << " fallback=" << candidate.fallback()
                      << " reason=" << candidate.fallback_reason()
                      << " sdk_verify=" << verified << " sampled_pages=" << sample.pages
                      << " query_rc=" << sample.query_rc << " query_errno=" << sample.query_errno
                      << " nodes=";
            for (int node : sample.nodes) std::cerr << node << ',';
            std::cerr << '\n';
            failed |= hbw_policy == hbm::Policy::Require && verified != 1;
            buffer = std::move(candidate);
        };
        auto raw = [&](const char *name, const FloatField &field, size_t stride,
                       hbm::HbwBuffer &buffer) {
            if (!field.empty()) copy(name, field.data() + (size_t)first_aggregate * stride,
                                     owned * stride, buffer);
        };
        const size_t B = block_sites, C = coarse_dof;
        raw("links", links, 144 * B, hbw_links);
        raw("diag", diag, 144 * B, hbw_diag);
        raw("clover_inverse", clover_inverse, 144 * B, hbw_inverse);
        raw("basis", basis, 24 * 12 * 2 * B, hbw_basis);
        copy("coarse_columns", coarse_columns.data(), coarse_columns.size(), hbw_coarse_columns);
        copy("coarse_inverse_columns", coarse_inverse_columns.data(), coarse_inverse_columns.size(),
             hbw_coarse_inverse_columns);
    } catch (const std::exception &e) {
        // All ranks still enter the final collective before require can throw.
        std::cerr << "HBW rank=" << native_rank << " allocation_error=" << e.what() << '\n';
        failed = 1;
    }
    std::cerr << "HBW rank=" << native_rank << " sidecar_bytes=" << used << " cap=" << cap
              << " raw_replicas_retained=1\n";
    MPI_Allreduce(MPI_IN_PLACE, &failed, 1, MPI_INT, MPI_MAX, native_comm);
    if (failed && hbw_policy == hbm::Policy::Require)
        throw std::runtime_error("KUPL HBW owned assets failed allocation or SDK verification");
}
