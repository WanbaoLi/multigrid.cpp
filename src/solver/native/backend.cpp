#include "backend.hpp"
#include "lqcd/core/clover.h"
#include "lqcd/core/dslash.h"
#include "multigrid.hpp"
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <iostream>
namespace lqcd {
class NativeBackend final : public Backend {
    lqcd_config config;
    Geometry geometry;
    MPI_Comm comm;
    Gauge gauge;
    Multigrid hierarchy;
    std::unique_ptr<NativeMG> solver;
    Vector rhs;
    std::vector<Vector> batch_rhs;
    size_t volume;
    int setup_passes = 2, setup_iterations = 3, setup_smooth = 12;

    void configure_setup() {
        const char *names[3] = {"LQCD_MG_SETUP_PASSES", "LQCD_MG_SETUP_ITERATIONS",
                                "LQCD_MG_SETUP_SMOOTH"};
        const int lower[3] = {0, 1, 0}, upper[3] = {8, 12, 64};
        int values[3] = {2, 3, 12};
        int invalid = 0;
        for (int i = 0; i < 3; ++i) {
            const char *text = std::getenv(names[i]);
            if (!text)
                continue;
            // Accept decimal digits only: reject whitespace, signs, suffixes,
            // empty strings and overflow rather than silently using a default.
            bool digits = *text != '\0';
            for (const char *p = text; *p; ++p)
                digits = digits && *p >= '0' && *p <= '9';
            errno = 0;
            char *end = nullptr;
            const long value = std::strtol(text, &end, 10);
            if (!digits || errno == ERANGE || end == text || *end != '\0' || value < lower[i] ||
                value > upper[i]) {
                invalid = 1;
            } else {
                values[i] = static_cast<int>(value);
            }
        }
        // Every rank reaches the same collectives even on malformed input.
        // Do this before any rank can enter hierarchy setup communication.
        int minimum[3], maximum[3], any_invalid;
        MPI_Allreduce(values, minimum, 3, MPI_INT, MPI_MIN, comm);
        MPI_Allreduce(values, maximum, 3, MPI_INT, MPI_MAX, comm);
        MPI_Allreduce(&invalid, &any_invalid, 1, MPI_INT, MPI_MAX, comm);
        if (any_invalid || minimum[0] != maximum[0] || minimum[1] != maximum[1] ||
            minimum[2] != maximum[2])
            throw Error(LQCD_INVALID_ARGUMENT,
                        "LQCD_MG_SETUP_PASSES (0..8), LQCD_MG_SETUP_ITERATIONS (1..12), "
                        "LQCD_MG_SETUP_SMOOTH (0..64) must be decimal integers and agree "
                        "on every MPI rank");
        setup_passes = values[0];
        setup_iterations = values[1];
        setup_smooth = values[2];
    }

  public:
    NativeBackend(const lqcd_config &c, const Geometry &g, MPI_Comm communicator)
        : config(c), geometry(g), comm(communicator) {
        configure_setup();
        for (auto key :
             {"NATIVE_SAP_STEPS", "NATIVE_SAP_CYCLES", "NATIVE_COARSE_IT", "NATIVE_OUTER_FLOAT"})
            if (std::getenv(key))
                throw Error(LQCD_UNSUPPORTED, "experimental NATIVE_* overrides are supported only "
                                              "by bench_native, not the production API");
        if (c.process_grid[0] != 1 || c.process_grid[1] != 1 || c.process_grid[2] != 1)
            throw Error(LQCD_UNSUPPORTED,
                        "native CPU currently supports t-slab MPI decomposition only");
        if (c.levels != 2 || c.t_boundary != -1)
            throw Error(LQCD_UNSUPPORTED,
                        "native CPU currently supports two levels and antiperiodic time");
        for (int d = 0; d < 4; d++)
            if (c.lattice[d] / c.block[d] < 4 || (c.lattice[d] / c.block[d]) % 2)
                throw Error(LQCD_UNSUPPORTED, "native SAP requires even coarse extents >=4");
        Options o;
        o.nx = c.lattice[0];
        o.ny = c.lattice[1];
        o.nz = c.lattice[2];
        o.nt = c.lattice[3];
        o.mass = c.mass;
        o.csw = c.csw;
        o.bx = c.block[0];
        o.by = c.block[1];
        o.bz = c.block[2];
        o.bt = c.block[3];
        gauge.o = o;
        volume = (size_t)o.nx * o.ny * o.nz * o.nt;
        gamma_init();
    }
    void load_gauge(const Vector &in) override {
        gauge.u.resize(volume * 36);
        MPI_Allgather(in.data(), in.size() * 2, MPI_DOUBLE, gauge.u.data(), in.size() * 2,
                      MPI_DOUBLE, comm);
        gauge.loaded = true;
        build_clover(gauge, gauge.clover);
    }
    void setup() override {
        auto &m = hierarchy;
        auto &o = gauge.o;
        m.o = o;
        m.cx = o.nx / o.bx;
        m.cy = o.ny / o.by;
        m.cz = o.nz / o.bz;
        m.ct = o.nt / o.bt;
        m.block_volume = o.bx * o.by * o.bz * o.bt;
        m.n_fine = volume;
        m.n_coarse = volume / m.block_volume;
        m.coarse_dof = 48;
        m.basis.assign(volume * 12 * 48, Complex{});
        m.stencil.assign(m.n_coarse * 9 * 48 * 48, Complex{});
        for (size_t b = 0; b < m.n_coarse; b++)
            for (int a = 0; a < 48; a++)
                m.stencil[b * 9 * 48 * 48 + a * 48 + a] = 1.;
        solver = std::make_unique<NativeMG>(gauge, hierarchy, comm, config.seed);
        solver->generate_basis(hierarchy, setup_smooth, 0);
        for (int pass = 0; pass < setup_passes; ++pass)
            solver->generate_basis(hierarchy, 0, setup_iterations);
        solver->verify();
        solver->place_hot_data();
    }
    void apply(const Vector &in, Vector &out) override {
        solver->apply(in, out);
#pragma omp parallel for schedule(static)
        for (size_t i = 0; i < out.size(); i++)
            out[i] *= 4 + config.mass;
    }
    SolveInfo solve(const Vector &b, Vector &x, double tol) override {
        rhs.resize(b.size());
        const double factor = 1 / (4 + config.mass);
#pragma omp parallel for schedule(static)
        for (size_t i = 0; i < b.size(); i++)
            rhs[i] = b[i] * factor;
        MPI_Barrier(comm);
        const double start = MPI_Wtime();
        solver->solve(rhs, x, tol, 300, 24);
        const double elapsed = MPI_Wtime() - start;
        double maximum;
        MPI_Allreduce(&elapsed, &maximum, 1, MPI_DOUBLE, MPI_MAX, comm);
        return {solver->iterations, true, maximum};
    }

    std::vector<SolveInfo> solve_batch(const std::vector<Vector> &b, std::vector<Vector> &x,
                                       double tol) override {
        batch_rhs.resize(b.size());
        const double factor = 1 / (4 + config.mass);
        for (size_t column = 0; column < b.size(); ++column) {
            batch_rhs[column].resize(b[column].size());
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < b[column].size(); ++i)
                batch_rhs[column][i] = b[column][i] * factor;
        }
        MPI_Barrier(comm);
        const double start = MPI_Wtime();
        auto iterations = solver->solve_batch(batch_rhs, x, tol, 300, 24);
        double elapsed = MPI_Wtime() - start, maximum;
        MPI_Allreduce(&elapsed, &maximum, 1, MPI_DOUBLE, MPI_MAX, comm);
        std::vector<SolveInfo> result;
        for (int count : iterations)
            result.push_back({count, true, maximum});
        return result;
    }
};
std::unique_ptr<Backend> make_native(const lqcd_config &c, const Geometry &g, MPI_Comm comm) {
    return std::make_unique<NativeBackend>(c, g, comm);
}
} // namespace lqcd
