// Auxiliary cache/codegen experiment. Never a full12 performance result.
#include "wilson_sve.hpp"
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <stdexcept>
#include <vector>

int main(int argc, char **argv) {
#if !defined(__ARM_FEATURE_SVE)
    std::fprintf(stderr,"ARM SVE target required\n");return 2;
#else
    if (argc != 3) throw std::runtime_error("usage: clover_micro block_sites repetitions");
    const int sites=std::atoi(argv[1]), repetitions=std::atoi(argv[2]);
    if ((sites!=432 && sites!=864)||repetitions<1||repetitions>100000)
        throw std::runtime_error("Bounded representative block and count required");
    std::mt19937 generator(5112);
    std::uniform_real_distribution<float> sample(-.5f,.5f);
    std::vector<float> matrix(144*sites), source(24*sites), result(24*sites,19.f);
    for(auto &v:matrix)v=sample(generator);
    for(auto &v:source)v=sample(generator);
    const int begin=0,end=sites/2;
    auto apply=[&] {
        lqcd_native::arm::clover_range_sve(sites,matrix.data(),source.data(),result.data(),begin,end);
        // Make every call's stores observable without adding a vector scan.
        asm volatile("" : : "r"(result.data()) : "memory");
    };
    apply();double maximum=0;
    for(int component=0;component<12;++component)
        for(int site=begin;site<end;++site) {
            double real=0,imaginary=0;
            for(int column=0;column<6;++column) {
                const int m=(component*6+column)*2*sites+site;
                const int x=2*((component/6)*6+column)*sites+site;
                real+=(double)matrix[m]*source[x]-(double)matrix[m+sites]*source[x+sites];
                imaginary+=(double)matrix[m]*source[x+sites]+(double)matrix[m+sites]*source[x];
            }
            maximum=std::max(maximum,std::abs((double)result[2*component*sites+site]-real));
            maximum=std::max(maximum,std::abs((double)result[(2*component+1)*sites+site]-imaginary));
        }
    if (!std::isfinite(maximum)||maximum>2e-5)throw std::runtime_error("Independent dense Clover oracle failed");
    for(int run=0;run<100;++run)apply();
    for(int repeat=0;repeat<5;++repeat) {
        const auto before=std::chrono::steady_clock::now();
        for(int run=0;run<repetitions;++run)apply();
        const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-before).count();
        double checksum=0;for(float value:result)checksum+=value;
        std::printf("CLOVER_MICRO {\"sites\":%d,\"vector_bytes\":%u,\"reuse\":%s,\"repeat\":%d,\"calls\":%d,\"seconds\":%.12g,\"max_abs_oracle_error\":%.12g,\"checksum\":%.12g,\"full12_metric\":false}\n",
            sites,(unsigned)svcntb(),lqcd_native::arm::sve_clover_reuse_enabled()?"true":"false",repeat,repetitions,seconds,maximum,checksum);
    }
#endif
}
