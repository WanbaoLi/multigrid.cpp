#include "environment.hpp"
#include <cmath>
#include <cstdlib>
namespace lqcd_native::detail {
MPI_Comm native_comm = MPI_COMM_SELF;
int native_rank = 0, native_size = 1;
unsigned native_seed = 1024;
int setting(const char *name, int fallback) {
    auto v = std::getenv(name);
    return v ? std::atoi(v) : fallback;
}
// Double Krylov fields contain only this rank's lexical t slab. Convergence
// scalars cover the full lattice and must make every rank take the same branch.
double distributed_norm(const Field &v) {
    double sum = 0;
#pragma omp parallel for reduction(+ : sum) schedule(static)
    for (size_t i = 0; i < v.size(); i++)
        sum += std::norm(v[i]);
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &sum, 1, MPI_DOUBLE, MPI_SUM, native_comm);
    return std::sqrt(sum);
}
Complex distributed_dot(const Field &a, const Field &b) {
    double re = 0, im = 0;
#pragma omp parallel for reduction(+ : re, im) schedule(static)
    for (size_t i = 0; i < a.size(); i++) {
        const Complex z = std::conj(a[i]) * b[i];
        re += z.real();
        im += z.imag();
    }
    double sum[2] = {re, im};
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, sum, 2, MPI_DOUBLE, MPI_SUM, native_comm);
    return {sum[0], sum[1]};
}
double fine_norm(const FloatField &v) {
    double sum = 0;
    // Fine fields retain global-index storage, with only this slab owned.
    const size_t first = v.size() * native_rank / native_size;
    const size_t last = v.size() * (native_rank + 1) / native_size;
#pragma omp parallel for reduction(+ : sum) schedule(static) if (v.size() > 100000)
    for (size_t i = first; i < last; i++)
        sum += (double)v[i] * v[i];
    if (native_size > 1) {
        double total;
        MPI_Allreduce(&sum, &total, 1, MPI_DOUBLE, MPI_SUM, native_comm);
        sum = total;
    }
    return std::sqrt(sum);
}
double coarse_norm(const FloatField &v) {
    // Coarse Krylov fields contain owned entries only, never replicated.
    double sum = 0;
#pragma omp parallel for reduction(+ : sum) schedule(static) if (v.size() > 100000)
    for (size_t i = 0; i < v.size(); i++)
        sum += (double)v[i] * v[i];
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &sum, 1, MPI_DOUBLE, MPI_SUM, native_comm);
    return std::sqrt(sum);
}
Complex coarse_dot(const FloatField &a, const FloatField &b) {
    double re = 0, im = 0;
#pragma omp parallel for reduction(+ : re, im) schedule(static) if (a.size() > 100000)
    for (size_t i = 0; i < a.size() / 2; i++) {
        re += (double)a[2 * i] * b[2 * i] + (double)a[2 * i + 1] * b[2 * i + 1];
        im += (double)a[2 * i] * b[2 * i + 1] - (double)a[2 * i + 1] * b[2 * i];
    }
    if (native_size > 1) {
        double sums[2] = {re, im};
        MPI_Allreduce(MPI_IN_PLACE, sums, 2, MPI_DOUBLE, MPI_SUM, native_comm);
        re = sums[0];
        im = sums[1];
    }
    return {re, im};
}
void coarse_axpy(FloatField &y, Complex z, const FloatField &x) {
    float ar = z.real(), ai = z.imag();
#pragma omp parallel for schedule(static) if (y.size() > 100000)
    for (size_t i = 0; i < y.size() / 2; i++) {
        float xr = x[2 * i], xi = x[2 * i + 1];
        y[2 * i] += ar * xr - ai * xi;
        y[2 * i + 1] += ar * xi + ai * xr;
    }
}

} // namespace lqcd_native::detail
