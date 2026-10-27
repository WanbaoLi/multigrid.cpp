# CPU library comparison on Xeon 8458P

The drivers use the existing post-stout `24x24x24x64` LIME-derived gauge and
one spin-0/color-0 point source. All solve the same Clover-Wilson equation:
mass=-0.277, csw=1, periodic space, antiperiodic time. Final full residual gate
is 1e-8. No run starts from a previous solution.

`prepare.py` creates binary input from
`PyQCU/data/lime_mg_20261013/input.h5`. It explicitly verifies the unitary spin
basis transformation for DDalphaAMG/openQCD. Their native operator is
`M=D/(2*kappa)`, so both RHS and probe image are rescaled. The same scaling is
used for Grid, whose spin basis already matches the canonical one.

Each driver verifies a full random-field `M*probe` before solve timing, then
checks full residuals after both solves. `verify.py` converts saved solutions
back to the canonical layout and checks them against QUDA. Finally `run.sh`
calls the independent `multigrid.cpp` full operator on all three solutions.

## Sources and builds

Sources/builds/dependencies are isolated under `.cache/cpu_libraries/`.

| Library | Version | Build used |
|---|---|---|
| ETMC DDalphaAMG | `9c723a818b4b1d69b7547d33087ab0c520eba38c` | GCC 14.4, MPI 5.0.10, SSE/OpenMP, `-O3 -march=native -fopenmp -fcommon` |
| Grid | `3232b438f2cf729e515c185e2dbf29d7cc276bb7` | GCC 14.4, MPI 4.1.6, AVX512, `--dslash-asm`, OpenMP |
| openQCD | 2.4.3 | GCC 14.4, MPI 5.0.10, `AVX FMA3 PM`, `-O3 -mfpmath=sse -mno-avx -fopenmp` |

The downloaded openQCD archive SHA256 is
`d7c84e41caea0282dd065bbc62626a0446fae65a1f3530ea1f1a5d75cdfe90de`.
Eigen 3.4.0 SHA256 is
`b4c198460eba6f28d34894e3a5710998818515104d6e74e5cc331ce31e46e626`.

DDalphaAMG uses its documented `BASIS0` option in `src/clifford.h` so its
spin convention matches openQCD. No solver kernels were changed. Build:

```bash
make -C .cache/cpu_libraries/DDalphaAMG -j16 \
  lib/libDDalphaAMG.a include/DDalphaAMG.h \
  CC=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/mpicc \
  'CFLAGS=-std=gnu99 -O3 -march=native -fopenmp -fcommon -Wno-error=implicit-function-declaration' \
  LIMEFLAGS= LIMELIB=
```

LIME parsing is intentionally external to all measured solves; all three
libraries consume exactly the same already-smeared gauge.

Grid dependencies GMP, MPFR and FFTW are in `.cache/cpu_libraries/deps`;
Eigen 3.4.0 is linked under `Grid/Grid/Eigen`. After its bootstrap/filelist
generation, the configure options are:

```text
--enable-simd=AVX512 --enable-comms=mpi-auto
--disable-gparity --disable-fermion-reps
--with-fftw=.../deps --with-gmp=.../deps --with-mpfr=.../deps
CXXFLAGS='-O3 -march=native'
```

Only `make -C Grid libGrid.a -j16` is required from the build tree; building all
Grid examples/benchmarks is not required. Driver compilation uses the build's
`grid-config --cxxflags --ldflags --libs`, plus explicit source and generated
`Grid/Config.h` include paths. Use the matching MPI 4 launcher for Grid.

`openqcd.cmake` builds the MPI modules (excluding `modules/nompi`) and the
driver. Its `include/global.h` geometry is:

```text
NPROC = (4,1,1,1)
L     = (16,24,24,24)
L_TRD = (16,8,12,8)
```

Therefore there are 18 threads per rank and 72 physical cores in total.
openQCD's geometric thread blocks cannot produce 88 for this volume: the
factor 11 does not divide any lattice dimension. We do not oversubscribe or
alter the physical lattice to claim an 88-core result.

## Solver choices

- DDalphaAMG: library-default three-level adaptive mixed-precision MG,
  first aggregation `(t,z,y,x)=(4,6,6,6)`, deterministic per-rank seeds,
  8 ranks × 11 threads. Iterations are outer FGMRES counts.
- openQCD: deflated SAP-GCR, SAP/subspace blocks 4^4, 24 deflation vectors,
  6 generation iterations, SAP MR count 4, cycles 5, GCR restart 24.
  4 ranks × 18 threads. Iterations are outer GCR counts.
- Grid: even-odd BiCGStab with mixed-precision iterative refinement,
  inner tolerance .01, double final correction. Target Schur tolerance 1e-9
  ensures the common full-system gate 1e-8. 8 ranks × 11 threads.
  Inner BiCGStab, final-double and refinement counts are recorded separately;
  their sum is not an MG outer-iteration count.
- PyQCU: experimental real/imag split + precomputed tensors + torch.compile,
  existing CPU BiCGStab, 88 threads.
- multigrid.cpp: existing full-system MG/GCR(8), 88 threads, imported canonical
  basis from `.cache/runs/run-Kc1cnYeU/quda/quda_near_null_canonical.bin`.

## Re-run

After builds, run from the `lqcd` workspace:

```bash
OPENBLAS_NUM_THREADS=1 /public2/home/lwb_720/miniconda3/envs/pytorch/bin/python \
  multigrid.cpp/benchmarks/reference-libraries/prepare.py
bash multigrid.cpp/benchmarks/reference-libraries/run.sh
```

The script creates a fresh run directory and records it in
`.cache/cpu_libraries/last_run.txt`. All five implementations are run
sequentially. Setup, I/O, compilation, and independent checks are excluded
from solve timings. Use the second solve; preserve the first for transparency.

This is a comparison of implemented solver stacks, not a controlled comparison
of the same algorithm or equal precision at every internal level. The action,
gauge, RHS and full-operator correctness gate are aligned. The 72-core openQCD
row must remain labeled, and all results concern one propagator column.
