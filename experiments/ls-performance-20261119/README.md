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
  upstream URL as origin.
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
  the same warmed full12 API scope and 12.682 s in the native solver.
  Its separate hierarchy setup took 222.573 s. Independent verification
  passed all thirteen fields with maximum residual `4.82e-9`. In this
  workload, the reusable-hierarchy API control was 17.67× faster than
  the complex128 BiCGStab path. The separate raw periodic single-source
  tests measure a different operator and right-hand side.
- Job `2169656` retries Legacy MG. Upstream writes a HDF5 cache root
  and a sibling JSON manifest. The original controller passed a JSON
  root name, so the paths collided. The retry passes an HDF5 root.
- Job `2169510`, output `~/lqcd-run/mg-l24-reliable-sap-run02`. One
  hierarchy and the frozen `820918f` library. The three interleaved cases
  test the control, fusing the FP64 residual update and norm, and splitting
  SAP work by block and RHS to balance the thread team. Each case receives
  three timed rounds following its warm-up, with independent verification.
- Job `2169391` passed the actual PyQUDA MPI2 loader test. The output
  matched every element of all twelve input columns after the EO conversion.
- Job `2169509` builds the opt-in AArch64 coefficient tiling candidate
  `6b7c1c7`. Threads visit all RHS columns before moving to the next
  64- or 128-site tile. The first MPI2 test geometry violated the native
  solver's coarse extent constraints. Job `2169687` uses a valid MPI2
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
