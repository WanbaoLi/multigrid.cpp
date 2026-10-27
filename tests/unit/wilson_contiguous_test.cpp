#include "wilson_kernel.hpp"
#include <array>
#include <climits>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
using namespace lqcd_native::x86;

static void check(const std::vector<float>& a, const std::vector<float>& b,
                  int B, int begin, int end, bool exact) {
    double err=0, norm=0;
    for(int c=0;c<24;c++) for(int s=0;s<B;s++) {
        const size_t k=(size_t)c*B+s;
        if (s<begin || s>=end || exact) {
            if(a[k]!=b[k]) throw std::runtime_error("inactive/exact gather comparison failed");
        } else {
            err+=std::pow((double)a[k]-b[k],2); norm+=(double)b[k]*b[k];
        }
    }
    if(!std::isfinite(err) || std::sqrt(err/std::max(norm,1e-30))>2e-6)
        throw std::runtime_error("generic comparison failed");
}
static std::vector<float> pack(const std::vector<float>& a,int B) {
    std::vector<float> p(((B+15)/16)*144*16,0);
    for(int c=0;c<144;c++) for(int s=0;s<B;s++)
        p[((s/16)*144+c)*16+s%16]=a[c*B+s];
    return p;
}
int main() {
#if !defined(__AVX512F__)
    std::cout<<"SKIP contiguous Wilson requires AVX512\n";
#else
    const int gp[4][4]={{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    const float gr[4][4]={{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    const float gi[4][4]={{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::mt19937 rng(23712);
    std::uniform_real_distribution<float> value(-.5f,.5f);
    int checks=0, planned=0;
    for(auto shape : {std::array<int,4>{2,3,3,1},{2,3,5,1},{4,6,6,3},{6,6,6,4}})
    for(bool eo : {false,true}) for(int origin : {0,1}) {
        const int B=shape[0]*shape[1]*shape[2]*shape[3];
        std::vector<float> diag(144*B),links(144*B),src(24*B);
        for(auto* a:{&diag,&links,&src}) for(auto& x:*a) x=value(rng);
        auto pd=pack(diag,B),pl=pack(links,B);
        auto slot=[&](std::array<int,4> p) {
            int lex=p[0]+shape[0]*(p[1]+shape[1]*(p[2]+shape[2]*p[3]));
            return eo ? ((p[0]+p[1]+p[2]+p[3]+origin)&1)*(B/2)+lex/2 : lex;
        };
        std::vector<int> neighbor(8*B,-1);
        for(int lex=0;lex<B;lex++) {
            int k=lex; std::array<int,4> p;
            for(int d=0;d<4;d++){p[d]=k%shape[d];k/=shape[d];}
            int s=slot(p);
            for(int dir=0;dir<8;dir++) {
                auto q=p; q[dir/2]+=dir%2 ? -1:1;
                if(q[dir/2]>=0 && q[dir/2]<shape[dir/2]) neighbor[dir*B+s]=slot(q);
            }
        }
        for(bool random_metadata : {false,true}) {
            auto nb=neighbor;
            int plan[16]; std::fill(plan,plan+16,INT_MIN);
            if(random_metadata) {
                for(int d=0;d<8;d++) for(int s=0;s<B;s++)
                    nb[d*B+s]=rng()%4==0 ? -1 : (s<B/2 ? B/2:0)+(int)(rng()%(B/2));
            } else {
                for(int h=0;h<2;h++) for(int d=0;d<8;d++) {
                    int delta=INT_MIN; bool consistent=true;
                    for(int s=h*(B/2);s<(h?B:B/2);s++) if(nb[d*B+s]>=0) {
                        int candidate=nb[d*B+s]-s;
                        if(delta==INT_MIN) delta=candidate;
                        else if(candidate!=delta) consistent=false;
                    }
                    if(consistent) plan[h*8+d]=delta;
                    planned+=plan[h*8+d]!=INT_MIN;
                }
            }
            for(int begin : {0,1,7,B/2-1,B/2,B/2+1,108,540}) {
                if(begin<0||begin>=B) continue;
                for(int extent : {1,7,19,B}) {
                    int end=std::min(B,begin+extent);
                    for(bool clover:{false,true}) {
                        std::vector<float> expected(24*B,7),gather=expected,actual=expected;
#define RUN(C) \
                        wilson_clover_block_impl<true,int,C>(0,B,diag.data(),links.data(),nb.data(),gp,gr,gi,src.data(),expected.data(),begin,end); \
                        wilson_avx512<C,int,true>(B,pd.data(),pl.data(),nb.data(),gp,gr,gi,src.data(),gather.data(),begin,end,0); \
                        wilson_avx512<C,int,true>(B,pd.data(),pl.data(),nb.data(),gp,gr,gi,src.data(),actual.data(),begin,end,0,plan)
                        if(clover){RUN(true);}else{RUN(false);}
#undef RUN
                        check(actual,gather,B,begin,end,true);
                        check(actual,expected,B,begin,end,false); ++checks;
                    }
                    if(eo || random_metadata) {
                        int stop=std::min(end,begin<B/2 ? B/2:B);
                        auto expected=src,actual=src;
                        wilson_avx512<false,int,true>(B,pd.data(),pl.data(),nb.data(),gp,gr,gi,expected.data(),expected.data(),begin,stop,0);
                        wilson_avx512<false,int,true>(B,pd.data(),pl.data(),nb.data(),gp,gr,gi,actual.data(),actual.data(),begin,stop,0,plan);
                        check(actual,expected,B,begin,stop,true); ++checks;
                    }
                }
            }
        }
    }
    if(!planned) throw std::runtime_error("no contiguous plans exercised");
    std::cout<<"PASS contiguous Wilson checks="<<checks<<" planned_directions="<<planned<<"\n";
#endif
}
