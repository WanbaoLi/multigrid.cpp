#pragma once
#include <complex>
#include <cstddef>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using Field = std::vector<Complex>;
constexpr int FINE_DOF = 12;
constexpr int COARSE_DOF = 48;

struct Lattice {
    int nx = 24, ny = 24, nz = 24, nt = 64;
};

// Contiguous spinors: [t,z,y,x][rhs][spin][color].
size_t site_index(int x, int y, int z, int t, const Lattice &o);
size_t spinor_index(size_t s, int r, int sp, int c, int nr);
int wrap(int a, int n);
void read_binary(const std::string &path, Field &v);
void dump(const std::string &path, const Field &v);
Complex dot(const Field &a, const Field &b);
double norm(const Field &a);
void axpy(Field &y, Complex a, const Field &x);
