#include "validation.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>

void check_coarse_operator(const Gauge &g, const Multigrid &m) {
    if (!g.o.coarse_source.empty()) {
        Field e(m.n_coarse * m.coarse_dof), ac, rap;
        read_binary(g.o.coarse_source, e);
        apply_coarse(g, m, e, ac, 1);
        apply_coarse_matrixfree(g, m, e, rap, 1);
        dump(g.o.trace + "/ace_same_input.bin", ac);
        dump(g.o.trace + "/rap_same_input.bin", rap);
        Field diff = ac;
        axpy(diff, -1., rap);
        double error = norm(diff) / std::max(norm(rap), 1e-300);
        std::cerr << "Ac same-input RAP relative error " << error << "\n";
        if (!std::isfinite(error) || error > 1e-12)
            throw std::runtime_error("same-input RAP FAIL");
    }
    if (!g.o.trace.empty()) {
        const size_t cb = coarse_site_index(1, 1, 1, 1, m);
        for (int spin = 0; spin < 2; ++spin)
            for (int vec = 0; vec < 2; ++vec) {
                Field e(m.n_coarse * m.coarse_dof, Complex{}), p, r;
                e[cb * m.coarse_dof + spin * 24 + vec] = 1.;
                prolong_field(m, e, p, 1);
                restrict_field(m, p, r, 1);
                Field block(m.block_volume * 12);
                for (int lt = 0; lt < m.o.bt; ++lt)
                    for (int lz = 0; lz < m.o.bz; ++lz)
                        for (int ly = 0; ly < m.o.by; ++ly)
                            for (int lx = 0; lx < m.o.bx; ++lx) {
                                int x = m.o.bx + lx, y = m.o.by + ly, z = m.o.bz + lz,
                                    t = m.o.bt + lt;
                                size_t fs = site_index(x, y, z, t, m.o);
                                int ls = local_site(x, y, z, t, m);
                                for (int a = 0; a < 12; ++a) {
                                    block[ls * 12 + a] = p[fs * 12 + a];
                                    p[fs * 12 + a] = 0.;
                                }
                            }
                if (norm(p) != 0.)
                    throw std::runtime_error("P support FAIL");
                Field rb(r.begin() + cb * m.coarse_dof, r.begin() + (cb + 1) * m.coarse_dof);
                std::fill(r.begin() + cb * m.coarse_dof, r.begin() + (cb + 1) * m.coarse_dof,
                          Complex{});
                if (norm(r) != 0.)
                    throw std::runtime_error("R support FAIL");
                std::string stem =
                    g.o.trace + "/transfer_" + std::to_string(spin) + "_" + std::to_string(vec);
                dump(stem + "_p.bin", block);
                dump(stem + "_r.bin", rb);
            }
    }

    for (int trial = 0; trial < 3; ++trial) {
        Field x(m.n_coarse * (size_t)m.coarse_dof), y_sparse, y_rap;
        for (size_t i = 0; i < x.size(); ++i)
            x[i] = Complex(std::sin(0.17 * (double)(i + 1 + 97 * trial)),
                           std::cos(0.11 * (double)(i + 3 + 31 * trial)));
        apply_coarse(g, m, x, y_sparse, 1);
        apply_coarse_matrixfree(g, m, x, y_rap, 1);
        Field d = y_sparse;
        axpy(d, -1., y_rap);
        double error = norm(d) / std::max(norm(y_rap), 1e-300);
        std::cerr << "Ac check " << trial << " relative error " << error << "\n";
        if (!std::isfinite(error) || error > 1e-12)
            throw std::runtime_error("Ac = RAP FAIL");
    }
}
void diagnose_one_coarse_site(const Gauge &g, const Multigrid &m) {
    int bx = std::min(1, m.cx - 2), by = std::min(1, m.cy - 2), bz = std::min(1, m.cz - 2),
        bt = std::min(1, m.ct - 2);
    size_t source = coarse_site_index(bx, by, bz, bt, m);
    const int dx[9] = {0, 1, -1, 0, 0, 0, 0, 0, 0}, dy[9] = {0, 0, 0, 1, -1, 0, 0, 0, 0},
              dz[9] = {0, 0, 0, 0, 0, 1, -1, 0, 0}, dt[9] = {0, 0, 0, 0, 0, 0, 0, 1, -1};
    const char *name[9] = {"onsite", "+X", "-X", "+Y", "-Y", "+Z", "-Z", "+T", "-T"};
    const size_t blockmat = (size_t)m.coarse_dof * m.coarse_dof;
    std::vector<Field> ref(9, Field(blockmat, Complex{}));
    for (int col = 0; col < m.coarse_dof; ++col) {
        Field e(m.n_coarse * (size_t)m.coarse_dof, Complex{}), y;
        e[source * (size_t)m.coarse_dof + col] = 1.;
        apply_coarse_matrixfree(g, m, e, y, 1);
        for (int dir = 0; dir < 9; ++dir) {
            size_t row =
                coarse_site_index((bx + dx[dir] + m.cx) % m.cx, (by + dy[dir] + m.cy) % m.cy,
                                  (bz + dz[dir] + m.cz) % m.cz, (bt + dt[dir] + m.ct) % m.ct, m);
            for (int r = 0; r < m.coarse_dof; ++r)
                ref[dir][r * m.coarse_dof + col] = y[row * (size_t)m.coarse_dof + r];
        }
    }
    for (int dir = 0; dir < 9; ++dir) {
        int ld = dir == 0 ? 0 : (dir % 2 ? dir + 1 : dir - 1);
        double n2 = 0, e2 = 0, mx = 0;
        int mr = 0, mc = 0;
        Complex rv{}, lv{};
        size_t row =
            coarse_site_index((bx + dx[dir] + m.cx) % m.cx, (by + dy[dir] + m.cy) % m.cy,
                              (bz + dz[dir] + m.cz) % m.cz, (bt + dt[dir] + m.ct) % m.ct, m);
        for (int r = 0; r < m.coarse_dof; ++r)
            for (int c = 0; c < m.coarse_dof; ++c) {
                Complex a = ref[dir][r * m.coarse_dof + c],
                        b = m.stencil[(row * 9 + ld) * blockmat + r * m.coarse_dof + c];
                n2 += std::norm(a);
                e2 += std::norm(a - b);
                if (std::abs(a - b) > mx) {
                    mx = std::abs(a - b);
                    mr = r;
                    mc = c;
                    rv = a;
                    lv = b;
                }
            }
        std::cerr << name[dir] << " relative Frobenius error "
                  << std::sqrt(e2 / std::max(n2, 1e-300)) << " max_abs " << mx << " max_entry ("
                  << mr << "," << mc << ") ref " << rv << " local " << lv << "\n";
    }
    for (int dir = 1; dir < 9; ++dir) {
        double best = 1e300;
        int bd = -1;
        size_t row =
            coarse_site_index((bx + dx[dir] + m.cx) % m.cx, (by + dy[dir] + m.cy) % m.cy,
                              (bz + dz[dir] + m.cz) % m.cz, (bt + dt[dir] + m.ct) % m.ct, m);
        for (int ld = 1; ld < 9; ++ld) {
            double n2 = 0, e2 = 0;
            for (int r = 0; r < m.coarse_dof; ++r)
                for (int c = 0; c < m.coarse_dof; ++c) {
                    Complex a = ref[dir][r * m.coarse_dof + c],
                            b = m.stencil[(row * 9 + ld) * blockmat + r * m.coarse_dof + c];
                    n2 += std::norm(a);
                    e2 += std::norm(a - b);
                }
            if (e2 / std::max(n2, 1e-300) < best) {
                best = e2 / std::max(n2, 1e-300);
                bd = ld;
            }
        }
        std::cerr << name[dir] << " best local direction " << name[bd] << " relative error "
                  << std::sqrt(best) << "\n";
    }
}
