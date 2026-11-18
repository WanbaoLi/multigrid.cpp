# LingSheng solver and configuration-generation experiments

## L24 propagator

The common comparison uses a real `24³×64` LIME field, 16 MPI ranks,
mass `-0.277`, Clover coefficient `1.160920226`, one stout step
with `rho=0.125`, an antiperiodic fermion time boundary, and twelve
independent zero-start point-source columns. Compare warm solve/API time,
setup time separately, and independent FP64 full-operator residuals at
`1e-8`. Preserve the lexical complex128 NPY shape
`(64,24,24,24,4,4,3,3)` in sink/source spin and then sink/source color order.

- PyQCU 0.1.18 at `cf3464c7218b9cedfa12076dd374c674087bd5ca`.
  The login node cannot resolve GitHub. The remote Git checkout uses a thin
  bundle with the prior PyQCU repository as its object store and retains the
  upstream URL as origin. A clean persistent checkout is available at
  `~/lqcd-run/pyqcu-upstream-cf3464c` on LingSheng.
- Job `2169362`, output `~/lqcd-run/pyqcu-cf3464c-run04`. Includes raw
  report-style single-RHS runs, matched BiCGStab and Legacy MG full12
  runs, and the frozen `efe57de` solver control on the same node.
- PyQCU single-RHS BiCGStab passed at 0.443 s (complex64, seeded random
  source, tolerance `1e-6`) and 1.006 s (complex128, constant source,
  tolerance `1e-9`), using the raw periodic gauge.
  With matched physics and 32 threads per rank, its full12 BiCGStab
  warmed API median was 231.663 s on cn12075. All twelve columns passed
  both NumPy and independent C++ checks with a maximum residual of
  `5.63e-10`.
- The frozen MG/SAP flexible GCR control on cn12075 took 13.113 s in
  the same warmed full12 API scope and 12.685 s in the native solver.
  Its separate hierarchy setup took 222.573 s. Independent verification
  passed all thirteen fields with maximum residual `4.82e-9`. In this
  workload, the reusable-hierarchy API control was 17.67× faster than
  the complex128 BiCGStab path. The separate raw periodic single-source
  tests measure a different operator and right-hand side.
- Job `2169656` retries Legacy MG. Upstream writes a HDF5 cache root
  and a sibling JSON manifest. The original controller passed a JSON
  root name, so the paths collided. With an HDF5 root the three
  periodic complex128 samples passed, with solves of 1.205, 1.190
  and 1.213 s and NumPy residual `7.53e-10`. The matched full12
  case reached the solve and aborted when coarse BiCGStab missed its
  inner target. The printed norms were `1.6755e-2` and `3e-6`.
  Job `2170012` retries with coarse tolerance factor `1e5`
  and retains the outer tolerance `1e-8` and independent checks.
- Job `2169865`, output `~/lqcd-run/mg-l24-reliable-sap-run03`. One
  hierarchy and the frozen `820918f` library. The three interleaved cases
  test the control, fusing the FP64 residual update and norm, and splitting
  SAP work by block and RHS to balance the thread team. Each case receives
  four timed rounds following its warm-up, with independent verification.
  All cases passed the independent 12-column test on cn12124. API medians
  were 15.173 s for the control, 15.058 s for fused reliable residuals,
  and 15.178 s for RHS-split SAP. The fused change was 0.76% faster in
  this allocation. A repeat allocation is needed to establish the gain.
- Job `2169391` passed the actual PyQUDA MPI2 loader test. The output
  matched every element of all twelve input columns after the EO conversion.
- Job `2169509` builds the opt-in AArch64 coefficient tiling candidate
  `6b7c1c7`. Threads visit all RHS columns before moving to the next
  64- or 128-site tile. The first MPI2 test geometry violated the native
  solver's coarse extent constraints. Job `2169866` uses a valid MPI2
  regression fixture before timing off/64/128 on real L24. The three
  timing cases share the library and hierarchy.

The old PyQCU run failed because the packaging subprocess timed out after
60 seconds. The replacement records packaging independently of the physics
benchmarks. Earlier attempts in this campaign hit the shared-directory quota.
Builds and benchmark arrays now use the compute node's temporary filesystem.
The first SAP tuning allocation, `2169363`, failed before the payload
started because the compute node's scheduler directory exhausted its
inodes. The first tiling build, `2169502`, was missing the top-level build
file after sparse checkout. The second build uses the full source in scratch.
The second SAP run, `2169510`, stopped because its controller omitted the
required source digest. Both pending experiments now pass the archive
digest of the matching library source to `bench_full12.py`.

## HMC

- Job `2169360` compares direct block assembly to the original dense
  expansion on the same fields and momenta at `2⁴` and `2³×4`, then runs
  an 80-trajectory leapfrog chain.
- Job `2169361` uses five Omelyan steps per trajectory, compared with ten
  leapfrog steps. Both use eleven force evaluations. The ten-test physics
  suite passed on cn12038. In the equal-force one-field test, absolute
  energy error was `0.0210409452` with Omelyan and `0.1337056014` with
  leapfrog. Both 80-trajectory chains completed and all eight saved LIME
  files passed independent CRC, plaquette, SU(3) and operator checks.
  After the first 40 trajectories, leapfrog and Omelyan acceptance was
  97.5% and 100%, and RMS energy error was 0.06864 and 0.01600,
  respectively. Their separately scheduled wall times combine kernel cost
  and node load. Job `2169487` interleaves ten-step leapfrog and
  five- and three-step Omelyan on sixteen identical initial conditions.
  Three-step Omelyan used seven force evaluations and took 2.670 s
  versus 4.127 s for leapfrog. The RMS energy errors were 0.05703 and 0.09084.
  Job `2169517` repeated the three-step setting over 80 trajectories.
  It accepted 79/80 overall and 40/40 after the first 40 trajectories,
  with post-warm-up RMS energy error 0.04543. All four saved LIME
  configurations passed independent verification.
- Job `2169372` checks the matrix-free Wilson–Clover application and its
  link gradient against the dense reference at both sea masses. All eleven
  checks passed. Job `2169446` extended the comparison to the even Schur
  operator, local odd-site Clover determinant, log-weight gradient and
  six independent shifted FP64 solves. The first shifted test uncovered
  a bad complex dot product on the installed PyTorch build. Explicit real
  reductions passed all 13 checks and reached a maximum shifted residual
  of `7.81e-13`.
- Job `2169527` passed fourteen checks. Matrix-free rational powers at the
  strange mass agreed with a dense eigensolve within `3.21e-13` relative
  over the tested spectral interval. Job `2169538` passed fifteen checks,
  including the strange-pseudofermion force against a dense finite
  difference with absolute discrepancy `2.05e-11`.
- Job `2169650` passed sixteen checks, including complete 2+1
  pseudofermion refresh, rational MD and dense Metropolis on a hot field.
  The complete-force finite-difference discrepancy was `1.82e-9`.
  Its pilot uses eight trajectories with a fixed strange spectral interval.
- Job `2169686` verified multi-shift CG. Five shifts used 22 normal
  applications with shared Krylov vectors versus 59 independently, with
  maximum true residual `7.81e-13`. The optimized rational force also
  accumulates the pole contributions before differentiating the shared
  Clover graph. Job `2169722` measured 106.694 s versus 19.065 s on
  identical gauge links, pseudofermions and 48 poles, a 5.60× gain for
  the strange action and force. The maximum link-gradient difference
  was `4.58e-16`. Job `2169695` passed all seventeen tests and
  ran eight trajectories with rational MD and dense exact Metropolis.
  Seven trajectories were accepted and both saved LIME files passed
  independent verification.

### Matrix-free refresh and endpoint pilot

On cn12038, job `2169886` moved gauge-dependent parity hops and the
odd Clover inverse outside the Krylov and pole loops. Three alternating
matched samples reduced the strange action and force median from 34.908
to 26.115 s. Job `2169956` grouped pole fields in batches of eight; in
its separate matched measurement the median fell from 5.521 to 3.342 s.
The maximum link-gradient discrepancies were `6.11e-16` and
`3.35e-16`. The two measurements ran at different node loads.

Job `2169940` passed 18 tests including dense-oracle refresh, endpoint
Hamiltonian, force and reversibility comparisons. The `2×2×4×4`
matrix-free run accepted all four trajectories and three saved LIME
files passed the independent scalar operator, CRC and plaquette gates.
The strange determinant certificate uses a sufficient strict-accretivity
bound based on local Clover eigenvalues and unitary Wilson hopping.
This pilot used heavy validation masses 0.5 and 0.8. The sufficient bound
cannot certify the benchmark's negative strange mass.

Job `2169993` verified the streamed LIME writer with the independent
reader across multiple chunks, including a partial final chunk. Job
`2170005` ran `4⁴` with this writer and grouped pole fields. The three
trajectories took 41.153, 44.784 and 46.232 s. Two were accepted.
Both saved LIME files passed independent checks and contain the same
gauge field because the last proposal was rejected. The previous
frozen HMC version `b9556bb` also passed
15 tests on node5005 through itp. The independent C++ and MPI LIME
checks were skipped in that run. The later `f15edc2` snapshot passed
17 tests on node5005, including the independent C++ Dirac comparison.
The PyTorch environment lacked MPI Python bindings. The adaptive
endpoint and refresh each selected 48 poles, with endpoint energy
agreement `1.14e-13` against the dense oracle.

Jobs `2170028`, `2170115` and `2170133` check smaller rational
refresh and acceptance expansions, storage of the two 6×6 Clover
blocks, and direct Wilson staples against their respective reference
evaluators. On cn12038 the pole selection reduced both expansions from
128 to 48 poles with dense-oracle endpoint energy difference
`3.41e-13`. The direct staple gradient agreed with differentiation of
the plaquette loops within `5.33e-15` across three lattice geometries,
including `4⁴`. The matrix-free path uses FP64 true-residual checks
in every shifted solve.

The compact Clover implementation passed all three physics tests
in job `2170115`. Its timing controller failed while unpacking the
benchmark cases. Job `2170195` reruns the corrected paired timer.

Direct assembly reduced the paired median four-step MD time from 3.266 to
2.212 s on `2⁴` and from 6.343 to 3.477 s on `2³×4` on cn12038.
Ten alternating measurements used identical initial links and momenta.
The maximum force discrepancy was `4.45e-16` and the final links differed
by less than `3e-15`. Raw samples are in `hmc-paired.json`.

[Grid's minimum-norm and nested integrators](https://github.com/paboyle/Grid/blob/3232b438f2cf729e515c185e2dbf29d7cc276bb7/Grid/qcd/hmc/integrators/Integrator_algorithm.h)
provide the Omelyan step sequence. The [one-flavor even–odd rational
action](https://github.com/paboyle/Grid/blob/3232b438f2cf729e515c185e2dbf29d7cc276bb7/Grid/qcd/action/pseudofermion/OneFlavourEvenOddRationalRatio.h)
is the reference for adding the strange-quark factor. The next RHMC comparison
needs a bounded spectral interval, shifted-solve residuals, the even–odd
Clover determinant factor, and an independent dense finite-difference
force test. Production scaling also requires a compiled link force and
MPI halo exchanges.

[QUDA's BiCGStab kernel](https://github.com/lattice/quda/blob/af7e15080e247795ef076b6d9284478755a9a683/lib/inv_bicgstab_quda.cpp)
uses a residual-drop criterion for reliable updates. Compare reliable-update
frequency and time in profile data before changing our GCR correction policy.
Retain the independent FP64 convergence check across candidates.

### Native and distributed RHMC

Job `2170342` passed twenty checks and ran three native-assisted
trajectories at `4⁴`, accepting two. Both saved configurations passed
the independent SciDAC and scalar Dirac checks. The paired rerun
(`native-rhmc-trajectory-paired.json`) uses the same field and RNG state
for each Torch/native pair. The complete trajectory median fell from
41.809 to 12.479 s (3.350×), with all acceptance decisions equal.
The largest end-to-end link discrepancy was `2.13e-15` and the largest
Hamiltonian discrepancy was `1.82e-12`. On `8⁴` the paired Schur normal
application was 10.228× faster with the native backend. These jobs used
validation masses 0.5 and 0.8 with beta 5.6 and cSW 1.

Jobs `2170388`, `2170397`, `2170417`, `2170444` and `2170526` test
two and four time ranks. They cover native Schur, packed collective
shifted residuals, Clover and link gradient exchange, local-gauge
coefficient preparation, and projected half-spin spinor exchange.
The full distributed RHMC path in `101d1de` adds local heatbath, force
and Metropolis. The two- and four-rank trajectory checks in job
`2170504` agreed with the dense endpoint within `4.55e-13` and
reproduced the links under reversal within `4.00e-15`. Node5005 through itp passed the
three targeted tests with snapshot `8ad2514`. Its benchmark showed
large run-to-run timing variation, so its numerical results are
the cross-platform check for this snapshot.

Job `2170664` rechecked the reusable native scratch and typed CG scalar
reductions at MPI2 and MPI4. Job `2170685` pinned each time rank to its
own CPU on cn12039 and generated two `4⁴` LIME files each with one and
four ranks. The four-rank trajectories ran in 7.890 and 8.513 s. MD
accounted for 5.942 and 6.004 s. All four fields passed the independent
SciDAC CRC, plaquette, SU(3) and C++ Dirac gates. The maximum four-rank
Dirac discrepancy was `1.19e-16`. The one- and four-rank chains use
different random streams; their timings are stage profiles. The earlier
unpinned MPI4 pilot and the pinned run differ in software, affinity and
wait policy, so those timings cannot isolate a single cause.

Job `2170699` kept rank placement fixed for an interleaved comparison
of force implementations on identical fields and pseudofermions.
Backpropagating accumulated coefficient gradients once reduced the
`4⁴` force median from 3.084 to 2.053 s. Its `8⁴` measurements had
substantial variation and did not establish a gain (19.119 versus
25.017 s). The maximum force difference was `1.78e-15` at either volume.
The same job ran a three-trajectory `8⁴` pilot. All three proposals
were accepted. Both saved configurations passed independent verification,
with largest scalar operator discrepancy `1.15e-16`. Its timings of 46.4,
49.1 and 123.3 s show substantial runtime variation.

Job `2170744` split MD timing into coefficient construction, Krylov
preparation and solves, and spinor and gauge differentiation. Preparation
and solves used 21.73 s out of 27.92 s in MD on its profiled `4⁴`
trajectory. These are per-phase rank maxima.

Job `2170768` held the refresh and endpoint quadratures fixed and tried
64, 32 and 24 poles in the strange MD force on `4⁴`, rotating execution
order across three identical-input comparisons. The respective complete
trajectory medians were 8.824, 6.966 and 6.144 s. The 64-pole samples
included one 23.19 s outlier. Every proposal was accepted. Relative to
64 poles, the 32-pole setting differed by at most `2.99e-10` in force and
`1.50e-9` in delta-H; for 24 poles the differences were `4.36e-8` and
`2.61e-7`. Both candidates passed the reversal checks. Job `2170870`
extends the pairing to `8⁴` and uses 32 MD poles for a `12⁴` pilot.
[Grid's general rational-ratio action](https://github.com/paboyle/Grid/blob/3232b438f2cf729e515c185e2dbf29d7cc276bb7/Grid/qcd/action/pseudofermion/GeneralEvenOddRationalRatio.h)
also supports setting the MD and acceptance rational degrees separately.

Job `2170780` tested GCC's `-fcx-limited-range` in an experimental
library build. The normal application speedups were 1.168×, 1.089× and
1.016× on `4⁴`, `8⁴` and `12⁴`. The largest discrepancy against Torch
was `8.96e-16`. The flag remains outside the production build.

Job `2170886` specialized the real and imaginary unit phases in the
DeGrand–Rossi projector. It measured 1.042×, 1.049× and 1.050× on
`4⁴`, `8⁴` and `12⁴` without the experimental GCC flag. Both kernels
agreed with Torch within `9e-16`. The four-rank Schur and shifted
residual tests passed with the new kernel. The pre-specialization
snapshot also passed the complete pinned two- and four-rank RHMC gates
in job `2170879`, replacing the unpinned duplicate `2170587`.

The `8⁴` pairing in job `2170870` passed all three same-input matches
and both reduced-pole reversal checks. The 64, 32 and 24-pole trajectory
medians were 45.132, 28.580 and 26.576 s. The 32-pole candidate was faster
than the control in all three pairs and changed delta-H by at most
`3.12e-9`. The 24-pole candidate changed delta-H by at most `6.48e-7`
and had one slow 75.28 s sample. All acceptance decisions agreed. The
six-rank `12⁴` pilot uses 32 poles in MD and the same high-precision
refresh and acceptance expansions.

### ARM propagation and Legacy MG follow-up

Job `2169866` interleaved disabled, 64-site and 128-site RHS tiling at
`24⁴`. Its verifier controller expected a missing byte extractor;
job `2170458` reused the original arrays and a frozen standalone
extractor. All three sets of 12 saved columns passed an independent
scalar C++ operator check with maximum relative residual `4.819e-9`.
The respective warmed wall medians were 13.664, 13.651 and 13.663 s.
The matching summed API medians were 13.592, 13.579 and 13.591 s.
The timing spread gives no reason to change the default.

PyQCU job `2170012` relaxed the Legacy MG coarse tolerance. Coarse
BiCGStab met its local convergence criterion, but the outer correction
then requested the fine-grid fallback. The strict MG gate terminated
the run before a full 12-column benchmark was available.

The next L24 trial interleaved coarse GCR iteration caps of 40, 12 and
8 on one hierarchy with 16 ranks. Job `2170607` completed timing and its
control verifier before a publication path error. Job `2170759` verified
the original arrays from the same compute node and recovered the reports.
All cases passed independent full12 verification. The warm wall medians
were 15.657, 15.304 and 16.726 s, with total outer iterations of 289,
310 and 365 per propagator. Cap 12 was 2.25% faster in this allocation
and had maximum true residual `4.89e-9`. The diagnostic coarse time
fell as the cap was reduced, while more outer iterations increased SAP
time. The default remains 40 pending a matched repeat.
