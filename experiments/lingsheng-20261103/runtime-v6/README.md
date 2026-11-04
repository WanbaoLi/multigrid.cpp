# Worker8 runtime comparison and solve profile

This archive continues the hierarchy-reuse objective. The measured numerical
implementation remains accepted attempt052, source5fe1b5f, library SHA
`d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82`.
No numerical source was changed or promoted in this round. The campaign is
unfinished. Helper tests are infrastructure checks, not solver acceptance.

## Closed task141: five verified processes, incomplete runtime comparison

Actual allocation2023152, cn19483, exclusive592 CPUs; placement/setup37,
solve32 except the explicit37-thread candidate;16 MPI ranks and batch2.
Each process builds its own hierarchy, warms one full12 solve, then runs three
full12 samples from zero initial guesses. The existing independent scalar
reference checks every column and the coordinate-matched stored solution.

| Process | Steady full12 median, seconds | Independent maximum residual |
| --- | ---: | ---: |
| team32-a | 16.966943 | 4.819e-9 |
| team37 | 17.231334 | 4.819e-9 |
| team32-b | 16.048009 | 4.819e-9 |
| SDK default first control | 16.270775 | 4.819e-9 |
| SDK PASSIVE, zero spin | 37.157624 | 4.819e-9 |

All five passed all12 scalar and stored-solution checks. Maximum stored-solution
relative error among these cases was1.224e-11, below1e-6. The scalar threshold
was1e-8. The fixed-team group's control drift was5.726%, above5%;37 threads
were slower in these samples. Preserve no-adoption and avoid a precise causal
thread-speed estimate. The inherited gate text says ranges overlap whenever
the candidate is not entirely faster; that text should not be interpreted as
a mathematical claim that these particular intervals intersect.

Old-GOMP/default failed before original Solver.setup because capture expected
the wrong environment. The runtime comparison never reached its two remaining
processes or closing control, and did not adopt a runtime candidate. PASSIVE's
large slowdown is a measured observation from the partial comparison, not a
completed two-sided runtime verdict.

## Attributed failure and a new version

The actual MPI launcher prepends its library directory twice. When the frozen
benchmark later applies an explicit context LD_LIBRARY_PATH, os.environ is
replaced with that explicit value. SDK controls have no such context key and
keep the launch prefix. Version5 incorrectly added the prefix in both cases.
The environment-only task142 passed with exact failed-case launcher arguments
and stage overrides. Code inspection of the unchanged benchmark explains the
subsequent overwrite. Actual mapped DSOs must still be checked: changing
os.environ after startup is not evidence that the ELF loader changed a DSO.

New runtime-only-v6 models these two paths exactly, preserves actual sidecars,
and changes one expected-LD expression in the old audit AST. A fresh five-case
2x2 runtime bracket retains all original precision, noise, >=3% gain, disjoint
range, <=5% control-drift, loader and shared-object-closure gates. No old sample
is imported. The implementation inherits scientific trial and decision methods.
Five Linux contract tests passed, including applying the actual frozen benchmark
context function under all four combinations. The new runtime comparison and
its old-runtime native smoke were **not launched** before connection loss.
Future dispatch requires a new valid allocation and new prepared identities;
the archived concrete worker8 preparer is not permission to use an expired job.

## Task143: actual solve sampling, independent validation pending retrieval

The new solve-profile-v7 preserves the original49Hz cycles:u recording and
DWARF4096 stack collection, only for the final unranked full12 call at ranks0/8.
It preserves the original benchmark clocks and publication/validation wrappers.
Every returned column of that sampled call passed finite true-residual<=1e-8
and convergence checks. The last light diagnostic sample is saved for the
independent scalar/gold check; the sampled verbose output is not saved.

The site's perf5.10 does not accept a tid sort key. Its pid sort key includes
the task TID, as documented in the
[Linux5.10 perf manual](https://raw.githubusercontent.com/torvalds/linux/v5.10/tools/perf/Documentation/perf-report.txt).
The new decoder uses comm,pid,dso,symbol. Six Linux routing/scope/stats contracts
passed. The earlier unexecuted v6 prototype is preserved in runtime-v5.

Benchmark and all selected-rank decodes returned success. Last observed
task state at UTC05:51 was independent validation running; its final result and
cleanup have not been retrieved. The downloaded wrapper summary confirms
sampled-call checks, not independent precision completion. Diagnostic sample
median17.291392s is unranked and must not replace ordinary best timing.

The downloaded two thread reports contain32 sampled threads each. Rough sums
of the printed rounded percentages place about41% of user cycles in libgomp
and54-55% in native code. These rounded sums exceed100% slightly; an exact
period-sum postprocessor is prepared but its upload/execution was blocked.
These are CPU-cycle observations at two ranks, not elapsed-time savings or a
whole-node bottleneck proof. Fine application, local application/SAP, transfer,
and coarse application warrant inspection before selecting another kernel.

## Evidence and resumption

files-manifest.json pins140 files (3.82MB). Task141 small-evidence export
contains66 files, independently checked against original/export hashes locally.
It omits field arrays and uses the existing environment redactor. Original
remote files remain untouched. Export archive SHA:
`dab33de0f5e4d88305f06d84ff0c49454374d375f2e0828d8cb25929aa9ac4b6`.

At UTC08:20-08:25 on2026-11-04, direct SSH to10.44.9.4:22 repeatedly timed out;
itp and node5005 were reachable. Worker8's recorded safe deadlineUTC07:55:30
had passed. This is a running-condition blocker, not completion of optimization.

On reconnection: retrieve143 terminal status/cleanup, full independent result,
runtime maps and original perf data; validate their hashes. Inspect scheduler
and owned process state. Start a fresh exclusive allocation with full affinity,
SVE and HBW probes. Rebind a fresh runtime-only comparison to that epoch and
qualify the old-runtime smoke first. Then use the completed profile to select
kernel/compiler work and finish pending haloV2 ARM MPI/SVE qualification.
Final matched DDR/best/DDR, fresh node5005 comparison, coherent best-source
build/run commands and the requested GitHub upload remain outstanding.
