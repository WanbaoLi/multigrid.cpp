# Restore the previous uniform 16-MPI LingSheng recipe

The user requires both real-input geometries to use 16 MPI ranks. The temporary
C32 eight-rank health run is a diagnostic result, not the requested comparison.

Hypothesis before the run: restoring the shared immutable coefficients from
`73531ac` / `a35c3a4` makes the previous C32 16-MPI recipe usable in the current
clean directory layout. This removes per-process copies of the double gauge,
Clover, setup basis and coarse stencil. Private float/packed coefficients,
spinors, Krylov workspaces and halos remain independent. The solve algorithm
and tolerance are unchanged. Coarse setup assembly remains serialized across
MPI processes because the original scatter-add writes neighboring rows.

Historical experience read first: `a35c3a4:experiments/ls-shared-uniform-20261112/README.md`.
That implementation was opt-in and passed old real-input residual checks;
those results do not validate this restoration. Do not repeat the eight-rank
fallback: keep the fixed topology and report a resource block if needed.

Validation plan: ordinary and shared MPI2 CTest gates, followed by current
C24 and C32 16-MPI runs, each with three single-column and three full12
zero-start samples after one setup. Independently apply the scalar operator to
the saved single output and every full12 column. Require true relative
residual at most `1e-8` and single/full12 first-column agreement within `1e-6`.
Report setup and stout separately. Use the historical 37 placement/setup
threads and 32 solve threads, batch 2, grid `1,1,1,16`, blocks `6,6,6,4` and
`8,8,8,4`. Commit/push the restored code before remote compilation or runs.

Completed at `efe57de52223a6f7f5177ac731c33e762070b327`, pushed before remote
compilation. LingSheng job `2117750` on `cn12118` succeeded; selected CTest
30/30 passed, including shared operator, lifecycle and full12 gates.
Current C24/C32 each passed thirteen independent scalar checks at `1e-8`.
All measurements used zero guesses and required no correction solves.

| Geometry | Setup | Warm single | Warm full12 | Maximum independent residual |
|---|---:|---:|---:|---:|
| 24³×64 | 224.591 s | 1.274 s | 14.853 s | 4.819e-9 |
| 32³×64 | 487.831 s | 5.297 s | 63.850 s | 4.876e-9 |

The old C32 sixteen-rank recipe measured about 64.897 s; current performance
is consistent with that recipe. Do not attribute the difference from the
eight-rank nonshared diagnostic to a single kernel optimization. The opt-in
shared implementation is now revalidated in the clean source layout; the
ordinary runtime remains available and is still the default when the explicit
shared environment is absent. Node5005 also rebuilt this revision, passed
30/30 CTest and all real-input residual checks at sixteen ranks.

See [the report](../../docs/single-node-health-20261113.md) and the four formal
result JSON files under `experiments/single-node-health-20261113/` for inputs,
first/second/steady timings, precision, parameters and replay commands.
