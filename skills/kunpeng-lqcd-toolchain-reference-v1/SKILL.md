---
name: kunpeng-lqcd-toolchain-reference-v1
description: Apply frozen GCC12 AArch64 and LLVM17 OpenMP references when comparing installed LingSheng compiler or runtime variants for multigrid.cpp; keep experiment results outside this skill.
---

# LingSheng toolchain reference

Frozen2026-11-04. Verify manifest.json; never append experimental results here.
New versions require another snapshot. Read [sources](references/sources.md)
and [site evidence](references/site-evidence.json) before choosing a toolchain.
The separate frozen kunpeng-lqcd-reference remains the source for KUPL/KML ABI,
SVE/SME and NUMA constraints; this snapshot does not replace those facts.

- Distinguish compiler from loaded runtime: the accepted052 library used GNU10.3.1
  while already loading SDK GCC12 GOMP/C++. Recompiling with GCC12 is a different
  experiment from selecting its GOMP library.
- Begin a compiler comparison with the same source, runtime paths, physics,
  algorithm, flags and resource plan. Native architecture queries/builds run on
  the allocated compute node. Preserve scalable SVE and test16/32/64-byte lengths.
  Inspect actual codegen and all loaded dependencies; version names do not prove
  speed, matching flags or SME execution.
- GCC12 enabling vectorization at-O2 does not explain a win over an-O3 baseline.
  Select a compiler experiment using actual hot code/codegen, then measure full12.
- LLVM's GOMP bridge source motivates ABI inspection, not a vendor-binary
  compatibility promise. Check imported symbols, symbol versions and relocation
  closure before mixing KUPL with libomp; verify actual single-runtime mapping
  and affinity. Changing compiler plus runtime is a combined experiment.
- Read the old BiSheng RNG/setup failure first. The observed long-double hotspot
  was in setup. Hierarchy reuse changes its priority, but the real allocation
  budget must still include setup; do not silently add fast-math or replace RNG.
- All compiler variants require their own numerical tests and independent full12
  residual/reference checks. Preserve iteration counts and hierarchy differences;
  a compiler's changed arithmetic or library headers can change setup results.

These are candidate-selection constraints, not evidence of a speedup. Reuse the
campaign ledger, accepted snapshots and rollback; ordinary complete12 comparisons
remain the promotion criterion.
