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
- Job `2169363`, output `~/lqcd-run/mg-l24-reliable-sap-run01`. One
  hierarchy and the frozen `820918f` library. The three interleaved cases
  test the control, fusing the FP64 residual update and norm, and splitting
  SAP work by block and RHS to balance the thread team. Each case receives
  three timed rounds following its warm-up, with independent verification.
- Job `2169391` passed the actual PyQUDA MPI2 loader test. The output
  matched every element of all twelve input columns after the EO conversion.

The old PyQCU run failed because the packaging subprocess timed out after
60 seconds. The replacement records packaging independently of the physics
benchmarks. Earlier attempts in this campaign hit the shared-directory quota.
Builds and benchmark arrays now use the compute node's temporary filesystem.

## HMC

- Job `2169360` compares direct block assembly to the original dense
  expansion on the same fields and momenta at `2⁴` and `2³×4`, then runs
  an 80-trajectory leapfrog chain.
- Job `2169361` uses five Omelyan steps per trajectory, compared with ten
  leapfrog steps. Both use eleven force evaluations. The ten-test physics
  suite passed on cn12038. In the equal-force one-field test, absolute
  energy error was `0.0210409452` with Omelyan and `0.1337056014` with
  leapfrog. Chain statistics and configuration verification follow separately.
- Job `2169372` checks the matrix-free Wilson–Clover application and its
  link gradient against the dense reference at both sea masses. All eleven
  checks passed. Job `2169405` extends the comparison to the even Schur
  operator, the local odd-site Clover determinant and the log-weight gradient.

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
