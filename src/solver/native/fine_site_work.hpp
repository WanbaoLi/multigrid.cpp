#pragma once
#include <algorithm>
#include <cstddef>
#include <vector>

namespace lqcd_native::detail {
// Flatten valid output sites, retaining contiguous block-local ranges for SIMD.
// Geometry is built once; partition using the actual team size on every call.
struct FineSiteWork {
    struct Span {
        int block, begin, end;
    };
    std::vector<Span> spans;
    std::vector<std::size_t> offsets{0};

    void add(int block, int begin, int end) {
        if (begin >= end)
            return;
        spans.push_back({block, begin, end});
        offsets.push_back(offsets.back() + std::size_t(end - begin));
    }
    template <class Apply> void run(int thread, int threads, Apply apply) const {
        const std::size_t total = offsets.back();
        const std::size_t chunk = total / threads + (total % threads != 0);
        std::size_t first = std::min(total, chunk * thread);
        const std::size_t last = std::min(total, first + chunk);
        if (first == last)
            return;
        auto i = std::size_t(std::upper_bound(offsets.begin(), offsets.end(), first) -
                             offsets.begin() - 1);
        while (first < last) {
            const auto &span = spans[i];
            const auto end = std::min(last, offsets[i + 1]);
            apply(span.block, span.begin + int(first - offsets[i]),
                  span.begin + int(end - offsets[i]));
            first = end;
            ++i;
        }
    }
};
} // namespace lqcd_native::detail
