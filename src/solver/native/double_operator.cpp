#include "hierarchy.hpp"
#include <climits>
#include <stdexcept>

using namespace lqcd_native::detail;

// Rank-local lexicographic double operator. The scalar core apply_dirac remains
// separate as the numerical oracle; gauge and clover are still global assets.
void NativeMG::Impl::apply_double(const Field &localin, Field &localout) const {
    if (&localin == &localout) {
        Field temporary;
        apply_double(localin, temporary);
        localout.swap(temporary);
        return;
    }
    const auto &o = gauge.o;
    const size_t spatial_sites = (size_t)o.nx * o.ny * o.nz;
    const int local_t = o.nt / native_size;
    const size_t local_sites = spatial_sites * local_t;
    const size_t face_complex = spatial_sites * 12;
    int invalid = o.nt % native_size != 0 || local_t < 1 ||
                  localin.size() != local_sites * 12 || face_complex > INT_MAX / 2;
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &invalid, 1, MPI_INT, MPI_MAX, native_comm);
    if (invalid)
        throw std::runtime_error("double operator requires a complete local lexical t slab");
    localout.resize(localin.size());
    const size_t global_start = (size_t)native_rank * local_sites;
    const double kappa = 1. / (2. * (4. + o.mass));
    const size_t strides[4] = {1, (size_t)o.nx, (size_t)o.nx * o.ny, spatial_sites};
    const int extents[4] = {o.nx, o.ny, o.nz, o.nt};

    auto site_apply = [&](size_t local_site) {
        const size_t global_site = global_start + local_site;
        const int local_time = local_site / spatial_sites;
        const int coordinate[4] = {
            (int)(local_site % o.nx), (int)((local_site / o.nx) % o.ny),
            (int)((local_site / ((size_t)o.nx * o.ny)) % o.nz),
            native_rank * local_t + local_time};
        const Complex *center = localin.data() + local_site * 12;
        Complex *result = localout.data() + local_site * 12;
        // Wilson clover commutes with gamma5, hence two independent 6x6
        // chiral blocks. Keep the original double coefficients, not float diag.
        for (int a = 0; a < 12; a++) {
            Complex value{};
            const int chiral_start = (a / 6) * 6;
            for (int j = chiral_start; j < chiral_start + 6; j++)
                value += gauge.clover[global_site * 144 + a * 12 + j] * center[j];
            result[a] = value;
        }
        for (int mu = 0; mu < 4; mu++)
            for (int backward = 0; backward < 2; backward++) {
                const bool wrapped = backward ? coordinate[mu] == 0
                                              : coordinate[mu] == extents[mu] - 1;
                size_t neighbor_site;
                if (backward)
                    neighbor_site = wrapped ? global_site + (extents[mu] - 1) * strides[mu]
                                            : global_site - strides[mu];
                else
                    neighbor_site = wrapped ? global_site - (extents[mu] - 1) * strides[mu]
                                            : global_site + strides[mu];
                const Complex *neighbor_spinor;
                if (native_size > 1 && mu == 3 && backward && local_time == 0)
                    neighbor_spinor = double_recv_lower.data() + (local_site % spatial_sites) * 12;
                else if (native_size > 1 && mu == 3 && !backward && local_time == local_t - 1)
                    neighbor_spinor = double_recv_upper.data() + (local_site % spatial_sites) * 12;
                else
                    neighbor_spinor = localin.data() + (neighbor_site - global_start) * 12;
                // Gauge links are untwisted. Apply antiperiodicity only at
                // the global time wrap, never at an internal MPI boundary.
                const double weight = mu == 3 && wrapped ? kappa : -kappa;
                const double sign = backward ? 1. : -1.;
                // Project upper spin components and reconstruct lower ones;
                // gr/gi encode exact 0,+/-1 gamma entries in the DR basis.
                for (int spin = 0; spin < 2; spin++) {
                    const int paired = gp[mu][spin];
                    const Complex projector(sign * gr[mu][spin], sign * gi[mu][spin]);
                    const Complex reconstruct(sign * gr[mu][paired], sign * gi[mu][paired]);
                    Complex projected[3];
                    for (int c = 0; c < 3; c++)
                        projected[c] = neighbor_spinor[spin * 3 + c] +
                                       projector * neighbor_spinor[paired * 3 + c];
                    for (int c = 0; c < 3; c++) {
                        Complex transported{};
                        for (int j = 0; j < 3; j++) {
                            const Complex link = backward ? std::conj(gauge.at(neighbor_site, mu, j, c))
                                                          : gauge.at(global_site, mu, c, j);
                            transported += link * projected[j];
                        }
                        result[spin * 3 + c] += weight * transported;
                        result[paired * 3 + c] += weight * reconstruct * transported;
                    }
                }
            }
    };

    if (native_size == 1) {
#pragma omp parallel for schedule(static)
        for (size_t site = 0; site < local_sites; site++)
            site_apply(site);
        return;
    }
    double_recv_lower.resize(face_complex);
    double_recv_upper.resize(face_complex);
    const int count = (int)(face_complex * 2);
    const int previous = (native_rank + native_size - 1) % native_size;
    const int next = (native_rank + 1) % native_size;
    MPI_Request requests[4];
    // Lexical faces are contiguous. Sends alias immutable input, and every
    // request completes before returning or allowing the caller to modify it.
    MPI_Irecv(double_recv_upper.data(), count, MPI_DOUBLE, next, 30, native_comm, &requests[0]);
    MPI_Irecv(double_recv_lower.data(), count, MPI_DOUBLE, previous, 31, native_comm, &requests[1]);
    MPI_Isend(localin.data(), count, MPI_DOUBLE, previous, 30, native_comm, &requests[2]);
    MPI_Isend(localin.data() + (local_sites - spatial_sites) * 12, count, MPI_DOUBLE,
              next, 31, native_comm, &requests[3]);
    if (!halo_overlap) {
        MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
#pragma omp parallel for schedule(static)
        for (size_t site = 0; site < local_sites; site++)
            site_apply(site);
        return;
    }
    const size_t interior_first = spatial_sites;
    const size_t interior_last = std::max(interior_first, local_sites - spatial_sites);
#pragma omp parallel
    {
        const int thread = omp_get_thread_num(), threads = omp_get_num_threads();
        if (thread == 0) {
            // MPI_THREAD_FUNNELED: the calling/main thread drives progress.
            MPI_Waitall(4, requests, MPI_STATUSES_IGNORE);
            if (threads == 1)
                for (size_t site = interior_first; site < interior_last; site++)
                    site_apply(site);
        } else {
            const size_t count_interior = interior_last - interior_first;
            const size_t first = interior_first + count_interior * (thread - 1) / (threads - 1);
            const size_t last = interior_first + count_interior * thread / (threads - 1);
            for (size_t site = first; site < last; site++)
                site_apply(site);
        }
#pragma omp barrier
        // For a single local time slice the two faces coincide; execute once.
#pragma omp for schedule(static)
        for (size_t face_site = 0; face_site < std::min(local_sites, 2 * spatial_sites); face_site++) {
            const size_t site = face_site < spatial_sites ? face_site
                : local_sites - spatial_sites + face_site - spatial_sites;
            site_apply(site);
        }
    }
}
