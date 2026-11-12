# CPU FP32 / FP64 register FMA microbenchmark

This is an independent compute-throughput test, not a Wilson–Clover benchmark,
LINPACK result, memory-bandwidth test or vendor theoretical peak.

Build on the allocated target CPU:

```sh
c++ -O3 -std=c++17 -march=native -pthread fma_bench.cpp -o fma_bench
objdump -d fma_bench > fma_bench.disassembly.txt
./fma_bench --cpus 16 --precision fp32 --seconds 1 --repeats 3 > single-fp32.json
./fma_bench --cpus 0,1,2,3 --precision fp64 --seconds 1 --repeats 3 > group-fp64.json
```

Use the actual scheduler-allowed physical CPUs, one worker per physical core.
The program rejects SMT siblings and CPUs outside its initial allowed affinity.
Each worker is explicitly bound to one CPU, and CPU IDs are checked again before
and after every timed sample. AArch64 SVE reports both `svcntb()` and the Linux
per-thread `PR_SVE_GET_VL`; AArch64 without compile-time SVE uses NEON. x86 requires
AVX512F. Native binaries must not be transferred to incompatible CPUs.

The timed loop keeps 24 independent AArch64 accumulators or 16 AVX512 accumulators
in vector registers. Each iteration executes two passes of vector FMA: add
`0.5 * 2^-10`, then add `(-0.5) * 2^-10`. Starting from 1, these intermediates and
the final result are exactly representable in both precisions. Every vector lane
must return to 1; the final nonzero checksum and maximum error are recorded.
`asm volatile` prevents deletion, merging or scalar replacement of the FMAs.
There are no loads, stores or clock calls in the hot iteration loop. Confirm
the generated `fmla` / `vfmadd231p[s|d]` instructions in disassembly.

For N iterations, A accumulators and L lanes, the exact arithmetic count is
`N * A * 2 passes * L * 2 FLOPs/FMA`. Integer loop-control instructions are excluded.
Thread creation, allocation, calibration, synchronization and checksum reduction
are excluded from individual kernel times. The whole-team interval is the latest
kernel end minus the earliest kernel start, so start-time skew and scheduling
delays within the team are included. Final register stores and tiny kernel
initialization are included. Each worker calibrates concurrently before timed
samples; the default target is one second per sample, three samples.

Success writes exactly one JSON document to stdout and no diagnostics to stderr.
Fields include `status`, `isa`, `precision`, `threads`, `accumulators`,
`fma_passes_per_iteration`, `flops_per_fma_per_lane`, per-worker placement/width,
per-sample `seconds`, `flops`, `gflops`, per-thread iterations/timestamps/checksum,
`median_gflops` and `max_gflops`. Always require `status=PASS` before reporting rates.
Report the median as sustained measured throughput; the largest sample is only
the best observed sample. Different clock/power policy, contention and vector
instruction throughput can affect results. This test does not exercise SME/AMX
matrix operations, GPU tensor cores or numerical solver memory access.
