#include "hierarchy.hpp"
#include "../../support/hbm_placement.hpp"
#include <iostream>
#include <limits>

using namespace lqcd_native::detail;

void NativeMG::place_hot_data() {
    impl->prepare_hbw_assets();
    namespace hbm = lqcd_native::hbm;
    const auto plan = hbm::from_environment();
    const int mode = static_cast<int>(plan.mode);
    int minimum, maximum;
    MPI_Allreduce(&mode, &minimum, 1, MPI_INT, MPI_MIN, native_comm);
    MPI_Allreduce(&mode, &maximum, 1, MPI_INT, MPI_MAX, native_comm);
    int invalid = minimum != maximum || (plan.mode == hbm::Mode::Off && !plan.error.empty());
    MPI_Allreduce(MPI_IN_PLACE, &invalid, 1, MPI_INT, MPI_MAX, native_comm);
    if (invalid)
        throw std::runtime_error("HBM mode must be off/prefer/require and agree across ranks");
    if (plan.mode == hbm::Mode::Off)
        return;

    auto &m = *impl;
    const size_t owned = m.end_aggregate - m.first_aggregate;
    struct HotRange { const char *name; hbm::Range range; };
    std::vector<HotRange> hot;
    auto add = [&](const char *name, auto &field, size_t per_block) {
        if (field.empty())
            return;
        using T = typename std::decay_t<decltype(field)>::value_type;
        hot.push_back({name, {field.data() + (size_t)m.first_aggregate * per_block,
                              owned * per_block * sizeof(T)}});
    };
    const size_t B = m.block_sites, C = m.coarse_dof;
    add("links", m.links, 144 * B);
    add("diag", m.diag, 144 * B);
    add("clover_inverse", m.clover_inverse, 144 * B);
    add("basis", m.basis, 24 * 12 * 2 * B);
    add("coarse", m.coarse, 9 * C * C * 2);
    add("coarse_inverse", m.coarse_inverse, C * C * 2);
    add("neighbor", m.neighbor, 8 * B);
    add("neighbor32", m.neighbor32, 8 * B);
    add("inner", m.inner, 8 * B);
    // Cap this migration request at 1GiB/rank; this is not a reservation or
    // a discovery of hardware capacity. Untargeted storage keeps its existing
    // allocator/numactl policy (which need not be DDR).
    constexpr size_t budget = size_t(1024) * 1024 * 1024;
    size_t used = 0, bound = 0, samples = 0, resident = 0, skipped = 0;
    int failed = !plan.error.empty();
    // This path migrates already allocated/touched pages. It does not select
    // KUPL or memkind allocation, and memory-only is only a topology hint;
    // actual residency is reported below by move_pages samples.
    std::set<int> allowed_nodes;
    const bool allowed_known = hbm::allowed_mems(allowed_nodes);
    std::ostringstream allowed_text;
    for (int node : allowed_nodes)
        allowed_text << (allowed_text.tellp() > 0 ? "," : "") << node;
    std::cerr << "HBM rank=" << native_rank << " cpu_node=" << plan.cpu_node
              << " target=" << plan.memory_node << " mode=" << mode
              << " allocator=posix_memalign migration=mbind_MOVE residency_query=move_pages"
              << " allowed_mems=" << (allowed_known ? allowed_text.str() : "unknown")
              << " hardware_memory_mode=unknown target_kind=memory_only_candidate"
              << " first_touch_policy=inherited_at_initialization"
              << " original_residency=unmeasured";
    if (!plan.error.empty())
        std::cerr << " error=" << plan.error;
    std::cerr << '\n';
    for (const auto &item : hot) {
        if (item.range.bytes > budget - used) {
            skipped += item.range.bytes;
            continue;
        }
        used += item.range.bytes;
        auto report = hbm::place(plan, item.range);
        bound += report.bound_bytes;
        samples += report.sampled_pages;
        resident += report.resident_on_target;
        failed |= !report.requirement_met;
        std::cerr << "HBM rank=" << native_rank << " range=" << item.name
                  << " eligible_bytes=" << report.eligible_bytes
                  << " bound_bytes=" << report.bound_bytes
                  << " samples=" << report.sampled_pages
                  << " target_pages=" << report.resident_on_target
                  << " elsewhere_pages=" << report.elsewhere
                  << " unknown_pages=" << report.unknown
                  << " attempted=" << report.attempted
                  << " mbind_rc=" << report.mbind_rc
                  << " mbind_errno=" << report.mbind_errno
                  << " query_rc=" << report.query_rc
                  << " query_errno=" << report.query_errno
                  << " error=" << report.error << '\n';
    }
    std::cerr << "HBM rank=" << native_rank << " summary_bytes=" << bound
              << " sampled_target=" << resident << '/' << samples
              << " budget_skipped_bytes=" << skipped << '\n';
    MPI_Allreduce(MPI_IN_PLACE, &failed, 1, MPI_INT, MPI_MAX, native_comm);
    if (failed && plan.mode == hbm::Mode::Require)
        throw std::runtime_error("HBM placement or sampled residency verification failed on at least one rank");
}
