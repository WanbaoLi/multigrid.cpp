#pragma once
#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#if defined(__ARM_FEATURE_SVE)
#include <arm_sve.h>
// ACLE SVE: https://arm-software.github.io/acle/main/acle.html
// svld1_gather_s32index_f32 takes element indices (not byte offsets).
namespace lqcd_native::arm {
inline bool sve_enabled() {
    static const bool enabled = [] {
        const char *s = std::getenv("LQCD_ARM_SVE");
        return !s || std::atoi(s) != 0;
    }();
    return enabled;
}
// Process-wide opt-in: the accepted gather path stays the default.
inline bool sve_planned_enabled() {
    static const bool enabled = [] {
        const char *value = std::getenv("LQCD_ARM_SVE_PLANNED");
        return value && value[0] == '1' && value[1] == '\0';
    }();
    return enabled;
}
// Only the addressing changes; projection and link arithmetic remain shared.
inline svfloat32_t sve_source_load(svbool_t valid, const float *source,
                                   svint32_t index, bool contiguous,
                                   std::ptrdiff_t base) {
    if (contiguous)
        return svld1_f32(valid, source + base);
    return svld1_gather_s32index_f32(valid, source, index);
}
inline svint32_t sve_indices(svbool_t pg, const int *p, int /*count*/) {
    return svld1_s32(pg, p);
}
inline svint32_t sve_indices(svbool_t pg, const std::ptrdiff_t *p, int count) {
    // Global callers must check the complete float-field size <= INT_MAX.
    // SVE vectors cannot exceed 2048 bits (64 float lanes). Convert only
    // active entries, so a partial final vector never reads past the table.
    int32_t narrow[64];
    for (int lane = 0; lane < count; ++lane) narrow[lane] = static_cast<int32_t>(p[lane]);
    return svld1_s32(pg, narrow);
}
inline void clover_range_sve(int B, const float *matrix, const float *src,
                             float *out, int begin, int end) {
    for (int a = 0; a < 12; ++a)
        for (int site = begin; site < end; site += svcntw()) {
            const svbool_t pg = svwhilelt_b32((uint64_t)site, (uint64_t)end);
            svfloat32_t yr = svdup_f32(0), yi = svdup_f32(0);
            for (int j = 0; j < 6; ++j) {
                const float *m = matrix + (a * 6 + j) * 2 * B + site;
                const float *x = src + 2 * ((a / 6) * 6 + j) * B + site;
                const auto mr = svld1_f32(pg,m), mi = svld1_f32(pg,m+B);
                const auto xr = svld1_f32(pg,x), xi = svld1_f32(pg,x+B);
                yr=svadd_f32_x(pg,yr,svsub_f32_x(pg,svmul_f32_x(pg,mr,xr),svmul_f32_x(pg,mi,xi)));
                yi=svadd_f32_x(pg,yi,svadd_f32_x(pg,svmul_f32_x(pg,mr,xi),svmul_f32_x(pg,mi,xr)));
            }
            svst1_f32(pg,out+2*a*B+site,yr);
            svst1_f32(pg,out+(2*a+1)*B+site,yi);
        }
}

// local_plan is optional metadata for Local=true only, 16 ints per block:
// [half][direction] = neighbour_site - source_site for all nonnegative
// neighbour entries in that half, or INT_MIN when nonuniform/empty. The
// hierarchy validates this invariant at construction. Inactive output sites
// are untouched. Hopping-only src/out may alias on disjoint parity ranges.
template<bool Local, class Offset, bool Clover>
inline void wilson_sve(int cb, int B, const float *diag, const float *links,
                       const Offset *neighbor, const int gp[4][4], const float gr[4][4],
                       const float gi[4][4], const float *src, float *out, int begin, int end,
                       const int *local_plan = nullptr) {
    if constexpr(Clover) {
        clover_range_sve(B,diag,src+(Local?0:(size_t)cb*24*B),out,begin,end);
    } else {
        for(int a=0;a<24;++a) for(int s=begin;s<end;s+=svcntw())
            svst1_f32(svwhilelt_b32((uint64_t)s,(uint64_t)end),out+a*B+s,svdup_f32(0));
    }
    for(int site=begin;site<end;site+=svcntw()) {
        const svbool_t pg=svwhilelt_b32((uint64_t)site,(uint64_t)end);
        const int count=(end-site<(int)svcntw()?end-site:(int)svcntw());
        for(int dir=0;dir<8;++dir) {
            const auto index=sve_indices(pg,neighbor+(size_t)dir*B+site,count);
            const auto valid=svcmpge_n_s32(pg,index,0);
            if(!svptest_any(pg,valid)) continue;
            bool contiguous = false;
            std::ptrdiff_t base = 0;
            if constexpr (Local) {
                // Plans describe valid neighbours only. Keep the actual index
                // predicate above: a Dirichlet hole may extrapolate in bounds.
                const int half = site >= B / 2 ? 1 : 0;
                const bool same_half = half || site + count <= B / 2;
                if (local_plan && same_half) {
                    const int delta = local_plan[half * 8 + dir];
                    base = (std::ptrdiff_t)site + delta;
                    // Never form a negative/out-of-allocation C++ pointer,
                    // even for masked lanes. Straddling vectors use gather.
                    contiguous = delta != INT_MIN && base >= 0 && base + count <= B;
                }
            }
            for(int sp=0;sp<2;++sp) for(int color=0;color<3;++color) {
                const int gs=gp[dir/2][sp];
                const float sign=dir%2?1.f:-1.f;
                const float pr=sign*gr[dir/2][sp], pi=sign*gi[dir/2][sp];
                svfloat32_t hr=svdup_f32(0),hi=svdup_f32(0);
                for(int j=0;j<3;++j) {
                    const float *v=src+(sp*3+j)*2*B,*w=src+(gs*3+j)*2*B;
                    const auto vr=sve_source_load(valid,v,index,contiguous,base);
                    const auto vi=sve_source_load(valid,v+B,index,contiguous,base);
                    const auto wr=sve_source_load(valid,w,index,contiguous,base);
                    const auto wi=sve_source_load(valid,w+B,index,contiguous,base);
                    const auto zr=svsub_f32_x(pg,svadd_f32_x(pg,vr,svmul_n_f32_x(pg,wr,pr)),svmul_n_f32_x(pg,wi,pi));
                    const auto zi=svadd_f32_x(pg,svadd_f32_x(pg,vi,svmul_n_f32_x(pg,wi,pr)),svmul_n_f32_x(pg,wr,pi));
                    const float *u=links+(dir*9+color*3+j)*2*B+site;
                    const auto ar=svld1_f32(valid,u),ai=svld1_f32(valid,u+B);
                    hr=svadd_f32_x(pg,hr,svsub_f32_x(pg,svmul_f32_x(pg,ar,zr),svmul_f32_x(pg,ai,zi)));
                    hi=svadd_f32_x(pg,hi,svadd_f32_x(pg,svmul_f32_x(pg,ar,zi),svmul_f32_x(pg,ai,zr)));
                }
                float *yr=out+(sp*3+color)*2*B+site,*yi=yr+B;
                float *lr=out+(gs*3+color)*2*B+site,*li=lr+B;
                const float rr=sign*gr[dir/2][gs],ri=sign*gi[dir/2][gs];
                svst1_f32(pg,yr,svadd_f32_x(pg,svld1_f32(pg,yr),hr));
                svst1_f32(pg,yi,svadd_f32_x(pg,svld1_f32(pg,yi),hi));
                svst1_f32(pg,lr,svadd_f32_x(pg,svld1_f32(pg,lr),svsub_f32_x(pg,svmul_n_f32_x(pg,hr,rr),svmul_n_f32_x(pg,hi,ri))));
                svst1_f32(pg,li,svadd_f32_x(pg,svld1_f32(pg,li),svadd_f32_x(pg,svmul_n_f32_x(pg,hi,rr),svmul_n_f32_x(pg,hr,ri))));
            }
        }
    }
}
} // namespace lqcd_native::arm
#endif
