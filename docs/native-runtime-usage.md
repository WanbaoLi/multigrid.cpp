# Project-owned CPU MG runtime

## Build

From the parent `lqcd` workspace:

```bash
MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda \
BUILD_DIR="$PWD/multigrid.cpp/build/runtime" \
LQCD_TEST_PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
bash multigrid.cpp/tools/build_runtime.sh
ctest --test-dir multigrid.cpp/build/runtime --output-on-failure
```

The Open MPI test commands explicitly use `--bind-to none` so Open MPI 5
process binding does not confine an OpenMP test rank to one core. The NUMA
launcher likewise disables MPI binding before applying its own CPU placement.

The default is `LQCD_DD_REFERENCE=OFF`. `liblqcd_cpu.so` contains project-owned
setup, transfer, coarse assembly, SAP and Krylov code. It neither calls nor links
DDalphaAMG, Grid, openQCD or QUDA. The old reference executable remains available
as a separately invoked numerical oracle.

## Run using real PyQUDA CPU fields

The explicit `threads=88` example below reproduces the original manual
88-core acceptance configuration. For a resource-independent application,
omit `threads`: the binding uses the first `OMP_NUM_THREADS` value, then the
process CPU affinity (or CPU count where affinity discovery is unavailable).
Use the NUMA launcher below to select physical cores rather than SMT threads.

```python
from lqcd_cpu import Solver

with Solver([24,24,24,64], [1,1,1,1],
            backend="x86", mass=-0.277, csw=1, t_boundary=-1,
            threads=88, levels=2, block=[6,6,6,4], seed=1024,
            normalization="mass") as mg:
    mg.load_pyquda_gauge(gauge)  # host complex128, untwisted links
    setup_seconds = mg.setup()  # generates its own near-null basis
    x1 = mg.solve_pyquda(source, tol=1e-8)
    x2 = mg.solve_pyquda(source, tol=1e-8)
    print(mg.last_result)
```

Set `PYTHONPATH=multigrid.cpp/python` and
`LQCD_CPU_LIBRARY=$PWD/multigrid.cpp/build/runtime/liblqcd_cpu.so`.
Use the same MPI implementation as mpi4py. For the single-process 88-core
profile, run under `numactl --interleave=all` with `OMP_PROC_BIND=spread`,
`OMP_PLACES=cores`, `OMP_NUM_THREADS=88`, `OPENBLAS_NUM_THREADS=1`.
The second solve still starts from zero, only the hierarchy/workspace is reused.

The `mass` equation is `Mx=b`; the `kappa` equation is `(2*kappa*M)x=b`.
Input rescaling must be explicit when matching a PyQUDA high-level helper.
The native public API keeps all previously tested PyQUDA EO-x field layout,
lexicographic layout, source preservation and propagation-column conventions.

## Real-input reproduction

These explicit 88-thread and 8×11-thread commands are historical manual
acceptance profiles, not fixed runtime requirements.

```bash
export LQCD_CPU_LIBRARY="$PWD/multigrid.cpp/build/runtime/liblqcd_cpu.so"
OMP_NUM_THREADS=88 OMP_PROC_BIND=spread OMP_PLACES=cores OPENBLAS_NUM_THREADS=1 \
numactl --interleave=all /public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
  multigrid.cpp/benchmarks/runtime/benchmark_runtime.py --backend x86 \
  --grid 1 1 1 1 --threads 88 --levels 2 --twelve-rhs \
  --output .cache/native-mg/reproduction
OPENBLAS_NUM_THREADS=1 /public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
  multigrid.cpp/benchmarks/runtime/verify_runtime_columns.py .cache/native-mg/reproduction
```

Input comes from the unchanged LIME-derived HDF5 fixture. The production setup
does not read `.basis`/`.stencil` caches or imported external null vectors.
Development-only `bench_native` can load those assets for kernel isolation;
such diagnostic runs are not the end-to-end acceptance run.

MPI alternative: `mpirun -n 8 --map-by ppr:4:socket:PE=11 --bind-to core`,
`--grid 1 1 1 8 --threads 11`, with `OMP_PROC_BIND=close`.
Only t-slab MPI is currently supported. Unsupported x/y/z decompositions,
three-level mode and periodic time are rejected explicitly. Clover csw is configurable.
See `native-backend-status.md` for replicated setup/verification storage limits.

For direct LIME input, optional CPU stout smearing, twelve point-source columns
and PyQUDA-loadable output, see [the complete propagator workflow](propagator.md).

## Next targets

The compute kernel boundary is `src/solver/native/kernels.hpp`, selecting x86
AVX512 or AArch64 ARM kernels. Shared MG logic resides in `src/solver/native/`.
ARM NEON clover and portable OpenMP SIMD Wilson kernels are implemented;
SVE/SME and Sunway remain future targets and must meet the same numerical gates.
Future multi-node work must first remove the
remaining global setup/verification replicas and generalize halo decomposition.

## NUMA-aware launch

`run_numa.py` discovers physical cores from Linux sysfs and the caller's CPU
cpuset. It starts one MPI rank for each selected NUMA node, pins that rank to
that node, and sets OpenMP to the available physical cores. The default uses
all allowed cores in each NUMA node, so it does not assume 88, 256, or 304
cores. Open MPI must be the same MPI implementation used by `mpi4py`.

```bash
# Inspect placement without starting MPI:
python multigrid.cpp/tools/run_numa.py --dry-run -- \
  python multigrid.cpp/benchmarks/runtime/benchmark_runtime.py --output .cache/native-mg/numa

# Run (grid and threads are inferred by the benchmark):
python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/benchmarks/runtime/benchmark_runtime.py \
  --output .cache/native-mg/numa
```

Use `--numa-nodes 0,2-3` to select nodes or `--threads N` to use the same
number of physical cores per rank. The runtime currently requires one complete
time aggregate per t-slab, so the launcher rejects rank counts that do not
divide `Lt` or leave complete `block[3]` aggregates. It also rejects a thread
override that exceeds a selected NUMA node's allowed physical cores. Keep
Open MPI's process binding disabled (`--bind-to none` is supplied by the
launcher); the launcher performs the final affinity assignment inside each
rank. Communication remains collective at the public API boundary.
The launcher geometry defaults to the real fixture (`--lattice 24 24 24 64`,
`--block 6 6 6 4`); override both to match other applications. These flags
validate placement and do not modify application arguments.

The launcher sets CPU affinity only. Under the normal Linux memory policy,
newly touched pages are placed near the bound process. It does not enforce or
reset a memory policy and does not migrate existing pages. Launch without
an inherited `numactl --interleave` policy when testing NUMA-local allocation. This launcher is currently
single-host only and does not claim multi-node or Sunway support. NUMA metadata
can be used on Linux ARM. See [ARM backend validation](arm-backend.md) for the
Kunpeng-920 numerical backend and its verified ISA scope.


## MPI thread support and communication diagnostics

The caller owns MPI initialization and must keep the communicator alive until
all solver contexts are closed. Initialize with at least `MPI_THREAD_FUNNELED`
when using more than one OpenMP thread; the runtime checks this. All MPI calls
and collective public API calls are made on the MPI main thread. The runtime
does not require `MPI_THREAD_MULTIPLE` or background MPI progress threads.
Different ranks may select different OpenMP thread counts without changing the
collective lattice/operator configuration.

The default native path overlaps nonblocking time-boundary exchange with
interior work. Set `LQCD_HALO_OVERLAP=0` for a blocking-order comparison, keeping
the same lattice, source, seed, rank placement and thread counts. For example:

```bash
LQCD_HALO_OVERLAP=0 python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/benchmarks/runtime/benchmark_runtime.py \
  --output .cache/native-mg/numa-blocking
LQCD_HALO_OVERLAP=1 python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/benchmarks/runtime/benchmark_runtime.py \
  --output .cache/native-mg/numa-overlap
```

Run these consecutively, without concurrent CPU benchmarks, and compare second
and steady complete-API times after the correctness checks pass. Setting
`LQCD_HALO_PROFILE=1` additionally prints a `native_halo_profile` JSON line for
each solve. Fine and coarse counters include call counts, outgoing bytes,
packing/posting, waiting, interior/boundary computation, overlap-region and
operator-total durations. Each reported metric is an **independent maximum
across ranks of that rank's local sum**. The metrics are nonadditive: maxima
can come from different ranks and overlap-region durations include concurrent
work. They are diagnostics, not a decomposition of solver wall time, a direct
measurement of hardware communication progress, or proof of a speedup. Disable
profiling for final performance comparisons.

To independently check a benchmark run that exported only its single source:

```bash
python multigrid.cpp/benchmarks/runtime/verify_runtime_columns.py \
  .cache/native-mg/numa-overlap --single-column
```

The verifier's OpenMP count comes from `--threads`, `OMP_NUM_THREADS`, or the
process affinity, in that order. Omitting `--single-column` retains the complete
12-column verification path for runs made with `--twelve-rhs`.

## Correction tolerance and setup update

`LQCD_ADAPTIVE_CORRECTION=1` is the default. Each mixed-precision correction
uses a relative inner tolerance
`clamp(0.5 * requested_tolerance / current_full_relative_residual, 1e-3, 0.1)`.
This avoids unnecessary float iterations near the final target; the full double
residual is recomputed after every correction and remains the acceptance gate.
Set `LQCD_ADAPTIVE_CORRECTION=0` for the fixed `1e-3` inner-tolerance reference
when comparing iteration counts and timings.

`LQCD_SETUP_UPDATE=inverse` retains the default adaptive inverse-iteration setup.
The optional `LQCD_SETUP_UPDATE=paper` uses the test-vector update corresponding
to Algorithm 5.1 of the original DDalphaAMG paper. In the measured two-rank,
22-thread-per-rank comparison, the second API solve took 3.829 seconds for
`paper` and 3.713 seconds for `inverse`. This does not demonstrate a benefit
for the paper update; `inverse` remains the default. See
[numa-results.md](numa-results.md) for the full benchmark context.
Both choices build the hierarchy from the project's own code and seeded test
vectors.

Set these environment variables consistently on **all MPI ranks before context
creation/setup**. Do not change them between solves of an existing context.
Record the selected setup and correction modes alongside the seed, process grid,
thread placement and second/steady timings when comparing runs.


## Even-odd preconditioning

Production defaults are `LQCD_SAP_EO=1` and `LQCD_COARSE_EO=1`. They enable
project-owned even-odd preconditioning inside the fine SAP block solves and
coarse solve. External PyQUDA EO-x packing and the public full Wilson-clover
equation are unchanged. Fine fields use an internal block-local even-odd layout;
this is separate from the external field layout.

Each fine SAP block uses four MR steps on its even Schur complement and then
reconstructs the odd component. The coarse solver uses even-odd Schur GCR and
odd reconstruction, with its `0.1` relative residual criterion measured against
the original full coarse RHS. The outer solver still solves the full
Wilson-clover system, and double full-residual checks enforce the requested
physical tolerance. Local Schur stopping criteria are not substitutes for this
outer acceptance gate.

The fine EO packing requires an even x block extent. Other block extents may
be odd provided the existing lattice/decomposition rules hold; aggregate counts
must remain even and at least four per direction. Set either flag to `0` only
for diagnostic comparisons with its legacy solver. Set both flags consistently
on every MPI rank before context creation/setup. The `inverse` setup update
remains the default.

The latest correction-target safety factor is `0.5`. Earlier EO measurements
using factor `0.25` are intermediate results and must not be presented as final
acceptance of the changed factor; see the dated benchmark report for provenance.

## Tune thread counts without rebuilding the hierarchy

After `setup()`, call `Solver.set_threads(n)` collectively on the MPI main
thread to change each rank's OpenMP count. Counts may differ across ranks.
This updates compute resources only: it does not rebuild the hierarchy or
change the operator, source, seed, or requested tolerance. The context must be
Ready. Positive counts and MPI thread support are checked collectively before
any rank's configuration changes. Historical libraries lacking the new C ABI
symbol can still load; calling the setter on them reports unsupported.

The setter does not enlarge CPU affinity or OpenMP places. Allocate the maximum
CPU set needed for the entire sweep at launch. In particular, keep the NUMA
launcher's `--threads` unset to expose all allowed physical cores, and pass the
initial solve count to the **benchmark**. For example, this machine currently
has 44 physical cores per NUMA node:

```bash
python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/benchmarks/runtime/benchmark_runtime.py \
  --threads 22 --thread-sweep 32 44 11 --repeats 3 --twelve-rhs \
  --output .cache/native-mg/numa-thread-sweep
```

These counts illustrate this machine's allocation, not runtime constants;
choose counts within the allowed physical cores of every rank on another
machine. One generated hierarchy is reused for all cases. The benchmark
records each case's first/second/steady samples and selects the count with the
best measured steady median for the subsequent 12-column propagator. The
actual propagator count is recorded as `twelve_rhs_threads`; do not infer it
from the initial run's `threads`. This bounded sweep identifies the best tested
configuration, not a hardware-independent optimum.
