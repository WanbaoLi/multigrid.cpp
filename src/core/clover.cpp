#include "lqcd/core/clover.h"

struct Matrix3 {
    Complex v[3][3]{};
    Complex *operator[](int i) { return v[i]; }
    const Complex *operator[](int i) const { return v[i]; }
};
static Matrix3 m3_mul(const Matrix3 &a, const Matrix3 &b) {
    Matrix3 c;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            for (int k = 0; k < 3; k++)
                c[i][j] += a[i][k] * b[k][j];
    return c;
}
static Matrix3 m3_dag(const Matrix3 &a) {
    Matrix3 c;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            c[i][j] = std::conj(a[j][i]);
    return c;
}
static Matrix3 m3_add(const Matrix3 &a, const Matrix3 &b) {
    Matrix3 c;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            c[i][j] = a[i][j] + b[i][j];
    return c;
}

// Construct the uncompressed Wilson Clover matrix from the anti-Hermitian
// four-leaf field strength (sum - sum^dagger)/8, for pairs
// (1,0),(2,0),(2,1),(3,0),(3,1),(3,2). The two Hermitian 6x6 blocks
// act directly on spin pairs (0,1) and (2,3) in the DeGrand-Rossi convention.
// This is the normalization checked against the QUDA oracle.
static void build_clover_site(const Gauge &g, int x, int y, int z, int t, Complex out[12][12],
                              double coeff) {
    Matrix3 F[6]{};
    int dx[4] = {1, 0, 0, 0}, dy[4] = {0, 1, 0, 0}, dz[4] = {0, 0, 1, 0}, dt[4] = {0, 0, 0, 1};
    auto U = [&](int xx, int yy, int zz, int tt, int m) -> Matrix3 {
        Matrix3 a;
        size_t s =
            site_index(wrap(xx, g.o.nx), wrap(yy, g.o.ny), wrap(zz, g.o.nz), wrap(tt, g.o.nt), g.o);
        for (int r = 0; r < 3; r++)
            for (int c = 0; c < 3; c++)
                a[r][c] = g.at(s, m, r, c);
        return a;
    };
    int pairs[6][2] = {{1, 0}, {2, 0}, {2, 1}, {3, 0}, {3, 1}, {3, 2}};
    for (int q = 0; q < 6; q++) {
        int mu = pairs[q][0], nu = pairs[q][1];
        Matrix3 sum{};
        // U(x,mu) U(x+mu,nu) U^dag(x+nu,mu) U^dag(x,nu)
        sum = m3_add(
            sum,
            m3_mul(m3_mul(U(x, y, z, t, mu), U(x + dx[mu], y + dy[mu], z + dz[mu], t + dt[mu], nu)),
                   m3_mul(m3_dag(U(x + dx[nu], y + dy[nu], z + dz[nu], t + dt[nu], mu)),
                          m3_dag(U(x, y, z, t, nu)))));
        // U(x,nu) U^dag(x+nu-mu,mu) U^dag(x-mu,nu) U(x-mu,mu)
        sum =
            m3_add(sum, m3_mul(m3_mul(U(x, y, z, t, nu),
                                      m3_dag(U(x + dx[nu] - dx[mu], y + dy[nu] - dy[mu],
                                               z + dz[nu] - dz[mu], t + dt[nu] - dt[mu], mu))),
                               m3_mul(m3_dag(U(x - dx[mu], y - dy[mu], z - dz[mu], t - dt[mu], nu)),
                                      U(x - dx[mu], y - dy[mu], z - dz[mu], t - dt[mu], mu))));
        // U^dag(x-nu,nu) U(x-nu,mu) U(x+mu-nu,nu) U^dag(x,mu)
        sum =
            m3_add(sum, m3_mul(m3_mul(m3_dag(U(x - dx[nu], y - dy[nu], z - dz[nu], t - dt[nu], nu)),
                                      U(x - dx[nu], y - dy[nu], z - dz[nu], t - dt[nu], mu)),
                               m3_mul(U(x + dx[mu] - dx[nu], y + dy[mu] - dy[nu],
                                        z + dz[mu] - dz[nu], t + dt[mu] - dt[nu], nu),
                                      m3_dag(U(x, y, z, t, mu)))));
        // U^dag(x-mu,mu) U^dag(x-mu-nu,nu) U(x-mu-nu,mu) U(x-nu,nu)
        sum =
            m3_add(sum, m3_mul(m3_mul(m3_dag(U(x - dx[mu], y - dy[mu], z - dz[mu], t - dt[mu], mu)),
                                      m3_dag(U(x - dx[mu] - dx[nu], y - dy[mu] - dy[nu],
                                               z - dz[mu] - dz[nu], t - dt[mu] - dt[nu], nu))),
                               m3_mul(U(x - dx[mu] - dx[nu], y - dy[mu] - dy[nu],
                                        z - dz[mu] - dz[nu], t - dt[mu] - dt[nu], mu),
                                      U(x - dx[nu], y - dy[nu], z - dz[nu], t - dt[nu], nu))));
        Matrix3 sd = m3_dag(sum);
        for (int r = 0; r < 3; r++)
            for (int c = 0; c < 3; c++)
                F[q][r][c] = (sum[r][c] - sd[r][c]) * 0.125;
    }
    Complex I(0, 1);
    // Build both chiral blocks and fill their Hermitian partners.
    Complex H[2][6][6]{};
    for (int ch = 0; ch < 2; ch++) {
        for (int i = 0; i < 6; i++)
            H[ch][i][i] = 0.5;
        Matrix3 B10{}, B20{};
        for (int r = 0; r < 3; r++)
            for (int c = 0; c < 3; c++) {
                B10[r][c] = I * coeff * (F[0][r][c] + (ch ? 1. : -1.) * F[5][r][c]);
                B20[r][c] = coeff * (F[1][r][c] + (ch ? -1. : 1.) * F[4][r][c] -
                                     I * (F[2][r][c] + (ch ? 1. : -1.) * F[3][r][c]));
            }
        for (int i = 0; i < 3; i++) {
            H[ch][i][i] = 0.5 * (1. - B10[i][i].real());
            H[ch][i + 3][i + 3] = 0.5 * (1. + B10[i][i].real());
        }
        auto set = [&](int i, int j, Complex v) {
            H[ch][i][j] = 0.5 * v;
            H[ch][j][i] = std::conj(0.5 * v);
        };
        set(1, 0, -B10[1][0]);
        set(2, 0, -B10[2][0]);
        set(2, 1, -B10[2][1]);
        for (int c = 0; c < 3; c++) {
            set(3, c, B20[0][c]);
            set(4, c, B20[1][c]);
            set(5, c, B20[2][c]);
        }
        set(4, 3, B10[1][0]);
        set(5, 3, B10[2][0]);
        set(5, 4, B10[2][1]);
    }
    // The canonical QUDA DeGrand-Rossi field layout is already the chiral
    // ordering used by the two stored 6x6 blocks: spins (0,1) and (2,3).
    // Apply the blocks directly in spin-major/color-minor order.
    for (int so = 0; so < 4; so++)
        for (int co = 0; co < 3; co++)
            for (int si0 = 0; si0 < 4; si0++)
                for (int ci = 0; ci < 3; ci++)
                    out[so * 3 + co][si0 * 3 + ci] =
                        (so / 2 == si0 / 2) ? 2.0 * H[so / 2][(so % 2) * 3 + co][(si0 % 2) * 3 + ci]
                                            : Complex{};
}
void build_clover(const Gauge &g, Field &all) {
    const Options &o = g.o;
    size_t n = (size_t)o.nx * o.ny * o.nz * o.nt;
    all.resize(n * 144);
#pragma omp parallel for collapse(4) schedule(static)
    for (int t = 0; t < o.nt; t++)
        for (int z = 0; z < o.nz; z++)
            for (int y = 0; y < o.ny; y++)
                for (int x = 0; x < o.nx; x++) {
                    Complex m[12][12];
                    build_clover_site(g, x, y, z, t, m, o.csw / (2. * (o.mass + 4.)));
                    size_t s = site_index(x, y, z, t, o);
                    for (int i = 0; i < 12; i++)
                        for (int j = 0; j < 12; j++)
                            all[s * 144 + i * 12 + j] = m[i][j];
                }
}
// The local diagonal/clover contribution, exported separately for validation.
void apply_clover_only(const Gauge &g, const Field &in, Field &out, int nr) {
    const Options &o = g.o;
    size_t n = (size_t)o.nx * o.ny * o.nz * o.nt;
    out.assign(in.size(), Complex{});
#pragma omp parallel for collapse(4) schedule(static)
    for (int t = 0; t < o.nt; t++)
        for (int z = 0; z < o.nz; z++)
            for (int y = 0; y < o.ny; y++)
                for (int x = 0; x < o.nx; x++) {
                    size_t s = site_index(x, y, z, t, o);
                    for (int r = 0; r < nr; r++)
                        for (int a = 0; a < 12; a++)
                            for (int bs = 0; bs < 4; bs++)
                                for (int bc = 0; bc < 3; bc++)
                                    out[spinor_index(s, r, a / 3, a % 3, nr) + 0] +=
                                        g.clover[s * 144 + a * 12 + bs * 3 + bc] *
                                        in[spinor_index(s, r, bs, bc, nr)];
                }
}
