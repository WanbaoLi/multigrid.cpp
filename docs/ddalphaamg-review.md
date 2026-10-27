# DDalphaAMG paper and native implementation review

Reviewed and updated 2026-10-21. The initial audit covered the pre-overlap,
full-block-MR implementation; the status and measured follow-up below distinguish
that historical baseline from the current EO implementation.
The coarse Allgather observations below describe the pre-change baseline: the
current refactor has owned coarse Krylov vectors, local restriction/prolongation,
coarse nearest-neighbor halos, and global coarse dot/norm reductions. Fine and
coarse matvecs now have blocking and overlapped paths for measured comparison.
Fine local SAP EO and coarse Schur EO have both been implemented and validated
in all four on/off combinations and on the physical 24³×64 fixture. Both flags
now default to `1`; explicit `0` retains historical comparison paths. The latest
adaptive-correction factor is 0.5, and final acceptance of that latest setting
is still being rerun; the measured EO evidence below predates that factor change.

## Primary source and numerical interpretation

A. Frommer, K. Kahl, S. Krieg, B. Leder and M. Rottmann,
*Adaptive Aggregation Based Domain Decomposition Multigrid for the Lattice Wilson
Dirac Operator*, [arXiv:1303.1377v3, full paper](https://arxiv.org/pdf/1303.1377),
28 April 2014; first arXiv submission 6 March 2013.

The paper combines red-black SAP with adaptive aggregation. Locally coherent
slow components are represented by test vectors restricted to aggregates.
Chiral aggregates preserve gamma5 symmetry; local orthonormalization gives
P†P=I and the Galerkin operator Ac=P†DP (§3.2). A V-cycle first corrects the coarse
error, then smooths with SAP (§5). The coarse solve may be deliberately inaccurate;
a flexible outer Krylov method accommodates this changing preconditioner (§4.2).
Algorithm 5.1 improves the setup by updating each vector as
v ← v + C(v−Dv), followed by normalization, using the current V-cycle C.
The paper also observes that restriction/prolongation need no communication when
an aggregate belongs entirely to one process (§3.2).

## What the current project actually implements

The audit of the split files under `src/backends/x86/` and `src/backends/x86/multigrid.hpp` finds:

- Correct structural ingredients: chirally split 24-vector basis (48 coarse
  components), twice local MGS, direct RAP, coarse-first correction, red-black
  block Schur MR smoothing, coarse Schur GCR, flexible fine GCR and double
  full-residual correction. Full-block MR/full-coarse GCR remain comparison modes.
- The default adaptive update remains normalized `C(v)` three times per pass,
  with two passes. `LQCD_SETUP_UPDATE=paper` additionally implements Algorithm 5.1
  as `v+C(v-Dv)` followed by normalization, with collective mode validation.
  An earlier **full-block-MR** comparison at 2 MPI × 22 threads measured 3.829 s
  for paper update versus 3.713 s for inverse update, so inverse remains default.
  This does **not** compare EO+paper against EO+inverse; no such result is claimed.
- The reference-normalized fine operator is D=I+T−kappa H. The public mass
  convention multiplies this operator by (4+m). Source conversion and exported
  solution must use this same factor; do not rescale the result to minimize its
  difference from QUDA.
- SAP block geometry and aggregation geometry currently coincide. Their tuning
  is consequently coupled. Separating them is a future numerical/layout change,
  not a prerequisite for rank-independent OpenMP execution.
- The historical mixed-precision solve used a fixed inner reduction of 1e-3.
  The current adaptive target is `clamp(0.5*(tol/current_relative), 1e-3, 0.1)`;
  `current_relative` is recomputed using the complete double operator and
  collective norm after every correction. The earlier experimental factor was
  0.25. Neither factor changes the caller's final full-residual gate.

## Communication and ownership priorities

These recommendations follow from this project's data dependencies, rather than
claiming the paper prescribes a particular modern MPI/OpenMP implementation.

1. Keep rank topology, thread count, SIMD width, aggregate size and SAP block size
   separate. A launcher can select one rank per allowed NUMA domain and use the
   available physical cores of that domain as its OpenMP team. Explicit overrides
   are needed for schedulers and benchmarking. NUMA count need not divide a valid
   t-slab grid: reject unsupported decompositions clearly instead of silently
   changing the numerical blocks or oversubscribing processors.
2. The fine path has replaced blocking `Sendrecv` with posted receives/sends,
   interior work, completion, then boundary work. The send slices must remain unchanged until completion;
   the two-rank case has the same peer on both sides and needs distinct tags.
   In SAP, complete the halo for **each color** before dependent boundary work;
   lagging the red-to-black exchange changes the smoother. If a rank owns one or
   two coarse t planes, the interior may be empty and each boundary block must
   still execute exactly once.
3. A nonblocking call alone does not guarantee overlap. MPI may require explicit
   progress. Keep MPI calls on the initializing thread under FUNNELED semantics;
   measure exposed wait time and full solve wall time rather than claiming overlap
   from an `Irecv` in source code. Pack buffers can avoid long-lived send aliases.
4. The historical coarse solver allgathered restriction output, preconditioned
   vectors and coarse matrix-vector results. Those gathers have now been replaced
   by owned coarse storage, global dot/norm reductions and nearest-neighbor coarse
   halos. Restriction and prolongation are local to the owning aggregates.
5. Gauge, basis, Galerkin stencil and double reliability vectors remain globally
   allocated/replicated. Rank-local setup, local double operator and communicator
   coarsening should follow the fine overlap change. On a large MPI system these
   are more important than removing a few microseconds of halo wait.
6. Move global communicator/rank state into a context-owned geometry/halo object
   before permitting concurrent contexts. Hardware kernels should receive local
   arrays and neighbor metadata, not infer ownership from core counts.

## Required checks for an overlap change

Compare blocking and overlapped paths on identical seeds, fields and hierarchy.
Check random fine matvec, RP, RAP, full residual and solution against QUDA. Include
1, 2 and 4 ranks; include a local single-plane case; vary OpenMP threads independently
of ranks. Preserve zero initial guesses. The primary timing remains the second
complete API call, with setup separate and additional steady samples reported.
Do not infer multi-node scaling from same-node shared-memory MPI.

## Existing matching QUDA evidence and reproduction

`PyQCU/logs/lime_mg_20261013/quda.json` records the matching fixture baseline:
second synchronized solve **1.0449679605662823 s** on one H20, full residual
**7.828853353020274e-9**, 59 iterations. This is historical evidence, not a
2026-10-21 rerun. The old accepted CPU API time 3.609931 s is about 3.45 times
that device-resident QUDA solve, already within a factor of ten, but their timing
boundaries are not identical.

The generating script is
`PyQCU/pyqcu/testing/pyquda/test_lime_multigrid.py`. It uses the actual LIME,
one stout step rho=0.125, mass=-0.277, csw=1, anti-periodic time, point source,
24 near-null vectors and 6×6×6×4 aggregation. A separate output directory prevents
it from overwriting accepted `input.h5` and `quda_solution.h5`:

```bash
/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python -u \
  PyQCU/pyqcu/testing/pyquda/test_lime_multigrid.py --stage quda \
  --data .cache/numa-overlap/quda-fixture \
  --logs .cache/numa-overlap/quda-logs --repeat 4 --tol 1e-8
```

For a strict new comparison, prefer a runner reading the existing accepted HDF5
fixture. Reuse the script's Clover/MG construction, load untwisted gauge without
another stout operation, and use `b_mass=b_hdf5/(2*kappa)`. Record separately:

- Device-resident synchronized `invert` time for comparison to historical data.
- Host API time from host source upload through inversion and output download,
  with barriers and the maximum rank wall time. Return an ordinary PyQUDA EO-x
  host field. The CPU full API already includes its validation, so either include
  an equivalent true-residual calculation here or explicitly record the difference.
- Independent full residual outside the measurement, and global relative solution
  difference against the CPU result. Enforce residual ≤1e-8, solution difference
  <1e-6, and no initial-guess reuse or chronological recycling.

`multigrid.cpp/benchmarks/runtime/benchmark_runtime.py` already consumes the correct fixture,
checks its random operator against QUDA, and writes second full API/steady samples.
It uses `--levels 2` (now also the default).
The generic `benchmark_quda_lime_mpi.py` is a BiCGStab benchmark with different
source/default tolerances and is not a drop-in reference for this MG fixture.

The new `benchmarks/runtime/benchmark_pyquda_runtime.py` implements this fixture-reading
comparison, including `--grid 1 1 1 N`, rank-maximum timings, global residuals,
canonical output and optional `--cpu-solution-dir` live QUDA operator validation.
A typical one-GPU run is:

```bash
CUDA_VISIBLE_DEVICES=0 /public2/home/lwb_720/miniconda3/envs/pyquda/bin/python -u \
  multigrid.cpp/benchmarks/runtime/benchmark_pyquda_runtime.py \
  --output .cache/numa-overlap/quda1 --repeats 4 \
  --cpu-solution-dir .cache/native-mg/accepted_serial
```

For eight GPUs, leave all GPUs visible and launch the same script with
`mpirun -n 8`, `--grid 1 1 1 8`, and a separate output directory. The runner
has since been exercised in one- and eight-GPU comparisons; retain their distinct
hardware counts and timing boundaries when reporting the latest acceptance.

## Local even-odd SAP implementation

The original paper's §6/Table 6.1 specifies four odd-even-preconditioned MR steps
for each SAP block. The reference implementation confirms this arrangement:
`.cache/cpu_libraries/DDalphaAMG/src/oddeven_generic.c` contains
`apply_block_schur_complement_PRECISION` and `block_solve_oddeven_PRECISION`;
`src/linsolve_generic.c::local_minres_PRECISION` performs the fixed local MR steps.
These files are references, not linked production implementation.

For the project's existing **signed** hopping matrices, write the Dirichlet block
operator as

```text
A = [ Ae  Heo ]
    [ Hoe Ao  ].

Se = Ae - Heo Ao^-1 Hoe
be = re - Heo Ao^-1 ro
xe ≈ MR4(Se, be), starting from zero
xo = Ao^-1 (ro - Hoe xe).
```

This is ordinary elimination of the odd row. Every MR step computes `q=Se*r`,
`alpha=<q,r>/<q,q>`, `xe+=alpha*r`, `r-=alpha*q` on the retained parity only.
The resulting complete correction must obey
`(r-Ax)_o ≈ 0` and `(r-Ax)_e = be-Se*xe`, up to float roundoff. This identity
provides a stronger local test than observing eventual outer convergence.

Implementation requirements for the default `LQCD_SAP_EO=1` path:

- `Ae` and `Ao` are the existing normalized clover-plus-identity diagonal blocks.
  Links already contain `-kappa`; applying another sign or kappa breaks the
  Schur formula. No chiral mixing is introduced by reordering site parity.
- Parity comes from the full local coordinate sum, not an assumption that adjacent
  linear indices alternate. One even block extent suffices for balanced site
  counts. Unsupported shapes must fail explicitly or retain the ordinary path.
- The local operator has Dirichlet block boundaries. Hops leaving the block are
  absent, even when the neighboring global site happens to have a valid address.
- Keep the original odd RHS until reconstruction, clear all scratch entries read
  by kernels, and never include uninitialized eliminated entries in MR products.
- Precompute inverse clover blocks in double precision, test their products, then
  store the float representation. A pivoted complex inverse avoids assuming
  positive definiteness of a generic supplied clover block.
- This changes the approximate smoother and consequently may change setup and
  outer iteration counts. Compare complete solve time, not just one SAP call;
  one Schur application involves two half-parity hops plus diagonal work.

Validation order:

1. On nontrivial gauge/clover fields, check each inverse against its diagonal;
   unit gauge alone cannot exercise clover off-diagonals. Check that EO packing
   and unpacking preserve the ordinary local operator.
2. For random retained-parity `xe` and arbitrary `ro`, reconstruct `xo`; check
   the full local residual identity above against the ordinary full block apply.
   Exercise blocks at global boundaries as well as internal blocks.
3. Run exactly four Schur MR iterations, verifying the Schur recurrence residual
   against a fresh Schur apply and the reconstructed full odd residual. Four
   steps need not solve the block accurately; do not use outer tolerance as this
   test's local convergence requirement.
4. Run full operator, RP/RAP and complete double-residual gates for serial and
   MPI decompositions, including one aggregate plane per rank and both blocking
   and overlapping halos. Recheck a random RHS as well as the physical point RHS.
5. Rebuild each mode's own hierarchy with the same seed. Compare second full API
   and additional steady samples, reporting setup separately. Ordinary SAP is
   retained with `LQCD_SAP_EO=0` as the historical comparison path; EO is now the
   default following the component, full-solve and physical-fixture checks. The eight-GPU and one-GPU reference ratios must be stated separately.

The implementation was subsequently reviewed statically: it uses an
explicit even-x-block guard, global site parity within each block, matching
basis permutations and parity-split temporal faces. The signed hopping Schur
algebra and scratch-parity initialization are consistent. Its component check
compares the reconstructed correction through the existing full local operator,
including a vanishing odd residual. Numerical checks subsequently passed for all
four fine/coarse combinations and the physical fixture. Because random candidates are initially generated in internal
storage order, switching the EO layout changes their physical values even at the
same seed; performance comparisons therefore use independently generated
hierarchies rather than identical initial test vectors.

## Coarse even-odd implementation

`LQCD_COARSE_EO=1` is now the default coarse Schur solve; `0` retains the
original full coarse GCR for controlled comparison. This is separate from fine
block EO and does not turn the global fine outer operator into a Schur operator.
The coarse grid must have even extents so every nearest-neighbor hop changes
coarse site parity. All rank-local workvectors keep their full local length, with
excluded parity entries explicitly zero. Thus existing global coarse dot/norm
reductions remain correct without any replicated-vector sums.

The retained even system uses `Ce-Heo*Co^-1*Hoe`, reduced RHS
`be-Heo*Co^-1*bo`, and right preconditioner `Ce^-1`. The GCR restart remains 16
and maximum coarse iterations remains 40. Its stopping target uses 0.1 times
the **original full coarse RHS norm**, not the norm of the transformed RHS.
A fresh Schur residual is checked at restart/apparent convergence before odd
reconstruction. A capped approximate coarse solve is allowed, as in the full
coarse path; only the outer complete double residual accepts the physical solve.

The original full coarse operator remains the RAP reference. An additional
component gate builds a reconstructed full field from a random even field and
odd RHS, then checks the full residual against the independently formed Schur
residual (and zero odd residual). This isolates algebra/communication errors from
whether the capped coarse Krylov solve reaches its optional reduction target.

## Measured EO follow-up before the final correction-factor rerun

On the physical 24³×64 fixture, the fine/coarse EO configuration reduced the
observed correction-iteration total from 27 to 18. At **2 MPI × 36 threads**,
the second complete API call was **2.3919482194 s** and the steady median was
**2.3555922769 s**. The evidence is
`.cache/numa-mg-20261021/eo_sweep/threads_36/result.json`. This is a measured
configuration in the bounded scan, not a claim of a hardware-independent optimum.

The **2 MPI × 36 threads** 12-column phase took **28.6782058030 s**
(the sweep began at 32 threads but selected 36 for the 12-column phase).
All twelve exported columns passed the independent reference-operator check;
the maximum residual was **2.0305588445e-9**. Evidence:
`.cache/numa-mg-20261021/eo_sweep/result.json` and
`.cache/numa-mg-20261021/eo_sweep/independent_columns.json`. Do not attribute
the 12-column measurement to the 36-thread configuration.

These measurements support EO promotion but use the preceding correction factor.
They must not be relabeled as measurements of the current factor-0.5 binary; the
final acceptance rerun will supply that evidence separately. MPI CTest launchers
also now use explicit `--bind-to none`: the obsolete Open MPI environment setting
was ignored by PRTE, causing concurrently launched tests to share single-core
affinities and time out. Unbound reruns passed, with no solver change required
for that launch issue.
