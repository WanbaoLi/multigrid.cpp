# First Clover reuse: complete actual full12 bracket

Actual task160 on cn19480 passed and cleaned all children. Four fresh MPI
process groups each build their own hierarchy and solve a full12 warmup plus
three complete12 steady calls from zero guesses. Each saved result independently
passes the original scalar executable and the coordinate-matched ARM reference.

| Case | Steady full12 seconds | Median seconds |
| --- | --- | ---: |
| accepted052 opening | 13.777199845,13.809370602,13.674490572 | 13.777199845 |
| source861 reuse off | 13.725625782,13.584511999,13.611182689 | 13.611182689 |
| source861 reuse on | 14.066786440,14.212594259,14.186663551 | 14.186663551 |
| accepted052 closing | 13.991847214,14.025776460,14.133162269 | 14.025776460 |

Control median drift1.8043%. Reuse-on is2.9720/1.1471% slower than the two
controls and4.2280% slower than same-source off. Off gains1.2050/2.9559%,
below the3percent two-control threshold and overlapping the opening range.
Neither is adopted. Main best remains052.

All12 independent scalar residuals<=4.818859e-9. Reference relative error
maximum1.223230e-11; the different tiny output hashes from independent builds
remain within the fixed1e-6 solution limit. No sample is discarded.

Target qualification158 showed no SVE vector stack spills and unchanged primary
caller frames. Actual later micro161 confirms local six-row reuse slowdown.
That evidence motivates a separate two-row/pipeline retry; it does not prove a
cache cause alone. The new source067 remains unaccepted until its own actual
target qualification and full12 bracket. This result cannot be compared directly
with prior14.7second cn19486 controls as if only the code changed.

`archive-files.json` maps1035 exact exported reports/logs/publication closures
and helper records. Scientific arrays and measured binaries remain separately
on the shared compute filesystem. Ordinary timing has no perf/PMPI recording.
