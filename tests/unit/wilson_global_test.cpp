#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>

using namespace lqcd_native::x86;
int main() {
    // DR sparse gamma entries, X/Y/Z/T, identical mathematical convention.
    alignas(64) int gp[4][4] = {{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    alignas(64) float gr[4][4] = {{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    alignas(64) float gi[4][4] = {{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::mt19937 gen(52438);
    std::uniform_real_distribution<float> random(-.5f,.5f);
    double max_error = 0;
    for (int B : {2,7,17,18,27,30,35,70,864}) {
        const int blocks = 5;
        std::vector<float> src((size_t)blocks*24*B), diag(144*B), links(144*B);
        for (auto *v : {&src,&diag,&links}) for (auto &x : *v) x = random(gen);
        std::vector<std::ptrdiff_t> neighbors(8*B);
        for (auto &n : neighbors)
            n = gen()%5==0 ? -1 : (std::ptrdiff_t)(gen()%blocks)*24*B + gen()%B;
        for (int cb : {0,2,4}) for (int range=0;range<3;range++) for (int clover=0;clover<2;clover++) {
            const int begin = range==2 ? B/2 : 0, end = range==1 ? B/2 : B;
            std::vector<float> reference(24*B,7.f), actual=reference;
            if(clover)
                wilson_clover_block_impl<false,std::ptrdiff_t,true>(cb,B,diag.data(),links.data(),
                    neighbors.data(),gp,gr,gi,src.data(),reference.data(),begin,end);
            else
                wilson_clover_block_impl<false,std::ptrdiff_t,false>(cb,B,diag.data(),links.data(),
                    neighbors.data(),gp,gr,gi,src.data(),reference.data(),begin,end);
#if defined(__AVX512F__)
            const bool used = clover
                ? try_wilson_global_simd<true>(cb,B,diag.data(),links.data(),
                    neighbors.data(),gp,gr,gi,src.data(),actual.data(),begin,end,src.size())
                : try_wilson_global_simd<false>(cb,B,diag.data(),links.data(),
                    neighbors.data(),gp,gr,gi,src.data(),actual.data(),begin,end,src.size());
#else
            const bool used = false;
#endif
#if defined(__AVX512F__) && !defined(LQCD_DISABLE_LOCAL_AVX512)
            if (used != wilson_simd_enabled()) throw std::runtime_error("unexpected SIMD dispatch");
#endif
            if (!used) {
                if(clover)
                    wilson_clover_block_impl<false,std::ptrdiff_t,true>(cb,B,diag.data(),links.data(),
                        neighbors.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
                else
                    wilson_clover_block_impl<false,std::ptrdiff_t,false>(cb,B,diag.data(),links.data(),
                        neighbors.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
            }
            double delta=0, norm=0;
            for (int a=0;a<24;a++) for(int s=0;s<B;s++) {
                size_t k=a*B+s;
                if(s<begin||s>=end) {
                    if(actual[k]!=7.f) throw std::runtime_error("inactive output overwritten");
                } else {
                    delta+=std::pow((double)actual[k]-reference[k],2);
                    norm+=(double)reference[k]*reference[k];
                }
            }
            double error=std::sqrt(delta/norm);
            if(!std::isfinite(error)||error>2e-6) throw std::runtime_error("global SIMD mismatch");
            max_error=std::max(max_error,error);
        }
    }
    // Must return before reading any dummy pointers when int32 indexing fails.
    if(try_wilson_global_simd<true>(0,1,nullptr,nullptr,nullptr,gp,gr,gi,nullptr,nullptr,
                                    0,1,(size_t)INT_MAX+1))
        throw std::runtime_error("oversized geometry did not select fallback");
    std::cout<<"PASS global Wilson SIMD/tails/cross-block/clover/hop/oversized guard max_error="<<max_error<<'\n';
}
