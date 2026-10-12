#include "dslash.h"

// Euclidean gamma matrices.  gamma[mu][a][b] is used in (1 +/- gamma_mu).
Complex gamma_matrix[4][4][4];
void gamma_init()
{
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            for (int k = 0; k < 4; k++)
                gamma_matrix[i][j][k] = 0.;
    // QUDA's DeGrand-Rossi basis (gamma.cuh), directions X,Y,Z,T.
    // Each matrix is sparse; spelling out the entries keeps the projector
    // convention visible and avoids relying on a different gamma basis.
    Complex I(0, 1);
    // gamma_X: (0,3)=i, (1,2)=i, (2,1)=-i, (3,0)=-i
    gamma_matrix[0][0][3] = I;
    gamma_matrix[0][1][2] = I;
    gamma_matrix[0][2][1] = -I;
    gamma_matrix[0][3][0] = -I;
    // gamma_Y: (0,3)=-1, (1,2)=1, (2,1)=1, (3,0)=-1
    gamma_matrix[1][0][3] = -1.;
    gamma_matrix[1][1][2] = 1.;
    gamma_matrix[1][2][1] = 1.;
    gamma_matrix[1][3][0] = -1.;
    // gamma_Z: (0,2)=i, (1,3)=-i, (2,0)=-i, (3,1)=i
    gamma_matrix[2][0][2] = I;
    gamma_matrix[2][1][3] = -I;
    gamma_matrix[2][2][0] = -I;
    gamma_matrix[2][3][1] = I;
    // gamma_T: (0,2)=1, (1,3)=1, (2,0)=1, (3,1)=1
    gamma_matrix[3][0][2] = 1.;
    gamma_matrix[3][1][3] = 1.;
    gamma_matrix[3][2][0] = 1.;
    gamma_matrix[3][3][1] = 1.;
}
// Normalized M psi = Clover psi - kappa * sum_mu[(1-gamma_mu)U_mu psi(x+mu)+(1+gamma_mu)U_mu^dag psi(x-mu)].
void add_dslash(const Gauge &g, const Field &in, Field &out, int nr, double mass)
{
    const Options &o = g.o;
    double k = 1. / (2. * (mass + 4.));
#pragma omp parallel for collapse(4) schedule(static)
    for (int t = 0; t < o.nt; t++)
        for (int z = 0; z < o.nz; z++)
            for (int y = 0; y < o.ny; y++)
                for (int x = 0; x < o.nx; x++)
                {
                    size_t s = site_index(x, y, z, t, o);
                    for (int mu = 0; mu < 4; mu++)
                    {
                        int xx = x, yy = y, zz = z, tt = t;
                        if (mu == 0)
                            xx = wrap(x + 1, o.nx);
                        if (mu == 1)
                            yy = wrap(y + 1, o.ny);
                        if (mu == 2)
                            zz = wrap(z + 1, o.nz);
                        if (mu == 3)
                            tt = wrap(t + 1, o.nt);
                        size_t sf = site_index(xx, yy, zz, tt, o);
                        double pf = (mu == 3 && t == o.nt - 1) ? -1. : 1.;
                        xx = x;
                        yy = y;
                        zz = z;
                        tt = t;
                        if (mu == 0)
                            xx = wrap(x - 1, o.nx);
                        if (mu == 1)
                            yy = wrap(y - 1, o.ny);
                        if (mu == 2)
                            zz = wrap(z - 1, o.nz);
                        if (mu == 3)
                            tt = wrap(t - 1, o.nt);
                        size_t sb = site_index(xx, yy, zz, tt, o);
                        double pb = (mu == 3 && t == 0) ? -1. : 1.;
                        for (int r = 0; r < nr; r++)
                        {
                            Complex f[4][3]{}, b[4][3]{};
                            for (int a = 0; a < 4; a++)
                                for (int j = 0; j < 3; j++)
                                {
                                    for (int q = 0; q < 3; q++)
                                    {
                                        f[a][j] += g.at(s, mu, j, q) * in[spinor_index(sf, r, a, q, nr)];
                                        b[a][j] += std::conj(g.at(sb, mu, q, j)) * in[spinor_index(sb, r, a, q, nr)];
                                    }
                                }
                            for (int c = 0; c < 3; c++)
                                for (int a = 0; a < 4; a++)
                                {
                                    Complex vf = f[a][c], vb = b[a][c];
                                    for (int bspin = 0; bspin < 4; bspin++)
                                        if (gamma_matrix[mu][a][bspin] != Complex{})
                                        {
                                            vf -= gamma_matrix[mu][a][bspin] * f[bspin][c];
                                            vb += gamma_matrix[mu][a][bspin] * b[bspin][c];
                                        }
                                    out[spinor_index(s, r, a, c, nr)] -= k * (pf * vf + pb * vb);
                                }
                        }
                    }
                }
}

void apply_dslash(const Gauge &g, const Field &in, Field &out, int nr)
{
    out.assign(in.size(), Complex{});
    add_dslash(g, in, out, nr);
}
