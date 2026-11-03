---
name: kunpeng-lqcd-reference
description: Apply frozen official KUPL, KML, Arm SVE/SME and Linux NUMA references when optimizing the multigrid.cpp Wilson–Clover solver on LingSheng Kunpeng compute nodes. Use for library/ISA/memory/scheduling decisions; keep experiment records outside this reference skill.
---

# Kunpeng LQCD reference snapshot

Frozen reference date: 2026-11-03. This skill contains reference facts and applicability boundaries, not a changing optimization journal. Verify `manifest.json` before use. Keep this tree read-only after sealing; place source experiments, observations and retry decisions in the campaign directories. New documentation or SDK versions require a separately versioned reference snapshot, not an edit to this one.

Read [official sources](references/official-sources.md) for authoritative API/ISA rules, [installed SDK](references/installed-sdk.md) before calling KUPL/KML, and [hardware constraints](references/hardware-constraints.md) before choosing vector length, thread placement or memory policy. `references/sdk-evidence.json` records versioned file hashes and inspection methods.

## Decisions this reference changes

- Compile and probe on the allocated **compute node**. `ssh ls` reaches an older login CPU; native flags, reported vector width and NUMA topology there do not identify the target. Record actual allowed CPUs/memory nodes, HWCAP and per-thread vector length in every allocation.
- Installed HPCKit is **25.1.0.SPC001**. Public current manuals describe later APIs. In this installation `kupl_malloc(size_t)` has one argument; a newer example with a memory-kind argument is incompatible. Likewise the installed `kupl_parallel_for_desc_t` lacks newer `field_mask` members. Build against the inspected installed header, not a transcribed current example.
- Installed KML has `cblas_cgemv` and `cblas_cgemm`, but inspected 25.1 headers/SVE library do **not** expose `cblas_*gemm_batch`. A current batch-GEMM manual is an idea source, not evidence that the installed symbol exists.
- A 48-component complex coarse vector can use KML complex GEMV if matrix order, conjugation, scalar type and packing match exactly. Include packing, call overhead and any temporary copies in the experiment. First compare one BLAS thread per existing OpenMP worker with a safe library variant. Do not create nested full-node BLAS teams for each small matrix. Persist coefficient packing across solves when valid.
- KUPL offers persistent task graphs, executor groups, parallel loops and copy queues. These make scheduling/fusion/pipelining candidates possible; merely replacing OpenMP syntax is not evidence of a gain. Preserve MPI main-thread/funneled contracts and account for any second thread pool.
- `kupl_memcpy_async` names an API, not proof of hardware overlap. Public documentation describes synchronous fallback methods and says true asynchronous copy depends on SDMA. Require a successful compute-node capability check, an actually used backend, correct queue/event dependencies and an overlap experiment before claiming transfer/computation overlap.
- KUPL high-bandwidth allocation requires both available allowed nodes and actual allocation/residency evidence. `kupl_hbw_malloc` pairs only with `kupl_hbw_free`; a null allocation means that path was not used. After touching an owned buffer, `kupl_hbw_verify(ptr, bytes, 0)` returns 1 only when the whole range is classified as HBW. Memory-only topology alone does not prove a particular memory technology.
- SVE width is scalable and per thread. Keep predicates for tails/holes and index-range guards. A compile-time SVE macro does not prove runtime execution or speed. SME has distinct streaming mode, vector length, ZA state and calling conventions; SVE support or a 512-bit width alone does not justify hand-emitting SME instructions.

## Applying the facts to a campaign

Before each attempt read the writable history and current profile. State the bottleneck, one proposed change, expected mechanism, correctness checks and full-12-column comparison. If retrying a failed idea, identify what changed. Historical failures and local microbenchmarks help choose experiments; only matched, repeated **complete 12-column propagation API** timings with reliable independent numerical validation can promote a best version.

The project already has a portable/reference Wilson–Clover path, NUMA launcher, full residual checks, tests and KUPL HBW fallback. Reuse them. KML BLAS is an optional arithmetic backend candidate, not permission to relabel an external solver as the project's own multigrid algorithm. Preserve source normalization, boundary conditions, zero initial guesses and all 12 columns.

No speedup is promised by this skill. Facts here distinguish official API rules, observed installed implementation, historical project evidence and untested hypotheses; keep that distinction in future reports.
