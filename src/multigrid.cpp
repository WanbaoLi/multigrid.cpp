#include "multigrid.h"
#include "dirac.h"
#include "dslash.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>

// Each geometric aggregate has 48 = 2*24 QUDA coarse degrees of freedom.
// The canonical basis is block-major; coarse columns are contiguous.
// The older 12-DOF clover basis is retained for historical diagnostics.
// In both cases restriction is exactly the Hermitian transpose of P.
size_t coarse_site_index(int x, int y, int z, int t, const Multigrid &m)
{
    return (((size_t)t * m.cz + z) * m.cy + y) * m.cx + x;
}
int local_site(int x, int y, int z, int t, const Multigrid &m)
{
    return (((t % m.o.bt) * m.o.bz + (z % m.o.bz)) * m.o.by + (y % m.o.by)) * m.o.bx + (x % m.o.bx);
}
size_t basis_index(size_t cb, int ls, int a, int d, const Multigrid &m)
{
    return (((cb * (size_t)m.block_volume + (size_t)ls) * FINE_DOF + a) * (size_t)m.coarse_dof + d);
}
static void assemble_local_block(const Gauge &g, const Multigrid &m, size_t cb, Field &stencil)
{
    const double k = 1.0 / (2.0 * (-.277 + 4.0));
    int bx = cb % m.cx, by = (cb / m.cx) % m.cy;
    int bz = (cb / (m.cx * m.cy)) % m.cz, bt = cb / (m.cx * m.cy * m.cz);
    int ox = bx * m.o.bx, oy = by * m.o.by, oz = bz * m.o.bz, ot = bt * m.o.bt;
    std::map<size_t, std::vector<Complex>> out;
    for (int lt = 0; lt < m.o.bt; ++lt)
        for (int lz = 0; lz < m.o.bz; ++lz)
            for (int ly = 0; ly < m.o.by; ++ly)
                for (int lx = 0; lx < m.o.bx; ++lx)
                {
                    int x = ox + lx, y = oy + ly, z = oz + lz, t = ot + lt;
                    size_t fs = site_index(x, y, z, t, m.o);
                    int ls = local_site(x, y, z, t, m);
                    for (int d = 0; d < m.coarse_dof; ++d)
                    {
                        auto &local = out[fs];
                        if (local.empty())
                            local.assign((size_t)m.coarse_dof * FINE_DOF, Complex{});
                        // Local clover term.
                        for (int row = 0; row < 12; ++row)
                            for (int a = 0; a < 12; ++a)
                                local[d * 12 + row] += g.clover[fs * 144 + row * 12 + a] *
                                                       m.basis[basis_index(cb, ls, a, d, m)];
                        for (int mu = 0; mu < 4; ++mu)
                        {
                            int xp = x, yp = y, zp = z, tp = t, xm = x, ym = y, zm = z, tm = t;
                            if (mu == 0)
                            {
                                ++xp;
                                --xm;
                            }
                            if (mu == 1)
                            {
                                ++yp;
                                --ym;
                            }
                            if (mu == 2)
                            {
                                ++zp;
                                --zm;
                            }
                            if (mu == 3)
                            {
                                ++tp;
                                --tm;
                            }
                            xp = wrap(xp, m.o.nx);
                            yp = wrap(yp, m.o.ny);
                            zp = wrap(zp, m.o.nz);
                            tp = wrap(tp, m.o.nt);
                            xm = wrap(xm, m.o.nx);
                            ym = wrap(ym, m.o.ny);
                            zm = wrap(zm, m.o.nz);
                            tm = wrap(tm, m.o.nt);
                            double pf = (mu == 3 && t == 0) ? -1.0 : 1.0;
                            double pb = (mu == 3 && t == m.o.nt - 1) ? -1.0 : 1.0;
                            for (int a = 0; a < 4; ++a)
                                for (int c = 0; c < 3; ++c)
                                {
                                    Complex uf = 0, ub = 0;
                                    for (int ss = 0; ss < 4; ++ss)
                                        for (int q = 0; q < 3; ++q)
                                        {
                                            uf += g.at(site_index(xm, ym, zm, tm, m.o), mu, c, q) *
                                                  ((a == ss ? 1.0 : 0.0) - gamma_matrix[mu][a][ss]) *
                                                  m.basis[basis_index(cb, ls, ss * 3 + q, d, m)];
                                            ub += std::conj(g.at(fs, mu, q, c)) *
                                                  ((a == ss ? 1.0 : 0.0) + gamma_matrix[mu][a][ss]) *
                                                  m.basis[basis_index(cb, ls, ss * 3 + q, d, m)];
                                        }
                                    auto &om = out[site_index(xm, ym, zm, tm, m.o)];
                                    auto &op = out[site_index(xp, yp, zp, tp, m.o)];
                                    if (om.empty())
                                        om.assign((size_t)m.coarse_dof * FINE_DOF, Complex{});
                                    if (op.empty())
                                        op.assign((size_t)m.coarse_dof * FINE_DOF, Complex{});
                                    om[d * 12 + a * 3 + c] += -k * pf * uf;
                                    op[d * 12 + a * 3 + c] += -k * pb * ub;
                                }
                        }
                    }
                }
    for (const auto &entry : out)
    {
        size_t ds = entry.first;
        int x = ds % m.o.nx, y = (ds / m.o.nx) % m.o.ny;
        int z = (ds / (m.o.nx * m.o.ny)) % m.o.nz, t = ds / (m.o.nx * m.o.ny * m.o.nz);
        size_t db = coarse_site_index(x / m.o.bx, y / m.o.by, z / m.o.bz, t / m.o.bt, m);
        int ls = local_site(x, y, z, t, m);
        int dbx = db % m.cx, dby = (db / m.cx) % m.cy;
        int dbz = (db / (m.cx * m.cy)) % m.cz, dbt = db / (m.cx * m.cy * m.cz);
        int dir = 0;
        if (dbx != bx)
            dir = (bx == (dbx + 1) % m.cx) ? 1 : 2;
        else if (dby != by)
            dir = (by == (dby + 1) % m.cy) ? 3 : 4;
        else if (dbz != bz)
            dir = (bz == (dbz + 1) % m.cz) ? 5 : 6;
        else if (dbt != bt)
            dir = (bt == (dbt + 1) % m.ct) ? 7 : 8;
        for (int row = 0; row < m.coarse_dof; ++row)
            for (int col = 0; col < m.coarse_dof; ++col)
                for (int a = 0; a < 12; ++a)
                    stencil[(db * 9 + dir) * (size_t)m.coarse_dof * m.coarse_dof + row * m.coarse_dof + col] +=
                        std::conj(m.basis[basis_index(db, ls, a, row, m)]) * entry.second[col * 12 + a];
    }
}
void build_coarse_operator(const Gauge &g, Multigrid &m)
{
    m.o = g.o;
    if (m.o.bx <= 0 || m.o.by <= 0 || m.o.bz <= 0 || m.o.bt <= 0 ||
        m.o.nx % m.o.bx || m.o.ny % m.o.by || m.o.nz % m.o.bz || m.o.nt % m.o.bt ||
        m.o.nx / m.o.bx < 3 || m.o.ny / m.o.by < 3 || m.o.nz / m.o.bz < 3 || m.o.nt / m.o.bt < 3)
        throw std::runtime_error("MG needs complete blocks and at least three coarse sites per direction");
    m.cx = m.o.nx / m.o.bx;
    m.cy = m.o.ny / m.o.by;
    m.cz = m.o.nz / m.o.bz;
    m.ct = m.o.nt / m.o.bt;
    m.block_volume = m.o.bx * m.o.by * m.o.bz * m.o.bt;
    m.n_fine = (size_t)m.o.nx * m.o.ny * m.o.nz * m.o.nt;
    m.n_coarse = (size_t)m.cx * m.cy * m.cz * m.ct;
    m.coarse_dof = (m.o.basis == "canonical") ? COARSE_DOF : FINE_DOF;
    m.basis.assign(m.n_coarse * (size_t)m.block_volume * FINE_DOF * m.coarse_dof, Complex{});
    if (m.o.basis == "canonical")
    {
        std::ifstream f(m.o.basis_file, std::ios::binary);
        if (!f)
            throw std::runtime_error("cannot open canonical basis " + m.o.basis_file);
        const size_t n = m.n_coarse * 2ull * 24ull * m.block_volume * 2ull * 3ull;
        f.seekg(0, std::ios::end);
        const size_t bytes = f.tellg();
        f.seekg(0);
        std::vector<double> raw(n * 2);
        if (bytes == n * sizeof(std::complex<float>))
        {
            std::vector<float> legacy(n * 2);
            f.read(reinterpret_cast<char *>(legacy.data()), bytes);
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < raw.size(); ++i)
                raw[i] = legacy[i];
        }
        else if (bytes == n * sizeof(Complex))
        {
            f.read(reinterpret_cast<char *>(raw.data()), bytes);
        }
        else
            throw std::runtime_error("incorrect canonical basis file size");
        if (!f)
            throw std::runtime_error("short canonical basis file");
        auto qidx = [&](size_t cb, int cs, int v, int ls, int fs, int color)
        {
            return (((((cb * 2ull + (size_t)cs) * 24ull + (size_t)v) * (size_t)m.block_volume + (size_t)ls) * 2ull + (size_t)fs) * 3ull + (size_t)color);
        };
#pragma omp parallel for schedule(static)
        for (size_t cb = 0; cb < m.n_coarse; ++cb)
            for (int cs = 0; cs < 2; ++cs)
                for (int v = 0; v < 24; ++v)
                    for (int ls = 0; ls < m.block_volume; ++ls)
                        for (int fs = 0; fs < 2; ++fs)
                            for (int color = 0; color < 3; ++color)
                            {
                                size_t qi = qidx(cb, cs, v, ls, fs, color);
                                Complex z((double)raw[2 * qi], (double)raw[2 * qi + 1]);
                                int a = (2 * cs + fs) * 3 + color;
                                int d = cs * 24 + v;
                                m.basis[basis_index(cb, ls, a, d, m)] = z;
                            }
    }
    if (m.o.basis != "canonical")
        // Start with a clover-informed block-constant basis.  The normalization
        // makes P^dagger P=I to roundoff while retaining local spin/color mixing.
        for (int bt = 0; bt < m.ct; ++bt)
            for (int bz = 0; bz < m.cz; ++bz)
                for (int by = 0; by < m.cy; ++by)
                    for (int bx = 0; bx < m.cx; ++bx)
                    {
                        size_t cb = coarse_site_index(bx, by, bz, bt, m);
                        for (int lt = 0; lt < m.o.bt; ++lt)
                            for (int lz = 0; lz < m.o.bz; ++lz)
                                for (int ly = 0; ly < m.o.by; ++ly)
                                    for (int lx = 0; lx < m.o.bx; ++lx)
                                    {
                                        int x = bx * m.o.bx + lx, y = by * m.o.by + ly;
                                        int z = bz * m.o.bz + lz, t = bt * m.o.bt + lt;
                                        size_t fs = site_index(x, y, z, t, m.o);
                                        int ls = local_site(x, y, z, t, m);
                                        for (int a = 0; a < 12; ++a)
                                            for (int d = 0; d < m.coarse_dof; ++d)
                                            {
                                                if (m.o.basis == "canonical")
                                                    continue;
                                                Complex v = (a == d ? Complex(1.0) : Complex(0.0));
                                                // Local clover information supplies the block basis shape.
                                                v += 0.25 * (g.clover[fs * 144 + a * 12 + d] - (a == d ? Complex(1.0) : Complex(0.0)));
                                                m.basis[basis_index(cb, ls, a, d, m)] = v;
                                            }
                                    }
                        for (int d = 0; d < m.coarse_dof; ++d)
                        {
                            double n = 0;
                            for (int ls = 0; ls < m.block_volume; ++ls)
                                for (int a = 0; a < 12; ++a)
                                    n += std::norm(m.basis[basis_index(cb, ls, a, d, m)]);
                            if (m.o.basis != "canonical")
                            {
                                if (m.o.basis != "canonical")
                                {
                                    n = std::sqrt(n);
                                    for (int ls = 0; ls < m.block_volume; ++ls)
                                        for (int a = 0; a < 12; ++a)
                                            m.basis[basis_index(cb, ls, a, d, m)] /= n;
                                }
                            }
                        }
                    }
    // Construct Ac = R A P once.  A coarse site_index has an onsite block and one
    // block for each nearest coarse neighbour; locality of the fine stencil
    // makes all other entries exactly zero.
    m.stencil.assign(m.n_coarse * 9ull * (size_t)m.coarse_dof * m.coarse_dof, Complex{});
#pragma omp parallel for schedule(dynamic, 1)
    for (size_t cb = 0; cb < m.n_coarse; ++cb)
        assemble_local_block(g, m, cb, m.stencil);
}
void prolong_field(const Multigrid &m, const Field &coarse, Field &fine, int nr)
{
    fine.assign(m.n_fine * (size_t)nr * 12, Complex{});
#pragma omp parallel for collapse(4) schedule(static)
    for (int t = 0; t < m.o.nt; ++t)
        for (int z = 0; z < m.o.nz; ++z)
            for (int y = 0; y < m.o.ny; ++y)
                for (int x = 0; x < m.o.nx; ++x)
                {
                    size_t fs = site_index(x, y, z, t, m.o), cb = coarse_site_index(x / m.o.bx, y / m.o.by, z / m.o.bz, t / m.o.bt, m);
                    int ls = local_site(x, y, z, t, m);
                    for (int r = 0; r < nr; ++r)
                        for (int a = 0; a < 12; ++a)
                        {
                            Complex v = 0;
                            for (int d = 0; d < m.coarse_dof; ++d)
                                v += m.basis[basis_index(cb, ls, a, d, m)] * coarse[(cb * (size_t)nr + r) * m.coarse_dof + d];
                            fine[spinor_index(fs, r, a / 3, a % 3, nr)] = v;
                        }
                }
}
void restrict_field(const Multigrid &m, const Field &fine, Field &coarse, int nr)
{
    coarse.assign(m.n_coarse * (size_t)nr * m.coarse_dof, Complex{});
#pragma omp parallel for schedule(static)
    for (size_t block = 0; block < m.n_coarse; ++block)
    {
        int bx = block % m.cx, by = (block / m.cx) % m.cy;
        int bz = (block / (m.cx * m.cy)) % m.cz, bt = block / (m.cx * m.cy * m.cz);
        for (int lt = 0; lt < m.o.bt; ++lt)
            for (int lz = 0; lz < m.o.bz; ++lz)
                for (int ly = 0; ly < m.o.by; ++ly)
                    for (int lx = 0; lx < m.o.bx; ++lx)
                    {
                        int x = bx * m.o.bx + lx, y = by * m.o.by + ly, z = bz * m.o.bz + lz, t = bt * m.o.bt + lt;
                        size_t fs = site_index(x, y, z, t, m.o), cb = coarse_site_index(x / m.o.bx, y / m.o.by, z / m.o.bz, t / m.o.bt, m);
                        int ls = local_site(x, y, z, t, m);
                        for (int r = 0; r < nr; ++r)
                            for (int d = 0; d < m.coarse_dof; ++d)
                            {
                                Complex v = 0;
                                for (int a = 0; a < 12; ++a)
                                    v += std::conj(m.basis[basis_index(cb, ls, a, d, m)]) * fine[spinor_index(fs, r, a / 3, a % 3, nr)];
                                coarse[(cb * (size_t)nr + r) * m.coarse_dof + d] += v;
                            }
                    }
    }
}
void apply_coarse_matrixfree(const Gauge &g, const Multigrid &m, const Field &x, Field &y, int nr)
{
    Field fine_x, fine_y;
    prolong_field(m, x, fine_x, nr);
    apply_dirac(g, fine_x, fine_y, nr);
    restrict_field(m, fine_y, y, nr);
}
void apply_coarse(const Gauge &g, const Multigrid &m, const Field &x, Field &y, int nr)
{
    if (!m.stencil.empty())
    {
        y.assign(m.n_coarse * (size_t)nr * m.coarse_dof, Complex{});
        const int dx[9] = {0, 1, -1, 0, 0, 0, 0, 0, 0};
        const int dy[9] = {0, 0, 0, 1, -1, 0, 0, 0, 0};
        const int dz[9] = {0, 0, 0, 0, 0, 1, -1, 0, 0};
        const int dt[9] = {0, 0, 0, 0, 0, 0, 0, 1, -1};
#pragma omp parallel for collapse(4) schedule(static)
        for (int bt = 0; bt < m.ct; ++bt)
            for (int bz = 0; bz < m.cz; ++bz)
                for (int by = 0; by < m.cy; ++by)
                    for (int bx = 0; bx < m.cx; ++bx)
                    {
                        size_t cb = coarse_site_index(bx, by, bz, bt, m);
                        for (int dir = 0; dir < 9; ++dir)
                        {
                            size_t sb = coarse_site_index((bx + dx[dir] + m.cx) % m.cx,
                                              (by + dy[dir] + m.cy) % m.cy,
                                              (bz + dz[dir] + m.cz) % m.cz,
                                              (bt + dt[dir] + m.ct) % m.ct, m);
                            for (int r = 0; r < nr; ++r)
                                for (int a = 0; a < m.coarse_dof; ++a)
                                {
                                    Complex v = 0;
                                    for (int d = 0; d < m.coarse_dof; ++d)
                                        v += m.stencil[(cb * 9 + dir) * (size_t)m.coarse_dof * m.coarse_dof + a * m.coarse_dof + d] * x[(sb * (size_t)nr + r) * m.coarse_dof + d];
                                    y[(cb * (size_t)nr + r) * m.coarse_dof + a] += v;
                                }
                        }
                    }
        return;
    }
    throw std::runtime_error("coarse stencil has not been built");
}
static void coarse_solve(const Gauge &g, const Multigrid &m, const Field &b, Field &x, int nr)
{
    x.assign(b.size(), Complex{});
    Field r = b;
    double bn = std::max(norm(b), 1e-300);
    std::vector<Field> zs, qs;
    static bool first = true;
    int iterations = 0;
    std::ofstream history;
    if (first && !g.o.trace.empty())
    {
        history.open(g.o.trace + "/coarse.history");
        history << std::setprecision(17) << "0 1\n";
    }
    for (int it = 0; it < 8; ++it)
    {
        Field z = r, q;
        apply_coarse(g, m, z, q, nr);
        for (size_t j = 0; j < qs.size(); ++j)
        {
            Complex beta = dot(qs[j], q) / std::max(std::real(dot(qs[j], qs[j])), 1e-300);
            axpy(z, -beta, zs[j]);
            axpy(q, -beta, qs[j]);
        }
        double den = std::real(dot(q, q));
        if (den == 0)
            break;
        Complex alpha = dot(q, r) / den;
        axpy(x, alpha, z);
        axpy(r, -alpha, q);
        zs.push_back(std::move(z));
        qs.push_back(std::move(q));
        iterations = it + 1;
        if (history)
            history << iterations << " " << norm(r) / bn << "\n";
        if (norm(r) / bn < 0.5)
            break;
    }
    if (first && !g.o.trace.empty())
        std::ofstream(g.o.trace + "/coarse.iterations") << iterations << "\n";
    first = false;
}
// QUDA CA-GCR with nu_post=Nkrylov=1: a one-vector minimal residual
// correction. No clover inverse or Jacobi step appears in this algorithm.
static void smooth(const Gauge &g, Field &x, const Field &b, int nr, int steps)
{
    if (steps != 1)
        throw std::runtime_error("oracle smoother requires Nkrylov=1");
    Field ax, r = b, ar;
    apply_dirac(g, x, ax, nr);
    axpy(r, -1., ax);
    apply_dirac(g, r, ar, nr);
    double den = dot(ar, ar).real();
    if (den > 0)
        axpy(x, dot(ar, r) / den, r);
}
void vcycle(const Gauge &g, const Multigrid &m, Field &x, const Field &b, int nr)
{
    Field rc, ec;
    restrict_field(m, b, rc, nr); // nu_pre=0, zero initial guess
    coarse_solve(g, m, rc, ec, nr);
    prolong_field(m, ec, x, nr);
    static bool first = true;
    const bool trace = first && !g.o.trace.empty();
    if (trace)
    {
        dump(g.o.trace + "/b.bin", b);
        dump(g.o.trace + "/rc.bin", rc);
        dump(g.o.trace + "/ec.bin", ec);
        dump(g.o.trace + "/pe.bin", x);
        Field ac;
        apply_coarse(g, m, ec, ac, nr);
        dump(g.o.trace + "/ace.bin", ac);
    }
    smooth(g, x, b, nr, 1);
    if (trace)
        dump(g.o.trace + "/x.bin", x);
    first = false;
}
