# Current-allocation profile150, completed

The unchanged accepted052 native source/library ran on exclusive cn19486 in
worker10, after runtime confirmation151 closed. One complete12 warmup, three
light diagnostic solves and the final sampled verbose full12 call completed.
The final sampled call checked all12 native true-residual/convergence results;
its output was not saved. The saved final light output passed independent
scalar/reference checks for all12 columns: maximum residual4.818858113e-9 and
maximum reference relative error1.719173293e-16. Owned task cleanup was empty.
No diagnostic time was ranked or promoted.

| Representative rank | Samples | Sampled threads | Native cycles | GOMP cycles |
| --- | ---: | ---: | ---: | ---: |
| 0 | 14542 | 32 | 54.978% | 40.385% |
| 8 | 13033 | 32 | 52.796% | 42.767% |

Fine batch application accounted for9.24/8.70% of sampled user cycles; local
application8.81/8.34%; the explicit reused Wilson kernel6.15/6.01%. These are
leaf cycle fractions summed over threads at two ranks, not elapsed-time savings
or exhaustive full-node samples. They support kernel/data-reuse and scheduling
investigation but cannot rank implementations.

The light median full12 diagnostic was15.598133689s. Sequential coarse halo
rank-max envelopes summed to1.665465217s, of which waits were1.224111121s;
10354 calls carried508919808 bytes. The10.677% region hint includes arrival
skew, is nonadditive with overlapping compute and is not a speedup prediction.
It supports a bounded HaloV2 trial after full ARM numerical qualification.

Every310-file export payload was verified locally; the308 committed small
records use record-map.json. The two raw perf files remain in the full local
and remote archives. Archive SHA256:
94decad07697644f94b10b28f5db39917dd27cd147ccb6cc621dfe352f6603dd.
Manifest SHA256:
6e0f45209b4737321b59e3e5d825e6025146db9a5cf7cbb4ae51b2e58a62955c.
Exact period analysis SHA256:
121de5c46966b69a1918109d8a73ef64570224f40b4768b7c2b9743145d1c697.
Original and redacted-export hashes are separate. The exact live-parent guard
and unchanged inner task are included; no current successful djob query is
claimed. The archived allocation deadline must never be reused after expiry.
