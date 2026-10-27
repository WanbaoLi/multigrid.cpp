#include "transfer_sve.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

int main() {
#if !defined(__ARM_FEATURE_SVE)
    std::cout << "SKIP: SVE transfer requires an SVE target\n";
#else
    std::mt19937 random(20261026);
    std::uniform_real_distribution<float> value(-.5f, .5f);
    constexpr int prefix = 3, suffix = 5;
    for (int sites : {1,3,7,15,16,17,31,33,70,432,864}) {
        std::vector<float> basis(48 * sites), coefficients(48);
        for (float &x : basis) x = value(random);
        for (float &x : coefficients) x = value(random);
        std::vector<float> real(prefix + sites + suffix, 17.f), imag = real;
        for (int site = 0; site < sites; ++site) {
            real[prefix + site] = value(random);
            imag[prefix + site] = value(random);
        }
        auto expected_real = real, expected_imag = imag;
        for (int site = 0; site < sites; ++site) {
            double re = real[prefix + site], im = imag[prefix + site];
            for (int vector = 0; vector < 24; ++vector) {
                const size_t base = (size_t)vector * 2 * sites + site;
                const double br = basis[base], bi = basis[base + sites];
                const double zr = coefficients[2 * vector], zi = coefficients[2 * vector + 1];
                re += br * zr - bi * zi;
                im += br * zi + bi * zr;
            }
            expected_real[prefix + site] = (float)re;
            expected_imag[prefix + site] = (float)im;
        }
        const auto original_basis = basis, original_coefficients = coefficients;
        lqcd_native::arm::prolongate_component_sve(
            sites, basis.data(), coefficients.data(), real.data() + prefix, imag.data() + prefix);
        for (size_t i = 0; i < real.size(); ++i)
            if (!std::isfinite(real[i]) || !std::isfinite(imag[i]) ||
                std::abs(real[i] - expected_real[i]) > 2e-5f ||
                std::abs(imag[i] - expected_imag[i]) > 2e-5f)
                throw std::runtime_error("SVE prolongation changed accumulation or overwrote tail");
        if (basis != original_basis || coefficients != original_coefficients)
            throw std::runtime_error("SVE prolongation modified an input");
    }
    std::cout << "PASS SVE prolongation double oracle, nonzero accumulation, unaligned output and tails\n";
#endif
}
