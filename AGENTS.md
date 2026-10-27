# multigrid.cpp

CPU Wilson-Clover solver runtime with a stable C ABI and PyQUDA-compatible host
fields. Production backends are hardware targets (x86, arm, sw), not library
names. DDalphaAMG is an external reference adapter, not self-developed MG.
The current acceptance target is project-owned MG under 5 seconds on the real
24^3x64 fixture with full relative residual <=1e-8. Previous DD wrapper timings
do NOT satisfy this target. See `docs/roadmap.md` for scope
and `docs/backend-architecture.md` for field, normalization and MPI contracts.

- Public API: `include/lqcd/lqcd.h`; implementation: `src/runtime/`,
  `src/solver/native/` contains the shared MG/SAP/Krylov/MPI implementation.
  Hardware factories/kernels live in `src/backends/x86/` and `src/backends/arm/`;
  portable Wilson mathematics live in `src/backends/portable/`. Python: `python/lqcd_cpu/`.
  External solver wrappers belong under `src/references/`, opt-in only.
- Production defaults include even-odd Schur solves in SAP blocks and the coarse
  solver. Legacy non-EO modes are diagnostic comparisons, not the default path.
- Rank topology and host thread counts are separate resources. Use the NUMA
  launcher/allowed physical CPUs rather than hardcoded core counts; changing
  threads after setup must remain collective and must not rebuild the hierarchy.
- The original `multigrid` executable is the independent numerical reference.
  Preserve that independent validation path while replacing/optimizing backends.
- No third-party structs in the public ABI. Keep setup, layout conversion,
  solver-only, full API and independent validation timings distinct.
- MPI topology, host threads, NUMA placement, SIMD ISA and offloaded workers
  are separate configuration concerns. Do not map Sunway worker counts blindly
  to OpenMP threads or claim untested target hardware support.
- External fields use DR spin basis and explicit mass/kappa normalization.
  Gauge links are untwisted; backend applies temporal boundary once.
- The native runtime currently permits one live context per MPI process. Context calls
  are collective and made on the MPI main thread; no MPI work in Python GC.
- Test changes with CTest (including MPI runtime tests when configured).
  Real-input acceptance uses `benchmarks/runtime/benchmark_runtime.py`; the 12-column path
  is independently checked by `benchmarks/runtime/verify_runtime_columns.py`.
- Performance results must pass true residuals and include zero initial guesses,
  thread/rank configuration, first/second/steady samples and whether correction
  solves occurred. Report bounded scans as best in the tested set, not global optima.
- Keep source/build/data artifacts and upstream license notices separate.
  Do not relabel the external backend as a newly authored MG algorithm.
