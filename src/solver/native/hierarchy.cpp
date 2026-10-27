#include "hierarchy.hpp"
#include "kernels.hpp"
#include "lqcd/core/dslash.h"
#include <climits>
#include <cmath>
#include <cctype>
#include <cstdlib>
#include <string>

using namespace lqcd_native::detail;

void NativeMG::Impl::configure_solve() {
    const char *names[] = {"LQCD_MG_SAP_STEPS", "LQCD_MG_SAP_CYCLES", "LQCD_MG_COARSE_IT",
                          "LQCD_MG_COARSE_TOL", "LQCD_CORRECTION_BASE_TOL",
                          "LQCD_FLOAT_CORRECTION_VERIFY", "LQCD_FINE_TEAM_FUSED", "LQCD_COARSE_CGS2"};
    double values[] = {(double)setting("NATIVE_SAP_STEPS", 4),
                       (double)setting("NATIVE_SAP_CYCLES", 2),
                       (double)setting("NATIVE_COARSE_IT", 40), .1, 1e-3, 0., 1., 0.};
    const double lower[] = {1., 1., 1., 1e-4, 1e-6, 0., 0., 0.};
    const double upper[] = {32., 8., 200., .9, .1, 1., 1., 1.};
    int invalid = 0;
    for (int i = 0; i < 8; i++) {
        if (const char *raw = std::getenv(names[i])) {
            char *end;
            values[i] = std::strtod(raw, &end);
            if (end == raw)
                invalid = 1;
            while (std::isspace((unsigned char)*end))
                ++end;
            if (*end)
                invalid = 1;
        }
        if (!std::isfinite(values[i]) || values[i] < lower[i] || values[i] > upper[i] ||
            ((i < 3 || i > 4) && values[i] != std::floor(values[i])))
            invalid = 1;
    }
    double minimum[8], maximum[8];
    std::copy_n(values, 8, minimum);
    std::copy_n(values, 8, maximum);
    MPI_Allreduce(MPI_IN_PLACE, &invalid, 1, MPI_INT, MPI_MAX, native_comm);
    MPI_Allreduce(MPI_IN_PLACE, minimum, 8, MPI_DOUBLE, MPI_MIN, native_comm);
    MPI_Allreduce(MPI_IN_PLACE, maximum, 8, MPI_DOUBLE, MPI_MAX, native_comm);
    for (int i = 0; i < 8; i++)
        if (minimum[i] != maximum[i])
            invalid = 1;
    if (invalid)
        throw std::runtime_error("MG solve tuning must be finite, in range and identical on every rank");
    sap_steps = (int)values[0];
    sap_cycles = (int)values[1];
    coarse_it = (int)values[2];
    coarse_tolerance = values[3];
    correction_base_tol = values[4];
    float_correction_verify = values[5] != 0;
    fine_team_fused = values[6] != 0;
    coarse_cgs2 = values[7] != 0;
}

NativeMG::Impl::Impl(const Gauge &gg, const Multigrid &mm, bool eo)
    : gauge(gg), hierarchy(mm), block_sites(hierarchy.block_volume),
      aggregate_count(hierarchy.n_coarse), coarse_dof(hierarchy.coarse_dof),
      fine_sites(hierarchy.n_fine), sap_eo(eo) {
    if (hierarchy.ct % native_size)
        throw std::runtime_error("native MPI requires complete t-slab aggregates");
    first_aggregate = aggregate_count * native_rank / native_size;
    end_aggregate = aggregate_count * (native_rank + 1) / native_size;
    aggregates_per_tslice = hierarchy.cx * hierarchy.cy * hierarchy.cz;
    if (coarse_dof != 48)
        throw std::runtime_error("native first prototype requires chirally split 24-vector basis");
    links.resize(fine_sites * 144);
    diag.resize(fine_sites * 144);
    basis.resize(fine_sites * 12 * 24 * 2);
    coarse.resize(hierarchy.stencil.size() * 2);
    neighbor.resize(fine_sites * 8);
    if (fine_sites <= (size_t)INT_MAX / 24)
        neighbor32.resize(fine_sites * 8);
    inner.resize(fine_sites * 8);
    lex.resize(fine_sites);
    if (sap_eo)
        local_lex.resize(fine_sites);
    colors.resize(aggregate_count);
    cneighbor.resize(aggregate_count * 9);
    for (int mu = 0; mu < 4; mu++)
        for (int a = 0; a < 4; a++)
            for (int s = 0; s < 4; s++)
                if (std::abs(gamma_matrix[mu][a][s]) > 0) {
                    gp[mu][a] = s;
                    gr[mu][a] = gamma_matrix[mu][a][s].real();
                    gi[mu][a] = gamma_matrix[mu][a][s].imag();
                }
    auto blocked = [&](int x, int y, int z, int t) {
        const int ls = local_site(x, y, z, t, hierarchy);
        const int slot = sap_eo ? ((x + y + z + t) & 1) * (block_sites / 2) + ls / 2 : ls;
        return (int)(coarse_site_index(x / hierarchy.o.bx, y / hierarchy.o.by, z / hierarchy.o.bz,
                                       t / hierarchy.o.bt, hierarchy) *
                         block_sites +
                     slot);
    };
#pragma omp parallel for schedule(static)
    for (int cb = 0; cb < aggregate_count; cb++) {
        int bc[4] = {cb % hierarchy.cx, (cb / hierarchy.cx) % hierarchy.cy,
                     (cb / (hierarchy.cx * hierarchy.cy)) % hierarchy.cz,
                     cb / (hierarchy.cx * hierarchy.cy * hierarchy.cz)};
        colors[cb] = (bc[0] + bc[1] + bc[2] + bc[3]) & 1;
        cneighbor[cb * 9] = cb;
        int dims[4] = {hierarchy.o.nx, hierarchy.o.ny, hierarchy.o.nz, hierarchy.o.nt},
            bs[4] = {hierarchy.o.bx, hierarchy.o.by, hierarchy.o.bz, hierarchy.o.bt};
        int cd[4] = {hierarchy.cx, hierarchy.cy, hierarchy.cz, hierarchy.ct};
        for (int mu = 0; mu < 4; mu++)
            for (int pm = 0; pm < 2; pm++) {
                int q[4];
                std::copy(bc, bc + 4, q);
                q[mu] = (q[mu] + (pm ? -1 : 1) + cd[mu]) % cd[mu];
                cneighbor[cb * 9 + 1 + mu * 2 + pm] =
                    coarse_site_index(q[0], q[1], q[2], q[3], hierarchy);
            }
        for (int ls = 0; ls < block_sites; ls++) {
            int q = ls, p[4];
            for (int d = 0; d < 4; d++) {
                p[d] = bc[d] * bs[d] + q % bs[d];
                q /= bs[d];
            }
            const int s =
                sap_eo ? ((p[0] + p[1] + p[2] + p[3]) & 1) * (block_sites / 2) + ls / 2 : ls;
            size_t fs = site_index(p[0], p[1], p[2], p[3], hierarchy.o);
            lex[(size_t)cb * block_sites + s] = fs;
            if (sap_eo)
                local_lex[(size_t)cb * block_sites + s] = ls;
            for (int a = 0; a < 12; a++)
                for (int j = 0; j < 6; j++) {
                    auto v = gauge.clover[fs * 144 + a * 12 + (a / 6) * 6 + j];
                    diag[((size_t)cb * 144 + (a * 6 + j) * 2) * block_sites + s] = v.real();
                    diag[((size_t)cb * 144 + (a * 6 + j) * 2 + 1) * block_sites + s] = v.imag();
                }
            for (int mu = 0; mu < 4; mu++)
                for (int pm = 0; pm < 2; pm++) {
                    int np[4];
                    std::copy(p, p + 4, np);
                    np[mu] = (np[mu] + (pm ? -1 : 1) + dims[mu]) % dims[mu];
                    int nb = blocked(np[0], np[1], np[2], np[3]), dir = 2 * mu + pm;
                    neighbor[((size_t)cb * 8 + dir) * block_sites + s] =
                        (std::ptrdiff_t)(nb / block_sites) * 24 * block_sites + nb % block_sites;
                    inner[((size_t)cb * 8 + dir) * block_sites + s] =
                        nb / block_sites == cb ? nb % block_sites : -1;
                    size_t ns = site_index(np[0], np[1], np[2], np[3], hierarchy.o);
                    double factor = -1 / (2 * (4 + gauge.o.mass));
                    if (mu == 3 && ((!pm && p[3] == dims[3] - 1) || (pm && p[3] == 0)))
                        factor = -factor;
                    for (int a = 0; a < 3; a++)
                        for (int j = 0; j < 3; j++) {
                            auto v = factor * (pm ? std::conj(gauge.at(ns, mu, j, a))
                                                  : gauge.at(fs, mu, a, j));
                            size_t k =
                                ((size_t)cb * 144 + (dir * 9 + a * 3 + j) * 2) * block_sites + s;
                            links[k] = v.real();
                            links[k + block_sites] = v.imag();
                        }
                }
            for (int a = 0; a < 12; a++)
                for (int v = 0; v < 24; v++) {
                    auto z = hierarchy.basis[basis_index(cb, ls, a, (a / 6) * 24 + v, hierarchy)];
                    size_t k = ((size_t)cb * 24 * 12 * 2 + (a * 24 + v) * 2) * block_sites + s;
                    basis[k] = z.real();
                    basis[k + block_sites] = z.imag();
                }
        }
    }
    // Derive contiguous source offsets from the actual local neighbor table,
    // not parity/geometry assumptions. Missing Dirichlet neighbors remain
    // masked by the kernel. Odd-volume legacy blocks keep the last site in
    // the second half. Nonuniform or empty directions use ordinary gathers.
    if (local_contiguous) {
        local_load_offsets.assign((size_t)(end_aggregate - first_aggregate) * 16, INT_MIN);
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; ++cb)
            for (int half = 0; half < 2; ++half)
                for (int dir = 0; dir < 8; ++dir) {
                    const int begin = half == 0 ? 0 : block_sites / 2;
                    const int end = half == 0 ? block_sites / 2 : block_sites;
                    const int *indices = inner.data() + ((size_t)cb * 8 + dir) * block_sites;
                    int delta = INT_MIN;
                    bool uniform = true;
                    for (int s = begin; s < end; ++s) {
                        if (indices[s] < 0)
                            continue;
                        const int candidate = indices[s] - s;
                        if (delta == INT_MIN)
                            delta = candidate;
                        else if (delta != candidate) {
                            uniform = false;
                            break;
                        }
                    }
                    if (uniform)
                        local_load_offsets[(size_t)(cb - first_aggregate) * 16 + half * 8 + dir] = delta;
                }
    }
    // Geometry and block colors do not change between operator applications.
    // Retain the exact ascending-block order of the former per-call lists;
    // using actual colors also handles odd spatial aggregate extents.
    if (native_size > 1) {
        for (int cb = first_aggregate; cb < end_aggregate; cb++) {
            const bool lower = cb < first_aggregate + aggregates_per_tslice;
            const bool upper = cb >= end_aggregate - aggregates_per_tslice;
            const int begin_t = lower ? 1 : 0;
            const int end_t = hierarchy.o.bt - (upper ? 1 : 0);
            if (begin_t < end_t) {
                fine_interior_work[0].push_back(cb);
                fine_interior_work[colors[cb] + 1].push_back(cb);
            }
            if (lower || upper) {
                fine_boundary_work[0].push_back(cb);
                fine_boundary_work[colors[cb] + 1].push_back(cb);
            }
        }
    }
    if (sap_eo)
        build_clover_inverse();
    if (!neighbor32.empty()) {
#pragma omp parallel for schedule(static)
        for (size_t k = 0; k < neighbor.size(); k++) {
            const std::ptrdiff_t value = neighbor[k];
            if (value < 0 || value > INT_MAX)
                throw std::runtime_error("global neighbor offset does not fit int32");
            neighbor32[k] = (int)value;
        }
    }
#pragma omp parallel for schedule(static)
    for (size_t k = 0; k < hierarchy.stencil.size(); k++) {
        coarse[2 * k] = hierarchy.stencil[k].real();
        coarse[2 * k + 1] = hierarchy.stencil[k].imag();
    }
    coarse_inverse.resize(aggregate_count * coarse_dof * coarse_dof * 2);
#pragma omp parallel for schedule(static)
    for (int cb = 0; cb < aggregate_count; cb++) {
        std::vector<Complex> a(coarse_dof * coarse_dof), inv(coarse_dof * coarse_dof);
        for (int i = 0; i < coarse_dof; i++) {
            inv[i * coarse_dof + i] = 1.;
            for (int j = 0; j < coarse_dof; j++)
                a[i * coarse_dof + j] =
                    hierarchy
                        .stencil[(size_t)cb * 9 * coarse_dof * coarse_dof + i * coarse_dof + j];
        }
        for (int k = 0; k < coarse_dof; k++) {
            int pivot = k;
            for (int i = k + 1; i < coarse_dof; i++)
                if (std::abs(a[i * coarse_dof + k]) > std::abs(a[pivot * coarse_dof + k]))
                    pivot = i;
            for (int j = 0; j < coarse_dof; j++) {
                std::swap(a[k * coarse_dof + j], a[pivot * coarse_dof + j]);
                std::swap(inv[k * coarse_dof + j], inv[pivot * coarse_dof + j]);
            }
            auto scale = a[k * coarse_dof + k];
            for (int j = 0; j < coarse_dof; j++) {
                a[k * coarse_dof + j] /= scale;
                inv[k * coarse_dof + j] /= scale;
            }
            for (int i = 0; i < coarse_dof; i++)
                if (i != k) {
                    auto factor = a[i * coarse_dof + k];
                    for (int j = 0; j < coarse_dof; j++) {
                        a[i * coarse_dof + j] -= factor * a[k * coarse_dof + j];
                        inv[i * coarse_dof + j] -= factor * inv[k * coarse_dof + j];
                    }
                }
        }
        for (int j = 0; j < coarse_dof * coarse_dof; j++) {
            coarse_inverse[((size_t)cb * coarse_dof * coarse_dof + j) * 2] = inv[j].real();
            coarse_inverse[((size_t)cb * coarse_dof * coarse_dof + j) * 2 + 1] = inv[j].imag();
        }
    }
    fine_rhs.resize(fine_sites * 24);
    fine_correction.resize(fine_sites * 24);
#if defined(LQCD_NATIVE_PACKED_WILSON)
    use_packed_coefficients =
        lqcd_native::kernels::wilson_simd_enabled() && setting("LQCD_WILSON_PACKED", 1) != 0;
    if (use_packed_coefficients) {
        const size_t tiles = ((size_t)block_sites + 15) / 16;
        packed_block_stride = tiles * 144 * 16;
        const size_t count = (size_t)(end_aggregate - first_aggregate) * packed_block_stride;
        packed_links.resize(count);
        packed_diag.resize(count);
        if (sap_eo)
            packed_inverse.resize(count);
#pragma omp parallel for schedule(static)
        for (int cb = first_aggregate; cb < end_aggregate; cb++) {
            const size_t dst_base = (size_t)(cb - first_aggregate) * packed_block_stride;
            const size_t src_base = (size_t)cb * 144 * block_sites;
            for (size_t tile = 0; tile < tiles; tile++)
                for (int plane = 0; plane < 144; plane++) {
#pragma omp simd
                    for (int lane = 0; lane < 16; lane++) {
                        const size_t site = tile * 16 + lane;
                        const size_t dst = dst_base + (tile * 144 + plane) * 16 + lane;
                        const size_t src = src_base + (size_t)plane * block_sites + site;
                        packed_links[dst] = site < (size_t)block_sites ? links[src] : 0.f;
                        packed_diag[dst] = site < (size_t)block_sites ? diag[src] : 0.f;
                        if (sap_eo)
                            packed_inverse[dst] =
                                site < (size_t)block_sites ? clover_inverse[src] : 0.f;
                    }
                }
        }
    }
#endif
}

void NativeMG::Impl::build_clover_inverse() {
    clover_inverse.resize(fine_sites * 144);
    int invalid = 0;
#pragma omp parallel for schedule(static) reduction(| : invalid)
    for (int cb = first_aggregate; cb < end_aggregate; cb++)
        for (int s = 0; s < block_sites; s++)
            for (int ch = 0; ch < 2; ch++) {
                Complex a[36], inv[36]{};
                double scale = 0;
                const size_t fs = lex[(size_t)cb * block_sites + s];
                for (int i = 0; i < 6; i++) {
                    inv[i * 6 + i] = 1.;
                    for (int j = 0; j < 6; j++) {
                        a[i * 6 + j] = gauge.clover[fs * 144 + (ch * 6 + i) * 12 + ch * 6 + j];
                        scale = std::max(scale, std::abs(a[i * 6 + j]));
                    }
                }
                bool bad = !std::isfinite(scale) || scale == 0;
                for (int k = 0; k < 6 && !bad; k++) {
                    int pivot = k;
                    for (int i = k + 1; i < 6; i++)
                        if (std::abs(a[i * 6 + k]) > std::abs(a[pivot * 6 + k]))
                            pivot = i;
                    if (!std::isfinite(std::abs(a[pivot * 6 + k])) ||
                        std::abs(a[pivot * 6 + k]) < 1e-14 * scale) {
                        bad = true;
                        break;
                    }
                    for (int j = 0; j < 6; j++) {
                        std::swap(a[k * 6 + j], a[pivot * 6 + j]);
                        std::swap(inv[k * 6 + j], inv[pivot * 6 + j]);
                    }
                    const Complex diagonal = a[k * 6 + k];
                    for (int j = 0; j < 6; j++) {
                        a[k * 6 + j] /= diagonal;
                        inv[k * 6 + j] /= diagonal;
                    }
                    for (int i = 0; i < 6; i++)
                        if (i != k) {
                            const Complex factor = a[i * 6 + k];
                            for (int j = 0; j < 6; j++) {
                                a[i * 6 + j] -= factor * a[k * 6 + j];
                                inv[i * 6 + j] -= factor * inv[k * 6 + j];
                            }
                        }
                }
                if (bad) {
                    invalid = 1;
                    continue;
                }
                for (int i = 0; i < 6; i++)
                    for (int j = 0; j < 6; j++) {
                        const float re = inv[i * 6 + j].real(), im = inv[i * 6 + j].imag();
                        if (!std::isfinite(re) || !std::isfinite(im))
                            invalid = 1;
                        const size_t index =
                            ((size_t)cb * 144 + ((ch * 6 + i) * 6 + j) * 2) * block_sites + s;
                        clover_inverse[index] = re;
                        clover_inverse[index + block_sites] = im;
                    }
            }
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &invalid, 1, MPI_INT, MPI_MAX, native_comm);
    if (invalid)
        throw std::runtime_error("EO SAP clover inverse is singular or nonfinite");
}

NativeMG::NativeMG(const Gauge &g, const Multigrid &m, MPI_Comm comm, unsigned seed) {
    native_comm = comm;
    native_seed = seed;
    MPI_Comm_rank(comm, &native_rank);
    MPI_Comm_size(comm, &native_size);
    int thread_level = MPI_THREAD_SINGLE;
    MPI_Query_thread(&thread_level);
    int insufficient =
        native_size > 1 && omp_get_max_threads() > 1 && thread_level < MPI_THREAD_FUNNELED;
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &insufficient, 1, MPI_INT, MPI_MAX, comm);
    if (insufficient)
        throw std::runtime_error(
            "native hybrid MPI requires MPI_Init_thread with MPI_THREAD_FUNNELED or higher");
    const char *setup_update = std::getenv("LQCD_SETUP_UPDATE");
    const std::string setup_mode = setup_update ? setup_update : "inverse";
    int invalid_setup = (setup_mode != "inverse" && setup_mode != "paper") ? 1 : 0;
    if (native_size > 1)
        MPI_Allreduce(MPI_IN_PLACE, &invalid_setup, 1, MPI_INT, MPI_MAX, comm);
    if (invalid_setup)
        throw std::runtime_error("LQCD_SETUP_UPDATE must be inverse or paper");
    const int setup_value = setup_mode == "paper" ? 1 : 0;
    int setup_min = setup_value, setup_max = setup_value;
    if (native_size > 1) {
        MPI_Allreduce(MPI_IN_PLACE, &setup_min, 1, MPI_INT, MPI_MIN, comm);
        MPI_Allreduce(MPI_IN_PLACE, &setup_max, 1, MPI_INT, MPI_MAX, comm);
    }
    if (setup_min != setup_max)
        throw std::runtime_error("LQCD_SETUP_UPDATE must agree on every MPI rank");
    const char *eo_env = std::getenv("LQCD_SAP_EO");
    const std::string eo_mode = eo_env ? eo_env : "1";
    int invalid_eo = eo_mode != "0" && eo_mode != "1";
    int eo_min = eo_mode == "1", eo_max = eo_min;
    int odd_bx = eo_min && (m.o.bx % 2 != 0);
    MPI_Allreduce(MPI_IN_PLACE, &invalid_eo, 1, MPI_INT, MPI_MAX, comm);
    MPI_Allreduce(MPI_IN_PLACE, &eo_min, 1, MPI_INT, MPI_MIN, comm);
    MPI_Allreduce(MPI_IN_PLACE, &eo_max, 1, MPI_INT, MPI_MAX, comm);
    MPI_Allreduce(MPI_IN_PLACE, &odd_bx, 1, MPI_INT, MPI_MAX, comm);
    if (invalid_eo || eo_min != eo_max)
        throw std::runtime_error("LQCD_SAP_EO must be 0 or 1 and agree on every MPI rank");
    if (odd_bx)
        throw std::runtime_error("LQCD_SAP_EO=1 requires an even x block size");
    const char *coarse_env = std::getenv("LQCD_COARSE_EO");
    const std::string coarse_mode = coarse_env ? coarse_env : "1";
    int invalid_coarse = coarse_mode != "0" && coarse_mode != "1";
    int coarse_min = coarse_mode == "1", coarse_max = coarse_min;
    MPI_Allreduce(MPI_IN_PLACE, &invalid_coarse, 1, MPI_INT, MPI_MAX, comm);
    MPI_Allreduce(MPI_IN_PLACE, &coarse_min, 1, MPI_INT, MPI_MIN, comm);
    MPI_Allreduce(MPI_IN_PLACE, &coarse_max, 1, MPI_INT, MPI_MAX, comm);
    if (invalid_coarse || coarse_min != coarse_max)
        throw std::runtime_error("LQCD_COARSE_EO must be 0 or 1 and agree on every MPI rank");
    int invalid_coarse_geometry = coarse_min && (m.cx < 2 || m.cy < 2 || m.cz < 2 || m.ct < 2 ||
                                                 m.cx % 2 || m.cy % 2 || m.cz % 2 || m.ct % 2);
    MPI_Allreduce(MPI_IN_PLACE, &invalid_coarse_geometry, 1, MPI_INT, MPI_MAX, comm);
    if (invalid_coarse_geometry)
        throw std::runtime_error("LQCD_COARSE_EO=1 requires even coarse extents >=2");
    impl = std::make_unique<Impl>(g, m, eo_min != 0);
    impl->coarse_eo = coarse_min != 0;
    impl->setup_update = setup_value ? SetupUpdate::Paper : SetupUpdate::Inverse;
    int profile = impl->halo_profile ? 1 : 0;
    MPI_Allreduce(MPI_IN_PLACE, &profile, 1, MPI_INT, MPI_MIN, comm);
    impl->halo_profile = profile != 0;
    int adaptive = impl->adaptive_correction ? 1 : 0;
    MPI_Allreduce(MPI_IN_PLACE, &adaptive, 1, MPI_INT, MPI_MIN, comm);
    impl->adaptive_correction = adaptive != 0;
    // These switches change the collective reduction sequence. Validate them
    // once at context construction so a rank-local environment typo cannot
    // deadlock the solver halfway through a solve.
    auto collective_binary_setting = [&](const char *name, int fallback) {
        const char *raw = std::getenv(name);
        const int value = raw ? std::atoi(raw) : fallback;
        int invalid = value == 0 || value == 1 ? 0 : 1;
        int minimum = value, maximum = value;
        MPI_Allreduce(MPI_IN_PLACE, &invalid, 1, MPI_INT, MPI_MAX, comm);
        MPI_Allreduce(MPI_IN_PLACE, &minimum, 1, MPI_INT, MPI_MIN, comm);
        MPI_Allreduce(MPI_IN_PLACE, &maximum, 1, MPI_INT, MPI_MAX, comm);
        if (invalid || minimum != maximum)
            throw std::runtime_error(std::string(name) + " must be 0 or 1 and agree on every MPI rank");
        return value != 0;
    };
    impl->coarse_empty_interior = collective_binary_setting("LQCD_COARSE_EMPTY_INTERIOR", 1);
    impl->coarse_fused = collective_binary_setting("LQCD_COARSE_FUSED", 0);
    impl->coarse_sve = collective_binary_setting("LQCD_ARM_COARSE_SVE", 0);
    (void)collective_binary_setting("LQCD_GCR_FUSED", 1);
    const char *hbw_raw = std::getenv("LQCD_HBW_ALLOC");
    const std::string hbw_mode = hbw_raw ? hbw_raw : "off";
    int hbw_value = hbw_mode == "off" ? 0 : hbw_mode == "prefer" ? 1 :
                    hbw_mode == "require" ? 2 : -1;
    int hbw_min = hbw_value, hbw_max = hbw_value;
    MPI_Allreduce(MPI_IN_PLACE, &hbw_min, 1, MPI_INT, MPI_MIN, comm);
    MPI_Allreduce(MPI_IN_PLACE, &hbw_max, 1, MPI_INT, MPI_MAX, comm);
    if (hbw_min < 0 || hbw_min != hbw_max)
        throw std::runtime_error("LQCD_HBW_ALLOC must be off, prefer or require and agree on every MPI rank");
    impl->hbw_policy = hbw_value == 2 ? lqcd_native::hbm::Policy::Require :
                       hbw_value == 1 ? lqcd_native::hbm::Policy::Prefer :
                                        lqcd_native::hbm::Policy::Off;
    impl->configure_solve();
}

NativeMG::~NativeMG() = default;
