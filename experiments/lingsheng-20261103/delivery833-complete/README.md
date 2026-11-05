# Actual deliverable source on node5005

Exact source833f873 restores the numerical/build/runtime files to accepted052
source5fe1b5f while retaining framework and evidence changes. Fresh configured
build and31 selected CTest checks passed. ARM-specific explicit skips are listed
in the exported test summary and do not qualify ARM execution.

Two fresh ordinary processes each built their own hierarchy and ran one full12
warmup plus three steady full12 calls. All columns use zero guesses and pass
the independent original scalar executable and coordinate-matched x86 reference.

| Process | Steady full12 seconds | Median | Scalar max residual | Solution max relative error |
| --- | --- | ---: | ---: | ---: |
| 110 | 6.172580617,6.180711100,6.183250051 | 6.180711100 | 9.169763e-9 | 9.915889e-8 |
| 111 | 6.120672389,6.136863181,6.144592965 | 6.136863181 | 9.169763e-9 | 9.915889e-8 |

Control median drift0.7145%. Setup API111.945/112.586seconds, outside the
steady solve metric. Native setup timer was not reported and remains null.
16MPI ranks,16 placement/setup threads and12 solve threads per rank;256 allowed
physical cores and192 active solve threads. Direct SSH: no scheduler exclusivity.
Binary868a97c25e1dcae918534a7f644bc5869fc2080a4ef80c4714551263e9e0cbbd.

First attempt100 failed before numerical execution: the outer driver pinned
historical benchmark711df30, whereas delivery833 contains reviewed benchmark68650d7
with thread-team metadata and stronger independent-output identity checks.
Its original failure/logs remain included. New110/111 explicitly pin68650d7;
solver, clocks, tolerance and stored expected scientific digests were unchanged.

`archive-files.json` maps564 exact exported payloads to their original paths and
checksums. Scientific arrays/binaries stay on the shared compute filesystem.
