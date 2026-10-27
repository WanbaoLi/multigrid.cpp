#pragma once
#include "environment.hpp"
#include "batched_state.hpp"
#include "multigrid.hpp"
#include <cstddef>
#include "../../support/hbw_buffer.hpp"

using lqcd_native::detail::FloatField;
using lqcd_native::detail::HaloStats;
using lqcd_native::detail::setting;
using lqcd_native::detail::SetupUpdate;
namespace hbm = lqcd_native::hbm;

// Aggregate-major storage; method bodies are grouped by algorithm in .cpp files.
struct NativeMG::Impl {
    std::vector<BatchKrylovWorkspace> batch_workspace;
    std::vector<FloatField> batch_coarse_rhs, batch_coarse_correction, batch_sap_image;
    void fine_apply_batch(const std::vector<const FloatField *> &src,
                          const std::vector<FloatField *> &out, int color = -1) const;
    void apply_vcycle_batch(const std::vector<const FloatField *> &src,
                            const std::vector<FloatField *> &dst);
    void sap_batch(const std::vector<const FloatField *> &src,
                   const std::vector<FloatField *> &dst, int cycles);
    bool batch_gcr_update(BatchKrylovWorkspace &w);
    const Gauge &gauge;
    const Multigrid &hierarchy;
    int block_sites, aggregate_count, coarse_dof;
    size_t fine_sites;
    int first_aggregate, end_aggregate, aggregates_per_tslice;
    FloatField links, diag, basis, coarse, coarse_inverse, clover_inverse;
    hbm::Policy hbw_policy = hbm::Policy::Off;
    hbm::HbwBuffer hbw_links, hbw_diag, hbw_inverse, hbw_basis;
    hbm::HbwBuffer hbw_coarse_columns, hbw_coarse_inverse_columns;
    void prepare_hbw_assets();
    const float *hot_block(const FloatField &raw, const hbm::HbwBuffer &hot,
                          int cb, size_t stride) const {
        return hot ? static_cast<const float *>(hot.data()) + (size_t)(cb-first_aggregate)*stride
                   : raw.data() + (size_t)cb*stride;
    }
    const float *links_block(int cb) const { return hot_block(links, hbw_links, cb, 144ull*block_sites); }
    const float *diag_block(int cb) const { return hot_block(diag, hbw_diag, cb, 144ull*block_sites); }
    const float *inverse_block(int cb) const { return hot_block(clover_inverse, hbw_inverse, cb, 144ull*block_sites); }
    const float *basis_block(int cb) const { return hot_block(basis, hbw_basis, cb, 24ull*12*2*block_sites); }
    const float *coarse_column_block(int cb) const {
        const auto base = hbw_coarse_columns ? static_cast<const float *>(hbw_coarse_columns.data()) : coarse_columns.data();
        return base + (size_t)(cb-first_aggregate)*9*coarse_dof*coarse_dof*2;
    }
    const float *coarse_inverse_column_block(int cb) const {
        const auto base = hbw_coarse_inverse_columns ? static_cast<const float *>(hbw_coarse_inverse_columns.data()) : coarse_inverse_columns.data();
        return base + (size_t)(cb-first_aggregate)*coarse_dof*coarse_dof*2;
    }

    // Rank-owned coefficient tiles: [owned aggregate][tile][144 planes][16 lanes].
    // Raw arrays remain available for portable / pointer-width fallback paths.
    FloatField packed_links, packed_diag, packed_inverse;
    bool use_packed_coefficients = false;
    size_t packed_block_stride = 0;
    // Owned block / half / direction; INT_MIN requests ordinary gather.
    std::vector<int> local_load_offsets;
    bool local_contiguous = setting("LQCD_LOCAL_CONTIGUOUS", 1) != 0;
    // Component-zero float offsets for full hops. Pointer-width indexing
    // avoids integer division in the SIMD kernel without a 32-bit size limit.
    std::vector<std::ptrdiff_t, lqcd_native::WorkspaceAllocator<std::ptrdiff_t>> neighbor;
    // Compact global offsets for AVX512 gathers.  The 32-bit representation
    // is valid when the complete field fits in signed int32 float elements;
    // pointer-width neighbor remains the correctness fallback.
    std::vector<int, lqcd_native::WorkspaceAllocator<int>> neighbor32;
    std::vector<int, lqcd_native::WorkspaceAllocator<int>> inner, colors, cneighbor;
    std::vector<size_t, lqcd_native::WorkspaceAllocator<size_t>> lex;
    std::vector<int, lqcd_native::WorkspaceAllocator<int>> local_lex;
    // Immutable owned-block schedules: slot 0 = all, slots 1/2 = colors 0/1.
    std::vector<int> fine_interior_work[3], fine_boundary_work[3];
    bool sap_eo;
    bool coarse_eo = false;
    int gp[4][4];
    float gr[4][4], gi[4][4];
    FloatField fine_rhs, fine_correction, coarse_rhs, coarse_correction, sap_image;
    // Optional persistent coarse Schur workspaces. Default path remains the
    // allocation-based reference; owner may place these buffers in HBW.
    mutable FloatField coarse_schur_hop, coarse_schur_extended;
    bool coarse_fused = setting("LQCD_COARSE_FUSED", 0) != 0;
    bool coarse_sve = setting("LQCD_ARM_COARSE_SVE", 0) != 0;
    mutable bool coarse_pack_ready = false;
    mutable FloatField coarse_columns, coarse_inverse_columns;
    void prepare_coarse_columns() const;
    // Reusable outer workspaces. Every solve still zeros x and recomputes all
    // directions; retaining allocations does not retain an initial guess.
    FloatField outer_rhs, outer_solution, outer_residual, outer_image;
    Field reliable_residual, reliable_image, reliable_delta;
    std::vector<FloatField> outer_images, outer_directions;
    // Separate buffers keep active MPI sends immutable and disjoint receives
    // valid even when both periodic neighbours are the same rank.
    mutable FloatField send_lower, send_upper, recv_lower, recv_upper;
    mutable Field double_recv_lower, double_recv_upper;
    mutable FloatField coarse_send_lower, coarse_send_upper, coarse_recv_lower, coarse_recv_upper;
    bool halo_overlap = setting("LQCD_HALO_OVERLAP", 1) != 0;
    bool coarse_empty_interior = setting("LQCD_COARSE_EMPTY_INTERIOR", 1) != 0;
    bool halo_profile = setting("LQCD_HALO_PROFILE", 0) != 0;
    bool adaptive_correction = setting("LQCD_ADAPTIVE_CORRECTION", 1) != 0;
    bool float_correction_verify = false;
    bool fine_team_fused = true;
    bool coarse_cgs2 = false;
    double correction_base_tol = 1e-3, coarse_tolerance = .1;
    SetupUpdate setup_update = SetupUpdate::Inverse;
    bool profile_active = false;
    mutable HaloStats fine_halo_stats, coarse_halo_stats;
    void begin_halo_profile();

    void report_halo_profile();

    std::vector<FloatField> test_vectors;
    double restrict_seconds = 0, coarse_seconds = 0, prolong_seconds = 0, sap_seconds = 0;
    int sap_steps = setting("NATIVE_SAP_STEPS", 4), sap_cycles = setting("NATIVE_SAP_CYCLES", 2),
        coarse_it = setting("NATIVE_COARSE_IT", 40);
    Impl(const Gauge &gg, const Multigrid &mm, bool eo = false);

    // Validated collective tuning, also callable between independent solves.
    // Changing these values does not reuse an old solution or rebuild P/R.
    void configure_solve();

    void build_clover_inverse();

    void local_range(int cb, const float *src, float *out, int parity, bool clover) const;

    void clover_range(int cb, const float *src, float *out, int parity, bool inverse) const;

    void solve_sap_block_eo(int cb, FloatField &rr, FloatField &ar, FloatField &dx,
                            const float *source, const float *image) const;

    void verify_eo(const FloatField &probe) const;

    void block_apply(int cb, const float *src, float *out, bool local) const;

    // SAP consumes only the active color's image. Other blocks in out remain
    // untouched; the default computes the complete owned image for Krylov.
    void fine_apply(const FloatField &src, FloatField &out, int color = -1) const;

    // Local t-slab, lexicographic complex128; normalized identically to apply_dirac.
    void apply_double(const Field &localin, Field &localout) const;

    void sap(const FloatField &b, FloatField &solution, int cycles);

    void restrict_to_coarse(const FloatField &fine, FloatField &cr) const;

    void prolongate_add(const FloatField &cr, FloatField &fine) const;

    void coarse_block_apply(int cb, const FloatField &src, FloatField &out,
                            bool diagonal = true) const;

    void coarse_apply(const FloatField &src, FloatField &out, int color = -1,
                      bool diagonal = true) const;

    void coarse_diagonal(const FloatField &src, FloatField &out, int color, bool inverse) const;

    void coarse_copy_color(const FloatField &src, FloatField &out, int color) const;

    void coarse_schur(const FloatField &even, FloatField &out) const;

    void coarse_reduced_rhs(const FloatField &b, FloatField &reduced) const;

    void coarse_reconstruct(const FloatField &b, const FloatField &even, FloatField &out) const;

    void coarse_solve_eo(const FloatField &b, FloatField &out) const;

    void verify_coarse_eo(const FloatField &probe) const;

    void coarse_solve(const FloatField &b, FloatField &x) const;

    void precondition(const Field &b, Field &out);

    void encode_fine(const Field &b, FloatField &out) const;

    void decode_fine(const FloatField &in, Field &out) const;

    void apply_vcycle(const FloatField &source, FloatField &dest);

    Complex fine_dot(const FloatField &a, const FloatField &b) const;

    void fine_axpy(FloatField &y, Complex v, const FloatField &x) const;

    void fine_copy(const FloatField &source, FloatField &dest) const;

    int solve_float_gcr(const FloatField &b, FloatField &solution, double tol, int budget,
                        int restart);
};
