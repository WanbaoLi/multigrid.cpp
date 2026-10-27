#include "wilson_kernel.hpp"
#include "transfer_avx512.hpp"
#include "lqcd/core/dslash.h"
#include <chrono>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>

using namespace lqcd_native::x86;

int main(int argc, char **) {
    gamma_init();
    alignas(64) int gp[4][4]{};
    alignas(64) float gr[4][4]{}, gi[4][4]{};
    for (int mu = 0; mu < 4; mu++)
        for (int a = 0; a < 4; a++)
            for (int b = 0; b < 4; b++)
                if (gamma_matrix[mu][a][b] != Complex{}) {
                    gp[mu][a] = b;
                    gr[mu][a] = gamma_matrix[mu][a][b].real();
                    gi[mu][a] = gamma_matrix[mu][a][b].imag();
                }
    std::mt19937 rng(1427);
    std::uniform_real_distribution<float> random(-.5f, .5f);
    double maximum = 0;
    for (int B : {2, 14, 17, 30, 32, 35, 70, 864}) {
        std::vector<float> diag(144 * B), links(144 * B), input(24 * B);
        for (auto *v : {&diag, &links, &input})
            for (float &x : *v) x = random(rng);
        std::vector<int> neighbors(8 * B);
        for (int d = 0; d < 8; d++)
            for (int s = 0; s < B; s++)
                neighbors[d * B + s] = (rng() % 5 == 0) ? -1 :
                    (B % 2 ? rng() % B : (s < B / 2 ? B / 2 : 0) + rng() % (B / 2));
        for (int mode = 0; mode < 7; mode++) {
            const bool clover = mode < 3;
            const bool alias = mode == 3 || mode == 4;
            if (alias && B % 2) continue;
            const int begin = mode == 2 || mode == 4 || mode == 6 ? B / 2 : 0;
            const int end = mode == 1 || mode == 3 || mode == 5 ? B / 2 : B;
            std::vector<float> expected = alias ? input : std::vector<float>(24 * B, 7.f);
            std::vector<float> actual = expected;
            const float *reference_source = alias ? expected.data() : input.data();
            const float *actual_source = alias ? actual.data() : input.data();
            if (clover) {
                wilson_clover_block_impl<true, int, true>(0, B, diag.data(), links.data(),
                    neighbors.data(), gp, gr, gi, reference_source, expected.data(), begin, end);
                wilson_local_dispatch<true>(0, B, diag.data(), links.data(), neighbors.data(),
                    gp, gr, gi, actual_source, actual.data(), begin, end);
            } else {
                wilson_clover_block_impl<true, int, false>(0, B, diag.data(), links.data(),
                    neighbors.data(), gp, gr, gi, reference_source, expected.data(), begin, end);
                wilson_local_dispatch<false>(0, B, diag.data(), links.data(), neighbors.data(),
                    gp, gr, gi, actual_source, actual.data(), begin, end);
            }
            double numerator = 0, denominator = 0;
            for (int a = 0; a < 24; a++)
                for (int s = 0; s < B; s++) {
                    const size_t k = a * B + s;
                    if (s < begin || s >= end) {
                        if (actual[k] != expected[k]) throw std::runtime_error("inactive parity overwritten");
                    } else {
                        numerator += std::pow((double)actual[k] - expected[k], 2);
                        denominator += (double)expected[k] * expected[k];
                    }
                }
            const double error = std::sqrt(numerator / denominator);
            if (!std::isfinite(error) || error > 2e-6)
                throw std::runtime_error("local SIMD/reference mismatch B=" + std::to_string(B));
            maximum = std::max(maximum, error);
        }
#if defined(__AVX512F__)
        {
            std::vector<int> invalid(8 * B, -1);
            std::vector<float> expected(24 * B, 7.f), actual = expected;
            const int begin = B / 2;
            wilson_clover_block_impl<true, int, true>(0, B, diag.data(), links.data(),
                invalid.data(), gp, gr, gi, input.data(), expected.data(), begin, B);
            clover_range_avx512(B, diag.data(), input.data(), actual.data(), begin, B);
            double delta = 0, scale = 0;
            for (int i = 0; i < 24 * B; i++) {
                delta += std::pow((double)actual[i]-expected[i],2);
                scale += (double)expected[i]*expected[i];
            }
            const double error = std::sqrt(delta/scale);
            if (!std::isfinite(error) || error > 2e-6) throw std::runtime_error("clover tile mismatch");
            maximum = std::max(maximum, error);
        }
#endif
        if (argc > 1 && B == 864) {
            std::vector<float> output(24 * B);
            auto time = [&](bool optimized) {
                const auto begin = std::chrono::steady_clock::now();
                for (int repeat = 0; repeat < 1000; repeat++) {
                    if (optimized)
                        wilson_local_dispatch<true>(0, B, diag.data(), links.data(), neighbors.data(),
                            gp, gr, gi, input.data(), output.data(), 0, B / 2);
                    else
                        wilson_clover_block_impl<true, int, true>(0, B, diag.data(), links.data(),
                            neighbors.data(), gp, gr, gi, input.data(), output.data(), 0, B / 2);
#if defined(__GNUC__)
                    asm volatile("" : : "g"(output.data()) : "memory");
#endif
                }
                return std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
            };
            // Warm each implementation before the reported microbenchmark.
            time(false); time(true);
            std::cout << "microbenchmark generic_seconds=" << time(false)
                      << " dispatch_seconds=" << time(true) << '\n';
        }
    }
#if defined(__AVX512F__)
    for (int sites : {18, 27, 864}) {
        std::vector<float> basis(48 * sites), coarse(48), real(sites), imag(sites);
        for (auto *v : {&basis, &coarse, &real, &imag})
            for (float &x : *v) x = random(rng);
        auto expected_real = real, expected_imag = imag;
        for (int v = 0; v < 24; v++)
            for (int s = 0; s < sites; s++) {
                const float br = basis[2 * v * sites + s];
                const float bi = basis[(2 * v + 1) * sites + s];
                expected_real[s] += br * coarse[2*v] - bi * coarse[2*v+1];
                expected_imag[s] += br * coarse[2*v+1] + bi * coarse[2*v];
            }
        prolongate_component_avx512(sites, basis.data(), coarse.data(), real.data(), imag.data());
        double delta = 0, reference = 0;
        for (int s = 0; s < sites; s++) {
            delta += std::pow((double)real[s]-expected_real[s],2) + std::pow((double)imag[s]-expected_imag[s],2);
            reference += (double)expected_real[s]*expected_real[s] + (double)expected_imag[s]*expected_imag[s];
        }
        const double error = std::sqrt(delta/reference);
        if (!std::isfinite(error) || error > 2e-6) throw std::runtime_error("prolongation SIMD mismatch");
        maximum = std::max(maximum, error);
    }
#endif
    std::cout << "PASS local Wilson clover/hop/parity-alias/tails max_relative_error=" << maximum
#if defined(__AVX512F__) && !defined(LQCD_DISABLE_LOCAL_AVX512)
              << (wilson_simd_enabled() ? " implementation=AVX512" : " implementation=generic")
#else
              << " implementation=generic"
#endif
              << std::endl;
}
