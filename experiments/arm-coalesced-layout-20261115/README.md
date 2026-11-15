# ARM coefficient tiling campaign

Status: implementation candidate, not promoted; compute-node validation pending.
Base: `develop` at `141db3982afdbf3f64dd025831bc9edd6adbaa1e`.
Frozen `skills/kunpeng-lqcd-reference/manifest.json` verified before edits.

## Evidence and hypothesis

The input is already converted from PyQUDA DR fields to aggregate-major,
component-major spinors, with contiguous sites and separate EO halves. Gauge
and Clover coefficients similarly have 144 real planes per aggregate. SVE
loads coefficient planes contiguously, but the 864-site aggregate separates
adjacent planes by 3456 bytes. A 16-site Wilson tile touches 144 distinct plane
fragments in each matrix. Neighbour spinors still require gathers. Thus this
experiment does not claim the input was previously unvectorized.

Archived `profile150-complete` measured Wilson-related work and 40--43% GOMP
user-cycle samples at two ranks; these are neither whole-node wall fractions
nor measured memory bandwidth. Small-loop scheduling is a competing bottleneck.
The old half-block contiguous-source plan and transfer-vectorization trials
did not show stable end-to-end gains. This candidate changes **coefficient
layout**, with existing projection reuse retained, rather than repeating flags.

Trial A: store rank-owned links, Clover and Clover inverse as
`[site/16][144 real planes][site%16]`, using the existing x86 packer's exact
layout and keeping its independent kernels intact. This groups a matrix tile
into 9 KiB and limits vectors to tile boundaries at every SVE length. Clover
visits all output components within the tile. Pack once in setup, retain the
raw arrays for fallbacks, allocate the packed hot arrays through the existing
KUPL policy/cap and verify their residency. Extra packed storage and setup copy
cost are reported separately; no solve-time repacking is permitted.

Risk: more address arithmetic, smaller runs on longer SVE lengths, poorer
spinor/output locality, and packing may not matter if gathers or GOMP dominate.
Arithmetic order per output, source index policy, spin projection, boundary
conditions, stopping criterion and external fields are unchanged.

## Reproduction and numerical gates

Commit and publish this revision before remote execution. On an exclusive
592-core compute allocation, invoke:

```bash
bash tools/optimization/run_arm_packed_comparison.sh /ABS/NEW_OUTPUT_ROOT /ABS/GAUGE24.lime
```

The tracked runner performs baseline / packed / baseline on the **same node**,
with fresh native builds and CTest, and independently checks saved one-column
and twelve-column results through the original scalar executable. Each context
reads the real 24^3x64 gauge, smears once, builds once, then reuses its hierarchy
for three zero-start samples per solve width. The first is warmup; retain both
steady samples. No smear, I/O, packing or setup belongs in solve timings.

16 time-slab MPI ranks, one per NUMA domain; setup 37 allowed physical workers,
solve 32 workers, block 6x6x6x4, two RHS per batch; relative full residual
<=1e-8 in every column. Keep solver-only, API, first/second/steady, correction
counts and independent reference residuals distinct. A final diagnostic full12
records stage times outside ranked measurements. Baseline brackets diagnose
drift. A single packed sample is not a global optimum.

New kernel CTests compare random packed coefficients with the portable Wilson
oracle and double-accumulated Clover, including holes, unaligned ranges, tails,
compact/wide indices and hopping alias on disjoint EO halves. Absolute local
tolerance 2e-5 follows existing float kernel gates; complete propagation must
still meet the independent double true-residual gate. MPI tests additionally
cover the activated packed backend and mixed batch12 under shared coefficients.

Rollback: leave `LQCD_ARM_WILSON_PACKED=0` (the default), or use the unchanged
`lingsheng-shared-uniform.json` production profile. Best correct implementation
is not replaced unless matched complete-solve evidence supports promotion.

## Reusing an already qualified build

`tools/optimization/run_arm_packed_reuse.sh FROZEN_SOURCE CHECKED_BASELINE NEW_ROOT GAUGE`
continues from a completed original baseline without rebuilding or repeating the
same CTests. It requires the same physical node, clean frozen source at the
recorded commit, a completed independent baseline gate, candidate-on MPI/kernel
CTest evidence, and successful checks of the recorded executable/library hashes.
It then runs packed and original contexts with the same compiled binary. Set
`LQCD_CONTROLLER_COMMIT` to the published controller revision. Metadata keeps
controller and compiled-source provenance separate and labels reused CTests.
The checked baseline is linked into the fresh comparison directory; interrupted
outputs remain in their original directory. New solves retain independent
13-column scalar residual checks and all warm/steady timing samples.
