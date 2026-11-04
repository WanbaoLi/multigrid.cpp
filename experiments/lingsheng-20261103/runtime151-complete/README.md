# Completed runtime confirmation151

Three fresh ordinary full12 processes on the same exclusive cn19486 allocation:
SDK default A / old GOMP default / SDK default B. Every process built its own
hierarchy, warmed one complete12 solve, timed three complete12 solves with zero
guesses and passed all12 independent scalar and stored-solution checks. The
source and native library remained exactly accepted052. Actual loaded runtime
maps, environment/affinity and dependency closure passed. Owned task cleanup
finished without survivors. The historical147 samples were not reused.

| Case | Steady full12 median | Maximum scalar residual | Maximum reference error |
| --- | ---: | ---: | ---: |
| SDK default A | 15.126734123s | 4.818858113e-9 | 1.719173293e-16 |
| old GOMP default | 14.440682654s | 4.818858113e-9 | 0 |
| SDK default B | 14.410181753s | 4.818784496e-9 | 1.223229313e-11 |

No adoption. Control drift was4.9725%, inside the5% gate, but the candidate was
0.2117% slower than B and its timing range overlapped B. It had to beat both
controls by at least3%. Its4.535% gain against A alone is not a reproducible
runtime benefit. Together with147 and the two slow PASSIVE variants, this lowers
the priority of these runtime options. It does not establish equivalence for
every OpenMP implementation or workload. The retained pointer remains052.

manifest.json preserves original and redacted-export hashes. record-map.json
maps every one of767 exact exported files to short committed paths for Windows.
Raw outputs and the complete archive remain outside Git. Archive SHA256:
4d331463f5d8112761b149e4fc63a7903b8b686642565f53591cf59a017cc2d3.
Manifest SHA256:
4666730727a8654630984c57405cc477bf9b459e642135782799cb772c63c976.

The151 task used a separately pinned live-parent guard because current djob
queries timed out. Its initial allocation authentication is labeled initial;
actual worker identity, allocation, affinity, ownership and valid deadline were
checked again at entry. Numerical/comparison gates were unchanged. A fresh150
unranked profile of the unchanged best is running as the next serial task.
This completed experiment is not completion of the overall optimization task.
