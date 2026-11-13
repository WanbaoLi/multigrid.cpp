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

Status: implementation and validation pending. Results and exact source commit
will be recorded here after the run; no speedup is claimed in advance.
