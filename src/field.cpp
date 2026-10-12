#include "field.h"
#include <cmath>
#include <fstream>
#include <stdexcept>

size_t site_index(int x, int y, int z, int t, const Lattice &o) { return (((size_t)t * o.nz + z) * o.ny + y) * o.nx + x; }
size_t spinor_index(size_t s, int r, int sp, int c, int nr) { return (s * nr + r) * 12 + sp * 3 + c; }
int wrap(int a, int n) { return (a + n) % n; }
void read_binary(const std::string &p, Field &v)
{
    std::ifstream f(p, std::ios::binary);
    if (!f)
        throw std::runtime_error("cannot open " + p);
    f.read(reinterpret_cast<char *>(v.data()), v.size() * sizeof(Complex));
    if (f.gcount() != (std::streamsize)(v.size() * sizeof(Complex)) || f.peek() != EOF)
        throw std::runtime_error("incorrect binary size: " + p);
}
void dump(const std::string &path, const Field &v)
{
    if (path.empty())
        return;
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char *>(v.data()), v.size() * sizeof(Complex));
    if (!f)
        throw std::runtime_error("cannot write " + path);
}
Complex dot(const Field &a, const Field &b)
{
    double re = 0, im = 0;
#pragma omp parallel for reduction(+ : re, im) schedule(static) if (a.size() > 100000)
    for (size_t i = 0; i < a.size(); i++)
    {
        Complex z = std::conj(a[i]) * b[i];
        re += z.real();
        im += z.imag();
    }
    return Complex(re, im);
}
double norm(const Field &a) { return std::sqrt(dot(a, a).real()); }
void axpy(Field &y, Complex a, const Field &x)
{
#pragma omp parallel for schedule(static) if (y.size() > 100000)
    for (size_t i = 0; i < y.size(); i++)
        y[i] += a * x[i];
}
