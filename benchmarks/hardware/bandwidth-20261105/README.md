# NUMA-bound streaming bandwidth benchmark

This independent microbenchmark measures logical Read / Copy / Triad bandwidth;
it does not modify the solver and is not a hardware memory-controller counter.
Build on the actual target with `-O3 -std=c++17 -pthread -march=native -ldl`, without
fast-math. Supported kernels explicitly use ordinary SVE or AVX512 loads/stores.
Neither target uses non-temporal stores. Inspect the generated code.

The completed comparison is kept as an external run artifact; raw reports and
large evidence archives are intentionally outside the source tree. Its
headline uses 48 GiB on each platform and HPCKit 26.1 for LingSheng HBW
classification. The older 25.1 SDK misclassifies the final memory-only domain
in this allocation; the all-domain 25.1 diagnostic is excluded. Exact final
job scripts and plans belong in the external evidence archive, including
`memory261-large.sh`, `ddr261.plan` and `hbw261.plan`.

The text plan has one worker per line: `group_id cpu_id memory_node` (comments
begin with `#`). Workers in a group share three arrays and divide them into
disjoint ranges. All workers must use distinct allowed physical cores; each
group must have one explicit allowed memory node. For example:

```text
0 0 0
0 1 0
1 32 1
1 33 1
```

Run:

```sh
./bandwidth_bench --plan plan.txt --mib-per-array-per-group 512 --passes 4 --repeats 5 > result.json
```

Each array has a separate guarded VMA. `MPOL_BIND` is applied before parallel
first touch; allocation or binding failure is fatal. Transparent huge pages are
disabled for these mappings to make `/proc/self/numa_maps` base-page accounting
unambiguous. After touch and after measurement the benchmark queries sampled
pages with `move_pages`, and records full per-VMA counts from `numa_maps`. A
placement is accepted only if one of those methods verifies all queried pages
on the requested node. Both methods and their raw errors/counts are preserved.
The program loads system `libnuma.so.1` and calls its typed `mbind` wrapper,
with a full unsigned-long node mask instead of `target+1` as its bit capacity;
this avoids old-kernel mask-boundary behavior without relaxing page validation.
The benchmark never silently falls back to default memory. Node identity alone
does not establish HBM technology: the orchestrator must retain topology, SDK
classification and capacity evidence for its HBM/DDR labels. With optional
`--kupl-lib /absolute/path/libkupl.so`, the installed `kupl_hbw_verify(ptr,bytes,0)`
also classifies every complete array after initialization and after timing;
`sdk_verify_before/after` records 1=HBW, 0=not entirely HBW, -1=SDK error,
-2=SDK not requested. The orchestrator must gate the expected HBM/DDR class.

Double precision kernels use stable arrays `a=1, b=2, c=3`. Read sums `b`; Copy
sets `a=b`; Triad sets `a=b+3*c`. Every timed sample records exact analytical
checksums, and Copy/Triad fully scan their output outside timing. Every worker
is bound to a single physical CPU, checked before and after each sample, with
its actual SVE vector length recorded. Successful output has `status=PASS` and
all `max_abs_error=0`.

Logical traffic is Read=8, Copy=16, Triad=24 bytes per double element per pass.
Ordinary write-allocate traffic can exceed these values; no claim is made that
logical GB/s equals all memory-controller bus bytes. GB/s means 10^9 bytes/s.

One warm pass is excluded for each kernel. Each sample starts after a team
barrier, then performs continuous passes without per-pass team barriers.
Compiler memory fences (no hardware instruction) preserve each repeated pass.
Its wall interval is earliest worker start to latest worker finish, including
startup skew and scheduling delays; it is
not the sum of independently measured worker peak bandwidths. Every original
sample is preserved and the median is reported. Ensure array sizes greatly
exceed the relevant shared cache and repeat at a larger size before calling
the result sustained external-memory bandwidth. Allocation, first touch,
placement queries and checksum scans are excluded from timed intervals.

JSON fields: `schema`, `status`, `hostname`, `isa`, `precision`, `store_policy`,
`threads`, `groups`, `bytes_per_array_per_group`, `passes`, `repeats`, `placement`
(per array mbind and before/after page-residence evidence), `workers` (CPU and
SVE checks), and `kernels` (Read/Copy/Triad samples, logical bytes, GB/s and
per-thread timestamps/checksums, median/max). Failures return nonzero.
