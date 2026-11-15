# ARM coefficient tiling campaign

Status: Trials A and B completed and independently correct; no promotion.
Supplementary same-binary original-layout follow-up after B is resource-blocked
and queued, **not completed**. See `followup-pending.json` for the timestamped state.
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
Set `LQCD_LAYOUT_CASES=baseline-b` for a single original-layout follow-up after
a qualified packed context; its seed is explicitly named `checked-packed`.

## Trial B hypothesis: specialize dispatch

Trial A passed the independent 13-column residual gate but its warmed API
median was 14.8743 s, versus the first baseline's 14.5919 s. The final rank-0
diagnostic SAP sum increased from 5.84525 s to 6.15731 s; coarse timings did
not explain that increase. Await the second original baseline before ranking.
This is one negative result, not grounds to discard every coefficient layout.

Inspection of Trial A's generated ARM binary found the mixed local/global,
Clover/hopping packed dispatcher body was 0x3cd8 bytes with a 400-byte entry
stack frame. One accepted raw local SVE body was 0x8ac bytes with a 272-byte
entry frame. Different functions need different frames, so these numbers do
not by themselves prove the slowdown's cause. They justify a bounded codegen
experiment: specialize local/global and Clover/hopping at compile time, keeping
coefficient layout, arithmetic, allocation, vector length and physics fixed.
Compare resulting function sizes/frames, required CTest/MPI gates, independent
residuals and warmed complete12 timings. Do not promote from a smaller frame
or isolated kernel timing alone. Original Trial A binaries/results remain frozen.

## Completed Trial A bracket

`summary-A.json` is generated by the published reducer at `c552866`, from
completed independently verified original / packed / original runs on cn19672.
All three used **one identical binary** from source `820918f`.

| Case | Warm full12 native solver median | Warm full12 API median |
|---|---:|---:|
| Original before | 14.122205 s | 14.591878 s |
| Packed A | 14.402341 s | 14.874289 s |
| Original after | 14.486748 s | 14.992009 s |

The packed result is 0.684% slower than the mean original bracket; the original
medians drift by 2.548%. No stable benefit is demonstrated. The second original
SAP sum was 6.12488 s, close to packed A's 6.15731 s, so the first-baseline SAP
increase cannot be assigned wholly to layout or dispatch. Trial B is a bounded
codegen hypothesis test, not a confirmed root-cause fix. All 39 saved column
checks passed <=1e-8; output hashes differ, so no bitwise equivalence is claimed.

Job 2135811 completed the first baseline and all 34 required CTests (including
candidate-on MPI gates), then was deliberately terminated during the duplicate
packed build. No numerical failure is inferred from that scheduler FAILED state.
Continuation job 2136318 reused the qualified binary, completed both subsequent
contexts and succeeded. Frozen source/build files were not edited while running.
The vector-length probe job 2135942 succeeded on cn12038: all six 16/32/64-byte,
reuse-on/off cases passed. Its published controller is `86cc9af`; the binary is
from `820918f`. Trial B's frozen source is `c552866`, job 2136624.

## Completed Trial B and checkpoint

Job 2136624 succeeded on cn19672. All 34 selected CTests passed, including
the activated packed MPI2 and batch12 paths. `result-B.json` retains the real
health result, all first/second/steady samples, correction/iteration metadata,
the 13 independent scalar checks, parsed CTest evidence and diagnostic stages.
Its `original_health_result_sha256` identifies the unaugmented remote JSON.

Warm complete12 native median: **14.777750863 s**; API median: **15.264690465 s**.
Warm single native median: 1.3300427095 s; setup: 207.309983014 s.
Independent maximum residual: 4.818844220e-9, no outer API correction solves.
The final diagnostic SAP sum was 6.23564 s; coarse 4.812175 s. The diagnostic
is unranked and remains rank-0 local stage wall sums.

`codegen-A.json` and `codegen-B.json` were generated with the published inspection
tool at `ac2db0e`, after verifying AArch64 ELF machine type. Binary source revisions
are recorded separately. A's mixed body had 15576 bytes / 400-byte entry frame.
B split it into local hopping (3484 / 384), local Clover (4836 / 400) and global
Clover (7848 / 256). Different bodies include different dispatch alternatives;
these sizes are **not** dynamic instruction counts or proof of spill cost.
The selected symbols have zero static SVE fused-multiply-add sites. This is an
arithmetic candidate, not a measured compute/bandwidth-bound diagnosis.

Two rounds did not beat this campaign's best original-layout complete12 median
of 14.122205249 s. The native/API clocks, numerical gate and original source are
preserved in `best-known.json`. Its source archive is kept outside the repository;
no binary, configuration array or raw test log is committed.

Do not infer that every data-reordering direction is exhausted. The implemented
16-site scheme adds masked segments on unaligned time faces: an interior parity
range [108,324) has 15 vector segments versus the original's 14 at 16 float lanes;
the complete split block has 58 versus 56. SAP half-blocks are aligned. ARM
cross-RHS tile fusion was not implemented; it would be a distinct retry with a
new reuse mechanism. Full solve evidence, not static byte counts, must rank it.

The final same-binary original-layout follow-up uses controller `4f3392e`, frozen
source/library `c552866`, job **2137061**, requested cn19672/592 CPUs. At the
recorded checkpoint the node had another running job and only 342 CPUs free;
Donau could not grant an exclusive allocation. The queued script automatically
performs all solves and independent checks when granted the node. Expected output:
`/home/share/nsls_lwb/lqcd-run/arm-pack-20261115/run04/baseline-b/L24/result.json`.
This pending comparison is neither a passed test nor a completed optimization.
