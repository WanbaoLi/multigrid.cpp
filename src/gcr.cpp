#include "gcr.h"
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>

void solve_gcr(const LinearOperator &apply, const LinearOperator &precondition, const Field &b, Field &x, const GcrOptions &o)
{
    x.assign(b.size(), Complex{});
    Field ax, r;
    apply(x, ax);
    r = b;
    axpy(r, -1., ax);
    double bn = std::max(norm(b), 1e-300);
    std::vector<Field> zs, qs;
    std::ofstream history(o.out + ".history");
    history << std::setprecision(17) << "0 1\n";
    int iterations = 0;
    for (int it = 0; it < o.maxit; ++it)
    {
        Field z;
        if (!precondition)
            z = r;
        else
            precondition(r, z);
        Field q;
        apply(z, q);
        for (size_t j = 0; j < qs.size(); ++j)
        {
            Complex beta = dot(qs[j], q) / std::max(std::real(dot(qs[j], qs[j])), 1e-300);
            axpy(z, -beta, zs[j]);
            axpy(q, -beta, qs[j]);
        }
        Complex alpha = dot(q, r) / std::max(std::real(dot(q, q)), 1e-300);
        axpy(x, alpha, z);
        axpy(r, -alpha, q);
        zs.push_back(std::move(z));
        qs.push_back(std::move(q));
        double rel = norm(r) / bn;
        iterations = it + 1;
        history << iterations << " " << rel << "\n";
        if (it % 10 == 0)
            std::cerr << "GCR iter " << iterations << " residual " << rel << "\n";
        if (rel < o.tol || zs.size() == (size_t)o.restart || iterations == o.maxit)
        {
            apply(x, ax);
            r = b;
            axpy(r, -1., ax);
            if (norm(r) / bn < o.tol)
                break;
            zs.clear();
            qs.clear();
        }
    }
    std::ofstream(o.out + ".iterations") << iterations << "\n";
}
