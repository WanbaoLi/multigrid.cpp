# multigrid.cpp

CPU Wilson-Clover solver runtime with a stable C ABI and PyQUDA-compatible host
fields. Production backends are hardware targets (x86, arm, sw), not library
names. DDalphaAMG is an external reference adapter, not self-developed MG.
The user revised the current delivery target on 2026-11-05 to project-owned MG
under 15 seconds for one source's complete 12-column solve after hierarchy reuse,
on the real 24^3x64 fixture with full relative residual <=1e-8. The earlier
under-5-second research goal is not this delivery's acceptance requirement.
Previous DD wrapper timings do NOT satisfy this target. See `docs/roadmap.md` for scope
and `docs/backend-architecture.md` for field, normalization and MPI contracts.

- Public API: `include/lqcd.h`; implementation: `src/runtime/`,
  `src/solver/native/` contains the shared MG/SAP/Krylov/MPI implementation.
  Hardware factories/kernels live in `src/backends/x86/` and `src/backends/arm/`;
  portable Wilson mathematics live in `src/backends/portable/`. Python: `bindings/lqcd_cpu/`.
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

## GitHub alignment (user requirement, 2026-11-12)

- GitHub repository `https://github.com/WanbaoLi/multigrid.cpp` is the canonical
  record for this project's authored source, build/run scripts, configurations,
  tests and experimental implementations, including code used outside the main
  checkout on desktops or remote machines.
- Commit and push each code revision before distributing or running that revision
  elsewhere. Fixes require a new committed and pushed revision; do not leave an
  undocumented remote-only or desktop-only implementation. Include auxiliary
  experiment and validation scripts in the corresponding branch.
- Record the GitHub branch and exact commit for local exports, desktop deliveries,
  remote source checkouts and measured builds. Keep stable and experimental
  revisions distinguishable; do not overwrite a frozen stable snapshot with
  unrelated experiments.
- At delivery, push all changes made for the task and verify that the remote
  branch resolves to the intended commit. If upload fails, report the pending
  revision and failure instead of claiming GitHub alignment. Preserve unrelated
  work in a shared workspace; do not silently publish another task's unfinished
  changes.
- Keep large input configurations, propagator arrays and platform binaries out
  of the source repository; preserve their source commit and integrity metadata.
  Retain original provenance for any downloaded third-party source.

## Repository layout (user requirement, 2026-11-13)

- Keep only build metadata, README, agent instructions and license notices at
  the root. Reference manuals belong in `docs/reference/`.
- Keep the project's `LICENSE` at the root; third-party provenance and license
  explanations belong in `docs/third-party.md`.
- `include/lqcd.h` is the installed public C header. Keep implementation
  headers next to their sources in `src/`; do not restore `include/lqcd/`.
- Python bindings live in `bindings/lqcd_cpu/`; use `bindings` as `PYTHONPATH`.
- Do not commit raw test logs, CMake caches, binaries or one-value residual
  copies. Store structured validation and timing summaries in `experiments/`
  and keep full run outputs outside the source checkout.
- Historical manifests retain original paths and hashes; see
  `experiments/README.md` for the pre-cleanup source commit.
