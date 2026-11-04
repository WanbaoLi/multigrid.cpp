# Completed retained-best solve profile143

Actual diagnostic task143 completed successfully on cn19483 in worker8. All12
saved columns passed the original scalar operator and stored-solution checks:
maximum relative residual4.8187845e-9; maximum reference-solution relative
error1.2232293e-11. The same source/library as accepted052 was used. Actual
task cleanup completed with no surviving owned processes.

Only ranks0 and8 were sampled, at49Hz user cycles with DWARF4096 call stacks.
The final sampled full12 call separately passed native convergence and finite
true-residual checks for all12 columns. Its output was not saved. Independent
scalar verification applies to the saved final light diagnostic round, as
documented by the wrapper. No diagnostic timing was promoted as ordinary time.

Exact period sums from the recorded data replace the earlier rounded estimates:

| Rank | Samples | Sampled threads | Native library cycles | OpenMP runtime cycles |
| --- | ---: | ---: | ---: | ---: |
|0|14773|32|54.140%|41.197%|
|8|13593|32|54.771%|40.754%|

No lost samples were reported. These CPU-cycle fractions do not measure wall
time or predict savings. OpenMP waiting includes arrival skew; the rest of the
node was not sampled. The actual ordinary runtime comparison is a separate
fresh experiment on another allocation and cannot reuse these diagnostic times
as performance controls.

Local application accounts for8.58/8.17% and the inlined fine batch range for
9.03/9.18% of user cycles at the two ranks. Standalone Clover contributes about
2.6%; it also runs within selected fine/local paths. Saved instruction annotation
shows contiguous coefficient loads and gathers in the local Wilson path. This
supports bounded cache/register-reuse and compiler experiments; it does not
establish a particular gain from any one instruction change.

The light diagnostic's median sum of coarse communication rank-max envelopes
was1.636s; waits1.181s;10354 calls;508.9MB payload. The diagnostic total was
17.291s. Envelopes include skew and are nonadditive with overlapping work, so
the observed9.46% coarse-region fraction is a trial-priority hint, not a speedup
bound. HaloV2 still requires its full ARM numerical qualification and ordinary
whole-solve trial.

archive-files.json binds the committed small records. Raw perf data and the
full312-file archive are retained locally under
outputs/optimization-20261103/profile143-complete and remotely under
R/exports/profile143-complete-v2, where R is
/home/share/nsls_lwb/.cache/mg-opt-20261103. Full archive SHA256:
17cb84d0b078f712d3c52438e7b9375fc17fc758b045c1160d32b19738073920.
Original report hashes and redacted-export hashes remain distinct in manifest.

The original export refused a payload above its source-reader1MB limit. That
failure is preserved. The v2 export uses a bounded128MB fixed-offset reader,
exact counts/EOF and stable file metadata, then independently checks the payload
digest. This changed only evidence export, after completed numerical verification.
