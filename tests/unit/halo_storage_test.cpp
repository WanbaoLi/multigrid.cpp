#include "solver/native/halo_storage.hpp"
#include <cassert>
#include <iostream>

using Buffer=std::vector<float,lqcd_native::WorkspaceAllocator<float>>;
using lqcd_native::detail::FineHaloStorage;

int main() {
    const size_t page=size_t(sysconf(_SC_PAGESIZE));
    const size_t face_bytes=std::max(size_t(1024*1024),128*page);
    const size_t face=face_bytes/sizeof(float),total=8*face;
    const size_t first=2*face+1,end=4*face-1;
    Buffer a(total),b(total),c(total);
    std::fill(a.begin()+first,a.begin()+end,11.f);
    std::fill(b.begin()+first,b.begin()+end,22.f);
    std::fill(c.begin()+first,c.begin()+end,33.f);
    a[first-1]=101.f; b[first-1]=202.f;
    const size_t lower=((first-face)*sizeof(float)+page-1)/page*page/sizeof(float);
    const size_t upper=(end*sizeof(float)+page-1)/page*page/sizeof(float);
    {
        FineHaloStorage pool(first,end,face,total);
        assert(pool.bind(a,0) && pool.bind(b,0) && pool.bind(c,1));
        assert(pool.slots()==2 && pool.bytes_per_slot()<=2*face_bytes);
        a[lower]=7.f; a[upper]=9.f;
        assert(b[lower]==7.f && b[upper]==9.f);
        assert(c[lower]==0.f && c[upper]==0.f);
        c[lower]=17.f;
        pool.bind(b,1);
        assert(b[lower]==17.f && a[lower]==7.f);
        pool.bind(b,0);
        assert(b[lower]==7.f && b[upper]==9.f);
        assert(a[first-1]==101.f && b[first-1]==202.f);
        for (size_t i=first;i<end;++i)
            assert(a[i]==11.f && b[i]==22.f && c[i]==33.f);
    }
    assert(a[lower]==7.f && b[upper]==9.f && c[lower]==17.f);
    {
        Buffer x(2*face),y(2*face);
        FineHaloStorage coincident(0,face,face,2*face);
        assert(coincident.bytes_per_slot()==face_bytes);
        coincident.bind(x,0); coincident.bind(y,0);
        x[face]=31.f;
        assert(y[face]==31.f);
    }
    {
        Buffer x(1024);
        FineHaloStorage small(256,512,256,1024);
        assert(!small.bind(x,0));
    }
    std::cout << "PASS reusable halo pages, RHS separation, owned partial pages and lifetime\n";
}
