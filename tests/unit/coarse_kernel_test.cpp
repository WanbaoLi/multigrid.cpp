#include "coarse_sve.hpp"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
int main() {
    std::mt19937 rng(731); std::uniform_real_distribution<float> random(-.5f,.5f);
    for (int n : {1,7,17,31,48,65}) {
        std::vector<float> row(n*n*2), packed(row.size()), src(n*2);
        for (auto *v : {&row,&src}) for (float &x:*v) x=random(rng);
        lqcd_native::arm::pack_coarse_columns(n,row.data(),packed.data());
        for(int a=0;a<n;++a)for(int j=0;j<n;++j)for(int ri=0;ri<2;++ri)
            if(packed[(2*j+ri)*n+a]!=row[(a*n+j)*2+ri]) throw std::runtime_error("pack mapping");
#if defined(__ARM_FEATURE_SVE)
        for(bool add:{false,true}) {
            // Guard output tails with sentinels and exercise accumulation over
            // multiple neighbours, matching coarse_apply direction semantics.
            std::vector<float> out(2*n+8,123.f);std::vector<double> ref(2*n);
            for(int i=0;i<2*n;++i){out[i]=random(rng);ref[i]=add?out[i]:0;}
            for(int dir=0;dir<3;++dir){
                for(int a=0;a<n;++a)for(int j=0;j<n;++j){
                    ref[2*a]+=(double)row[2*(a*n+j)]*src[2*j]-(double)row[2*(a*n+j)+1]*src[2*j+1];
                    ref[2*a+1]+=(double)row[2*(a*n+j)]*src[2*j+1]+(double)row[2*(a*n+j)+1]*src[2*j];
                }
                lqcd_native::arm::coarse_gemv_sve(n,packed.data(),src.data(),out.data(),add||dir>0);
            }
            for(int i=0;i<2*n;++i)if(!std::isfinite(out[i])||std::abs(out[i]-ref[i])>2e-5*(1+std::abs(ref[i])))throw std::runtime_error("coarse SVE double oracle");
            for(int i=2*n;i<(int)out.size();++i)if(out[i]!=123.f)throw std::runtime_error("coarse SVE tail overwrite");
        }
#endif
    }
#if defined(__ARM_FEATURE_SVE)
    std::cout<<"PASS coarse SVE pack/double GEMV oracle/add/tails\n";
#else
    std::cout<<"PASS coarse pack mapping; SVE execution unavailable on compiler target\n";
#endif
}
