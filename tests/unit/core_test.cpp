#include "lqcd/core/clover.h"
#include "lqcd/core/dirac.h"
#include "lqcd/core/dslash.h"
#include "lqcd/core/field.h"
#include "lqcd/core/gauge.h"
#include "lqcd/core/gcr.h"
#include "lqcd/core/multigrid.h"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <stdexcept>

static void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}
static double relative(const Field &a, const Field &b) {
    Field d = a;
    axpy(d, -1., b);
    return norm(d) / std::max(norm(b), 1e-300);
}
static Field sample(size_t n, double phase) {
    Field v(n);
    for (size_t i = 0; i < n; ++i)
        v[i] = Complex(std::sin(0.17 * i + phase), std::cos(0.11 * i - phase));
    return v;
}
int main() {
    try {
        const std::string files = "core-test-data";
        std::filesystem::create_directories(files);
        gamma_init();
        for (int mu = 0; mu < 4; ++mu)
            for (int nu = 0; nu < 4; ++nu)
                for (int a = 0; a < 4; ++a)
                    for (int b = 0; b < 4; ++b) {
                        Complex z = 0.;
                        for (int k = 0; k < 4; ++k)
                            z += gamma_matrix[mu][a][k] * gamma_matrix[nu][k][b] +
                                 gamma_matrix[nu][a][k] * gamma_matrix[mu][k][b];
                        require(std::abs(z - Complex(mu == nu && a == b ? 2. : 0.)) < 1e-15,
                                "gamma Clifford algebra");
                    }
        // General nonsymmetric complex system, independent of lattice operators.
        const Complex matrix[3][3] = {
            {4., Complex(1., .2), 0.}, {-.3, 3., .7}, {Complex(.1, -.2), -.4, 2.}};
        LinearOperator apply = [&](const Field &in, Field &out) {
            out.assign(3, {});
            for (int i = 0; i < 3; ++i)
                for (int j = 0; j < 3; ++j)
                    out[i] += matrix[i][j] * in[j];
        };
        Field exact = {Complex(1., .4), Complex(-2., .1), Complex(.3, -.8)}, b, x;
        apply(exact, b);
        GcrOptions solve_options{100, 1e-12, 3, files + "/gcr"};
        solve_gcr(apply, {}, b, x, solve_options);
        require(relative(x, exact) < 1e-12, "plain GCR nonsymmetric system");
        int calls = 0;
        LinearOperator diagonal = [&](const Field &in, Field &out) {
            ++calls;
            out = in;
            for (int i = 0; i < 3; ++i)
                out[i] /= matrix[i][i];
        };
        solve_gcr(apply, diagonal, b, x, solve_options);
        require(calls > 0 && relative(x, exact) < 1e-12, "preconditioned GCR nonsymmetric system");

        Options o;
        o.nx = o.ny = o.nz = o.nt = 6;
        o.bx = o.by = o.bz = o.bt = 2;
        o.basis_file = files + "/basis.bin";
        Gauge gauge{o};
        load_gauge(gauge);
        build_clover(gauge, gauge.clover);
        const size_t volume = 6 * 6 * 6 * 6;
        Field input = sample(volume * 12, .4), clover, hopping, full;
        apply_clover_only(gauge, input, clover, 1);
        require(relative(clover, input) < 1e-15, "unit gauge has identity Clover");
        apply_dslash(gauge, input, hopping, 1);
        apply_dirac(gauge, input, full, 1);
        axpy(clover, 1., hopping);
        require(relative(full, clover) < 1e-14, "Dirac=Clover+normalized Dslash");

        // Antiperiodic temporal plane wave is an eigenmode of translation.
        const double momentum = std::acos(-1.) / o.nt;
        const double kappa = 1. / (2. * (-.277 + 4.));
        const Field spinor = sample(12, .7);
        Field plane(volume * 12), expected(volume * 12);
        for (int t = 0; t < o.nt; ++t)
            for (int z = 0; z < o.nz; ++z)
                for (int y = 0; y < o.ny; ++y)
                    for (int xx = 0; xx < o.nx; ++xx) {
                        const auto s = site_index(xx, y, z, t, o);
                        const Complex phase = std::polar(1., momentum * t);
                        for (int a = 0; a < 4; ++a)
                            for (int c = 0; c < 3; ++c) {
                                Complex gv = 0.;
                                for (int d = 0; d < 4; ++d)
                                    gv += gamma_matrix[3][a][d] * spinor[d * 3 + c];
                                plane[s * 12 + a * 3 + c] = phase * spinor[a * 3 + c];
                                expected[s * 12 + a * 3 + c] =
                                    -kappa * phase *
                                    ((6. + 2. * std::cos(momentum)) * spinor[a * 3 + c] -
                                     Complex(0., 2. * std::sin(momentum)) * gv);
                            }
                    }
        apply_dslash(gauge, plane, hopping, 1);
        require(relative(hopping, expected) < 1e-14,
                "eight-direction hopping / temporal antiperiodic boundary");
        dump(files + "/field.bin", input);
        Field restored(input.size());
        read_binary(files + "/field.bin", restored);
        require(restored == input, "field binary round trip");

        // Independent sparse orthonormal 48-DOF basis on a small 3^4 coarse grid.
        const size_t blocks = 81, block_volume = 16;
        Field basis(blocks * 2 * 24 * block_volume * 2 * 3, Complex{});
        for (size_t cb = 0; cb < blocks; ++cb)
            for (int cs = 0; cs < 2; ++cs)
                for (int v = 0; v < 24; ++v)
                    basis[((cb * 2 + cs) * 24 + v) * block_volume * 6 + (v * 37) % 96] = 1.;
        dump(o.basis_file, basis);
        Multigrid mg;
        build_coarse_operator(gauge, mg);
        require(mg.coarse_dof == 48, "coarse space has 48 DOF");
        Field coarse = sample(blocks * 48, .2), p, r, ac, rap;
        prolong_field(mg, coarse, p, 1);
        restrict_field(mg, p, r, 1);
        require(relative(r, coarse) < 1e-14, "R P = I for orthonormal test basis");
        restrict_field(mg, input, r, 1);
        require(std::abs(dot(p, input) - dot(coarse, r)) / std::max(norm(p) * norm(input), 1e-300) <
                    1e-14,
                "R is the adjoint of P");
        apply_coarse(gauge, mg, coarse, ac, 1);
        apply_coarse_matrixfree(gauge, mg, coarse, rap, 1);
        require(relative(ac, rap) < 1e-12, "assembled coarse operator equals RAP");
        vcycle(gauge, mg, x, input, 1);
        require(std::isfinite(norm(x)), "Field-cycle finite correction");
        std::cout << "core tests PASS\n";
    } catch (const std::exception &e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
