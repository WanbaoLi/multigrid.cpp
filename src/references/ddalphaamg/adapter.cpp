#include "backend.hpp"
#include <cmath>
#include <omp.h>
extern "C" {
#include "DDalphaAMG.h"
}
namespace lqcd {
/* Exact orthogonal DR <-> DD BASIS0 spin transform, S=S^T=S^-1. */
static void spin_transform(const Vector &in, Vector &out) {
    out.resize(in.size());
    const double h = 1 / std::sqrt(2.);
#pragma omp parallel for schedule(static)
    for (size_t s = 0; s < in.size() / 12; s++)
        for (int c = 0; c < 3; c++) {
            auto a = in[s * 12 + c], b = in[s * 12 + 3 + c], d = in[s * 12 + 6 + c],
                 e = in[s * 12 + 9 + c];
            out[s * 12 + c] = -h * (a + b);
            out[s * 12 + 3 + c] = h * (-a + b);
            out[s * 12 + 6 + c] = h * (d + e);
            out[s * 12 + 9 + c] = h * (d - e);
        }
}
class DDBackend final : public Backend {
    Geometry geometry;
    Vector native_b, native_x;
    MPI_Comm parent;

  public:
    DDBackend(const lqcd_config &c, const Geometry &g, MPI_Comm comm) : geometry(g), parent(comm) {
        int key = 0;
        for (int d = 3; d >= 0; d--)
            key = key * c.process_grid[d] + g.coords[d];
        MPI_Comm ordered, cart;
        MPI_Comm_split(comm, 0, key, &ordered);
        int dims[4], periods[4] = {1, 1, 1, 1};
        for (int d = 0; d < 4; d++)
            dims[d] = c.process_grid[3 - d];
        MPI_Cart_create(ordered, 4, dims, periods, 0, &cart);
        MPI_Comm_free(&ordered);
        DDalphaAMG_init init{};
        DDalphaAMG_parameters p{};
        DDalphaAMG_status st{};
        init.comm_cart = cart;
        for (int d = 0; d < 4; d++) {
            init.global_lattice[d] = c.lattice[3 - d];
            init.procs[d] = dims[d];
            init.block_lattice[d] = c.block[3 - d];
        }
        init.kappa = 1 / (2 * (4 + c.mass));
        init.csw = c.csw;
        init.mu = 0;
        init.bc = c.t_boundary == -1 ? 1 : 0;
        init.number_of_levels = c.levels;
        init.number_openmp_threads = c.threads;
        int size;
        MPI_Comm_size(comm, &size);
        std::vector<unsigned> seeds(size);
        for (int i = 0; i < size; i++)
            seeds[i] = c.seed + (unsigned)i;
        init.rnd_seeds = seeds.data();
        DDalphaAMG_initialize(&init, &p, &st);
        MPI_Comm_free(&cart); // DD duplicates the supplied cartesian communicator.
        p.print = 0;
        DDalphaAMG_update_parameters(&p, &st);
    }
    ~DDBackend() override { DDalphaAMG_finalize(); }
    void load_gauge(const Vector &gauge) override {
        Vector native(gauge.size());
#pragma omp parallel for schedule(static)
        for (size_t s = 0; s < geometry.volume; s++)
            for (int mu = 0; mu < 4; mu++)
                for (int c = 0; c < 9; c++)
                    native[(s * 4 + mu) * 9 + c] = gauge[(s * 4 + 3 - mu) * 9 + c];
        DDalphaAMG_status st{};
        DDalphaAMG_set_configuration(reinterpret_cast<double *>(native.data()), &st);
        if (!st.success)
            throw Error(LQCD_INTERNAL_ERROR, "DDalphaAMG gauge import failed");
    }
    void setup() override {
        DDalphaAMG_status st{};
        DDalphaAMG_setup(&st);
        if (!st.success)
            throw Error(LQCD_INTERNAL_ERROR, "DDalphaAMG setup failed");
    }
    void apply(const Vector &in, Vector &out) override {
        spin_transform(in, native_b);
        native_x.resize(in.size());
        DDalphaAMG_status st{};
        DDalphaAMG_apply_operator(reinterpret_cast<double *>(native_x.data()),
                                  reinterpret_cast<double *>(native_b.data()), &st);
        spin_transform(native_x, out);
    }
    SolveInfo solve(const Vector &b, Vector &x, double tol) override {
        spin_transform(b, native_b);
        native_x.assign(b.size(), Complex{});
        DDalphaAMG_status st{};
        MPI_Barrier(parent);
        double begin = MPI_Wtime();
        DDalphaAMG_solve(reinterpret_cast<double *>(native_x.data()),
                         reinterpret_cast<double *>(native_b.data()), tol, &st);
        double elapsed = MPI_Wtime() - begin, maximum;
        MPI_Allreduce(&elapsed, &maximum, 1, MPI_DOUBLE, MPI_MAX, parent);
        spin_transform(native_x, x);
        return {st.iter_count, st.success != 0, maximum};
    }
};
std::unique_ptr<Backend> make_ddalphaamg(const lqcd_config &c, const Geometry &g, MPI_Comm comm) {
    return std::make_unique<DDBackend>(c, g, comm);
}
} // namespace lqcd
