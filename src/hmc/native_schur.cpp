#include "core/dslash.h"

#include <array>
#include <cstdint>

namespace {
struct Projector {
    int lower_spin;
    Complex phase;
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
                    if (element != Complex{})
                        values[direction][spin] = {lower, sign * element};
                }
        }
        return values;
    }();
    return table;
}

void hopping_sum(std::int64_t n, std::int64_t site, const std::int64_t *neighbors,
                 const Complex *links, const Complex *input, Complex (&sum)[4][3],
                 const ProjectorTable &table) {
    for (int direction = 0; direction < 8; ++direction) {
        const auto offset = n * direction + site;
        const Complex *spinor = input + 12 * neighbors[offset];
        const Complex *link = links + 9 * offset;
        for (int spin = 0; spin < 2; ++spin) {
            const auto [lower, phase] = table[direction][spin];
            Complex projected[3];
            for (int color = 0; color < 3; ++color)
                projected[color] = spinor[3 * spin + color] + phase * spinor[3 * lower + color];
            for (int row = 0; row < 3; ++row) {
                const Complex rotated = link[3 * row] * projected[0] +
                                        link[3 * row + 1] * projected[1] +
                                        link[3 * row + 2] * projected[2];
                sum[spin][row] += rotated;
                sum[lower][row] += std::conj(phase) * rotated;
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
#pragma omp for schedule(static)
        for (std::int64_t site = 0; site < n; ++site) {
            Complex sum[4][3]{};
            hopping_sum(n, site, neighbors + 8 * n, links + 72 * n, input, sum, table);
            Complex source[12];
            for (int spin = 0; spin < 4; ++spin)
                for (int color = 0; color < 3; ++color)
                    source[3 * spin + color] = -kappa * sum[spin][color];
            clover_product(odd_inverse + 72 * site, source, odd + 12 * site);
        }
#pragma omp for schedule(static)
        for (std::int64_t site = 0; site < n; ++site) {
            Complex sum[4][3]{};
            hopping_sum(n, site, neighbors, links, odd, sum, table);
            clover_product(even_clover + 72 * site, input + 12 * site, output + 12 * site);
            for (int spin = 0; spin < 4; ++spin)
                for (int color = 0; color < 3; ++color)
                    output[12 * site + 3 * spin + color] += kappa * sum[spin][color];
        }
    }
}
