# Repository refactor, 2026-11-13

The code revision is `941e350786be26b86a846048b57923387d213733` on `develop`.
See [the directory responsibilities](repository-layout.md).

## Source and API paths

- The public header is `include/lqcd.h`, installed as `<lqcd.h>`. C ABI symbols,
  structures and numerical operations are unchanged.
- Internal mathematical and runtime headers now live under `src/core/` and
  `src/runtime/`, beside their implementations. Internal include paths are
  private to the targets that need them.
- The Python source root is `bindings/`. The package and import remain
  `lqcd_cpu`; current CMake tests, tools, benchmarks and runbooks use the new
  path.
- The DOCX and PDF Kunpeng manuals live in `docs/reference/` with unchanged
  SHA256 checksums. No manuals or paper extracts remain at the repository root.

## Generated artifact removal

Removed 672 raw log/stdout/stderr files, three CMake caches and 168 duplicate
single-value residual files. Complete per-column values remain in structured
`verification.json` reports. Source, proposals, timing summaries and decisions
remain under the dated experiment directories.

Historical manifests still describe their original full exports and source
paths. They are preserved without rewriting hashes. For recovery from the
pre-cleanup commit, see [the experiment archive policy](../experiments/README.md).
New raw output, build caches and binaries are excluded by `.gitignore` and the
rules in `AGENTS.md`. Frozen reference skill contents were not changed.

## Verification

Local checks passed:

- The independent reference executable and core unit-test target compiled.
- Core and CLI CTest: four tests passed.
- Optimization framework tests: 51 tests ran, with three platform skips.
- Public header C11 syntax and Python compilation passed.
- The frozen auxiliary-source manifest verified all 127 files.
- `git diff --check` passed; no raw logs, CMake caches or duplicate residual
  outputs remain tracked.

The x86 runtime and all test targets were rebuilt on node5005 using GCC 14.4,
Python 3.12.14, Open MPI 5.0.10 and `tools/x86/build.sh`. The optional native
benchmark passed a C++17 syntax check with the migrated internal header paths;
the changed shell scripts passed `bash -n`. CMake installation into an external
prefix and a C11 compilation using the installed `<lqcd.h>` also passed.

The complete node5005 CTest run passed: **48/48, zero failures**, 553.54 seconds.
This includes serial, two/four-rank MPI, twelve-column batching, halo, EO SAP,
LIME, stout, propagator I/O/workflows and tuning contracts. ARM-only SVE kernel
checks print their target-conditional skip on x86; this is not a new LingSheng
hardware qualification.

An initial test run was interrupted after observing both unbound MPI ranks'
main threads on CPU 0 under OpenMP `close`. The x86 build script now configures
CTest with `--map-by slot:PE=2 --bind-to core`. This allocates separate core
sets to test ranks; production NUMA launch parameters remain in `run_numa.py`.

To reproduce the node5005 build and tests from the source root:

```bash
export PATH=/public2/home/lwb_720/miniconda3/envs/pyquda/bin:/public2/home/lwb_720/miniconda3/bin:$PATH
export PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python
export BUILD_DIR=$HOME/.cache/mg-layout-20261113/build
bash tools/x86/build.sh
OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close OPENBLAS_NUM_THREADS=1 \
  ctest --test-dir "$BUILD_DIR" --output-on-failure --parallel 1
```

The measured source checkout was
`/public2/home/lwb_720/.cache/mg-layout-20261113/source`. Build products and full
logs are in its parent run directory, outside that Git checkout.

This refactor does not establish a new real-configuration performance result.
