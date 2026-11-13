# Health-check artifacts

This directory contains only small JSON summaries from the 2026-11-13 real-input
checks. The full workflow is described in [the report](../../docs/single-node-health-20261113.md).

- `node5005-L24.json`, `node5005-L32.json`: current x86 revision, 16 MPI ranks,
  16 placement threads and 12 solve threads.
- `lingsheng-L24.json`, `lingsheng-L32.json`: `efe57de` shared ARM revision,
  16 MPI ranks over all sixteen NUMA domains, 37 placement/setup threads and
  32 solve threads. These are the formal matched-rank results.
- `lingsheng-L24-private-diagnostic.json`: earlier non-shared ARM revision,
  16 MPI ranks, 37 placement threads and 32 solve threads.
- `lingsheng-L32-8mpi-diagnostic.json`: earlier non-shared ARM revision,
  8 MPI ranks over NUMA 0–7. This is a memory diagnostic and is not the user's
  required sixteen-rank comparison.
- `node5005-diagnostic.json`: rank-0 local diagnostic timer samples used for
  candidate selection. They are supporting evidence, not wall-time attribution.

The JSON reports contain independent scalar residual checks and source,
geometry, resource and library metadata. Large gauge/solution arrays and raw
logs remain in the external node run directories.
