#include "src/solver/native/kernels.hpp"
#include <omp.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>
using Clock=std::chrono::steady_clock;
volatile double sink=0;
double now(){return std::chrono::duration<double>(Clock::now().time_since_epoch()).count();}
template<class T> struct Buffer {
    T *p; size_t n;
    Buffer(size_t count):n(count){if(posix_memalign((void**)&p,64,n*sizeof(T)))std::abort();}
    ~Buffer(){free(p);}
    T& operator[](size_t i){return p[i];}
};
double median(std::vector<double> a){std::sort(a.begin(),a.end());return a[a.size()/2];}
int main(int argc,char**argv){
    const int threads=argc>1?std::atoi(argv[1]):1, blocks=1024, B=864;
    omp_set_dynamic(0);omp_set_num_threads(threads);
    std::cout<<std::setprecision(12);
    std::cout<<"{\"threads\":"<<threads<<",\"compiler\":\""<<__VERSION__<<"\",\"sve_bytes\":";
#if defined(__ARM_FEATURE_SVE)
    std::cout<<svcntb();
#else
    std::cout<<0;
#endif
    std::cout<<",\"avx512\":";
#if defined(__AVX512F__)
    std::cout<<"true";
#else
    std::cout<<"false";
#endif
    if(threads==1){
        const long count=40000000;double value=.25,start=now();
        for(long i=0;i<count;i++)value=value*1.000000001+1.e-10;
        sink=value;std::cout<<",\"dependent_double_ns\":"<<(now()-start)*1.e9/count;
        Buffer<float> cache(4096);for(int i=0;i<4096;i++)cache[i]=.25f;
        std::vector<double> rates;
        for(int trial=0;trial<3;trial++){
            start=now();
            for(int k=0;k<20000;k++){
#pragma omp simd
                for(int i=0;i<4096;i++)cache[i]=cache[i]*.9999999f+1.e-8f;
                asm volatile(""::"r"(cache.p):"memory");
            }
            rates.push_back(2.*4096*20000/(now()-start)/1.e9);
        }
        sink=cache[0];std::cout<<",\"cache_fp32_gflops\":"<<median(rates);
    }
    {
        const size_t N=size_t(1)<<27;Buffer<float>a(N),b(N),c(N);
#pragma omp parallel for schedule(static)
        for(size_t i=0;i<N;i++){a[i]=0;b[i]=.25f;c[i]=.5f;}
        std::vector<double> rates;
        for(int trial=0;trial<4;trial++){
            double start=now();
            for(int k=0;k<4;k++){
#pragma omp parallel for schedule(static)
                for(size_t i=0;i<N;i++)a[i]=b[i]+.125f*c[i];
                asm volatile(""::"r"(a.p):"memory");
            }
            if(trial)rates.push_back(3.*sizeof(float)*N*4/(now()-start)/1.e9);
        }
        sink=a[N/2];if(a[N/2]!=.3125f)return 2;
        std::cout<<",\"triad_effective_GBps\":"<<median(rates);
    }
    int gp[4][4]={{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
    float gr[4][4]={{0,0,0,0},{-1,1,1,-1},{0,0,0,0},{1,1,1,1}};
    float gi[4][4]={{1,1,-1,-1},{0,0,0,0},{1,-1,-1,1},{0,0,0,0}};
    std::vector<int> inner(8*B);
    for(int t=0;t<4;t++)for(int z=0;z<6;z++)for(int y=0;y<6;y++)for(int x=0;x<6;x++){
        int lex=x+6*(y+6*(z+6*t)),s=((x+y+z+t)&1)*(B/2)+lex/2;
        int dims[4]={6,6,6,4};
        for(int d=0;d<8;d++){
            int n[4]={x,y,z,t},mu=d/2;n[mu]+=d%2?-1:1;
            bool valid=n[mu]>=0&&n[mu]<dims[mu];
            inner[d*B+s]=valid?((n[0]+n[1]+n[2]+n[3])&1)*(B/2)+(n[0]+6*(n[1]+6*(n[2]+6*n[3])))/2:-1;
        }
    }
    const size_t coeff=144*B,field=24*B;
    Buffer<float>diag(blocks*coeff),links(blocks*coeff),src(blocks*field),out(blocks*field);
#pragma omp parallel for schedule(static)
    for(int block=0;block<blocks;block++){
        for(size_t j=0;j<coeff;j++){
            diag[block*coeff+j]=float(int(j%29)-14)*.01f;
            links[block*coeff+j]=float(int(j%31)-15)*.01f;
        }
        for(size_t j=0;j<field;j++){src[block*field+j]=float(int(j%37)-18)*.01f;out[block*field+j]=0;}
    }
    auto kernel=[&](int block,float*dest){
        lqcd_native::kernels::wilson_clover_local_range(0,B,diag.p+block*coeff,
            links.p+block*coeff,inner.data(),gp,gr,gi,src.p+block*field,dest,1,true);
    };
    std::vector<float>reference(field,0);
    lqcd_native::portable::wilson_clover_block_impl<true,int,true>(0,B,diag.p,links.p,
        inner.data(),gp,gr,gi,src.p,reference.data(),B/2,B);
    kernel(0,out.p);
    double err=0,norm=0;for(size_t i=0;i<field;i++){
        err+=std::pow(double(out[i])-reference[i],2);norm+=double(reference[i])*reference[i];
    }
    double relative=std::sqrt(err/norm);if(!std::isfinite(relative)||relative>2.e-5)return 3;
    std::cout<<",\"kernel_relative_error\":"<<relative;
    if(threads==1){
        std::vector<double>times;
        for(int trial=0;trial<4;trial++){
            double start=now();for(int k=0;k<300;k++){
                kernel(0,out.p);asm volatile(""::"r"(out.p):"memory");
            }
            if(trial)times.push_back((now()-start)/300);
        }
        std::cout<<",\"hot_eo_wilson_us\":"<<median(times)*1.e6;
    }
    std::vector<double> times;
    for(int trial=0;trial<4;trial++){
        double start=now();
        for(int k=0;k<3;k++){
#pragma omp parallel for schedule(static)
            for(int block=0;block<blocks;block++)kernel(block,out.p+block*field);
        }
        if(trial)times.push_back((now()-start)/3);
    }
    sink=out[field-1];
    std::cout<<",\"streamed_1024_blocks_seconds\":"<<median(times)<<",\"checksum\":"<<sink<<"}\n";
}
