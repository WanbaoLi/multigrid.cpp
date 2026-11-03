# Installed implementation and ABI evidence

Inspected read-only through `ssh ls`, 2026-11-03. The inspected SDK is a shared installation. Reading its header/binary does not mean a compute-node operation or performance experiment has succeeded.

Resolved SDK root:

```text
/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
```

The `latest` link resolved to this exact directory. Hashes and inspected line numbers are in [sdk-evidence.json](sdk-evidence.json). These facts identify the installed implementation; public rolling manuals describe newer APIs in several places.

## KUPL memory, copy and scheduling

`kupl/gcc/release/include/kupl.h` contains:

| Feature | Installed evidence | Implementation boundary |
|---|---|---|
| Memory allocation | `kupl_malloc(size_t)` / `kupl_free(void*)`, header lines 474/481; HBW counterparts lines 492/499 | Do not substitute newer memory-kind signatures; preserve allocator ownership on fallback/exception/move paths. |
| HBW validation | Lines 504–552: touch-pages flag, verification returns -1/error, 0/not entirely HBW, 1/entirely HBW; availability returns 0/1; only BIND policy exposed | Check the whole requested range after it is touched; record independent page residence where supported. |
| Copies | Lines 583–626: synchronous/async 1D/2D operations, pitches and widths in bytes | The presence of a function cannot establish SDMA availability. Queues/events require proper lifecycle and completion before destination use or buffer reuse. |
| Scheduling | Lines 342–437: executor discovery/groups, barrier, loop concurrency, STATIC/DYNAMIC/TASK policies | Current newer documentation adds struct fields not present here. MPI must stay on its authorized main thread; avoid oversubscribing OpenMP and KUPL pools. |
| Copy-worker concurrency | Lines 444–468 expose global and local kernel concurrency setters/getters | A return of zero can mean all workers, not no worker. Record actual worker affinity/concurrency. |
| Resources | Queue create/destroy/wait, event create/destroy/wait, task/static graph functions are declared | Persistent resources and reusable graphs are candidates; constructing them per small operation could erase benefit. |

Read-only binary examination of `libkupl.so.25.1.0.SPC001` was repeated. Dynamic symbols include the above HBW/copy APIs and unresolved NUMA helpers. In code around addresses `0x74e4`–`0x7548`, the library obtains `numa_get_mems_allowed`, checks each node's CPU-mask weight, excludes nonempty CPU masks, and excludes nodes absent from the allowed-memory mask. Remaining nodes become candidates; later code checks NUMA distances. `kupl_hbw_check_available` at `0x76f0` reads a cached availability value. This is evidence of **allowed memory-only node filtering**, not a public complete source listing or a claim of unsupported-chip detection.

This explains the historical Oct26 result when only CPU-memory nodes 0–15 were allowed. It does not predict a new allocation with allowed nodes 0–31. Re-probe in that changed condition. Historical details: repository `docs/kupl-hbw-optimization.md`; its old false-allocation results are not retested facts.

## KML BLAS arithmetic and variants

Inspected `kml/gcc/include/kblas.h`:

- Lines 20–25: `BLASINT` is `int` unless `USE64BITINT` selects `long`. Match the linked library's integer ABI; do not redefine it based only on matrix size.
- C++ complex fallback has real and imaginary components; API complex scalar/data arguments use pointers. Map storage explicitly and check size/layout when crossing from `std::complex<float>` or split real/imag fields. A split-complex array is not directly an interleaved BLAS array.
- Lines 83–107 expose `BlasSetNumThreads`, `BlasSetNumThreadsLocal`, corresponding getters and `BlasGetParallel`; header models include sequential, ordinary-thread, OpenMP and KUPL.
- `cblas_cgemv` appears at line 356, `cblas_cgemm` at 531 and `cblas_cgemm3m` at 566. Header search found **no** `gemm_batch` declaration. SVE single-thread locked library's exported symbols likewise contain ordinary complex GEMV/GEMM but no `cblas_*gemm_batch`.

The installation provides `neon/kblas/{locking,nolocking,multi}`, `sve/kblas/{locking,nolocking,multi}` and `sme/kblas/{locking,nolocking,multi}` directories. `sve512` also exists for other KML components; do not infer its BLAS path.

The installed `kml/gcc/env/setvars.sh` selects:

| Recognized CPU identifier | General math directory | BLAS directory |
|---|---|---|
| 0x48-0xd01 | neon | neon |
| 0x48-0xd02, 0xd03, 0xd06 | sve | sve |
| 0x48-0xd22 | sve512 | sme |
| Unrecognized fallback | neon | initialized neon default |

This is an observed loader decision, not independent hardware-model identification. The environment script defaults to multi-thread BLAS. Record the selected path inside the compute job, not just after loading on login. An explicit absolute library path plus hash and resolved dependencies makes A/B comparisons more reliable.

`readelf -d` on the inspected GCC SVE `locking` library lists libc, libm and the AArch64 loader, with no external OpenMP runtime dependency in that list. That does not by itself prove all variants thread-safe. Follow the variant contract and validate concurrent calls. The unlocked variant must not be assumed safe for concurrent OpenMP callers merely because it is single-threaded internally.

Read-only disassembly of its public `cblas_cgemv` entry shows interface checking/dispatch and temporary-storage setup before an indirect internal call (around `0x5f648`–`0x5f688`). It does **not** reveal a full documented internal kernel source or guarantee every size reaches an SVE kernel. Small-call overhead and packing therefore need measurement. Check the actual executed backend before labeling a KML result SVE/SME.

`kml_service.h` defines separate KML service settings including thread count and numerical behavior options. Do not enable zero-skipping, denormal suppression, alternate complex formulas or fast-math implicitly during a layout experiment: they can change rounding/iteration behavior and require their own recorded correctness/performance comparison.

## Reinspection commands

These commands read the shared SDK and do not execute kernels:

```bash
sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
sha256sum "$sdk/kupl/gcc/release/include/kupl.h" "$sdk/kml/gcc/include/kblas.h"
nm -D "$sdk/kml/gcc/lib/sve/kblas/locking/libkblas.so.25.1.0.SPC001"
readelf -d "$sdk/kml/gcc/lib/sve/kblas/locking/libkblas.so.25.1.0.SPC001"
objdump -d --disassemble=kupl_hbw_check_available "$sdk/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001"
```

These observations satisfy inspection of applicable installed interfaces and portions of the binary implementation; they do not imply complete proprietary source availability or runtime acceleration.
