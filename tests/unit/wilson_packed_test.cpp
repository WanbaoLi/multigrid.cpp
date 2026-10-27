#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>

using namespace lqcd_native::x86;

static std::vector<float> pack(const std::vector<float> &source, int sites) {
    std::vector<float> result(((sites + 15) / 16) * 144 * 16,
                              std::numeric_limits<float>::quiet_NaN());
    for (int plane = 0; plane < 144; plane++)
        for (int site = 0; site < sites; site++)
            result[((site / 16) * 144 + plane) * 16 + site % 16] = source[plane * sites + site];
    return result;
}
static double check(const std::vector<float> &actual, const std::vector<float> &expected,
                    int sites, int begin, int end) {
    double delta = 0, norm = 0;
    for (int plane = 0; plane < 24; plane++)
        for (int site = 0; site < sites; site++) {
            const size_t k = plane * sites + site;
            if (site < begin || site >= end) {
                if (actual[k] != expected[k]) throw std::runtime_error("packed inactive lane overwritten");
            } else {
                delta += std::pow((double)actual[k] - expected[k], 2);
                norm += (double)expected[k] * expected[k];
            }
        }
    const double error = norm ? std::sqrt(delta / norm) : std::sqrt(delta);
    if (!std::isfinite(error) || error > 2e-6) throw std::runtime_error("packed Wilson mismatch");
    return error;
}
int main() {
    alignas(64) int gp[4][4] = {{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    alignas(64) float gr[4][4] = {{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    alignas(64) float gi[4][4] = {{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::mt19937 rng(931482);
    std::uniform_real_distribution<float> random(-.5f, .5f);
    double maximum = 0;
    int packed_calls = 0;
    for (int B : {18,30,864}) {
        std::vector<float> diag(144*B), links(144*B), src(3*24*B);
        for (auto *v : {&diag,&links,&src}) for (float &x : *v) x=random(rng);
        const auto packed_diag=pack(diag,B), packed_links=pack(links,B);
        std::vector<int> local(8*B);
        std::vector<std::ptrdiff_t> global(8*B);
        for (int d=0;d<8;d++) for(int s=0;s<B;s++) {
            // EO-safe opposite parity enables the hopping-only in-place test.
            local[d*B+s]=rng()%5==0 ? -1 : (s<B/2 ? B/2 : 0)+(int)(rng()%(B/2));
            global[d*B+s]=rng()%5==0 ? -1 : (std::ptrdiff_t)(rng()%3)*24*B+rng()%B;
        }
        for (int begin : {0,3,9,108,540}) {
            if(begin>=B) continue;
            for(int extent : {1,7,19,B}) {
                const int end=std::min(B,begin+extent);
                for(int mode=0;mode<4;mode++) {
                    const bool is_global=mode>=2, clover=mode%2==0;
                    std::vector<float> expected(24*B,7.f), actual=expected;
                    if(is_global) {
                        if(clover) wilson_clover_block_impl<false,std::ptrdiff_t,true>(1,B,diag.data(),links.data(),global.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                        else wilson_clover_block_impl<false,std::ptrdiff_t,false>(1,B,diag.data(),links.data(),global.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    } else {
                        if(clover) wilson_clover_block_impl<true,int,true>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                        else wilson_clover_block_impl<true,int,false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    }
                    bool used=false;
#if defined(__AVX512F__)
                    if(wilson_simd_enabled()) {
                        if(is_global) {
                            if(clover) wilson_avx512<true,std::ptrdiff_t,true>(B,packed_diag.data(),packed_links.data(),global.data(),gp,gr,gi,src.data(),actual.data(),begin,end,24*B);
                            else wilson_avx512<false,std::ptrdiff_t,true>(B,packed_diag.data(),packed_links.data(),global.data(),gp,gr,gi,src.data(),actual.data(),begin,end,24*B);
                        } else {
                            if(clover) wilson_avx512<true,int,true>(B,packed_diag.data(),packed_links.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end,0);
                            else wilson_avx512<false,int,true>(B,packed_diag.data(),packed_links.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end,0);
                        }
                        used=true; ++packed_calls;
                    }
#endif
                    if(!used) {
                        if(is_global) {
                            if(clover) wilson_global_dispatch<true>(1,B,diag.data(),links.data(),global.data(),gp,gr,gi,src.data(),actual.data(),begin,end,src.size());
                            else wilson_global_dispatch<false>(1,B,diag.data(),links.data(),global.data(),gp,gr,gi,src.data(),actual.data(),begin,end,src.size());
                        } else {
                            if(clover) wilson_local_dispatch<true>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
                            else wilson_local_dispatch<false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
                        }
                    }
                    maximum=std::max(maximum,check(actual,expected,B,begin,end));
                }
#if defined(__AVX512F__)
                if(wilson_simd_enabled()) {
                    std::vector<float> expected(24*B,7.f), actual=expected;
                    std::vector<int> no_hops(8*B,-1);
                    wilson_clover_block_impl<true,int,true>(0,B,diag.data(),links.data(),no_hops.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    clover_range_avx512<true>(B,packed_diag.data(),src.data(),actual.data(),begin,end);
                    maximum=std::max(maximum,check(actual,expected,B,begin,end)); ++packed_calls;
                    const int parity_end=begin<B/2 ? B/2 : B;
                    const int alias_end=std::min(end,parity_end);
                    expected.assign(src.begin(),src.begin()+24*B); actual=expected;
                    wilson_clover_block_impl<true,int,false>(0,B,diag.data(),links.data(),local.data(),gp,gr,gi,expected.data(),expected.data(),begin,alias_end);
                    wilson_avx512<false,int,true>(B,packed_diag.data(),packed_links.data(),local.data(),gp,gr,gi,actual.data(),actual.data(),begin,alias_end,0);
                    maximum=std::max(maximum,check(actual,expected,B,begin,alias_end)); ++packed_calls;
                }
#endif
            }
        }
    }
    std::cout<<"PASS packed Wilson both-edge-mask/global/local/clover/hop/alias max_error="<<maximum<<" packed_calls="<<packed_calls<<'\n';
}
