#include "hierarchy.hpp"
#include <iomanip>
#include <iostream>
#include <sstream>

using namespace lqcd_native::detail;

void NativeMG::Impl::begin_halo_profile() {
    fine_halo_stats.value.fill(0.);
    coarse_halo_stats.value.fill(0.);
    profile_active = halo_profile;
}

void NativeMG::Impl::report_halo_profile() {
    if (!profile_active)
        return;
    profile_active = false;
    double local[2 * HaloMetricCount], maximum[2 * HaloMetricCount];
    std::copy(fine_halo_stats.value.begin(), fine_halo_stats.value.end(), local);
    std::copy(coarse_halo_stats.value.begin(), coarse_halo_stats.value.end(),
              local + HaloMetricCount);
    MPI_Reduce(local, maximum, 2 * HaloMetricCount, MPI_DOUBLE, MPI_MAX, 0, native_comm);
    if (native_rank != 0)
        return;
    const char *names[HaloMetricCount] = {"calls",         "send_bytes",       "pack_post_s",
                                          "wait_s",        "interior_s",       "boundary_s",
                                          "compute_all_s", "overlap_region_s", "total_s"};
    std::ostringstream out;
    out << std::setprecision(12)
        << "native_halo_profile {\"aggregation\":\"independent_rank_max_of_local_sums\","
        << "\"ranks\":" << native_size << ",\"overlap\":" << (halo_overlap ? "true" : "false");
    for (int level = 0; level < 2; level++) {
        out << ",\"" << (level ? "coarse" : "fine") << "\":{";
        for (int k = 0; k < HaloMetricCount; k++)
            out << (k ? "," : "") << "\"" << names[k]
                << "\":" << maximum[level * HaloMetricCount + k];
        out << "}";
    }
    out << "}";
    std::cerr << out.str() << std::endl;
}
