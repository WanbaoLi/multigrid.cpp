#pragma once
#include "lqcd/lqcd.h"
#include <array>
#include <complex>
#include <memory>
#include <mpi.h>
#include <stdexcept>
#include <string>
#include <vector>
namespace lqcd {
using Complex = std::complex<double>;
using Vector = std::vector<Complex>;
struct Error : std::runtime_error {
    int code;
    Error(int c, const std::string &s) : std::runtime_error(s), code(c) {}
};
struct Geometry {
    std::array<int, 4> local{}, coords{};
    size_t volume = 0;
};
struct SolveInfo {
    int iterations;
    bool converged;
    double seconds;
};
class Backend {
  public:
    virtual ~Backend() = default;
    virtual void load_gauge(const Vector &gauge) = 0;
    virtual void setup() = 0;
    virtual void apply(const Vector &in, Vector &out) = 0;
    virtual SolveInfo solve(const Vector &b, Vector &x, double tol) = 0;
    virtual std::vector<SolveInfo> solve_batch(const std::vector<Vector> &b, std::vector<Vector> &x,
                                               double tol) {
        x.resize(b.size());
        std::vector<SolveInfo> result;
        for (size_t i = 0; i < b.size(); ++i)
            result.push_back(solve(b[i], x[i], tol));
        return result;
    }
};
std::unique_ptr<Backend> make_backend(const std::string &, const lqcd_config &, const Geometry &,
                                      MPI_Comm);
std::unique_ptr<Backend> make_ddalphaamg(const lqcd_config &, const Geometry &, MPI_Comm);
/* layout routines only change external packing; spin basis belongs to backend */
void unpack_gauge(const lqcd_field_view &, const Geometry &, Vector &);
void unpack_spinor(const lqcd_field_view &, const Geometry &, Vector &);
void pack_spinor(const Vector &, const Geometry &, lqcd_field_view &);
} // namespace lqcd
