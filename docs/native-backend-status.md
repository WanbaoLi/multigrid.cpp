# Native hardware backend status

The production runtime is project-owned aggregation MG. DDalphaAMG is an optional
**reference adapter** named `reference-ddalphaamg`, disabled by default. It is
compiled from `src/references/`, not `src/backends/`. `x86` and AArch64 `arm` are
hardware backends sharing one MG implementation. Sunway remains a planned target.

## Implemented numerical path

1. Clover-Wilson `D = I + T - kappa H`, external DeGrand–Rossi spin basis.
2. Seeded random near-null candidates, homogeneous red-black SAP smoothing.
3. Per-aggregate, per-chirality double-precision modified Gram–Schmidt, repeated
   twice, to construct 24 candidates and 48 chirally separated coarse DOF.
4. Direct project-owned Galerkin assembly `Ac=P†DP` as an onsite + 8-neighbor stencil.
5. Two adaptive passes; each applies three approximate inverse iterations using
   the previously constructed MG hierarchy, followed by reorthogonalization and
   Galerkin reconstruction. Setup reads no third-party null vectors.
6. V-cycle: coarse even-odd Schur GCR correction (onsite inverse, maximum40
   updates, restart16), with odd reconstruction and a relative tolerance .1
   measured against the original full coarse RHS. This is followed by two
   red-black SAP cycles: each fine block uses four MR iterations on the even
   Schur complement and reconstructs its odd component. Production defaults
   are `LQCD_SAP_EO=1` and `LQCD_COARSE_EO=1`; either flag set to zero selects
   its legacy diagnostic path.
7. Flexible right-preconditioned GCR in float, restart24; double-precision full
   residual updates and correction solves enforce the user tolerance. The float
   correction target is clamped to [1e-3,.1], using one half of the remaining
   relative tolerance budget. This avoids oversolving the last correction; the
   final full residual gate is unchanged. LQCD_ADAPTIVE_CORRECTION=0 selects the
   former fixed 1e-3 target for comparisons. Reported iterations sum all
   correction-solve updates.
8. Independent runtime full residual verification and external reference checks.

Fine fields use internal block-local even-odd packing; external PyQUDA EO-x
packing and the public full Wilson-clover equation remain unchanged. The fine
EO mode requires an even x block extent; other block extents can be odd.
The red-black domain geometry requires even aggregate counts >=4 in each
direction. Current production limits: two levels, isotropic lattice,
anti-periodic time, time-slab MPI decomposition, one active context/process.
Unsupported modes are explicitly rejected rather than being silently ignored.
Clover csw is configurable (including zero); the historical fixture used csw=1.
The complete LIME/stout/point-propagator workflow is documented in
[propagator.md](propagator.md).

## Hardware and transport

`src/backends/x86/wilson_kernel.hpp` implements half-spin projections, split
real/imag fields, site-wise OpenMP SIMD, block-local clover and gauge products.
`src/solver/native/` contains hierarchy construction, fine operator, SAP, coarse solver,
cycle, setup, solver, validation and halo profiling. `multigrid.hpp` is private and no
file calls an external solver. `src/backends/arm/` supplies its hardware factory,
NEON clover and portable Wilson dispatch. See [ARM validation](arm-backend.md).
The x86 build uses native CPU compiler optimization; no fast-math relaxation of
the residual gate is required.
Neighbour offsets are precomputed, eliminating integer division in the hopping
loop; local SAP retains 32-bit gathers and global indexing uses pointer-width
offsets. Each worker reuses half-spin scratch storage. SAP evaluates the global
image only on the block colour consumed by the current step.
Internal coefficient, index and scratch buffers use a 64-byte aligned allocator.
Individual rows are not assumed aligned when block sizes do not preserve that
alignment; odd-direction blocks and SIMD tails remain covered by tests.

MPI partitions complete aggregates along time. Fine float matvec uses two
nearest-neighbor physical-face exchanges (not entire aggregate planes). Fine
reductions reduce owned slices globally. Coarse Krylov vectors are rank-local;
restriction/prolongation are local and coarse matvec exchanges adjacent t planes.
Coarse dot/norm operations use global reductions rather than replicated vectors.

Both levels post nonblocking receives/sends. Under MPI_THREAD_FUNNELED, the MPI
main thread drives progress while OpenMP workers compute local interior work.
Fine work splits boundary aggregates into physical t slices, so only remote-dependent
faces wait; coarse work retains aggregate granularity. Single-thread or sufficiently
thin local domains have no useful overlap and remain correct. LQCD_HALO_OVERLAP=0 keeps the same packed
messages but waits before computation for a controlled comparison.
Boundary work is scheduled over a compact boundary list, so static scheduling
does not assign it only to the first/last few threads of a whole-domain loop.

The NUMA launcher discovers allowed physical CPUs and assigns one MPI process
per NUMA domain, with rank-local OpenMP counts and explicit places. Neither the
solver nor launcher assumes 88 cores. The launcher currently targets one Linux
host with Open MPI; arbitrary 4D partitions and multi-node launching remain future
work. See [代码阅读顺序](code-guide.md) and [native-runtime-usage.md](native-runtime-usage.md).

LQCD_HALO_PROFILE=1 prints optional per-solve fine/coarse timing and byte counters.
Each reported field is the independent maximum over ranks of local sums; wait
and computation overlap, so these fields must not be added as a wall-time total.
Diagnostics exclude setup and are disabled by default.

Production double fields are rank-local lexical t slabs. `double_operator.cpp`
uses double clover coefficients, half-spin hopping and nearest-neighbour halos
for both reliable updates and API final residuals. No full spinor is gathered
in the solve path. Distributed double norms/dots sum all owned entries and then
reduce collectively, keeping stopping decisions consistent across thread counts.
The independent scalar operator still checks the new double kernel during setup.

**Stage-1 memory/scalability limitation:** gauge, clover and Galerkin/basis setup
storage remain replicated across MPI ranks. Float fine workspaces retain global
index space, although only owned sites and required ghosts are initialized/read.
Setup still performs redundant global assembly. Local setup assets, compact fine
storage and a general multi-node topology remain future work; current single-node
timings do not establish multi-node scalability.

## Validation gates

- Distributed double kernel vs independent scalar reference (<2e-13).
- Random full-lattice float fine kernel vs independent double reference (<1e-6).
- Fine/coarse EO and legacy combinations, odd non-x aggregate extents and
  SIMD tails, independently checked on unit-gauge random fields.
- `R P` identity and `R D P` agreement (<2e-6 in float).
- Exact public full operator vs saved QUDA probe (<1e-11).
- Public API source preservation, zero source, layout conversions, MPI collectives.
- Every final solution has full double relative residual <=1e-8.
- Exported 12 columns independently checked by the old scalar C++ operator.

Historical benchmarks using imported basis or external DDalphaAMG are only
development comparisons, never the native acceptance record.
