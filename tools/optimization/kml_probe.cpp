// Auxiliary arithmetic probe, not a propagation benchmark or solver backend.
// Compile on the allocated ARM compute node, for example:
// g++ -O3 -std=c++17 -march=native -fopenmp -I$SDK/kml/gcc/include
//     -I$PROJECT/src/backends/arm kml_probe.cpp -ldl -o kml_probe
// ./kml_probe --library /absolute/versioned/sve/kblas/locking/libkblas.so... --threads 37
// GEMM widths 2/12 require a future lockstep coarse implementation; the current
// batched V-cycle calls independent coarse_solve functions sequentially.
#include "coarse_sve.hpp"
#include <kblas.h>
#include <omp.h>
#include <dlfcn.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
double seconds() {
    return std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
}
constexpr int dimension = 48, block_count = 64, guard = 8;
constexpr double error_limit = 2e-5;

std::string escaped(const std::string &s) {
    std::string out = "\"";
    for (unsigned char c : s) {
        if (c == '\\' || c == '"') { out += '\\'; out += c; }
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c < 32) out += '?';
        else out += c;
    }
    return out + '"';
}

struct Api {
    void *handle = nullptr;
    decltype(&cblas_cgemv) gemv = nullptr;
    decltype(&cblas_cgemm) gemm = nullptr;
    decltype(&BlasGetParallel) parallel = nullptr;
    std::string resolved;
    template<class Fn> Fn symbol(const char *name) {
        dlerror();
        void *address = dlsym(handle, name);
        const char *error = dlerror();
        if (error || !address) throw std::runtime_error(std::string("dlsym ") + name + ": " + (error ? error : "null"));
        Fn fn;
        static_assert(sizeof(fn) == sizeof(address), "POSIX function pointer representation required");
        std::memcpy(&fn, &address, sizeof(fn));
        return fn;
    }
    explicit Api(const std::string &path) {
        if (!std::filesystem::path(path).is_absolute()) throw std::runtime_error("library path must be absolute");
        handle = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL);
        if (!handle) throw std::runtime_error(std::string("dlopen: ") + dlerror());
        try {
            gemv = symbol<decltype(gemv)>("cblas_cgemv");
            gemm = symbol<decltype(gemm)>("cblas_cgemm");
            parallel = symbol<decltype(parallel)>("BlasGetParallel");
            if (parallel() != 0) throw std::runtime_error("probe requires a sequential KML variant (BlasGetParallel=0)");
            Dl_info info{};
            void *address = nullptr;
            std::memcpy(&address, &gemv, sizeof(address));
            if (!dladdr(address, &info) || !info.dli_fname) throw std::runtime_error("dladdr failed");
            resolved = std::filesystem::canonical(info.dli_fname).string();
            if (resolved != std::filesystem::canonical(path).string()) throw std::runtime_error("resolved GEMV symbol belongs to another library");
        } catch (...) { dlclose(handle); handle = nullptr; throw; }
    }
    ~Api() { if (handle) dlclose(handle); }
    Api(const Api &) = delete;
    Api &operator=(const Api &) = delete;
};

struct Fixture {
    int rhs;
    std::vector<float> matrices, packed, input, initial;
    std::vector<std::vector<float>> output;
    double coefficient_pack_seconds = 0, rhs_pack_seconds = 0;
    explicit Fixture(int width) : rhs(width),
        matrices(block_count * dimension * dimension * 2), packed(matrices.size()),
        input(block_count * dimension * width * 2), initial(input.size()),
        output(block_count, std::vector<float>(dimension * width * 2 + 2 * guard, 731.25f)) {
        std::mt19937 rng(1701);
        std::uniform_real_distribution<float> random(-.5f, .5f);
        for (float &v : matrices) v = random(rng);
        double start = seconds();
        for (int b = 0; b < block_count; ++b)
            lqcd_native::arm::pack_coarse_columns(dimension, matrix(b), packed.data() + matrix_stride() * b);
        coefficient_pack_seconds = seconds() - start;
        // Inputs first use independent contiguous interleaved complex vectors,
        // then become BLAS row-major [component][RHS][real/imag] panels.
        std::vector<float> columns(input.size());
        for (float &v : columns) v = random(rng);
        for (float &v : initial) v = random(rng);
        start = seconds();
        for (int b = 0; b < block_count; ++b)
            for (int r = 0; r < rhs; ++r)
                for (int a = 0; a < dimension; ++a)
                    for (int ri = 0; ri < 2; ++ri)
                        input[(b * dimension * rhs + a * rhs + r) * 2 + ri] =
                            columns[(b * rhs * dimension + r * dimension + a) * 2 + ri];
        rhs_pack_seconds = seconds() - start;
        reset();
    }
    size_t matrix_stride() const { return size_t(dimension) * dimension * 2; }
    size_t panel_stride() const { return size_t(dimension) * rhs * 2; }
    const float *matrix(int b) const { return matrices.data() + b * matrix_stride(); }
    const float *source(int b) const { return input.data() + b * panel_stride(); }
    float *dest(int b) { return output[b].data() + guard; }
    void reset() {
        for (int b = 0; b < block_count; ++b)
            std::copy_n(initial.data() + b * panel_stride(), panel_stride(), dest(b));
    }
    void guards_ok() const {
        for (const auto &field : output)
            for (int i = 0; i < guard; ++i)
                if (field[i] != 731.25f || field[field.size()-1-i] != 731.25f)
                    throw std::runtime_error("output guard overwritten");
    }
};

enum class Mode { Sve, Gemv, Gemm };
const char *label(Mode mode) {
    return mode == Mode::Sve ? "packed_custom_sve" : mode == Mode::Gemv ? "kml_rowmajor_cgemv" : "kml_rowmajor_cgemm";
}

void apply(const Api &api, Mode mode, Fixture &f, int block, bool add) {
    const float alpha[2] = {1.f, 0.f}, beta[2] = {add ? 1.f : 0.f, 0.f};
    if (mode == Mode::Sve) {
#if defined(__ARM_FEATURE_SVE)
        lqcd_native::arm::coarse_gemv_sve(dimension,
            f.packed.data() + f.matrix_stride() * block, f.source(block), f.dest(block), add);
#else
        throw std::runtime_error("custom SVE execution unavailable on this compiler target");
#endif
    } else if (mode == Mode::Gemv) {
        api.gemv(CblasRowMajor, CblasNoTrans, dimension, dimension, alpha,
                 f.matrix(block), dimension, f.source(block), 1, beta, f.dest(block), 1);
    } else {
        api.gemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
                 dimension, f.rhs, dimension, alpha, f.matrix(block), dimension,
                 f.source(block), f.rhs, beta, f.dest(block), f.rhs);
    }
    // Prevent elimination of repeated overwrite calls in the inlined kernel.
    asm volatile("" : : "r"(f.dest(block)) : "memory");
}

struct Error { double relative = 0, maximum_absolute = 0; };
Error verify(const Api &api, Mode mode, Fixture &f, bool add, int threads) {
    const auto matrices_before = f.matrices, input_before = f.input, packed_before = f.packed;
    f.reset();
    // beta=0 must ignore previous values, including NaNs.
    if (!add)
        for (int b = 0; b < block_count; ++b)
            std::fill_n(f.dest(b), f.panel_stride(), std::nanf(""));
    omp_set_num_threads(threads);
#pragma omp parallel for schedule(static)
    for (int b = 0; b < block_count; ++b) apply(api, mode, f, b, add);
    double error_squared = 0, reference_squared = 0, maximum = 0;
    for (int b = 0; b < block_count; ++b)
        for (int a = 0; a < dimension; ++a)
            for (int r = 0; r < f.rhs; ++r) {
                const size_t index = (a * f.rhs + r) * 2;
                double re = add ? f.initial[b * f.panel_stride() + index] : 0;
                double im = add ? f.initial[b * f.panel_stride() + index + 1] : 0;
                for (int j = 0; j < dimension; ++j) {
                    const double ar = f.matrix(b)[(a * dimension + j) * 2];
                    const double ai = f.matrix(b)[(a * dimension + j) * 2 + 1];
                    const double xr = f.source(b)[(j * f.rhs + r) * 2];
                    const double xi = f.source(b)[(j * f.rhs + r) * 2 + 1];
                    re += ar * xr - ai * xi; im += ar * xi + ai * xr;
                }
                const double dr = f.dest(b)[index] - re, di = f.dest(b)[index + 1] - im;
                if (!std::isfinite(dr) || !std::isfinite(di)) throw std::runtime_error("nonfinite oracle difference");
                error_squared += dr * dr + di * di;
                reference_squared += re * re + im * im;
                maximum = std::max({maximum, std::abs(dr), std::abs(di)});
            }
    f.guards_ok();
    if (matrices_before != f.matrices || input_before != f.input || packed_before != f.packed)
        throw std::runtime_error("read-only input was modified");
    Error result{std::sqrt(error_squared / std::max(reference_squared, 1e-300)), maximum};
    if (result.relative > error_limit) throw std::runtime_error("double oracle relative error exceeds 2e-5");
    return result;
}

double run(const Api &api, Mode mode, Fixture &f, bool add, int rounds) {
    const double start = seconds();
    for (int repeat = 0; repeat < rounds; ++repeat) {
#pragma omp parallel for schedule(static)
        for (int b = 0; b < block_count; ++b) apply(api, mode, f, b, add);
    }
    return seconds() - start;
}

void check_budget(double deadline) {
    if (seconds() > deadline) throw std::runtime_error("45-second probe budget exhausted; no complete result");
}
} // namespace

int main(int argc, char **argv) {
    try {
        std::string path;
        int concurrent_threads = 37;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--library" && i + 1 < argc) path = argv[++i];
            else if (arg == "--threads" && i + 1 < argc) concurrent_threads = std::stoi(argv[++i]);
            else throw std::runtime_error("usage: kml_probe --library ABSOLUTE_PATH [--threads 37]");
        }
        if (path.empty() || concurrent_threads < 1 || concurrent_threads > 64)
            throw std::runtime_error("library required; threads must be between 1 and 64");
        const double deadline = seconds() + 45.;
        omp_set_dynamic(0);
        // All dynamic loading and symbol resolution happen on the main thread.
        // Retain this handle until every OpenMP team and fixture has finished.
        Api api(path);
        std::cout << std::setprecision(12);
        std::cout << "{\"complete\":true,\"auxiliary_only\":true,\"metric\":\"seconds_per_block_including_OpenMP_team_scheduling\","
                     "\"dimension\":48,\"blocks\":64,\"library_requested\":" << escaped(path)
                  << ",\"library_resolved\":" << escaped(api.resolved)
                  << ",\"blas_parallel_type\":" << api.parallel()
                  << ",\"requested_library_does_not_prove_executed_SVE_or_SME\":true,\"compiler\":" << escaped(__VERSION__)
                  << ",\"sve_bytes\":";
#if defined(__ARM_FEATURE_SVE)
        std::cout << svcntb();
#else
        std::cout << 0;
#endif
        std::cout << ",\"samples\":[";
        bool first = true;
        double checksum = 0;
        for (int rhs : {1, 2, 12}) {
            Fixture fixture(rhs);
            for (Mode mode : {Mode::Sve, Mode::Gemv, Mode::Gemm}) {
                if (rhs != 1 && mode != Mode::Gemm) continue;
#if !defined(__ARM_FEATURE_SVE)
                if (mode == Mode::Sve) continue;
#endif
                for (bool add : {false, true}) {
                    std::vector<int> thread_counts{1};
                    if (concurrent_threads != 1) thread_counts.push_back(concurrent_threads);
                    for (int threads : thread_counts) {
                        check_budget(deadline);
                        omp_set_num_threads(threads);
                        int actual_threads = 0;
#pragma omp parallel
                        {
#pragma omp single
                            actual_threads = omp_get_num_threads();
                        }
                        if (actual_threads != threads) throw std::runtime_error("OpenMP did not create requested team");
                        const Error error = verify(api, mode, fixture, add, threads);
                        fixture.reset();
                        run(api, mode, fixture, add, 1); // warm worker/library state
                        int rounds = 1;
                        while (rounds < 256) {
                            check_budget(deadline);
                            const double elapsed = run(api, mode, fixture, add, rounds);
                            if (elapsed >= .02) break;
                            rounds *= 2;
                        }
                        std::vector<double> times;
                        for (int repeat = 0; repeat < 3; ++repeat) {
                            check_budget(deadline);
                            fixture.reset();
                            times.push_back(run(api, mode, fixture, add, rounds) / (rounds * block_count));
                        }
                        fixture.guards_ok();
                        for (int b = 0; b < block_count; ++b)
                            checksum += fixture.dest(b)[0] + fixture.dest(b)[fixture.panel_stride()-1];
                        if (!std::isfinite(checksum)) throw std::runtime_error("nonfinite checksum");
                        const auto raw_times = times;
                        std::sort(times.begin(), times.end());
                        if (!first) std::cout << ',';
                        first = false;
                        std::cout << "{\"mode\":" << escaped(label(mode)) << ",\"rhs\":" << rhs
                                  << ",\"beta\":" << (add ? 1 : 0) << ",\"threads\":" << threads
                                  << ",\"actual_threads\":" << actual_threads << ",\"rounds\":" << rounds
                                  << ",\"coefficient_pack_seconds\":" << (mode == Mode::Sve ? fixture.coefficient_pack_seconds : 0.)
                                  << ",\"rhs_panel_pack_seconds\":" << (mode == Mode::Gemm ? fixture.rhs_pack_seconds : 0.)
                                  << ",\"requires_future_lockstep_coarse_integration\":" << (rhs > 1 ? "true" : "false")
                                  << ",\"oracle_relative_error\":" << error.relative
                                  << ",\"oracle_max_absolute_error\":" << error.maximum_absolute
                                  << ",\"input_preserved\":true,\"output_guards_preserved\":true,\"median_seconds_per_block\":" << times[1]
                                  << ",\"samples_seconds_per_block\":[" << raw_times[0] << ',' << raw_times[1] << ',' << raw_times[2] << "]}";
                    }
                }
            }
        }
        check_budget(deadline);
        std::cout << "],\"checksum\":" << checksum << ",\"oracle_limit\":" << error_limit << "}\n";
        return 0;
    } catch (const std::exception &error) {
        // A partial stdout JSON is deliberately not a complete parseable report.
        std::cerr << "kml_probe failed: " << error.what() << '\n';
        return 1;
    }
}
