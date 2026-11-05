# Halo V2: completed full12 ordinary bracket

The actual worker10 task154 passed and cleaned all children. Every case uses
the real 24x24x24x64 fixture, zero guesses, one warmup and seven steady complete
12-column calls. All12 columns independently pass residual<=1e-8 and stored
solution relative error<=1e-6. `archive-files.json` maps each original path to
its exact exported Git payload and SHA256; large scientific arrays are retained
on the compute filesystem, not included here.

| Case | Median seconds | Scalar maximum residual | Solution maximum relative error |
| --- | ---: | ---: | ---: |
| Accepted052 opening control | 14.707597270 | 4.818785e-9 | 1.223230e-11 |
| New760, option off | 14.731991101 | 4.818859e-9 | 1.719174e-16 |
| New760, option on | 14.457430415 | 4.818859e-9 | 1.719174e-16 |
| Accepted052 closing control | 14.736364296 | 4.818785e-9 | 1.223230e-11 |

Opening/closing control drift is0.1956%. Candidate gains1.7009% and1.8928%
against those controls, below the frozen3% two-control adoption threshold.
The same-hierarchy on/off increment is1.8637% with separated ranges. The
default-off regression observed in the previous V1 direction is absent here,
but this does not justify relaxing the adoption gate. Best remains052.

The separate halo diagnostic is unranked. Its4700 batched calls count only the
grouped path, not all coarse calls; never compare4700 with the old10354 total
without accounting for unbatched calls. Raw final diagnostic logs are included.
Rank-max timing envelopes overlap and must not be added into a wall-time budget.

Decoded final verbose call:5654 total coarse calls,508919808 send bytes,
1.499605386seconds coarse total envelope and1.056500326seconds wait envelope.
The old150 diagnostic recorded10354 calls with the same send bytes; its coarse
total/wait envelopes were1.665465217/1.224111121seconds. These are separate
unranked diagnostic executions and support the mechanism, not a paired speedup.

The prior148 timeout and completed153 qualification remain separately archived.
No failed stage was rewritten and no old timing was relabelled as a fresh run.
