#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

namespace {
void compare(const std::vector<float> &actual, const std::vector<float> &expected) {
    for (size_t i = 0; i < actual.size(); ++i)
        if (!std::isfinite(actual[i]) || !std::isfinite(expected[i]) ||
            std::abs(actual[i] - expected[i]) > 2e-5f)
            throw std::runtime_error("SVE plan changed the operator or an inactive output");
}
}

int main() {
#if !defined(__ARM_FEATURE_SVE)
    std::cout << "SKIP: SVE planned addressing requires an SVE target\n";
#else
    namespace arm = lqcd_native::arm;
    int gp[4][4] = {{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    float gr[4][4] = {{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    float gi[4][4] = {{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::mt19937 rng(266);
    std::uniform_real_distribution<float> random(-.5f, .5f);
    for (int B : {7,18,30,70,864}) {
        int plan[16];
        std::vector<int> local(8 * B, -1), compact(8 * B);
        std::vector<std::ptrdiff_t> wide(8 * B);
        for (int half = 0; half < 2; ++half)
            for (int direction = 0; direction < 8; ++direction) {
                const int first = half ? B / 2 : 0, last = half ? B : B / 2;
                const int delta = half ? -B / 2 : B / 2;
                plan[half * 8 + direction] = direction == 7 ? INT_MIN : delta;
                for (int site = first; site < last; ++site) {
                    int target = site + delta;
                    // Missing neighbours can extrapolate to an in-bounds
                    // address: the load must still obey the actual mask.
                    if (target >= 0 && target < B && site % 5 != 1)
                        local[direction * B + site] = target;
                    if (direction == 7 && local[direction * B + site] >= 0)
                        local[direction * B + site] = half ? 0 : B / 2;
                    const int index = direction * B + site;
                    // General global addressing includes negative entries
                    // and neighbours in each of three source blocks.
                    compact[index] = site % 5 == 1 ? -1 : (direction % 3) * 24 * B + target % B;
                    wide[index] = compact[index];
                }
            }
        std::vector<float> source(72 * B), diag(144 * B), links(144 * B);
        for (auto *field : {&source, &diag, &links})
            for (float &value : *field)
                value = random(rng);
        for (int begin : {0,1,3,B / 2})
            for (int end : {B / 2,B - 1,B}) {
                if (begin >= end)
                    continue;
                for (bool clover : {false,true}) {
                    std::vector<float> expected(24 * B, 17.f), actual = expected;
                    if (clover) {
                        arm::wilson_clover_block_impl<true,int,true>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,source.data(),expected.data(),begin,end);
                        arm::wilson_local_dispatch<true>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,source.data(),actual.data(),begin,end,plan);
                    } else {
                        arm::wilson_clover_block_impl<true,int,false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,source.data(),expected.data(),begin,end);
                        arm::wilson_local_dispatch<false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,source.data(),actual.data(),begin,end,plan);
                    }
                    compare(actual, expected);
                    // Both compact and absent compact metadata must match
                    // the pointer-width portable oracle, including tails.
                    for (const int *metadata : {compact.data(), static_cast<int *>(nullptr)}) {
                        std::fill(expected.begin(), expected.end(), 17.f);
                        actual = expected;
                        if (clover) {
                            arm::wilson_clover_block_impl<false,std::ptrdiff_t,true>(1,B,diag.data(),links.data(),wide.data(),gp,gr,gi,source.data(),expected.data(),begin,end);
                            arm::wilson_global_dispatch<true>(1,B,diag.data(),links.data(),wide.data(),gp,gr,gi,source.data(),actual.data(),begin,end,source.size(),metadata);
                        } else {
                            arm::wilson_clover_block_impl<false,std::ptrdiff_t,false>(1,B,diag.data(),links.data(),wide.data(),gp,gr,gi,source.data(),expected.data(),begin,end);
                            arm::wilson_global_dispatch<false>(1,B,diag.data(),links.data(),wide.data(),gp,gr,gi,source.data(),actual.data(),begin,end,source.size(),metadata);
                        }
                        compare(actual, expected);
                    }
                }
            }
        std::vector<float> expected(source.begin(), source.begin() + 24 * B), actual = expected;
        arm::wilson_clover_block_impl<true,int,false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,expected.data(),expected.data(),0,B / 2);
        arm::wilson_local_dispatch<false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,actual.data(),actual.data(),0,B / 2,plan);
        compare(actual, expected);
    }
    // Check before either neighbour pointer can be read, even when the
    // optimized dispatch is enabled with compact metadata present.
    if (arm::try_wilson_global_simd<true>(0,1,nullptr,nullptr,nullptr,gp,gr,gi,nullptr,nullptr,0,1,
                                         (size_t)INT_MAX + 1, reinterpret_cast<int *>(1)))
        throw std::runtime_error("oversized compact SVE addressing did not fall back");
    std::cout << "PASS SVE local plans, holes, half/tail fallback, alias and compact global offsets\n";
#endif
}
