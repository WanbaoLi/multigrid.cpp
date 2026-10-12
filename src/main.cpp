#include "gcr.h"
#include "multigrid.h"
#include "validation.h"
#include "dirac.h"
#include "dslash.h"
#include "field.h"
#include "gauge.h"
#include "clover.h"
#include "runtime.h"
// A deliberately small, readable CPU Wilson-Clover-style multigrid reference.
// Layout: field[(site_index * nrhs + rhs) * 12 + spin * 3 + color], site_index=(t,z,y,x).
// The implementation is correctness-oriented and keeps every Multigrid operation visible.
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <string>
#include <iomanip>
#include <chrono>
#include <stdexcept>
static int probe_x = 0, probe_y = 0, probe_z = 0, probe_t = 0, probe_spin = 0, probe_color = 0;
static void solve(const Gauge &g, const Field &b, Field &x, int nr, const Options &o)
{
    const LinearOperator apply = [&](const Field &in, Field &out) { apply_dirac(g, in, out, nr); };
    const GcrOptions options{o.maxit, o.tol, o.restart, o.out};
    Multigrid m;
    if (o.plain)
    {
        solve_gcr(apply, {}, b, x, options);
        return;
    }
    build_coarse_operator(g, m);
    if (o.diagnose_ac)
        diagnose_one_coarse_site(g, m);
    if (o.check_ac)
        check_coarse_operator(g, m);
    if (o.check_only)
        return;
    const LinearOperator precondition = [&](const Field &in, Field &out) { vcycle(g, m, out, in, nr); };
    solve_gcr(apply, precondition, b, x, options);
}
static void help()
{
    std::cout << R"(multigrid.cpp --gauge gauge.bin --source source.bin --solver gcr|mg [options]
  --basis-file FILE     Required canonical 48-DOF basis for MG (default basis.bin)
  --out FILE            Solution and diagnostic prefix (default cpu_mg_solution.bin)
  --tol VALUE           Relative true-residual tolerance (default 1e-12)
  --maxiter N           Maximum outer updates (default 100)
  --restart N           GCR Krylov length (default 8)
  --dims X Y Z T        Lattice dimensions (default 24 24 24 64)
  --nrhs N              Contiguous RHS count (default 1)
  --point X Y Z T S C   Point source if --source is omitted (default all zero)
  --plain              Legacy alias for --solver gcr
  --basis canonical|clover   Imported 48-DOF or historical 12-DOF diagnostic basis
  --operator           Export fine A*source, Clover and hopping contributions
  --check-ac --check-only    Check preassembled Ac against matrix-free RAP
  --trace DIRECTORY    Export first V-cycle and coarse residual history
  --coarse-source FILE Use the same coarse input for Ac/RAP validation
  --validate-solution FILE  Recompute the true residual of an existing solution
  --diagnose-ac        Diagnose individual coarse stencil blocks
  --benchmark          Time repeated operator applications
  --help               Show this help

MG blocks are fixed at 6 6 6 4; no implicit basis generation.
Without --gauge a unit gauge is used. No compilation occurs when running.
)";
}
static bool parse(int ac, char **av, Options &o)
{
    for (int i = 1; i < ac; i++)
    {
        std::string a = av[i];
        auto value = [&]() -> std::string {
            if (i + 1 >= ac) throw std::runtime_error("missing value for " + a);
            return av[++i];
        };
        auto val = [&](int &x) { x = std::stoi(value()); };
        if (a == "--help" || a == "-h") { help(); return false; }
        else if (a == "--solver") {
            const std::string solver = value();
            if (solver != "gcr" && solver != "mg") throw std::runtime_error("solver must be gcr or mg");
            o.plain = solver == "gcr";
        }
        else if (a == "--plain")
            o.plain = true;
        else if (a == "--benchmark")
            o.benchmark = true;
        else if (a == "--check-only")
            o.check_only = true;
        else if (a == "--coarse-source")
            o.coarse_source = value();
        else if (a == "--validate-solution")
            o.validate_solution = value();
        else if (a == "--trace")
            o.trace = value();
        else if (a == "--restart")
            val(o.restart);
        else if (a == "--nrhs")
            val(o.nrhs);
        else if (a == "--maxiter")
            val(o.maxit);
        else if (a == "--gauge")
            o.gauge = value();
        else if (a == "--source")
            o.source = value();
        else if (a == "--out")
            o.out = value();
        else if (a == "--basis")
            o.basis = value();
        else if (a == "--basis-file")
            o.basis_file = value();
        else if (a == "--operator")
            o.operator_probe = true;
        else if (a == "--check-ac")
            o.check_ac = true;
        else if (a == "--diagnose-ac")
            o.diagnose_ac = true;
        else if (a == "--split")
            o.operator_probe = true;
        else if (a == "--point")
        {
            probe_x = std::stoi(value());
            probe_y = std::stoi(value());
            probe_z = std::stoi(value());
            probe_t = std::stoi(value());
            probe_spin = std::stoi(value());
            probe_color = std::stoi(value());
        }
        else if (a == "--dims")
        {
            o.nx = std::stoi(value());
            o.ny = std::stoi(value());
            o.nz = std::stoi(value());
            o.nt = std::stoi(value());
        }
        else if (a == "--tol")
            o.tol = std::stod(value());
        else
            throw std::runtime_error("unknown option: " + a);
    }
    if (o.basis == "quda") o.basis = "canonical"; // legacy CLI spelling
    if (o.basis != "canonical" && o.basis != "clover")
        throw std::runtime_error("basis must be canonical or clover");
    return true;
}
int main(int ac, char **av)
{
    try
    {
        const auto start = std::chrono::steady_clock::now();
        std::cout << std::setprecision(17);
        std::cerr << std::setprecision(17);
        Options o;
        if (!parse(ac, av, o)) return 0;
        if (!std::isfinite(o.tol) || o.tol <= 0 || o.maxit <= 0 || o.restart <= 0 || o.nrhs <= 0)
            throw std::runtime_error("invalid solver parameters");
        if (o.nx <= 0 || o.ny <= 0 || o.nz <= 0 || o.nt <= 0)
            throw std::runtime_error("lattice dimensions must be positive");
        if (o.source.empty() && (probe_x < 0 || probe_x >= o.nx || probe_y < 0 || probe_y >= o.ny ||
            probe_z < 0 || probe_z >= o.nz || probe_t < 0 || probe_t >= o.nt ||
            probe_spin < 0 || probe_spin >= 4 || probe_color < 0 || probe_color >= 3))
            throw std::runtime_error("point source outside lattice or spin/color range");
        gamma_init();
        Gauge g{o};
        load_gauge(g);
        build_clover(g, g.clover);
        size_t n = (size_t)o.nx * o.ny * o.nz * o.nt;
        Field b(n * o.nrhs * 12, Complex{});
        if (o.source.empty())
        {
            b[spinor_index(site_index(probe_x, probe_y, probe_z, probe_t, o), 0, probe_spin, probe_color, o.nrhs)] = 1.;
        }
        else
            read_binary(o.source, b);
        Field x;
        if (o.benchmark)
        {
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < b.size(); ++i)
                b[i] = Complex(std::sin(0.01 * i), std::cos(0.013 * i));
            apply_dirac(g, b, x, o.nrhs); // warm-up outside timing
            const double begin = wall_seconds();
            for (int i = 0; i < 10; ++i)
                apply_dirac(g, b, x, o.nrhs);
            const double seconds = (wall_seconds() - begin) / 10;
            std::cout << "threads " << thread_count() << " operator_seconds " << seconds << " norm " << norm(x) << "\n";
            return 0;
        }
        if (!o.operator_probe && !o.check_only)
        {
            std::ofstream params(o.out + ".params.json");
            params << std::setprecision(17) << "{\"tol\":" << o.tol
                   << ",\"restart\":" << o.restart << ",\"maxiter\":" << o.maxit
                   << ",\"initial_guess\":\"zero\",\"solve_type\":\"DIRECT\",\"mass\":-0.277,"
                   << "\"coarse_dof\":48,\"nu_pre\":0,\"nu_post\":1,\"coarse_tol\":0.5,\"coarse_maxiter\":8,"
                   << "\"coarse_solver\":\"GCR\",\"smoother\":\"CA_GCR\",\"threads\":" << thread_count()
                   << ",\"mg_enabled\":" << (o.plain ? "false" : "true")
                   << ",\"lattice\":[" << o.nx << "," << o.ny << "," << o.nz << "," << o.nt << "]"
                   << ",\"mg_block\":[[" << o.bx << "," << o.by << "," << o.bz << "," << o.bt << "]]"
                   << ",\"nvec\":24,\"kappa\":" << 1. / (2 * (-.277 + 4))
                   << ",\"clover_coeff_t\":1,\"clover_coeff_r\":1,\"anisotropy\":1,\"t_boundary\":-1}\n";
        }
        if (o.operator_probe)
        {
            apply_dirac(g, b, x, o.nrhs);
            Field cl;
            apply_clover_only(g, b, cl, o.nrhs);
            Field d = x;
            for (size_t i = 0; i < d.size(); i++)
                d[i] -= cl[i];
            std::ofstream(o.out + ".clover", std::ios::binary).write((char *)cl.data(), cl.size() * sizeof(Complex));
            std::ofstream(o.out + ".dslash", std::ios::binary).write((char *)d.data(), d.size() * sizeof(Complex));
            dump(o.out, x);
            std::cout << "wrote fine A*Field " << o.out << " norm " << norm(x) << "\n";
            return 0;
        }
        else if (!o.validate_solution.empty())
        {
            x.resize(b.size());
            read_binary(o.validate_solution, x);
        }
        else
            solve(g, b, x, o.nrhs, o);
        if (o.check_only)
            return 0;
        Field ax, rr;
        apply_dirac(g, x, ax, o.nrhs);
        rr = b;
        axpy(rr, -1., ax);
        double residual = norm(rr) / std::max(norm(b), 1e-300);
        std::cout << "true relative residual " << residual << "\n";
        std::ofstream(o.out + ".residual") << std::setprecision(17) << residual << "\n";
        dump(o.out, x);
        std::cout << "wrote " << o.out << " norm " << norm(x) << "\n";
        double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        std::ofstream(o.out + ".seconds") << std::setprecision(17) << seconds << "\n";
        if (!o.operator_probe && (!std::isfinite(residual) || residual > o.tol))
            throw std::runtime_error("solver true residual FAIL");
    }
    catch (const std::exception &e)
    {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
