# Single-node real-input health check, 2026-11-13

The node5005 checks used source revision
`37a79c5c57062fe8876b3176450d2fd26f3ec307`; the LingSheng job used
`dcae64a28beafdfc43e1c00e743a2b09fa1e8c81`. Both contain the same solver and
health driver; the latter additionally contains the resource-aware submission
and memory preflight wrapper.
The node5005 shared library was built at `1ddd69b`, before those wrapper-only
updates; `src/`, `include/` and `bindings/` are unchanged across these revisions.
Each case read one LIME gauge, applied one stout pass, built one hierarchy, then
timed three zero-start single-column solves and three zero-start complete
12-column solves. Stout and setup are reported separately and excluded from the
solve timings. Every measured output was independently checked with the scalar
reference at true relative residual `1e-8`; the single-column result and the
first full12 column also matched exactly in the saved fields.

| Machine | Geometry | MPI × placement threads | Solve threads | Block | Mass | Clover | Warm single | Warm full12 | Max independent residual |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| node5005 | 24³×64 | 16×16 | 12 | 6×6×6×4 | -0.277 | 1.160920226 | 0.692 s | 6.220 s | 9.170×10⁻⁹ |
| node5005 | 32³×64 | 16×16 | 12 | 8×8×8×4 | -0.279 | 1.1606789224 | 2.848 s | 30.132 s | 1.844×10⁻⁹ |
| LingSheng | 24³×64 | 16×37 | 32 | 6×6×6×4 | -0.277 | 1.160920226 | 1.158 s | 13.136 s | 4.819×10⁻⁹ |
| LingSheng | 32³×64 | 8×37, NUMA 0–7 | 32 | 8×8×8×4 | -0.279 | 1.1606789224 | 22.668 s | 345.479 s | 4.876×10⁻⁹ |

The LingSheng C32 run used eight MPI ranks because the current non-shared
hierarchy has a large per-rank memory footprint. The job requested one node,
592 CPUs and 480000 MB; its C32 memory preflight used eight NUMA domains and
measured no swap or OOM. This is a correctness and capacity-safe run, not the
best full-node C32 performance configuration. Its timing must not be compared
directly with the 16-rank C24 run.

The LingSheng job ran 27 selected CTest cases before the real-input checks.
The node5005 runtime was built with GCC 14.4/Open MPI and the LingSheng runtime
with the site GCC/HPCKit toolchain. Results and verification JSON are retained
in `experiments/single-node-health-20261113/`; raw logs and large arrays remain
outside the repository.

## What the measurements say

For node5005, the C32/C24 full12 ratio is `30.132/6.220 = 4.845`. The site-volume
ratio is `(32/24)^3 = 2.370`, while the second-round mean iteration count rises
from 21.4 to 41.8. Their product is about 4.63, leaving only about 1.05
for the remaining per-iteration effects. The first cause is the C32 iteration
count, followed by the larger operator volume.

The diagnostic rank-0 local accumulated timers on node5005 were:

| Geometry | Restriction | Coarse | Prolongation | SAP | Mean outer iterations |
|---|---:|---:|---:|---:|---:|
| C24 | 0.086 s | 0.173 s | 0.070 s | 0.467 s | 21.4 |
| C32 | 0.426 s | 0.311 s | 0.352 s | 2.711 s | 41.8 |

These are rank-local accumulations from diagnostic calls, not an MPI wall-time
decomposition. They identify SAP and convergence quality as the first candidates
to test; they do not prove that SAP alone accounts for the full wall time.

The next bounded experiments should be:

1. Compare `LQCD_SAP_SCHEDULE=0` and `2` with the same batch size, CPU masks,
   three full12 rounds and independent residual checks. Schedule 2 exposes one
   task per block and RHS and may reduce same-color idle time when C32 has enough
   blocks. Promote it only if complete12 wall time improves.
2. Compare the current coarse tolerance `0.05` against `0.02` at fixed coarse
   iteration limit, recording setup separately, outer iterations, coarse/SAP
   diagnostics and full12 wall time. This tests whether the C32 iteration count
   is caused by coarse correction quality.
3. Test an explicitly documented eight-rank, two-NUMA-per-rank launcher on
   LingSheng only after recording CPU and memory masks and first-touch placement.
   The current NUMA launcher uses one rank per NUMA domain, so it cannot claim
   that topology today. The potential mechanism is two local coarse time planes
   per rank and fewer MPI boundaries; cross-NUMA memory traffic could erase the
   benefit.

Shared immutable setup coefficients are absent from this source revision.
The old LingSheng deployment at `a35c3a4` has archived independent C24/C32
residual checks, but that code is not part of the present `develop` history.
Restoring it could reduce C32 memory and setup replication and permit a larger
rank/core configuration. That restoration requires a new source commit and
current-version validation; the old deployment's timings must not be attributed
to this health check.
