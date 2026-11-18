#include <cmath>
#include <complex>
#include <cstdint>

namespace {
using Complex = std::complex<double>;
using Matrix = Complex[3][3];

void multiply(const Matrix &left, const Matrix &right, Matrix &out) {
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col)
            out[row][col] = left[row][0] * right[0][col] +
                            left[row][1] * right[1][col] +
                            left[row][2] * right[2][col];
}

void solve_near_identity(Matrix &left, Matrix &right, Matrix &out) {
    // The Padé denominator stays strictly diagonally dominant inside
    // the norm cutoff, so a fixed elimination order suffices.
    for (int pivot = 0; pivot < 2; ++pivot) {
        for (int row = pivot + 1; row < 3; ++row) {
            const Complex factor = left[row][pivot] / left[pivot][pivot];
            for (int col = pivot + 1; col < 3; ++col)
                left[row][col] -= factor * left[pivot][col];
            for (int col = 0; col < 3; ++col)
                right[row][col] -= factor * right[pivot][col];
        }
    }
    for (int row = 2; row >= 0; --row) {
        const Complex inverse = 1. / left[row][row];
        for (int col = 0; col < 3; ++col) {
            Complex value = right[row][col];
            for (int k = row + 1; k < 3; ++k)
                value -= left[row][k] * out[k][col];
            out[row][col] = inverse * value;
        }
    }
}

bool pade_link(const Complex *gauge, const double *momentum, double step, Complex *out) {
    constexpr double inv_sqrt12 = 0.28867513459481288225;
    const double half_step = .5 * step;
    const double tail = (step * inv_sqrt12) * momentum[7];
    const double diagonal = half_step * momentum[6];
    Matrix x{};
    // Match the three off-diagonal generator pairs and the two diagonal
    // generators in reference.generators().
    x[0][0] = {0., diagonal + tail};
    x[1][1] = {0., tail - diagonal};
    x[2][2] = {0., -2. * tail};
    int component = 0;
    for (int row = 0; row < 2; ++row) {
        for (int col = row + 1; col < 3; ++col) {
            x[row][col] = {half_step * momentum[component + 1], half_step * momentum[component]};
            x[col][row] = -std::conj(x[row][col]);
            component += 2;
        }
    }
    for (int col = 0; col < 3; ++col) {
        const double norm = std::abs(x[0][col]) + std::abs(x[1][col]) + std::abs(x[2][col]);
        if (!(norm <= .25))
            return false;
    }

    Matrix squared, fourth, even, odd_polynomial, odd, denominator, numerator, links, rhs, rotated;
    multiply(x, x, squared);
    multiply(squared, squared, fourth);
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col) {
            const double identity = row == col ? 1. : 0.;
            even[row][col] = identity + (1. / 9.) * squared[row][col] + (1. / 1008.) * fourth[row][col];
            odd_polynomial[row][col] = .5 * identity + (1. / 72.) * squared[row][col] +
                                       (1. / 30240.) * fourth[row][col];
            links[row][col] = gauge[3 * row + col];
        }
    multiply(x, odd_polynomial, odd);
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col) {
            denominator[row][col] = even[row][col] - odd[row][col];
            numerator[row][col] = even[row][col] + odd[row][col];
        }
    multiply(numerator, links, rhs);
    solve_near_identity(denominator, rhs, rotated);
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col)
            out[3 * row + col] = rotated[row][col];
    return true;
}
}

extern "C" int lqcd_hmc_pade_drift(std::int64_t links, double step, int threads,
    const Complex *gauge, const double *momenta, Complex *output) {
    int outside = 0;
#pragma omp parallel for if(threads > 1 && links >= 128) num_threads(threads) schedule(static) reduction(|:outside)
    for (std::int64_t link = 0; link < links; ++link)
        outside |= !pade_link(gauge + 9 * link, momenta + 8 * link, step, output + 9 * link);
    return outside;
}
