#include "../../src/support/hbw_buffer.hpp"
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace lqcd_native::hbm;
namespace {
int allocs = 0, frees = 0;
void *last_raw = nullptr;
void check(bool x) {
    if (!x)
        throw std::runtime_error("HBW buffer invariant failed");
}
// Deliberately misalign the provider pointer; deallocator must receive that
// original pointer, not the aligned view returned to the caller.
void *fake_alloc(std::size_t n) {
    ++allocs;
    auto p = static_cast<char *>(std::malloc(n + 1));
    last_raw = p ? p + 1 : nullptr;
    return last_raw;
}
void fake_free(void *p) {
    if (p != last_raw)
        std::abort();
    ++frees;
    std::free(static_cast<char *>(p) - 1);
}
void *null_alloc(std::size_t) {
    ++allocs;
    return nullptr;
}
} // namespace
int main() {
    {
        HbwBuffer b(4097, 64, Policy::Off);
        check(bool(b) && !b.fallback());
        check((uintptr_t)b.data() % 64 == 0);
        auto moved = std::move(b);
        check(!b && bool(moved));
    }
    check(allocs == 0 && frees == 0);
    {
        Provider p{fake_alloc, fake_free, [](void *ptr, std::size_t bytes, int flags) {
                       check(ptr && bytes == 512 && flags == 0);
                       return 0; // successful allocation is deliberately NOT evidence of HBW
                   }};
        HbwBuffer b(512, 64, Policy::Require, 0, p);
        check(bool(b) && b.verify_hbw() == 0);
    }
    allocs = frees = 0;
    {
        HbwBuffer b(1024, 4096, Policy::Require, 0, {fake_alloc, fake_free});
        check(bool(b) && b.backend() == Backend::KUPL);
        check((uintptr_t)b.data() % 4096 == 0);
        check(b.allocation_bytes() == 5119);
        HbwBuffer dest(128);
        dest = std::move(b);
        check(!b && bool(dest));
        check(bool(dest));
    }
    check(allocs == 1 && frees == 1);
    {
        HbwBuffer b(1024, 64, Policy::Prefer, 0, {null_alloc, fake_free});
        check(bool(b) && b.fallback() && !b.fallback_reason().empty());
    }
    check(allocs == 2 && frees == 1);
    {
        HbwBuffer b(1024, 64, Policy::Require, 0, {null_alloc, fake_free});
        check(!b && !b.error().empty());
    }
    check(allocs == 3 && frees == 1);
    {
        HbwBuffer b(1024, 64, Policy::Require, 1024, {fake_alloc, fake_free});
        check(!b && !b.error().empty());
    }
    check(allocs == 3);
    {
        HbwBuffer b(1024, 64, Policy::Prefer, 1024, {fake_alloc, fake_free});
        check(bool(b) && b.fallback());
    }
    check(allocs == 3);
    {
        HbwBuffer b(2048, 64, Policy::Prefer, 1024);
        check(!b && !b.error().empty());
    }
    {
        HbwBuffer b(std::numeric_limits<std::size_t>::max(), 64, Policy::Off);
        check(!b && !b.error().empty());
        HbwBuffer bad(10, 65);
        check(!bad && !bad.error().empty());
        HbwBuffer z(0, 64, Policy::Require);
        check(z.size() == 0 && z.error().empty());
    }
    {
        HbwBuffer b(4096, 64, Policy::Off);
        auto s = b.sample_pages(2);
        check(s.pages <= 2);
        check(s.known + s.unknown == s.pages);
        check(b.sample_pages(0).pages == 0);
    }
    std::cout << "PASS HBW ownership, original-pointer pairing, moves, overalignment, overflow, "
                 "limits, null fallback, page query\n";
}
