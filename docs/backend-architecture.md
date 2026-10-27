# Hardware backend architecture

Public C ABI: `include/lqcd/lqcd.h`. CPU PyQUDA adapter: `python/lqcd_cpu`.
Runtime lifecycle/validation/layout: `src/runtime/`. Shared native algorithm: `src/solver/native/`; the private declaration is `src/solver/native/multigrid.hpp`. Hardware kernels/factories: `src/backends/x86/` and `src/backends/arm/`. Shared portable Wilson mathematics: `src/backends/portable/`.
External reference integration: `src/references/ddalphaamg/`, opt-in only.

```text
PyQUDA NumPy fields / C caller
            |
  C ABI + normalization/layout contract
            |
  runtime/context + hardware registry
            |
  common adaptive MG / SAP / Krylov / double reliable updates
            |
  x86 kernel policy + MPI transport
  ARM SVE/NEON/portable kernel policy + common MPI transport
  future Sunway worker executor + MPI transport
```

Both x86 and AArch64 ARM are implemented and selected at build time. Unknown/unbuilt hardware names fail. Library names are
not production hardware backends. The reference DD adapter is explicitly named
`reference-ddalphaamg` and is absent from the default production binary.

The public packing is PyQUDA EO-x or lex-tzyx, complex128, DeGrand–Rossi basis.
Normalization is explicit (`mass` or `kappa`); links are untwisted and the temporal
boundary is applied once. Calls are collective, MPI-main-thread-only, one live
runtime per process. No MPI action occurs from Python garbage collection.

The current native engine is two-level, with configurable finite csw, isotropic, antiperiodic time,
with complete aggregates partitioned in t. Unsupported modes are rejected.
The current C ABI allocates caller outputs through the Python adapter; source
preservation, repeated zero-start solves, zero RHS and column packing are tested.

MPI topology, host threading, SIMD width, NUMA policy and future offload workers
remain independent concerns. The current native MPI implementation has correct
halo/reduction semantics. Production double solver vectors and operator outputs
contain only owned lexical t slabs; reliable updates and final residual checks
use nearest-neighbour double halos, without full-spinor Allgather. Fine float
workspaces retain global indexing with only owned entries and received ghosts
initialized. Setup coefficients, gauge, clover and basis still use replicated
storage, so this is not yet a scalable multi-node memory model.

Fine-grid overlap splits the first/last aggregate at physical t-face granularity:
workers compute all slices whose neighbours are local while the MPI main thread
completes halo transfers. Only the two remote-dependent faces wait. The independent
scalar `multigrid` executable and the setup-only full scalar operator gate do not
use these production kernels.

See [完整中文源码导读](project-algorithm-guide.md), [代码阅读顺序](code-guide.md), [native-backend-status.md](native-backend-status.md) for exact algorithm,
transport and memory limitations, [numa-results.md](numa-results.md) for
current measured acceptance, and [native-runtime-usage.md](native-runtime-usage.md) for
build/API commands. Historical source and binary hashes in `numa-results.json` describe the measured 21 Oct version. Reference library comparisons live under `benchmarks/reference-libraries/`; they do not define the production backend.
