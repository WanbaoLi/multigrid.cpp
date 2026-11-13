# Repository layout

The `develop` branch keeps the files needed to build, test, run and understand
the project:

| Directory | Purpose |
|---|---|
| `src/` | Project implementation and hardware backends |
| `include/` | Public and core headers |
| `python/` | CPU runtime Python wrapper and workflows |
| `tools/` | Build, NUMA launch, input and validation commands |
| `tests/` | Unit, MPI and runtime tests |
| `benchmarks/` | Reproducible benchmark drivers and independent checks |
| `docs/` | Algorithm, backend, platform and runbook documentation |
| `profiles/` | Explicit machine and solver configurations |
| `experiments/` | Categorized, referenced experiment records and provenance |
| `skills/` | Frozen optimization references used by the project |
| `cmake/` | Build and CTest configuration |

Temporary comparison controllers and raw output copies were removed from the
main tree. Historical commits remain in Git history, while large input files,
build directories, binaries and local caches remain outside the repository.
