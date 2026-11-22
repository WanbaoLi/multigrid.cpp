# Grid Wilson–Clover wall sources on node5006

The benchmark uses upstream [Grid](https://github.com/paboyle/Grid) at
`3232b438f2cf729e515c185e2dbf29d7cc276bb7` and
[c-lime](https://github.com/usqcd-software/c-lime) at
`924aa0fce27a6cd73d94c9adc4b995f00e13232b`. The Grid source checkout is
`~/Grid` on node5006. GCC 13.4.0, MPICH, Grid GEN SIMD (64-byte vectors),
and the generic Wilson kernel are used. The topology is 16 MPI ranks
(2 per NUMA domain) with 16 OpenMP threads per rank, using the
repository's physical-core affinity launcher.

The driver reuses Grid's Wilson–Clover mixed-precision multigrid implementation
from `tests/solver/Test_multigrid_common.h`. It uses two levels, 40 coarse
basis components (20 near-null vectors and chiral doubling), and blocks
`3×6×6×2`. The outer solver is double-precision FGMRES on the normal
equations, with the single-precision MG preconditioner and internal
tolerance `1e-10`. The acceptance test applies the full Wilson–Clover
operator in double precision and requires each relative residual to meet
`1e-8`. The 12-column timing is the elapsed time for twelve sequential
solver calls sharing the hierarchy.

The verified `24³×64` `cfg_5000` is the same fixture as the H20 benchmark,
with SHA-256 `f9d2ae770c82bdb80c64491f7301c969420c25a5ba4645e406ef788efd210326`.
Grid reads and verifies the LIME configuration, applies one periodic
four-dimensional stout step with rho 0.125, and solves with mass −0.279,
Clover coefficient 1.160678675188, and an antiperiodic temporal boundary.
Each source is a unit wall at `t=0` in one spin–color component.

The run time is the maximum rank's time spent in the solver calls. Gauge
reading, stout, construction of Clover and the MG hierarchy, transformation
of the RHS for the normal equations, and explicit full-residual checks are
outside the timing. All solves start at zero. The first sample warms up,
the second is the formal result, and the third checks stability.

## Build and run

The working directory on node5006 is `~/.cache/grid-node5006-wall`. Prepare
`deps` there with conda-forge `gmp`, `mpfr`, `fftw`, and `mpich`.
Build c-lime with CMake Release and
`-DCMAKE_POSITION_INDEPENDENT_CODE=ON` into `lime-install`, and run
`~/Grid/bootstrap.sh` from the Grid source directory. The script uses
the GCC 13 toolchain prepared for the H20 tests and OpenSSL from the
existing Miniconda prefix.

```bash
ssh itp
ssh node5006
work="$HOME/.cache/grid-node5006-wall"
revision=bd0c4605f6484b0efd8e9cff35f4e2c822613150
bash "$work/driver-$revision/experiments/node5006-grid-wall-20261122/run.sh"
```

The script builds the Grid core and its single- and double-precision
Wilson–Clover instantiations, links the driver, verifies the input SHA-256,
pins ranks to allowed physical CPUs, and runs the benchmark. Full build
and run logs and large input data stay on the server.

The driver compiles against an include override applied by
`grid-float-blas.patch`. It fixes the scalar type and accumulation in
Grid's batched inner-product template, which is instantiated while compiling
the single-precision aggregation class. The benchmark runs the standard
aggregation setup. The affected template belongs to HDCG refinement.
