# GitHub source backup audit, 2026-11-12

Repository: https://github.com/WanbaoLi/multigrid.cpp

This is a source-backup audit, not a new numerical or performance acceptance.
The stable delivery remains `codex/final-stable-20261111` at
`9b99af20256f44390ad40a40cba69ee77a290e46`. Archived experiments are not
promoted to that delivery. Historical continuation notes describe their original
sessions; they are not instructions to launch or resume those jobs today.

## Access paths

Direct `ssh ls` and `ssh h20 'ssh ls hostname'` both reached `login09` with the
LingSheng shared home `/home/share/nsls_lwb`. They are two access routes to the
same code, not independent source copies. h20's own shared home is
`/public2/home/lwb_720`; it is also accessible through `ssh itp`.

## Uploaded revisions

| Location or experiment | Exact source commit | GitHub branch containing it |
| --- | --- | --- |
| Local current development before this archive | `43f910a1e11b97d248e6e72f7d28a2e7bad78bcb` | `codex/sun-cpu-20261111` |
| x86 final experiment branch | `d30cdd50e83e311bf374ca2bad9e6e0b349bb088` | `codex/x86-architecture-20261110` |
| LingSheng clover pair | `067b28bd787a6428400e23d683596cd2120c5f6a` | `archive/lingsheng-pair-067` |
| LingSheng clover reuse | `861613c703117c6b5b671e245a7142e217b09501` | `archive/lingsheng-reuse-861` |
| LingSheng halo v2 | `760666c8ac459ef062c749ee7ee9964c99e7c3c8` | `archive/lingsheng-halo-760` |
| LingSheng setup owned | `f94f27d2a07ff3363bea43c1a3b2ca45277de674` | `archive/lingsheng-setup-f94` |
| h20 phase4 fixed | `000b7da6cfb381bd60674f0d1930e20ae20dbe72` | `archive/lingsheng-phase4-000b` |
| h20 phase4 | `69c5818a36b43b934dcb77f7eec4508ef74f9264` | `archive/lingsheng-phase4-69c` |
| h20 setup best base | `b9939130d6fedc74db5faf1b05282cb3b92117cf` | `archive/lingsheng-bestbase-b993` |
| h20 coarse halo uncommitted source snapshot | `e8fe5c135d4c515fdd421493ee10810018ee9798` | `archive/h20-coarse-halo-wip-20261112` |

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
to a separate checkout, committed, and pushed to the WIP branch above.
The live remote tree was preserved. Git text newline normalization applies;
this is a Git source snapshot, not a byte-identical filesystem image.

`archive/local-code-20261112` captures the previously pending source,
scripts, and Markdown under `comparison-20261105-v4/`,
`benchmarks/hardware/`, and code copies under `outputs/`, together with this
inventory. These old experiments have not been rerun for this backup and do
not establish new performance claims. Build artifacts, Git bundles, large
input/output arrays, Python caches, and private paper extracts are excluded.

## Scope and reproduction

The checked solver source revisions are backed up on GitHub with their own
history. They intentionally do not all point to one commit. This audit does
not assert that every non-Git helper anywhere in either shared home was
enumerated or backed up. Downloaded third-party code retains its upstream
provenance.

To restore a source revision, clone this repository and check out the branch
listed above; use the exact commit to reproduce a historical build. Verify a
branch independently with `git ls-remote --heads origin BRANCH_NAME`.
Compilation and numerical reruns are outside this source-only backup.
