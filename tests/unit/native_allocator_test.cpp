#include "../../src/support/aligned_workspace.hpp"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}
template <class T> bool aligned(const T *pointer, std::size_t alignment) {
    return reinterpret_cast<std::uintptr_t>(pointer) % alignment == 0;
}
struct alignas(128) OverAligned {
    int value;
    explicit OverAligned(int v = 0) : value(v) {}
};
} // namespace

int main() {
    try {
        using Allocator = lqcd_native::WorkspaceAllocator<float>;
        for (std::size_t count : {1u, 17u, 432u, 864u, 20736u}) {
            std::vector<float, Allocator> values(count, 1.25f);
            require(aligned(values.data(), 64), "float storage is not 64-byte aligned");
            require(std::all_of(values.begin(), values.end(), [](float v) { return v == 1.25f; }),
                    "explicit fill did not initialize every element");

            auto copy = values;
            require(aligned(copy.data(), 64), "copied storage lost alignment");
            require(copy == values, "copy changed element values");
            copy.resize(count + 1, 2.5f);
            auto moved = std::move(copy);
            require(aligned(moved.data(), 64), "grown/moved storage lost alignment");
            require(moved.size() == count + 1 && moved.back() == 2.5f,
                    "growth/move did not preserve the appended fill value");
            require(std::all_of(moved.begin(), moved.end() - 1, [](float v) { return v == 1.25f; }),
                    "growth/move changed existing values");

            std::vector<float, Allocator> assigned(3, -1.f);
            assigned = values;
            require(aligned(assigned.data(), 64) && assigned == values,
                    "copy assignment changed alignment or values");
            assigned = std::move(moved);
            require(aligned(assigned.data(), 64) && assigned.size() == count + 1 &&
                        assigned.back() == 2.5f,
                    "move assignment changed alignment or values");
        }

        using OverAllocator = lqcd_native::WorkspaceAllocator<OverAligned>;
        std::vector<OverAligned, OverAllocator> wide;
        for (int i = 0; i < 17; i++)
            wide.emplace_back(i);
        require(aligned(wide.data(), alignof(OverAligned)),
                "over-aligned storage lost its type alignment");
        for (int i = 0; i < 17; i++)
            require(aligned(&wide[i], alignof(OverAligned)) && wide[i].value == i,
                    "over-aligned element construction or relocation failed");

        Allocator allocator;
        bool overflow_rejected = false;
        try {
            const std::size_t count = allocator.max_size() + 1;
            float *pointer = allocator.allocate(count);
            allocator.deallocate(pointer, count);
        } catch (const std::bad_alloc &) {
            overflow_rejected = true;
        }
        require(overflow_rejected, "allocation byte-count overflow was not rejected");
        std::cout
            << "native allocator: alignment, copy/move/fill, over-aligned type, overflow passed\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "native allocator test failed: " << error.what() << '\n';
        return 1;
    }
}
