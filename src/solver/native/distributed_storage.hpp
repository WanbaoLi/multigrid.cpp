#pragma once
#include "environment.hpp"
#include <cstdint>
#include <cmath>
#include <climits>
#include <stdexcept>

namespace lqcd_native::detail {
inline bool distributed_storage() { return setting("LQCD_DISTRIBUTED_STORAGE", 0) == 1; }

// Counter-based uniform probes: decomposition independent and no global RNG
// traversal/storage. They are setup probes, not production Monte Carlo RNG.
inline float setup_probe(std::uint64_t index, unsigned seed) {
    std::uint64_t z = index + (std::uint64_t(seed) << 32) + 0x9e3779b97f4a7c15ull;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ull;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebull;
    z ^= z >> 31;
    return float((z >> 40) * (1.0 / 8388608.0) - 1.0);
}

// Exchange contiguous global-index faces; chunk to stay inside MPI int counts.
// Called on the MPI main thread only; sends and receives never overlap owners.
inline void exchange_faces(Complex *data, size_t first, size_t end, size_t face,
                           size_t total, MPI_Comm comm, int tag) {
    int rank, ranks;
    MPI_Comm_rank(comm, &rank); MPI_Comm_size(comm, &ranks);
    if (ranks == 1) return;
    const size_t lower = (first + total - face) % total, upper = end % total;
    constexpr size_t chunk = 16 * 1024 * 1024; // complex elements
    for (size_t off = 0; off < face; off += chunk) {
        const int count = int(std::min(chunk, face-off) * 2);
        MPI_Sendrecv(data+first+off, count, MPI_DOUBLE, (rank+ranks-1)%ranks, tag,
                     data+upper+off, count, MPI_DOUBLE, (rank+1)%ranks, tag,
                     comm, MPI_STATUS_IGNORE);
        MPI_Sendrecv(data+end-face+off, count, MPI_DOUBLE, (rank+1)%ranks, tag+1,
                     data+lower+off, count, MPI_DOUBLE, (rank+ranks-1)%ranks, tag+1,
                     comm, MPI_STATUS_IGNORE);
    }
}
}
