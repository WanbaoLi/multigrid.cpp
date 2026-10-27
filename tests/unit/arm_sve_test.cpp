#include "wilson_kernel.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

int main() {
#if !defined(__ARM_FEATURE_SVE)
    std::cout << "SKIP ARM SVE kernel test: compiler target has no SVE feature\n";
    return 0;
#else
    std::mt19937 gen(2601);
    std::uniform_real_distribution<float> u(-.5f,.5f);
    for (int B : {3,7,17,31,64,864}) {
        std::vector<float> matrix(144*B), src(24*B), got(24*B, 19.f), ref=got;
        for (float &x : matrix) x=u(gen);
        for (float &x : src) x=u(gen);
        const int begin = B > 7 ? 3 : 1, end = B-1;
        for (int a=0; a<12; ++a) for (int s=begin; s<end; ++s) {
            double re=0, im=0;
            for (int j=0;j<6;++j) {
                const int m=(a*6+j)*2*B+s, x=2*((a/6)*6+j)*B+s;
                re+=(double)matrix[m]*src[x]-(double)matrix[m+B]*src[x+B];
                im+=(double)matrix[m]*src[x+B]+(double)matrix[m+B]*src[x];
            }
            ref[2*a*B+s]=(float)re; ref[(2*a+1)*B+s]=(float)im;
        }
        lqcd_native::arm::clover_range_sve(B,matrix.data(),src.data(),got.data(),begin,end);
        for (size_t i=0;i<got.size();++i)
            if (!std::isfinite(got[i]) || !std::isfinite(ref[i]) || !std::isfinite(got[i]-ref[i]) || std::abs(got[i]-ref[i])>2e-5f)
                throw std::runtime_error("SVE clover mismatch or tail overwrite");
    }
    int gp[4][4]={{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    float gr[4][4]={{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    float gi[4][4]={{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    using namespace lqcd_native::arm;
    for(int B:{18,30,70,864}) for(bool clover:{false,true}) {
        std::vector<float> src(72*B),d(144*B),link(144*B);
        for(auto *v:{&src,&d,&link})for(auto &x:*v)x=u(gen);
        std::vector<int> local(8*B);
        std::vector<std::ptrdiff_t> global(8*B);
        for(int dir=0;dir<8;++dir)for(int s=0;s<B;++s){
            local[dir*B+s]=gen()%5==0?-1:((s<B/2)?B/2:0)+gen()%(B/2);
            global[dir*B+s]=gen()%5==0?-1:(gen()%3)*24*B+gen()%B;
        }
        for(int begin:{0,3,B/2}) {
            int end=begin==B/2?B-1:B/2;
            for(bool islocal:{false,true}) {
                std::vector<float> expected(24*B,19),got=expected;
                if(islocal) {
                    if(clover) {
                        wilson_clover_block_impl<true,int,true>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                        wilson_local_dispatch<true>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,src.data(),got.data(),begin,end);
                    } else {
                        wilson_clover_block_impl<true,int,false>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                        wilson_local_dispatch<false>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,src.data(),got.data(),begin,end);
                    }
                } else if(clover) {
                    wilson_clover_block_impl<false,std::ptrdiff_t,true>(1,B,d.data(),link.data(),global.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    wilson_global_dispatch<true>(1,B,d.data(),link.data(),global.data(),gp,gr,gi,src.data(),got.data(),begin,end,src.size());
                } else {
                    wilson_clover_block_impl<false,std::ptrdiff_t,false>(1,B,d.data(),link.data(),global.data(),gp,gr,gi,src.data(),expected.data(),begin,end);
                    wilson_global_dispatch<false>(1,B,d.data(),link.data(),global.data(),gp,gr,gi,src.data(),got.data(),begin,end,src.size());
                }
                for(size_t i=0;i<got.size();++i)if(!std::isfinite(got[i]) || !std::isfinite(expected[i]) || !std::isfinite(got[i]-expected[i]) || std::abs(got[i]-expected[i])>2e-5f)throw std::runtime_error("SVE Wilson mismatch");
            }
        }
        // Local hopping permits source/output alias only on disjoint parity.
        std::vector<float> expected(src.begin(),src.begin()+24*B), got=expected;
        wilson_clover_block_impl<true,int,false>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,expected.data(),expected.data(),0,B/2);
        wilson_local_dispatch<false>(0,B,d.data(),link.data(),local.data(),gp,gr,gi,got.data(),got.data(),0,B/2);
        for(size_t i=0;i<got.size();++i)if(!std::isfinite(got[i]) || !std::isfinite(expected[i]) || !std::isfinite(got[i]-expected[i]) || std::abs(got[i]-expected[i])>2e-5f)throw std::runtime_error("SVE parity alias mismatch");
    }
    if(try_wilson_global_simd<true>(0,1,nullptr,nullptr,nullptr,gp,gr,gi,nullptr,nullptr,0,1,(size_t)INT_MAX+1))
        throw std::runtime_error("SVE oversized global geometry did not fall back");
    std::cout << "PASS ARM SVE predicated clover oracle/tails\n";
#endif
}
