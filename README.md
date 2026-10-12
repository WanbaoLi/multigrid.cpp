# multigrid.cpp

A deliberately small, readable CPU **Wilson–Clover multigrid** reference implementation in C++17.

This is a correctness-oriented code base: every multigrid operation (coarse operator
construction, prolongation, restriction, and the V-cycle) is kept visible and explicit
rather than hidden behind optimised kernels. It is intended as a study/reference
implementation, not a production solver.

## Features

- Wilson–Clover Dirac operator on a 4D lattice
- Canonical 48-DOF coarse basis (with a historical 12-DOF diagnostic mode)
- Coarse operator assembly plus a matrix-free RAP (`A_c` vs `A_c = R A P`) cross-check
- Flexible GCR outer solver with an optional multigrid V-cycle preconditioner
- OpenMP enabled by default when available

## Layout

```
include/    public headers
  clover.h  gauge.h  field.h     core lattice / gauge / field types
  dslash.h  dirac.h              hopping term and Dirac operator
  multigrid.h                    coarse-grid structures and V-cycle API
  gcr.h     options.h runtime.h  solver and CLI options
src/        implementations
  field.cpp gauge.cpp clover.cpp dslash.cpp dirac.cpp gcr.cpp multigrid.cpp main.cpp
```

Field memory layout is
`field[(site_index * nrhs + rhs) * 12 + spin * 3 + color]`
with `site_index = (t, z, y, x)`.

## Build

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

CMake options:

| Option             | Default | Description                                  |
| ------------------ | ------- | -------------------------------------------- |
| `MULTIGRID_OPENMP` | `ON`    | Link OpenMP when the compiler supports it     |
| `MULTIGRID_NATIVE` | `OFF`   | Add `-march=native -mtune=native` (GCC/Clang) |

## Usage

```
multigrid --gauge gauge.bin --source source.bin --solver gcr|mg [options]
```

Common options:

| Flag                        | Meaning                                                  |
| --------------------------- | -------------------------------------------------------- |
| `--solver gcr\|mg`          | Plain GCR solve or multigrid-preconditioned solve         |
| `--basis-file FILE`         | Canonical 48-DOF basis for MG (default `basis.bin`)       |
| `--basis canonical\|clover` | Imported 48-DOF or historical 12-DOF diagnostic basis     |
| `--dims X Y Z T`            | Lattice dimensions (default `24 24 24 64`)                |
| `--tol VALUE`               | Relative true-residual tolerance (default `1e-12`)        |
| `--maxiter N`               | Maximum outer updates (default `100`)                     |
| `--restart N`               | GCR Krylov length (default `8`)                           |
| `--nrhs N`                  | Contiguous right-hand-side count (default `1`)            |
| `--point X Y Z T S C`       | Point source used when `--source` is omitted              |
| `--out FILE`                | Solution / diagnostic prefix (default `cpu_mg_solution.bin`) |
| `--operator`                | Export `A*source`, Clover and hopping contributions       |
| `--check-ac` `--check-only` | Check preassembled `A_c` against matrix-free RAP          |
| `--trace DIR`               | Export the first V-cycle and coarse residual history      |
| `--coarse-source FILE`      | Use one coarse input for both `A_c` and RAP validation    |
| `--validate-solution FILE`  | Recompute the true residual of an existing solution       |
| `--diagnose-ac`             | Diagnose individual coarse stencil blocks                 |
| `--benchmark`               | Time repeated operator applications                       |
| `--help`                    | Show full help                                            |

Without `--gauge` a unit gauge is used. MG blocks are fixed at `6 6 6 4`; no implicit
basis generation is performed.

## Status

Reference implementation. The `tests/` sources referenced by `CMakeLists.txt`
(`tests/validation.cpp`, `tests/core_test.cpp`) are not part of this repository yet, so
configure the build with `-DBUILD_TESTING=OFF` and without the `multigrid` target if you
only want the core library:

```sh
cmake -S . -B build -DBUILD_TESTING=OFF
```
