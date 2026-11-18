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

The `12⁴` pilot completed three trajectories in 96.25, 95.86 and
98.21 s. The first warmup proposal was rejected and both subsequent
proposals were accepted. Both saved files passed the independent SciDAC
CRC, plaquette, SU(3) and scalar Dirac checks. The largest scalar Dirac
discrepancy was `1.15e-16`. Job `2171047` extends the same validation
parameters to the production spatial extent `24³×8`.

The `24³×8` eight-rank pilot accepted all three proposals in 344.40,
346.65 and 344.56 s. The two saved files passed SciDAC CRC, NumPy
plaquette and SU(3), and the independent scalar Dirac comparison.
Their largest scalar discrepancy was `1.15e-16`. This released the
`24³×64` job's verification dependency. The full-volume geometry
job subsequently entered the queue behind the scheduler limit.
On cn12048 the 64-rank `24³×64` job `2171098` accepted all three
proposals in 380.51, 309.63 and 286.10 s. The delta-H values were
0.13247, 0.13264 and 0.13175. This cold-start calibration used
`beta=5.6`, Wilson masses `0.5` and `0.8`, `cSW=1`, and trajectory
length `0.018`. Thermalization and autocorrelations remain unmeasured.
The two saved plaquettes were 0.9982771161 and 0.9974206523.
Independent SciDAC CRC, SU(3), and scalar C++ Dirac checks passed
for both files. The maximum relative operator discrepancy was
`1.15e-16`. Job `2171358` published the two 509609712-byte LIME files
to `~/lqcd-run/hmc-l24t64-publication-run01/published`. The SHA256
values in the verification manifest were reproduced on the local
copies. See [chain](distributed-l24t64-mpi64-chain.json) and
[verification](distributed-l24t64-mpi64-verification.json).

Job `2171240` compared a continuous three-trajectory chain with one
trajectory followed by a two-trajectory restart. The configurations
and per-rank RNG tables had identical digests on two ranks. Energies
and acceptance decisions matched exactly. An incompatible mass was
rejected before opening the new output directory, and the two resumed
LIME files passed independent verification.

Job `2171250` compared the optional analytic Clover-leaf adjoint to
ordinary Torch differentiation on four ranks. The independent gauge
gradient error was at most `3.59e-15`. Full RHMC force and split-link
reversal errors were `8.89e-16` and `6.11e-15`. The `12⁴` force
median fell from 25.56 to 22.32 s, while the `8⁴` median increased
from 4.77 to 4.88 s. `--direct-clover` selects the candidate.

Job `2171301` tested the optional `--packed-faces` kernel with
separate projected temporal receive buffers. It posts both directions
before waiting and reads the owned field directly. The Schur-normal
application at `24³×4` fell from 62.82 to 51.17 ms on four ranks.
The paired values were bitwise equal in all three tested geometries.
The two- and four-rank checks passed with true shifted residual at most
`9.76e-13`, and the complete four-rank RHMC gate passed. Job `2171328`
tested the combined packed faces and analytic Clover options over two
matched full `24³×4` trajectories. Median elapsed time fell from
353.72 to 322.66 s, with equal delta-H and Metropolis decisions and
maximum link difference `6.89e-15`. See the
[paired trajectories](distributed-packed-clover-l24t4-trajectory-paired.json).

Job `2171400` evaluated the optional Zolotarev inverse square root.
On the standard spectral interval it used 15 poles at the Metropolis
endpoint and 11 for the trial MD target, versus 48 and 32 with
quadrature. The 48-pole heatbath was identical in both branches.
Independent scalar grid error was `2.11e-13` or less on both tested
intervals. Two matched proposals at each geometry changed median
time from 11.79 to 8.11 s at `8⁴` and from 43.57 to 29.20 s at `12⁴`.
Every paired Metropolis decision agreed. Maximum paired link
and delta-H differences were `9.05e-13` and `1.85e-7`.

Job `2171435` checked Hamiltonian differences formed before the
rank reduction. Two- and four-rank values agreed with dense differences
within `1.78e-12`. A cancellation fixture recovered a unit difference
per rank between extensive values whose FP64 totals were equal.
The complete test used packed faces, analytic Clover and compact spin
with Zolotarev, and the separate MPI2 restart oracle still matched.

Job `2171391` compared `--compact-spin` with the four-spin force
contractions on four ranks. At `24³×4`, the force median changed
from 64.19 to 56.04 s across three pairs. The maximum force difference
was `8.89e-16` across all four volumes. The two- and four-rank dense
RHMC and reversal checks also passed.

Job `2171439` completed two `24³×64` trajectory pairs on the verified
`hmc_000002.lime` with 64 ranks. The first pair measured 284.69 s for
the control and 160.42 s with packed faces, analytic Clover derivatives,
compact spin and Zolotarev, before the proposal-gate job started.
The second pair's CPU masks overlapped job `2171511` on cn12048
and its timing is retained for diagnosis. Metropolis decisions agreed
in both pairs. The accepted proposal's maximum link difference was
`5.24e-13`. Job `2171511` captured the rejected pair's proposal
before Metropolis and measured maximum differences of `5.29e-13` in
the links, `1.06e-10` in the momenta, and `1.31e-5` in delta-H.
See [matched trajectories](distributed-l24t64-optimized-paired.json)
and the [pre-Metropolis comparison](distributed-l24t64-proposal-gate.json).

Job `2171445` reused the prepared Clover factors and Schur workspaces
between the heatbath and the initial Hamiltonian. Fields and individual
Hamiltonian terms were bitwise equal on both tested volumes. Four-rank
median time for those two operations fell from 7.23 to 6.79 s at
`12⁴` and from 15.42 to 14.44 s at `24³×4`. The two- and four-rank
dense and reversal gates passed. Job `2171491` compared differentiation
batch sizes of 4, 8 and 11 strange poles with identical force inputs.
Using all 11 poles together reduced median force time from 5.50 to
5.29 s at `12⁴` and from 12.66 to 12.16 s at `24³×4`, relative to a
batch of eight. The maximum force difference was `8.89e-16` and the
default batch passed the two-rank LIME and RNG restart tests. See
[timings](distributed-force-pole-batch-paired.json).

Job `2171526` exchanged half-spinors and their cotangents during
force differentiation. On four ranks the median force time changed
from 10.58 to 10.22 s at `12⁴` and from 30.26 to 23.92 s at
`24³×4`. The paired force agreed within `8.89e-16`. The two- and
four-rank dense force and link reversibility comparisons passed.
The new path is selected with `--compact-spin --projected-force-faces`.

Job `2171553` starts a fresh eight-trajectory chain with the combined
optimizations from the verified `hmc_000003.lime`. The new
`--initial-lime` mode checks dimensions and SciDAC CRC, uses the new
rank-local seeds, and records the input SHA256. A two-rank gate checks
fresh starts and exact restarts before the full-volume stage. This gate
passed, including rejection of a LIME field with mismatched dimensions.
The 64-rank stage is running on cn12051.

Job `2171561` holds the optimized algorithm, 64 ranks, input, and seeds
fixed while pairing sequential CPU binding with four ranks per NUMA
domain on an exclusive node. Both layouts record hashes of the
pre-Metropolis links and momentum. On cn12065 the compact layout
assigned 37 and 27 ranks to two NUMA domains, while the spread layout
assigned four ranks to each of 16 domains. The first matched sample
took 212.56 s compact and 141.04 s spread. The second took 223.70 and
140.61 s. The proposed links and momenta were bitwise equal within each
pair, with identical delta-H and decisions. One proposal was accepted
and one rejected. See the [exclusive comparison](rhmc-numa-placement/).
Job `2171615` waits for that comparison and then tests one, two, and
four cores per rank on an exclusive node. Each MPI rank keeps its lead
core and NUMA domain. The threaded cases independently read the fixed
input and compare proposal links and momenta against the one-core case.

Job `2171583` compares cached and rebuilt checkerboard indices for
RHMC. It runs native Schur, dense force and reversal gates on two and
four ranks, then paired force timings at `12⁴` and `24³×4` with bitwise
agreement required. Both rank counts passed the native Schur and dense
RHMC comparisons. Both paired force runs were bitwise equal. Median
times moved from 11.31 to 10.70 s at `12⁴` and from 49.60 to 50.29 s at
`24³×4`. The latter comparison overlapped a separate job on the same
node, so this series does not establish a consistent speedup.

On node5005 the `dac8425` build passed all five selected tests in the
`deepinfer-sm90` Python environment with SciPy 1.17.0 and Torch 2.13.0.
The cross-check covered the independently compiled C++ operator, native
Schur-normal, dense endpoints, the near-free determinant certificate,
and 15- and 19-pole Zolotarev scalar accuracy. See
[node5005 results](node5005-rhmc-dac8425.json).

Job `2171597` compares the optional `--light-heatbath-action` path
against the explicit light normal solve at the initial endpoint.
With a nonsingular Schur operator $S$, the freshly drawn light
field is $S^\dagger\eta$ and its initial action is $\|\eta\|^2$.
The implementation uses a collective Clover and gauge-link norm
bound before applying this identity. It retains the explicit solve
when the bound cannot certify nonsingularity and at the final endpoint.
The two- and four-rank tests matched the explicit initial light action
within `7.11e-15`, kept the heatbath fields bitwise equal, and
exercised the fallback with a singular Clover fixture.
The four-rank `24³×4` median for refresh and initial action fell from
31.98 to 27.91 s in three measured pairs. The refresh fields were
bitwise equal at both volumes and the largest relative change in
the explicit light action was `8.78e-17`. The `12⁴` timing overlapped
the geometry-cache job on cn12038. See the
[paired initial-phase timings](distributed-light-heatbath-action-paired.json).

Job `2171630` tests the optional `--real-krylov-dot` recurrence with
interleaved real FP64 buffers. It retains the explicit true-residual
norm and per-pole verification, checks the Schur solves against the
independent operator, and pairs initial-phase and force timings on
the same gauge, momentum and heatbath noise. The two- and four-rank
checks passed, with maximum independent shifted residual `9.76e-13`.
Both force comparisons agreed within `9.93e-16`. At `24³×4`, median
force time fell from 33.76 to 32.42 s while preparation and solve
increased from 12.63 to 12.77 s and the initial phase increased from
36.50 to 36.71 s. At `12⁴`, preparation and solve fell from 6.85 to
6.64 s. These phase timings do not establish a consistent solve speedup.
See the [paired real-buffer results](distributed-real-krylov-dot-paired.json).

Job `2171643` tested the optional `--pade-drift` small-step gauge update
in seven measured pairs per geometry. At `24³×4` the four-rank median
went from 380.41 to 274.46 ms. The maximum difference from the
eigendecomposition was `2.56e-15`, and the largest SU(3) and reversal
errors across both geometries were `5.22e-15` and `1.12e-15`.
The large-step fallback matched bitwise, and the two- and four-rank
dense RHMC and reversal gates passed. The norm cutoff uses the
FP64 degree-five bound in [Higham's matrix exponential analysis](https://epubs.siam.org/doi/10.1137/04061101X).
Job `2171666` uses the independently checked `24³×8` LIME field from
job `2171047` as the shared input for two full trajectory pairs. The
pair holds all other optimizations fixed and checks the proposed links,
momenta, delta-H, and acceptance before interpreting the timings.
The original controller stopped at a memory-only NUMA node with an
empty CPU list. Job `2171673` reuses the SHA256-checked library and LIME
file after correcting that preflight. The queued NUMA comparisons
received the same correction.
Across the [two matched pairs](distributed-pade-l24t8-trajectory-paired.json),
median drift time fell from 27.73 to 19.76 s, a 28.7% reduction.
Median whole-trajectory time moved from 647.19 to 642.68 s, and the
candidate was faster in one of the two pairs. All proposals were
accepted. The largest link and delta-H differences were `8.11e-15`
and `2.03e-9`, respectively.

Job `2171679` compares the optional `--shared-clover-spin` path, which
reuses the spin contractions before applying the two mass factors.
The Clover blocks were bitwise equal and the maximum force difference
was `8.89e-16`. On four ranks at `24³×4`, median coefficient build
fell from 0.553 to 0.524 s and total force from 11.118 to 11.057 s.
The two- and four-rank dense checks passed. See the
[paired Clover results](distributed-shared-clover-spin-paired.json).

Job `2171712` tests the native implementation of the same bounded
Padé drift against the tensor Padé and spectral versions. The native
path assembles the fixed SU(3) generators and solves the near-identity
3×3 system in one pass. The spectral drift covers larger arguments.
At `24³×4` the four-rank single-drift medians were 546.16 ms (spectral),
720.22 ms (tensor Padé), and 78.72 ms (native Padé). The native result
agreed with both controls within `2.56e-15`. All large-step fallbacks
were bitwise equal, and the two- and four-rank dense tests passed.
Job `2171748` extends the comparison to paired entire trajectories
using the verified `24³×8` field. See
[single-drift results](distributed-native-pade-drift-paired.json).
The node5005 comparison compiled the same C++ kernel independently
and used a single spatial `24³` slab. One-thread medians were
2.243 s (spectral), 1.416 s (tensor Padé), and 0.354 s (native).
The largest link discrepancy was `2.11e-15`. The four-thread
samples fluctuated, so the single-kernel test does not establish
whole-trajectory scaling. See [node5005 measurements](node5005-native-pade-961194b.json).

Job `2171768` passed all 13 NUMA launcher tests and generated a
[64-rank single-slice plan](distributed-rhmc-numa-launcher-l24t64.json)
on cn12048 with four physical cores per CPU NUMA domain. The same
launcher ran two- and four-rank dense RHMC tests with the optional
`--reuse-odd-inverse` force. The force reuses the Schur inverse for
the exact derivative of the odd Clover log determinant. The largest
dense force difference was `1.78e-13`. The matched force was bitwise
equal at both volumes. At `24³×4`, the median force changed from
11.64 to 11.35 s. See [force timings](distributed-odd-inverse-force-paired.json).

Job `2171795` compares the optional `--overlap-schur-faces` native
Schur path at `24³×64` with 32 and 64 ranks on the verified LIME
input. It evaluates the six spatial hoppings while the projected
time faces are in flight, then adds the temporal terms in order.
The test gates include the independent packed operator and shifted
solve comparisons and dense force and reversibility checks. Both
rank counts passed. The packed operators were bitwise equal, with
maximum shifted true residual `9.76e-13`.
At 32 ranks on the verified LIME input, both Schur-normal outputs
were bitwise equal. Per-application median time was 2.898 vs 2.815 s
at mass 0.5 and 2.862 vs 2.799 s at mass 0.8. The 64-rank timing
is in progress. See [32-rank overlap data](distributed-schur-overlap-paired-mpi32.json).

Job `2171814` checks reuse of the selected Hamiltonian endpoint when
the RHMC generator records observables. The code reuses the local gauge
action and certified strange spectrum for either accepted or rejected
proposals, then evaluates unitarity and determinant errors on the
selected field. It records observables time separately. The gate
compares against a fresh calculation after each possible decision
and checks the LIME and RNG restart before paired timings. Both
the two- and four-rank tests reproduced all observables exactly
after acceptance and after rejection. The two-rank LIME and RNG
restart digests also matched exactly. The four-rank `24³×4` median
observables time changed from 1.529 to 0.084 s across seven pairs.
See the [observables timings](distributed-reused-observables-paired.json).

Job `2171830` compares the optional `--gershgorin-strange` certificate
with the existing Clover eigenvalue bounds. It uses the row-sum
enclosure only when it certifies positivity and fits the fixed
rational interval. The checks include a dense Schur reference and a
deliberately tighter interval that exercises the eigenvalue fallback.
The dense, two-rank, four-rank and restart gates passed. The first
timing controller incorrectly required the row-sum bound to qualify
on every field. Retry `2171850` checked both paths. At `24³×4` the
row-sum certificate changed 0.364 to 0.073 s on the smoother field.
When its lower bound fell below the rational interval, the fallback
reproduced the eigenvalue bounds exactly and took 0.416 vs 0.364 s.
See [certificate results](distributed-gershgorin-strange-paired.json).

Job `2171040` replaced reverse differentiation of the Wilson plaquette
loops with owned-site staples and projects link derivatives via a color
matrix contraction. The contraction avoids constructing all eight
rotated 3×3 matrices per link. The direct derivative agreed with the
halo adjoint within `5.33e-15` on four ranks. Full RHMC force and
reversibility agreed with the reference within `1.23e-15` and
`4.25e-15`, respectively. The paired `4⁴` and `8⁴` force timing
changes were below 1%.

Job `2171036` held the `8⁴` MD approximation at 32 poles on four
ranks and compared true-residual tolerances `1e-12`, `1e-9` and
`1e-7`. Median trajectory times were 34.81, 32.13 and 31.15 s.
All acceptance decisions agreed and both candidates passed reversal.
Their largest changes in delta-H were `5.16e-9` and `1.06e-6`.
The refresh and endpoint tolerances were fixed for all three cases.

Job `2171059` compared fixed-length `0.08` proposals. With one slow
step, moving the gauge force to two inner Omelyan steps per drift
changed the `8⁴` trajectory median from 15.310 to 15.951 s and the
RMS Hamiltonian change from 1.520 to 0.209. Mean Metropolis probability
across four matched proposals changed from 0.219 to 0.812. With two
slow steps the corresponding RMS values were 0.400 and 0.053.
The four-rank force split and link reversal agreed within `8.89e-16`
and `7.56e-15`. Job `2171098` applies the split integrator at
`24³×64` after job `2171047` passes its `24³×8` file gates.

Job `2171164` passed the dense sign and spectral gates for the new
cold-field perturbation certificate at Wilson strange mass `-0.277`.
The free gap agreed with dense SVD within `4.5e-16`. At the perturbed
`2⁴` field the certified interval `[0.07191, 4.64407]` enclosed the
dense Schur-normal interval `[0.35793, 1.03569]`. A farther field was
correctly rejected by the certificate. The same job also attempts an
`8⁴` validation chain with this mass and trial light mass `-0.32`.
The first test controller, job `2171113`, used the wrong dense-model
keyword and stopped before running the chain.

The corrected job accepted all three `8⁴` proposals and saved two
independently verified LIME files. The largest scalar Dirac discrepancy
was `1.17e-16`. The final plaquette was 0.9997135 and the final
certified Schur-normal lower bound was `0.004128`. The run used a cold
start and trajectory length 0.006. It tests the negative-mass
certificate near the free field.

### ARM propagation and Legacy MG follow-up

Job `2169866` interleaved disabled, 64-site and 128-site RHS tiling at
`24³×64`. Its verifier controller expected a missing byte extractor;
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

Job `2170764` repeated the control and cap 12 and tried cap 14 and
reduced SAP smoothing. All 48 columns passed independent verification.
The wall medians were 19.822 s (control), 19.555 s (cap 12), 19.374 s
(cap 14) and 20.351 s (cap 12 plus three SAP steps). The cap 14
maximum residual was `4.91e-9`. Separate jobs `2171049` and
`2171082` compare smaller coarse OpenMP teams and CGS2 with two packed
MPI reductions when the coarse basis has more than two directions.

Job `2171049` again favored cap 14, with wall medians of 16.143 s
(cap 40 control) and 15.684 s (cap 14 with the full coarse team).
Reducing the coarse team to 16 or 8 threads increased the cap 14 median
to 16.501 and 19.517 s. All four cases passed the twelve-column
independent verification. Job `2171082` built the packed CGS2
candidate and passed its serial gate. The unbound MPI2 gate reached
the CTest timeout. The first retry, `2171303`, used a fixed-length
abbreviated commit comparison and exited in the preflight. Job
`2171323` checks the full SHA and reuses the same library on the same
node with distinct NUMA placements before the full-volume comparison.
The pinned two-rank fixture passed all widths with an independent
maximum residual of `3.97e-11`. Its eight cap-40 diagnostic calls
used 734 MPI reductions with packed MGS and 383 with packed CGS2.
The real L24 comparison passed 12 independent columns per case,
with maximum residual `4.91e-9`. Warmed wall medians were 20.483 s
for cap 40, 20.043 s for cap 14, 21.290 s for CGS2 cap 40, and
20.822 s for CGS2 cap 14. At cap 40 a separate diagnostic propagator
recorded 19,746 MPI allreduces with MGS and 9,020 with CGS2, with
identical coarse iteration totals. The sum of local rank-0 coarse
times rose from 4.964 to 5.876 s. Packed MGS with cap 14 remained
the fastest measured case in this allocation. See the
[real-L24 diagnostics](coarse-cgs2/diagnostics.json).

Job `2171520` holds the coarse cap at 14 and sweeps coarse residual
targets 0.1, 0.20 and 0.35 alongside the cap-40 control. It runs on
cn12065 after job `2171323` releases the allocation. Each case receives
an independent twelve-column verification.
The measured warmed medians were 21.914, 21.489, 22.506, and 24.871 s
for cap 40 and the three cap-14 targets, respectively. All four cases
passed independent twelve-column checks at maximum residuals
`4.82e-9`, `4.91e-9`, `4.49e-9`, and `4.97e-9`, respectively. The opt-in
[LingSheng L24 plan](../../profiles/optimization/lingsheng-l24-cap14-full12.json)
replays the previously verified cap-14 target of 0.1.

Job `2171659` reused the same library and cap-14 plan on the generated
`hmc_000003.lime` with source `(3,1,2,5)`, sample valence mass `-0.277`,
and one stout step. Hierarchy setup took 247.87 s and the two warmed
full12 solves had median 213.28 s. The columns took 212–226 iterations
in the first solve. The independent scalar C++ check passed the
twelve columns and the separate single-column control at maximum
relative residual `4.98e-9`. PyQUDA read all complex128 array elements
and spin-color columns exactly on 16 ranks. Job `2171855` published the
NPY to `~/lqcd-run/mg-l24-generated-propagator-publication-run01` and
verified its digest after the copy. See [end-to-end verification](generated-lime-propagator/).

Job `2171846` uses the verified, preprocessed gauge slabs and same
source to screen coarse iteration caps 14, 40, and 80 and a tighter
coarse residual target. Its two-column runs use one common hierarchy.
Any faster setting still needs full12 independent verification before use.

Job `2171803` compares the verified cap-14 solve with three hierarchy
construction budgets. It holds the input, node, seed, initial smooth
count of 12, and all solve settings fixed. The plans use two passes
with three updates, one with three, and one with two. Each plan has
one warm-up, three measured full12 calls, and independent verification.
See the [setup plans](setup-budget/).
