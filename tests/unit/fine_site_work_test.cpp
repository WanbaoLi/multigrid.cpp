#include "solver/native/fine_site_work.hpp"
#include <cassert>
#include <omp.h>
#include <vector>
using lqcd_native::detail::FineSiteWork;

int main() {
    // Noncontiguous blocks, EO parity halves, color subsets, time faces and
    // tiny/empty ranges must be visited exactly once, with no padded writes.
    for (int bt : {1, 2, 4})
        for (int parity : {1, 2})
            for (int mode = 0; mode < 3; ++mode) {
                const int B = 216 * bt, ps = B / parity, pf = 216 / parity;
                FineSiteWork work;
                std::vector<int> expected(64 * B, 0);
                for (int cb = 0; cb < 64; ++cb) {
                    if (mode == 2 && cb % 2)
                        continue;
                    for (int p = 0; p < parity; ++p) {
                        int begin = p * ps, end = begin + ps;
                        if (mode == 1) {
                            begin += pf;
                            end -= pf;
                        }
                        work.add(cb, begin, end);
                        for (int s = begin; s < end; ++s)
                            expected[cb * B + s] = 1;
                    }
                }
                for (int threads : {1, 2, 7, 19, 32, 37, 48, 128, 304}) {
                    std::vector<int> seen(expected.size(), 0);
                    std::vector<std::size_t> loads(threads, 0);
                    // Deterministic partition audit, independent of host core count.
                    for (int t = 0; t < threads; ++t)
                        work.run(t, threads, [&](int cb, int begin, int end) {
                            loads[t] += end - begin;
                            for (int s = begin; s < end; ++s)
                                ++seen[cb * B + s];
                        });
                    assert(seen == expected);
                    const auto total = work.offsets.back();
                    const auto base = total / threads, extra = total % threads;
                    for (int t = 0; t < threads; ++t) {
                        assert(loads[t] == base + (std::size_t(t) < extra));
                        if (total >= std::size_t(threads))
                            assert(loads[t] > 0);
                    }
                    std::fill(seen.begin(), seen.end(), 0);
#pragma omp parallel num_threads(std::min(threads, 37))
                    {
                        work.run(omp_get_thread_num(), omp_get_num_threads(),
                                 [&](int cb, int begin, int end) {
                                     for (int s = begin; s < end; ++s) {
#pragma omp atomic update
                                         ++seen[cb * B + s];
                                     }
                                 });
                    }
                    assert(seen == expected);
                }
            }
    // Enough sites must keep every team member active, even when ceil(N/T)
    // would have left the final threads empty (e.g. N=38, T=37).
    for (int count : {0, 3, 38, 100, 305}) {
        FineSiteWork small;
        small.add(0, 5, 5 + count);
        int visits = 0, active = 0;
        for (int t = 0; t < 37; ++t)
            small.run(t, 37, [&](int, int begin, int end) {
                visits += end - begin;
                ++active;
            });
        assert(visits == count);
        assert(active == std::min(count, 37));
    }
}
