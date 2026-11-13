# Repository layout

The `develop` branch contains the source needed to build, test and run the
solver. Each top-level directory has one responsibility:

| Directory | Purpose |
|---|---|
| `src/` | C++ implementation, shared native solver, hardware kernels and internal headers |
| `include/` | The installed public header `lqcd.h` |
| `bindings/lqcd_cpu/` | Python `lqcd_cpu` package for ctypes, mpi4py, LIME, stout and propagator I/O |
| `tools/` | Build, NUMA launch, input and validation commands |
| `tests/` | Unit, MPI and runtime tests |
| `benchmarks/` | Reproducible benchmark drivers and independent checks |
| `docs/` | Algorithm, API, platform, runbook and result documentation |
| `docs/reference/` | Original Kunpeng manuals and their integrity metadata |
| `profiles/` | Explicit machine and solver configurations |
| `experiments/` | Categorized, referenced experiment records and provenance |
| `skills/` | Frozen optimization references used by the project |
| `cmake/` | Build and CTest configuration |

`include/lqcd.h` is the only installed C ABI header. The previous
`include/lqcd/core` and `include/lqcd/runtime` headers are implementation
headers and now live beside their C++ sources under `src/`; this keeps the
public installation small and makes the API boundary explicit.

`bindings` is the Python source root and `lqcd_cpu` is the importable package.
Callers continue to use `from lqcd_cpu import Solver` after adding `bindings`
to `PYTHONPATH`.

The repository keeps structured experiment data needed to explain a result,
but excludes raw test logs, build trees, binaries, large input configurations
and generated propagator arrays. Temporary comparison directories are ignored
and must remain outside the checkout.
