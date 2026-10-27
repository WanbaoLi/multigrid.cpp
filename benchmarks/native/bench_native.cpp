#include "lqcd/core/clover.h"
#include "lqcd/core/dslash.h"
#include "lqcd/runtime/runtime.h"
#include "multigrid.hpp"
#include "environment.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc, char **argv) {
    int thread_support;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &thread_support);
    if (thread_support < MPI_THREAD_FUNNELED) {
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }
    try {
        if (argc != 4)
            throw std::runtime_error("usage: bench_native gauge source basis");
        Options o;
        o.gauge = argv[1];
        o.source = argv[2];
        o.basis_file = argv[3];
        gamma_init();
        Gauge g{o};
        load_gauge(g);
        build_clover(g, g.clover);
        Multigrid m;
        double start = wall_seconds();
        if (o.basis_file == "generate") {
            m.o = o;
            m.cx = o.nx / o.bx;
            m.cy = o.ny / o.by;
            m.cz = o.nz / o.bz;
            m.ct = o.nt / o.bt;
            m.block_volume = o.bx * o.by * o.bz * o.bt;
            m.n_fine = (size_t)o.nx * o.ny * o.nz * o.nt;
            m.n_coarse = m.n_fine / m.block_volume;
            m.coarse_dof = 48;
            m.basis.assign(m.n_fine * 12 * 48, 0.);
            m.stencil.assign(m.n_coarse * 9 * 48 * 48, 0.);
            for (size_t b = 0; b < m.n_coarse; b++)
                for (int a = 0; a < 48; a++)
                    m.stencil[b * 9 * 48 * 48 + a * 48 + a] = 1.;
        } else
            build_coarse_operator(g, m);
        if (auto v = std::getenv("NATIVE_LOAD")) {
            read_binary(std::string(v) + ".basis", m.basis);
            read_binary(std::string(v) + ".stencil", m.stencil);
        }
        NativeMG mg(g, m, MPI_COMM_WORLD);
        std::cout << "native setup " << wall_seconds() - start << std::endl;
        if (auto v = std::getenv("NATIVE_GENERATE")) {
            mg.generate_basis(m, std::atoi(v), 0);
            std::cout << "generated own basis " << wall_seconds() - start << std::endl;
        }
        if (auto v = std::getenv("NATIVE_ADAPT"))
            for (int pass = 0; pass < (std::getenv("NATIVE_ADAPT_PASSES")
                                           ? std::atoi(std::getenv("NATIVE_ADAPT_PASSES"))
                                           : 1);
                 pass++) {
                mg.generate_basis(m, 12, std::atoi(v));
                std::cout << "adapted own basis " << wall_seconds() - start << std::endl;
            }
        if (auto v = std::getenv("NATIVE_SAVE")) {
            dump(std::string(v) + ".basis", m.basis);
            dump(std::string(v) + ".stencil", m.stencil);
        }
        mg.verify();
        Field global_b(24 * 24 * 24 * 64 * 12), x, ax;
        read_binary(o.source, global_b);
        int rank, ranks;
        MPI_Comm_rank(MPI_COMM_WORLD, &rank);
        MPI_Comm_size(MPI_COMM_WORLD, &ranks);
        const size_t count = global_b.size() / ranks;
        Field b(global_b.begin() + count * rank, global_b.begin() + count * (rank + 1));
        global_b.clear();
        for (int run = 0; run < 2; run++) {
            start = wall_seconds();
            mg.solve(b, x, 1e-8, 300, 24);
            double seconds = wall_seconds() - start;
            mg.apply(x, ax);
            axpy(ax, -1., b);
            double r = lqcd_native::detail::distributed_norm(ax) /
                       lqcd_native::detail::distributed_norm(b);
            std::cout << std::setprecision(15) << "native solve " << run + 1 << " seconds "
                      << seconds << " residual " << r << " iterations " << mg.iterations
                      << std::endl;
            if (r > 1e-8)
                throw std::runtime_error("true residual gate failed");
        }
    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }
    MPI_Finalize();
}
