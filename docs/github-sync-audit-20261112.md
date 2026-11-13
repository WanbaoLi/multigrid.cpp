# GitHub source backup audit, 2026-11-12

Repository: https://github.com/WanbaoLi/multigrid.cpp

This is a source-backup audit, not a new numerical or performance acceptance.
The production source is maintained on `develop`. Historical continuation notes
describe their original sessions; they are not instructions to launch or resume
those jobs today.

## Access paths

Direct `ssh ls` and `ssh h20 'ssh ls hostname'` both reached `login09` with the
LingSheng shared home `/home/share/nsls_lwb`. They are two access routes to the
same code, not independent source copies. h20's own shared home is
`/public2/home/lwb_720`; it is also accessible through `ssh itp`.

## Uploaded source

The production source, x86 development and AMD runbook are merged into the
single `develop` branch. Experimental branch refs were removed after their
accepted or rejected changes were recorded in Git history. The deleted refs are
not required to build or reproduce the production entry points.

LingSheng repositories under `.cache/mg-opt-20261103/` and
`.cache/fair-solve-20261105-v4/` were checked. All nine checked Git working
trees were clean, including untracked files. The other checked source heads
`71160fac57d577d27423527e6b577c0593940d35`,
`297edfdd725f2905578556dd91f5580672c18e66`,
`96be7184ea565d084d8b38b9afc65257172b3293`,
`797ac9c9b5b09050d71251899f42201da2ac1266`, and
`d6eaddcd4de424924ce97ca2fedf9d3b9c32c349`
already exist in the uploaded development history.

h20's `.cache/mg-x86-20261110/{source,source-projector,source-tile}`
were clean at `cc3804e6c4b0feea52e64a493a73e60103753f5d`,
`7a6498426ab2689e8c83c1af28d39887f1df93e7`, and
`edd611bc9597766fb6cd43be41fd1d5246fac615` respectively; all are present
in the uploaded development history.

h20's `.cache/sun-cpu-20261111-v2/main.cpp` SHA256 is
`aaef64b9530af43196737eb84291605d61855ec9e56b19345436102ef0dbdc9a`,
matching tracked `experiments/su-n-cpu-20261111/main.cpp` from the uploaded
SU(N) development history.

## Unfinished and local source archives

The h20 coarse halo tree at
`.cache/mg-opt-coarse-halo-20261104/source-wip-000` had seven modified tracked
files and two untracked files. Its binary Git diff against base
`5fe1b5fd2702f799488a2b8119002c450de5b4cd` plus both new files was exported
to a separate checkout and retained as a historical commit.
The live remote tree was preserved. Git text newline normalization applies;
this is a Git source snapshot, not a byte-identical filesystem image.

The repository keeps production source, tests, tools, documentation, profiles,
benchmarks and the categorized `experiments/` records. Old comparison
controllers and raw hardware-output copies were removed from `develop` because
they duplicated evidence and were not production entry points. Their commits
remain recoverable from Git history and do not establish new performance
claims. Build artifacts, Git bundles, large input/output arrays, Python caches,
and private paper extracts are excluded.

## Scope and reproduction

The checked solver source revisions are backed up on GitHub with their own
history. They intentionally do not all point to one commit. This audit does
not assert that every non-Git helper anywhere in either shared home was
enumerated or backed up. Downloaded third-party code retains its upstream
provenance.

To restore a historical source revision, use its commit ID from Git history.
Normal development starts from `develop`.
Compilation and numerical reruns are outside this source-only backup.
