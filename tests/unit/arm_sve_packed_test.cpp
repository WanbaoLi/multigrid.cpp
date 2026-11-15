#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <vector>

#if defined(__ARM_FEATURE_SVE)
namespace {
std::vector<float> pack(const std::vector<float> &raw, int B) {
    std::vector<float> result(((B+15)/16)*144*16,
                              std::numeric_limits<float>::quiet_NaN());
    for (int s=0;s<B;++s) for (int p=0;p<144;++p)
        result[((s/16)*144+p)*16+s%16]=raw[p*B+s];
    return result;
}
void compare(const std::vector<float> &got, const std::vector<float> &expected) {
    for (size_t i=0;i<got.size();++i)
        if (!std::isfinite(got[i]) || !std::isfinite(expected[i]) ||
            std::abs(got[i]-expected[i])>2e-5f)
            throw std::runtime_error("packed SVE mismatch, padding read or inactive overwrite");
}
}
#endif

int main() {
#if !defined(__ARM_FEATURE_SVE)
    std::cout << "SKIP: packed coefficients require an SVE target\n";
#else
    namespace arm=lqcd_native::arm;
    int gp[4][4]={{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    float gr[4][4]={{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    float gi[4][4]={{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::mt19937 rng(26616);
    std::uniform_real_distribution<float> random(-.5f,.5f);
    for (int B:{7,18,30,70,864,2048}) {
        std::vector<float> d(144*B),u(144*B),src(72*B);
        for (auto *v:{&d,&u,&src}) for (float &x:*v) x=random(rng);
        const auto pd=pack(d,B),pu=pack(u,B);
        std::vector<int> local(8*B),compact(8*B);
        std::vector<std::ptrdiff_t> wide(8*B);
        for (int dir=0;dir<8;++dir) for (int s=0;s<B;++s) {
            const bool hole=rng()%5==0;
            local[dir*B+s]=hole?-1:(s<B/2?B/2:0)+rng()%(B/2);
            compact[dir*B+s]=hole?-1:(rng()%3)*24*B+rng()%B;
            wide[dir*B+s]=compact[dir*B+s];
        }
        for (int begin:{0,1,3,16,B/2}) for (int end:{B/2,B-1,B}) {
            if (begin>=end) continue;
            // Clover and its inverse use the same matrix layout. Check
            // against double accumulation, independently of the SVE path.
            std::vector<float> expected(24*B,17.f),actual=expected;
            for (int a=0;a<12;++a) for (int s=begin;s<end;++s) {
                double yr=0,yi=0;
                for (int j=0;j<6;++j) {
                    const int m=(a*6+j)*2*B+s,x=2*((a/6)*6+j)*B+s;
                    yr+=(double)d[m]*src[x]-(double)d[m+B]*src[x+B];
                    yi+=(double)d[m]*src[x+B]+(double)d[m+B]*src[x];
                }
                expected[2*a*B+s]=yr; expected[(2*a+1)*B+s]=yi;
            }
            arm::clover_range_sve<true>(B,pd.data(),src.data(),actual.data(),begin,end);
            compare(actual,expected);
            for (bool clover:{false,true}) {
                expected.assign(24*B,17.f); actual=expected;
                if (clover) {
                    arm::wilson_clover_block_impl<true,int,true>(0,B,d.data(),u.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    arm::wilson_sve<true,int,true,true>(0,B,pd.data(),pu.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
                } else {
                    arm::wilson_clover_block_impl<true,int,false>(0,B,d.data(),u.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    arm::wilson_sve<true,int,false,true>(0,B,pd.data(),pu.data(),local.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
                }
                compare(actual,expected);
            }
            expected.assign(24*B,17.f); actual=expected;
            arm::wilson_clover_block_impl<false,std::ptrdiff_t,true>(1,B,d.data(),u.data(),wide.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
            arm::wilson_sve<false,std::ptrdiff_t,true,true>(1,B,pd.data(),pu.data(),wide.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
            compare(actual,expected);
            arm::wilson_sve<false,int,true,true>(1,B,pd.data(),pu.data(),compact.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
            compare(actual,expected);
        }
        std::vector<float> expected(src.begin(),src.begin()+24*B),actual=expected;
        arm::wilson_clover_block_impl<true,int,false>(0,B,d.data(),u.data(),local.data(),gp,gr,gi,expected.data(),expected.data(),0,B/2);
        arm::wilson_sve<true,int,false,true>(0,B,pd.data(),pu.data(),local.data(),gp,gr,gi,actual.data(),actual.data(),0,B/2);
        compare(actual,expected);
    }
    std::cout << "PASS packed SVE: Clover, local/global, wide/compact, tails, holes, alias; VL="
              << svcntb() << " bytes\n";
#endif
}
