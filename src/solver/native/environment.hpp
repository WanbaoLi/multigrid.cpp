#pragma once
#include "../../support/aligned_workspace.hpp"
#include "lqcd/core/field.h"
#include "lqcd/runtime/runtime.h"
#include <algorithm>
#include <array>
#include <mpi.h>
#include <omp.h>

// Internal environment for the single active runtime context in this process.
namespace lqcd_native::detail {
extern MPI_Comm native_comm;
extern int native_rank, native_size;
extern unsigned native_seed;
enum class SetupUpdate { Inverse, Paper };
using FloatField = std::vector<float, WorkspaceAllocator<float>>;
// Opt-in measurements of halo operations only. Timing fields are sums
// over calls on one rank; export takes an independent rank maximum for
// each field. They are not additive (wait and interior overlap in time).
enum HaloMetric {
    Calls,
    SendBytes,
    PackPost,
    Wait,
    Interior,
    Boundary,
    ComputeAll,
    OverlapRegion,
    Total,
    HaloMetricCount
};
struct HaloStats {
    std::array<double, HaloMetricCount> value{};
    std::vector<std::array<double, 2>> workers;
};
struct HaloTrace {
    HaloStats &stats;
    bool enabled;
    double begin = 0, posted = 0;
    HaloTrace(HaloStats &s, bool on) : stats(s), enabled(on) {
        if (enabled) {
            begin = wall_seconds();
            stats.workers.assign(omp_get_max_threads(), {0., 0.});
        }
    }
    double now() const { return enabled ? wall_seconds() : 0.; }
    void post(int count) {
        if (enabled) {
            posted = wall_seconds();
            stats.value[Calls]++;
            stats.value[SendBytes] += 2. * count * sizeof(float);
            stats.value[PackPost] += posted - begin;
        }
    }
    void wait(double start) {
        if (enabled)
            stats.value[Wait] += wall_seconds() - start;
    }
    void interior(int tid, double start) {
        if (enabled)
            stats.workers[tid][0] = wall_seconds() - start;
    }
    void boundary(int tid, double start) {
        if (enabled)
            stats.workers[tid][1] = wall_seconds() - start;
    }
    void region() {
        if (enabled)
            stats.value[OverlapRegion] += wall_seconds() - posted;
    }
    void compute_all(double start) {
        if (enabled)
            stats.value[ComputeAll] += wall_seconds() - start;
    }
    ~HaloTrace() {
        if (enabled) {
            double interior_max = 0, boundary_max = 0;
            for (const auto &v : stats.workers) {
                interior_max = std::max(interior_max, v[0]);
                boundary_max = std::max(boundary_max, v[1]);
            }
            stats.value[Interior] += interior_max;
            stats.value[Boundary] += boundary_max;
            stats.value[Total] += wall_seconds() - begin;
        }
    }
};

int setting(const char *name, int fallback);
double distributed_norm(const Field &field);
Complex distributed_dot(const Field &a, const Field &b);
double fine_norm(const FloatField &field);
double coarse_norm(const FloatField &field);
Complex coarse_dot(const FloatField &a, const FloatField &b);
void coarse_axpy(FloatField &y, Complex coefficient, const FloatField &x);
} // namespace lqcd_native::detail
