# Hardware constraints and application mapping

Reference snapshot: 2026-11-03. Reconfirm volatile allocation facts before every measurement. Public Arm/GCC/Linux rules are linked in [official sources](official-sources.md); current site observations below come from this task's saved compute-node probes, not the SSH login host.

## Observed compute topology

The task's `cn22801` compute probe reported 608 physical cores, two sockets of 304 cores, one hardware thread per core, 16 CPU NUMA domains with 38 cores each and 16 memory-only NUMA domains. Allowed CPU sets gave 37 application cores per CPU domain, totaling 592. System-reported maximum frequency was 2 GHz; this is not an all-core measured frequency. SVE, SVE2 and SME flags were visible; current SVE vector length was 64 bytes. This is 16 single-precision or 8 double-precision lanes, but it does not establish vector instruction throughput, memory bandwidth or floating-point peak.

Evidence file relative to this workspace root: `outputs/performance-20261103/raw-arm/perf-20261103/ab-host.json`, SHA256 `3469dfd76ea445ae7df77e29d3dc9cac9b8fc093493182e2623437dd6a7442ad`.

That allocation allowed memory nodes **0–31**, unlike older Oct26 jobs limited to 0–15. A new KUPL availability/allocation/residency experiment is justified by that changed condition. It still must establish what memory type is accessible and where the data resides. The probe alone does not verify HBW classification, flat/cache mode or actual owned-page placement.

`login04` was an older Kunpeng CPU without the compute target's SVE/SME capabilities. Never compile native target code there and describe it as equivalent to compute-node native compilation.

## SVE and SME constraints

- Query Linux auxiliary-vector capabilities and `PR_SVE_GET_VL` in the actual worker context. A CPU/model label or compilation macro is not sufficient runtime detection.
- Use `svcntw`/`svcntd`-based stepping for scalable kernels; predicates must protect tail lanes, missing neighbors and parity-disjoint alias ranges. Width-specific optimization can be separately compiled and dispatched only to compatible vector lengths. Preserve the fallback.
- Do not infer “512-bit means equal throughput to AVX512”. Independent hardware/compiler/code properties include load/gather throughput, register pressure, address generation, arithmetic issue rate and frequency.
- SME adds streaming mode and separate vector length/ZA state. Keep ordinary C ABI boundaries correct; do not leave a caller unexpectedly in streaming mode or pass vector-length-dependent values across incompatible mode boundaries. Compiler ACLE feature support must be confirmed by a small compile/run/disassembly check on the intended target. Hardware flags do not retrofit SME intrinsics into GCC 10.3.
- A KML `sme` directory or a successful `dlopen` is not proof that a complex GEMV or GEMM size uses SME. Require correct output plus executed instruction/backend evidence when making that claim.

## NUMA, cache and memory constraints

CPU affinity and memory placement are separate. Record allowed memory nodes, requested policy, actual sampled pages, and per-domain owned-data bytes. Global hierarchy/setup replicas can exceed a small fast-memory domain's capacity; putting the entire process there is not a valid default. Prefer a bounded owned hot-data allocation or panel staging experiment with an explicit fallback and lifecycle.

For a staged copy/compute pipeline, identify which data is reused, copy distance, panel bytes, transfer time, useful compute time and dependency ordering. The next panel may copy while the current panel computes only if source/destination buffers are not concurrently reused. Two buffers alone do not guarantee overlap; measure trace/timing with and without the dependency-safe pipeline. Include final drain and copies in complete solve time.

Hardware cache capacities and effective working set differ from logical vector-array bytes. A logical triad rate is not measured DRAM bandwidth. Distinguish memory controller evidence from cache hits, write allocation, first touch and thread-launch overhead.

## Mapping to the current multigrid program

For the real 24×24×24×64 lattice, block dimensions 6×6×6×4 produce 1024 aggregate blocks globally. With 16 time-slab MPI processes, each has 64 blocks and one coarse time plane. A two-color SAP sweep has 32 local blocks of the active color. A 37-thread team consequently has insufficient independent block tasks to keep all threads busy in that stage. This geometry is a source fact, not a proof of any single overhead's measured share.

Coarse vectors have 48 complex components per coarse site, hence 6144 real floats per process in this layout. Current serial-threshold vector operations and collective reductions can dominate as fine work shrinks. Reasonable evidence-based candidates include coefficient reuse across RHS, fused small operations/loops, persistent worker teams, coarse-kernel layout, and reducing global synchronization while preserving the solver's numerical contract. A generic 48-by-48 BLAS call is only one candidate; repeated tiny dispatch and packing can make it slower than a fused custom kernel.

Before reattempting the old `LQCD_ARM_SVE_PLANNED` or `LQCD_ARM_SVE_TRANSFER` directions, read repository `docs/kunpeng-hpc-optimization.md` and the current campaign history. They improved some local work but had little whole-solve benefit at high thread counts. A changed layout, new compiler, different profile bottleneck or lower thread count can justify a specific retry; a new parameter value without a mechanism does not.

KUPL copy/task functions can help only where data dependencies and actual profile permit. Existing MPI halo overlap uses the MPI main thread and workers on interior points; neither KUPL nor SME removes that contract. With only one coarse time plane there is no coarse interior region in the current time-only decomposition, so hiding coarse halo behind nonexistent interior work is not an implementation plan.

The final metric remains a **measured complete 12-column solve**, zero guess for every column, same physics/input/normalization/precision threshold, same allocated-node resource accounting. Report setup and validation separately. Keep local kernel timings as supporting evidence and never promote a candidate solely from them.
