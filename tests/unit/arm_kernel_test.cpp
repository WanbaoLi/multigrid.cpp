#include "clover_neon.hpp"
#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
int main() {
    std::mt19937 rng(517);
    std::uniform_real_distribution<float> sample(-1,1);
    for(int B : {3,7,18,30,864}) for(int begin : {0,1,3}) {
        if(begin>=B) continue;
        const int end=B-1;
        std::vector<float> mat(144*B),src(24*B),actual(24*B,17),expected=actual;
        for(auto &v:mat)v=sample(rng);
        for(auto &v:src)v=sample(rng);
        for(int a=0;a<12;a++)for(int s=begin;s<end;s++) {
            double re=0,im=0;
            for(int j=0;j<6;j++) {
                int m=(a*6+j)*2*B+s,x=2*((a/6)*6+j)*B+s;
                re+=(double)mat[m]*src[x]-(double)mat[m+B]*src[x+B];
                im+=(double)mat[m]*src[x+B]+(double)mat[m+B]*src[x];
            }
            expected[2*a*B+s]=re;expected[(2*a+1)*B+s]=im;
        }
#if defined(__aarch64__)
        lqcd_native::arm::clover_range_neon(B,mat.data(),src.data(),actual.data(),begin,end);
#else
        // Exercise the ARM dispatch directly on hosts without ARM ISA.
        std::vector<float> links(144*B,0);
        std::vector<int> neighbor(8*B,-1);
        int gp[4][4]={};float gr[4][4]={},gi[4][4]={};
        lqcd_native::arm::wilson_local_dispatch<true>(0,B,mat.data(),links.data(),neighbor.data(),gp,gr,gi,src.data(),actual.data(),begin,end);
#endif
        for(size_t i=0;i<actual.size();i++)if(std::abs(actual[i]-expected[i])>2e-6)
            throw std::runtime_error("ARM clover/range/tail mismatch");
    }
    std::cout<<"ARM kernel independent double clover oracle passed\n";
}
