# Accepted052 new profile on worker11

Task155 passed both benchmark and independent12-column validation and cleaned
all children. Source/library/configuration are accepted052. Light diagnostic
steady calls are14.926449515,15.001681618,14.918348617 seconds; median14.926449515.
These are diagnostic observations, not an ordinary promotion comparison.
Independent scalar maximum residual4.818784496e-9. All12 reference errors pass.

Exact sampled user-cycle fractions at ranks0/8: native55.05/53.73%, GOMP40.94/
42.21%. Fine batched apply9.64/8.72%, local_range8.90/8.21%, explicit reused
Wilson6.49/5.76%. These are samples across32 threads at two ranks, not a whole
node elapsed-time split. In particular GOMP spin/arrival skew does not imply
that40% of wall time can be removed.

The sampled final verbose call passes native full12 true-residual statistics.
The saved output independently verified by the scalar executable and stored
solution is the final LIGHT call. Do not claim independent saved-field checking
of the sampled verbose output.

`archive-files.json` maps308 small exact Git payloads and two raw perf artifacts.
Both raw perf files remain in the local output archive and on the original
compute filesystem; they are omitted from Git. The complete310-file export
was locally verified against its manifest before creating these records.
