#include "hierarchy.hpp"
#include "distributed_storage.hpp"
#include <cmath>
#include <iostream>
#include <random>

using namespace lqcd_native::detail;

void NativeMG::generate_basis(Multigrid &m, int cycles, int adaptive) {
    if (native_rank == 0)
        std::cerr << "native setup update="
                  << (impl->setup_update == SetupUpdate::Paper ? "paper" : "inverse")
                  << " sap_cycles=" << cycles << " adaptive_steps=" << adaptive
                  << " sap_eo=" << impl->sap_eo << " coarse_eo=" << impl->coarse_eo << std::endl;
    std::vector<FloatField> vectors(24);
    for (auto &v : vectors)
        v.resize(impl->fine_sites * 24);
    // Adaptive passes immediately reuse the vectors produced by the prior
    // setup pass. Avoid consuming Gaussian RNG and writing an entire field
    // that would be discarded; the no-cache path remains bitwise identical.
    const bool reuse_vectors = adaptive && !impl->test_vectors.empty();
    FloatField zero(cycles ? impl->fine_sites * 24 : 0);
    const size_t owned_first = (size_t)impl->first_aggregate*24*impl->block_sites;
    const size_t owned_end = (size_t)impl->end_aggregate*24*impl->block_sites;
    if (cycles) std::fill(zero.begin()+owned_first, zero.begin()+owned_end, 0.f);
    for (int v = 0; v < 24; v++) {
        if (reuse_vectors)
            impl->fine_copy(impl->test_vectors[v], vectors[v]);
        else {
            std::mt19937 gen(native_seed + v);
            std::normal_distribution<float> normal;
            if (distributed_storage()) {
#pragma omp parallel for schedule(static)
                for (size_t i = owned_first; i < owned_end; ++i)
                    vectors[v][i] = setup_probe(i, native_seed+v);
            } else
                for (float &x : vectors[v]) x = normal(gen);
            if (cycles)
                impl->sap(zero, vectors[v], cycles);
        }
        if (adaptive) {
            for (int step = 0; step < adaptive; step++) {
                FloatField update;
                if (impl->setup_update == SetupUpdate::Paper) {
                    // DD-alphaAMG Algorithm 5.1: v <- v + C(v - Dv).
                    // Fine workspaces use owned entries plus exchange halos;
                    // never copy uninitialized off-rank workspace entries.
                    FloatField image, residual;
                    impl->fine_apply(vectors[v], image);
                    impl->fine_copy(vectors[v], residual);
                    impl->fine_axpy(residual, -1., image);
                    FloatField correction;
                    impl->apply_vcycle(residual, correction);
                    impl->fine_copy(vectors[v], update);
                    impl->fine_axpy(update, Complex(1., 0.), correction);
                } else
                    impl->apply_vcycle(vectors[v], update);
                double vn = fine_norm(update);
                if (!std::isfinite(vn) || vn == 0)
                    throw std::runtime_error("nonfinite or zero adaptive setup vector");
#pragma omp parallel for schedule(static)
                for (size_t i = (size_t)impl->first_aggregate * 24 * impl->block_sites;
                     i < (size_t)impl->end_aggregate * 24 * impl->block_sites; i++)
                    update[i] /= vn;
                vectors[v] = std::move(update);
            }
        }
        if (native_size > 1 && !m.distributed)
            MPI_Allgather(MPI_IN_PLACE, 0, MPI_DATATYPE_NULL, vectors[v].data(),
                          vectors[v].size() / native_size, MPI_FLOAT, native_comm);
        double vn = fine_norm(vectors[v]);
        if (!std::isfinite(vn) || vn == 0)
            throw std::runtime_error("nonfinite homogeneous setup vector");
        std::cerr << "setup vector " << v + 1 << " norm " << vn << std::endl;
    }
    const int basis_first = (m.synchronize_shared || m.distributed) ? impl->first_aggregate : 0;
    const int basis_end = (m.synchronize_shared || m.distributed) ? impl->end_aggregate : impl->aggregate_count;
    const size_t basis_stride = (size_t)impl->block_sites * 12 * m.coarse_dof;
    std::fill(m.basis.begin() + basis_first * basis_stride,
              m.basis.begin() + basis_end * basis_stride, Complex{});
#pragma omp parallel for schedule(static)
    for (int cb = basis_first; cb < basis_end; cb++)
        for (int cs = 0; cs < 2; cs++) {
            std::vector<Complex> block(24 * 6 * impl->block_sites);
            for (int v = 0; v < 24; v++) {
                auto col = block.data() + (size_t)v * 6 * impl->block_sites;
                for (int a = 0; a < 6; a++)
                    for (int s = 0; s < impl->block_sites; s++)
                        col[a * impl->block_sites + s] = {
                            vectors[v]
                                   [((size_t)cb * 24 + 2 * (cs * 6 + a)) * impl->block_sites + s],
                            vectors[v]
                                   [((size_t)cb * 24 + 2 * (cs * 6 + a) + 1) * impl->block_sites +
                                    s]};
                for (int pass = 0; pass < 2; pass++)
                    for (int j = 0; j < v; j++) {
                        auto prev = block.data() + (size_t)j * 6 * impl->block_sites;
                        Complex dot = 0;
                        for (int s = 0; s < 6 * impl->block_sites; s++)
                            dot += std::conj(prev[s]) * col[s];
                        for (int s = 0; s < 6 * impl->block_sites; s++)
                            col[s] -= dot * prev[s];
                    }
                double sum = 0;
                for (int s = 0; s < 6 * impl->block_sites; s++)
                    sum += std::norm(col[s]);
                sum = std::sqrt(sum);
                for (int s = 0; s < 6 * impl->block_sites; s++)
                    col[s] /= sum;
                for (int a = 0; a < 6; a++)
                    for (int s = 0; s < impl->block_sites; s++)
                        m.basis[basis_index(
                            cb,
                            impl->sap_eo ? impl->local_lex[(size_t)cb * impl->block_sites + s] : s,
                            cs * 6 + a, cs * 24 + v, m)] = col[a * impl->block_sites + s];
            }
        }
    if (m.synchronize_shared)
        m.synchronize_shared();
    if (m.distributed)
        exchange_faces(m.basis.data(), basis_first*basis_stride, basis_end*basis_stride,
            (size_t)impl->aggregates_per_tslice*basis_stride, m.basis.size(), native_comm, 62);
    for (size_t i = basis_first*basis_stride; i < basis_end*basis_stride; ++i)
        if (!std::isfinite(std::norm(m.basis[i])))
            throw std::runtime_error("nonfinite local basis");
    // Existing assembly scatters additions to neighboring rows. One process
    // owns the complete assembly, retaining its arithmetic order and avoiding
    // interprocess writes to the same matrix. Setup is timed separately.
    if (!m.synchronize_shared || native_rank == 0)
        rebuild_coarse_operator(impl->gauge, m);
    if (m.synchronize_shared)
        m.synchronize_shared();
    for (size_t i = (m.distributed ? m.first_block*9*48*48 : 0);
         i < (m.distributed ? m.end_block*9*48*48 : m.stencil.size()); ++i)
        if (!std::isfinite(std::norm(m.stencil[i])))
            throw std::runtime_error("nonfinite coarse stencil");
    auto &g = impl->gauge;
    const bool profile = impl->halo_profile;
    const bool adaptive_target = impl->adaptive_correction;
    const SetupUpdate setup_update = impl->setup_update;
    const bool sap_eo = impl->sap_eo;
    const bool coarse_eo = impl->coarse_eo;
    const auto hbw_policy = impl->hbw_policy;
    impl = std::make_unique<Impl>(g, m, sap_eo);
    impl->configure_solve();
    impl->coarse_eo = coarse_eo;
    impl->hbw_policy = hbw_policy;
    impl->halo_profile = profile;
    impl->adaptive_correction = adaptive_target;
    impl->setup_update = setup_update;
    impl->test_vectors = std::move(vectors);
}

void NativeMG::release_setup_vectors() {
    std::vector<FloatField>().swap(impl->test_vectors);
}
