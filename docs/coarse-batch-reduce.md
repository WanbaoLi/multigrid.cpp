# Independent RHS coarse reduction candidate

Status: opt-in implementation; no LingSheng performance promotion. The default
`LQCD_COARSE_BATCH_REDUCE=0` retains the established scalar coarse solver.

## Evidence and hypothesis

The completed 018 diagnostic recorded 40,652 `MPI_Allreduce` calls per rank for
one complete 12-column solve. That count covers the whole solver, not just the
coarse layer. Its 14.1-second mean accumulated reduction duration includes rank
arrival imbalance and measurement perturbation; it is not an additive estimate
of recoverable wall time. Ordinary 018 timings were also slower than the
uninstrumented 016 control. The candidate therefore tests a mechanism rather
than promising that duration as a speedup.

The existing batched V-cycle restricts several independent right-hand sides
(RHS), then completes each coarse solve in sequence. The candidate advances
their coarse GCR states together and packs independent dot products into one
reduction. This can remove collective startup/arrival costs while retaining
each RHS's arithmetic and convergence policy. It does not form cross-RHS Gram
matrices and is not a block Krylov algorithm. MPI remains on the calling main
thread, after OpenMP regions have joined.

The frozen `skills/kunpeng-lqcd-reference/` snapshot was reviewed. This change
adds no KUPL/KML dependency, vector-length assumption or new OpenMP pool. The
previous team-cap probe showed that repeated GNU OpenMP team changes can be
expensive; the supported batch uses one existing `CoarseThreadScope` around
the whole coarse batch and restores the caller's thread-count setting.

## Supported path and preserved behavior

Enable dynamically on an existing hierarchy with:

```sh
export LQCD_COARSE_BATCH_REDUCE=1
export LQCD_RHS_BATCH=2       # Also supported: 1 through 12.
```

The first implementation runs only when all of the following hold:

- More than one RHS remains active in the V-cycle.
- `LQCD_COARSE_EO=1` selects the even-odd coarse representation.
- `LQCD_COARSE_CGS2=0` selects modified Gram-Schmidt.
- `LQCD_GCR_FUSED=1` selects the existing fused GCR update.

Other valid configurations call the existing scalar coarse solver. A scalar
V-cycle already bypasses the batch routine. With the new flag disabled, the
original loop in `batched_cycle.cpp` still calls the unchanged scalar code.
The numerical bodies of the old scalar GCR and its fused step are unchanged.

Every RHS owns its reduced source, residual, solution, paired search/image
histories, source norm and residual norm. Zero sources retain zero solutions.
The iteration cap remains `LQCD_MG_COARSE_IT` (default 40); the restart remains
16 directions. A RHS that converges, breaks down, or refreshes its residual
does not force another RHS to stop or reset its history. Actual residuals are
recomputed at the same convergence/restart trigger as the scalar EO solver.

At each modified Gram-Schmidt direction index, local projections for active
RHS values are packed into a double vector and globally summed once. Each RHS
applies that projection before its next projection. The direction norm and
two complex-dot components are likewise packed, followed by the norm of the
actually rounded updated float residual. Residual refresh norms are packed
only for RHS values requiring a refresh. Norms and projections contain owned
coarse entries only. Halo exchange and matrix applications still finish one
RHS at a time in ascending RHS order; all existing halo calls, scratch buffers,
and message tags remain unchanged.

All active-set, breakdown and restart decisions depend on globally reduced
scalars, so all ranks execute the same collective order. Per-solve collective
tuning validation now includes both the new binary flag and `LQCD_GCR_FUSED`:
the latter was already dynamic in Python and determines this path's collective
sequence. The existing three validation collectives carry two extra doubles;
their count is unchanged. Invalid values or disagreement between ranks fail
before solver communication and leave the context reusable.
Validation also checks that `strtod` parsing agrees with the existing
`setting()->atoi` execution branch. For example, rank 0's `1e-400` and rank 1's
`0` both parse as the double zero, but `atoi` would select different branches.
Such underflow/rounding ambiguity is rejected collectively.

The local scalar loop order, precision and OpenMP thresholds are copied into
new helper functions rather than refactoring the old implementation. A longer
MPI reduction vector may select a different reduction tree and alter final
rounding. Bitwise equivalence is therefore not assumed. All acceptance still
requires the independent double full-operator residual gate.

## Validation and acceptance

`test_coarse_batch_reduce.py` uses a literal NumPy Wilson stencil and known
solutions on a unit gauge; it does not use the runtime operator as its oracle.
It checks widths 1, 2, 4 and 12, random/smooth/localized/oscillating/dependent
sources, mixed and all-zero sources, batch width changes on one hierarchy,
repeated contexts, team-cap restoration, CGS2/unfused/non-EO fallback, invalid
flags, rank disagreement, parser ambiguity and recovery after errors. Full residuals must be at
most `1e-10`; relative solution differences from known solutions and scalar
results must be below `1e-8`. Unchanged fallback results must agree below
`1e-12`. External zero columns also test outer active-set compaction; they do
not by themselves prove that the internal coarse-zero-source branch ran.

CTest adds `coarse_batch_reduce_serial`, `coarse_batch_reduce_mpi2`,
`batch12_coarse_reduce_mpi2`, and `runtime_batch_coarse_reduce`, and extends
`mg_tuning` invalid-value coverage. The existing 12-column and runtime-batch
tests exercise partial tails, duplicate columns, repeated solves, public API
strides and error recovery with the candidate enabled. Restart/cap behavior
also needs real-fixture validation: the small synthetic test does not promise
that every RHS reaches the 16-direction coarse restart.

With `LQCD_VERBOSE=1`, only rank 0 emits `native coarse batch reduce` JSON
records. They report attempted coarse iterations, 16-direction restarts,
actual-residual refreshes and cap exits for each RHS, plus the number of packed
reduction rounds and actual `MPI_Allreduce` calls. Serial runs have zero MPI
calls. These counters add no solver decisions. The public test captures this
evidence with coarse tolerance `1e-4` and caps 1/40/200, asserts an observed cap
exit, and explicitly reports whether restarts and staggered stops/refreshes
were observed. An unobserved branch remains a coverage limitation. Ordinary
performance runs keep verbose output disabled.

Run from a configured Linux build with NumPy, mpi4py and (for `runtime_batch`)
the existing PyQUDA test dependencies:

```sh
ctest --test-dir BUILD --output-on-failure -R \
  'coarse_batch_reduce|batch12_coarse_reduce|runtime_batch_coarse_reduce|mg_tuning'
```

`BUILD` means the build directory configured with `LQCD_BUILD_RUNTIME=ON`,
`BUILD_TESTING=ON` and `LQCD_TEST_PYTHON` naming its Python interpreter.

Local WSL x86 Debug and Release compilation with GCC 14.2/OpenMPI succeeded.
The WSL runtime condition blocked numerical execution: a restart cleared the
initial `/tmp` build/dependency directories, and subsequently even a two-rank
`hostname` launch stalled before creating application processes. The temporary
cache and logs from that attempt were removed from the production tree. No MPI
numerical pass is claimed. Local x86 tests, when available, validate algorithm
and communication logic; they cannot establish Arm/SVE behavior or enter
performance rankings.
LingSheng candidate-enabled runtime tests and real-gauge precision/performance
remain pending. The first test draft used an invalid 4-site extent with
2-site blocks; review corrected it to the existing legal 8-site geometry
before numerical execution. Backend geometry constraints are unchanged.

Before promotion, run the existing independent real-gauge 12-column verifier
with the unchanged `1e-8` double full-residual and solution-alignment gates.
Then compare matched repeated complete 12-column API timings against the
current best, with the same hierarchy, binary, topology, vector length, HBW
policy and thread placement. Include first/warm/steady samples; use PMPI only
in a separate diagnostic run to verify which reduction counts were removed.
Do not rank instrumented profile durations.

Keeping simultaneous histories increases coarse workspace approximately in
proportion to active batch width. Wider batches may lose cache locality or
increase allocation costs even when they remove more collectives. A failure
should first separate numerical/work-count changes, reduction-count savings,
workspace/cache effects and load imbalance before any retry. Only measured
full-solve improvement can justify enabling this candidate in a best version.
