#include "../../src/support/hbm_placement.hpp"
#include <iostream>
#include <stdexcept>
using namespace lqcd_native::hbm;
void check(bool ok) {
    if (!ok)
        throw std::runtime_error("HBM helper invariant failed");
}
int main() {
    std::set<int> a;
    check(parse_list("0,2-4,9", a) && a == std::set<int>({0, 2, 3, 4, 9}));
    for (auto text : {"-1", "1-0", "1,", "1,,2", "foo", "9999999999999999999"})
        check(!parse_list(text, a));
    std::vector<Node> n = {
        {0, false, {10, 20, 11, 30}}, {1, false, {20, 10, 30, 11}}, {2, true, {}}, {3, true, {}}};
    auto p = select(Mode::Require, 0, n, {0, 1, 2, 3});
    check(p.memory_node == 2 && p.error.empty());
    check(select(Mode::Prefer, 1, n, {2, 3}).memory_node == 3);
    check(select(Mode::Prefer, 0, n, {0, 1}).memory_node == -1);
    check(select(Mode::Prefer, 0, n, {3}).memory_node == 3);
    n[0].distances[3] = 11;
    check(!select(Mode::Require, 0, n, {2, 3}).error.empty());
    check(!select(Mode::Require, 2, n, {2, 3}).error.empty());
    auto r = full_pages({reinterpret_cast<void *>(4097), 12286}, 4096);
    check(r.begin == 8192 && r.bytes == 4096);
    check(full_pages({reinterpret_cast<void *>(4096), 4096}, 4096).bytes == 4096);
    check(full_pages({reinterpret_cast<void *>(4097), 4095}, 4096).bytes == 0);
    check(full_pages({reinterpret_cast<void *>(UINTPTR_MAX - 10), 20}, 4096).bytes == 0);
    auto off = place(Plan{}, {reinterpret_cast<void *>(1), 42});
    check(!off.attempted && off.requirement_met);
    auto failure = place(Plan{Mode::Require, 0, -1, "injected missing target"}, {nullptr, 0});
    check(!failure.attempted && !failure.requirement_met && !failure.error.empty());
#ifdef __linux__
    check(allowed_mems(a) && !a.empty());
#endif
    std::cout
        << "PASS HBM parsing, injected topology, cpuset filtering, alignment, off/error paths\n";
}
