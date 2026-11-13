# Experiment records

Experiments are grouped by hardware and campaign. Keep proposals, experiment
implementations, parameter files, machine/source metadata, numerical validation
and performance summaries here. Production entry points live in `tools/` and
`benchmarks/`; the dated controllers under these archives describe their
original sessions and are not instructions to restart old jobs.

Raw test and command logs are generated run artifacts. On 2026-11-13, 672 tracked
`.log`, `.stdout` and `.stderr` files were removed from the working tree.
Three CMake caches and 168 duplicate one-value residual output files were also
removed; the complete per-column residuals remain in `verification.json`.
Structured measurements, decisions and source hashes remain.
New logs must stay in an ignored or external run directory.

Historical archive manifests record the original full exports, including the
logs. They remain unchanged to preserve the recorded hashes; they do not claim
that every payload is still present in this reduced source checkout. The full
pre-cleanup tree is available at commit
`c2a04ff26b0faf74fa8aeb256d6bdf41d76dbbde`. To inspect an old log without restoring
it into the current branch:

```bash
git show c2a04ff:experiments/x86-20261110/evidence/tests-0.log
```

Source paths inside historical manifests describe that commit's layout.
For current source paths, use [the repository layout](../docs/repository-layout.md).
