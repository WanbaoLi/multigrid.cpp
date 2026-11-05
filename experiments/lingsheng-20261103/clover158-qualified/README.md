# Actual Clover ARM qualification on cn19480

Task158 passed and cleaned all descendants. Source861613c is based exactly on
accepted052 source5fe1b5f; the Clover flag is opt-in and default-off. This is
correctness/code-generation evidence, not a physical full12 speedup.

Actual target build, assembly,32 selected configured CTest checks and existing
dense Clover double oracle/tails/sentinels passed. Dense kernels ran at16/32/64
byte SVE lengths. A further independent native MPI2 backend oracle passed at
each of those three lengths with actual per-rank length and library identity
checks. Actual compiled library SHA256:
045fd4d62c27179b68e8d557bcd9fdfe9aeb707c4ec93b93b37ce02ebf6ceb10.

The reused kernel has no observed vector stack spill; its128-byte frame saves
general-purpose registers. The original/new local caller stack frames both
remain0x210bytes. Static instruction/load counts do not determine dynamic work
or speed: the new loop changes coefficient stream order as well as source reuse.
The ordinary old/new-off/new-on/old bracket must assess overall regression.

First ordinary launcher159 failed before creating an experiment state/attempt
or launching a numerical process because it referenced queue12 for the closed
qualification status. Its log/status/task are preserved. New160 derives both
qualification paths through one helper, and an actual-dependency integration
check passed before dispatch. Source, compiled library and precision gates
were unchanged. The160 ordinary task is separate and not claimed complete here.

`archive-files.json` maps47 exact exported metadata/log/codegen/helper payloads
to their original paths and SHA256 values. The actual qualification snapshot
and binaries remain on the compute shared filesystem.
