#include "core/dslash.h"

#include <array>
#include <cstdint>

namespace {
struct Projector {
    int lower_spin;
    double sign;
    bool imaginary;
};
using ProjectorTable = std::array<std::array<Projector, 2>, 8>;

const auto &projectors() {
    static const auto table = [] {
        gamma_init();
        ProjectorTable values{};
        for (int direction = 0; direction < 8; ++direction) {
            const double sign = direction % 2 == 0 ? -1. : 1.;
            for (int spin = 0; spin < 2; ++spin)
                for (int lower = 2; lower < 4; ++lower) {
                    const Complex element = gamma_matrix[direction / 2][spin][lower];
                    if (element != Complex{}) {
                        // Nonzero DeGrand–Rossi phases are ±1 or ±i.
                        const bool imaginary = element.real() == 0.;
                        const double component = imaginary ? element.imag() : element.real();
                        values[direction][spin] = {lower, sign * component, imaginary};
                    }
                }
        }
        return values;
    }();
    return table;
}

Complex rotate_phase(Complex value, double sign, bool imaginary) {
    return imaginary ? Complex{-sign * value.imag(), sign * value.real()} : sign * value;
}

template<bool PackedFaces = false>
void hopping_sum(std::int64_t n, std::int64_t site, const std::int64_t *neighbors,
                 const Complex *links, const Complex *input, Complex (&sum)[4][3],
                 const ProjectorTable &table, const Complex *lower_face, const Complex *upper_face) {
    for (int direction = 0; direction < 8; ++direction) {
        const auto offset = n * direction + site;
        const auto source = neighbors[offset];
        const Complex *spinor;
        bool already_projected = false;
        if constexpr (PackedFaces) {
            // Only temporal directions can carry a negative face offset.
            already_projected = source < 0;
            spinor = already_projected ?
                (direction == 6 ? upper_face : lower_face) + 6 * (-1 - source) : input + 12 * source;
        } else {
            spinor = input + 12 * source;
        }
        const Complex *link = links + 9 * offset;
        for (int spin = 0; spin < 2; ++spin) {
            const auto [lower, sign, imaginary] = table[direction][spin];
            const double reconstruction_sign = imaginary ? -sign : sign;
            Complex projected[3];
            for (int color = 0; color < 3; ++color) {
                projected[color] = spinor[3 * spin + color];
                if (!already_projected)
                    projected[color] += rotate_phase(spinor[3 * lower + color], sign, imaginary);
            }
            for (int row = 0; row < 3; ++row) {
                const Complex rotated = link[3 * row] * projected[0] +
                                        link[3 * row + 1] * projected[1] +
                                        link[3 * row + 2] * projected[2];
                sum[spin][row] += rotated;
                sum[lower][row] += rotate_phase(rotated, reconstruction_sign, imaginary);
            }
        }
    }
}

void clover_product(const Complex *blocks, const Complex *input, Complex *output) {
    for (int chiral = 0; chiral < 2; ++chiral)
        for (int row = 0; row < 6; ++row) {
            Complex value{};
            for (int col = 0; col < 6; ++col)
                value += blocks[36 * chiral + 6 * row + col] * input[6 * chiral + col];
            output[6 * chiral + row] = value;
        }
}

template<bool PackedFaces = false>
void odd_team(
    std::int64_t n, double kappa, const std::int64_t *neighbors,
    const Complex *links, const Complex *odd_inverse, const Complex *input,
    Complex *odd, const ProjectorTable &table,
    const Complex *lower_face = nullptr, const Complex *upper_face = nullptr) {
#pragma omp for schedule(static)
    for (std::int64_t site = 0; site < n; ++site) {
        Complex sum[4][3]{};
        hopping_sum<PackedFaces>(n, site, neighbors, links, input, sum, table, lower_face, upper_face);
        Complex source[12];
        for (int spin = 0; spin < 4; ++spin)
            for (int color = 0; color < 3; ++color)
                source[3 * spin + color] = -kappa * sum[spin][color];
        clover_product(odd_inverse + 72 * site, source, odd + 12 * site);
    }
}

template<bool PackedFaces = false>
void even_team(
    std::int64_t n, double kappa, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *input,
    const Complex *odd, Complex *output, const ProjectorTable &table,
    bool reflect_output, const Complex *lower_face = nullptr, const Complex *upper_face = nullptr) {
#pragma omp for schedule(static)
    for (std::int64_t site = 0; site < n; ++site) {
        Complex sum[4][3]{};
        hopping_sum<PackedFaces>(n, site, neighbors, links, odd, sum, table, lower_face, upper_face);
        Complex *result = output + 12 * site;
        clover_product(even_clover + 72 * site, input + 12 * site, result);
        for (int spin = 0; spin < 4; ++spin)
            for (int color = 0; color < 3; ++color) {
                auto &value = result[3 * spin + color];
                value += kappa * sum[spin][color];
                if (reflect_output && spin >= 2)
                    value = -value;
            }
    }
}

void schur_team(
    std::int64_t n, double kappa, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *odd_inverse,
    const Complex *input, Complex *odd, Complex *output,
    const ProjectorTable &table, bool reflect_output) {
    odd_team(n, kappa, neighbors + 8 * n, links + 72 * n, odd_inverse, input, odd, table);
    even_team(n, kappa, neighbors, links, even_clover, input, odd, output, table, reflect_output);
}
}

// Coefficients are in prepared parity-local order, with the time-boundary
// signs absorbed into the links. Each input and scratch spinor has n*12 entries.
extern "C" void lqcd_hmc_schur_apply(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *odd_inverse,
    const Complex *input, Complex *odd, Complex *output) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        schur_team(n, kappa, neighbors, links, even_clover, odd_inverse,
                   input, odd, output, table, false);
    }
}

extern "C" void lqcd_hmc_normal_apply(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *odd_inverse,
    const Complex *input, Complex *odd, Complex *intermediate, Complex *output) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        // In DeGrand–Rossi gamma5 = diag(+1,+1,-1,-1).
        schur_team(n, kappa, neighbors, links, even_clover, odd_inverse,
                   input, odd, intermediate, table, true);
        schur_team(n, kappa, neighbors, links, even_clover, odd_inverse,
                   intermediate, odd, output, table, true);
    }
}

// The opposite-parity input can include halo sites appended after the owned sites.
extern "C" void lqcd_hmc_schur_odd(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *odd_inverse, const Complex *even, Complex *odd) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        odd_team(n, kappa, neighbors, links, odd_inverse, even, odd, table);
    }
}

extern "C" void lqcd_hmc_schur_even(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *even,
    const Complex *odd, Complex *output) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        even_team(n, kappa, neighbors, links, even_clover, even, odd, output, table, false);
    }
}

// Encoded indices address the actual owned input or one packed temporal face.
extern "C" void lqcd_hmc_schur_odd_faces(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *odd_inverse, const Complex *even,
    const Complex *lower_face, const Complex *upper_face, Complex *odd) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        odd_team<true>(n, kappa, neighbors, links, odd_inverse, even, odd, table, lower_face, upper_face);
    }
}

extern "C" void lqcd_hmc_schur_even_faces(
    std::int64_t n, double kappa, int threads, const std::int64_t *neighbors,
    const Complex *links, const Complex *even_clover, const Complex *even, const Complex *odd,
    const Complex *lower_face, const Complex *upper_face, Complex *output) {
    const auto &table = projectors();
#pragma omp parallel if(n >= 128) num_threads(threads)
    {
        even_team<true>(n, kappa, neighbors, links, even_clover, even, odd, output,
                        table, false, lower_face, upper_face);
    }
}
