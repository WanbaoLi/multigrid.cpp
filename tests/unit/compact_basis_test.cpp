#include "core/coefficient_field.h"
#include <cassert>
int main() {
    CoefficientField basis; basis.reserve_sparse(4*12*48,true);
    for(size_t site=0;site<4;++site)
        for(size_t a=0;a<12;++a)
            for(size_t v=0;v<24;++v) {
                size_t i=(site*12+a)*48+(a/6)*24+v;
                basis[i]=Complex(i+1,-double(i));
            }
    const auto &view=basis;
    for(size_t i=0;i<4*12*48;++i)
        assert(view[i]==((i%48)/24==((i/48)%12)/6 ? Complex(i+1,-double(i)) : Complex{}));
    CoefficientField copy=basis;
    assert(copy[24]==Complex{} && copy[0]==Complex(1,0));
    bool rejected=false; try { basis.begin(); } catch(...) { rejected=true; }
    assert(rejected);
    basis.release_storage();assert(basis.empty());
}
