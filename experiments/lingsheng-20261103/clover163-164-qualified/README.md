# Two-row Clover retry: actual qualification and local diagnosis

Independent source067b28b changes six-row source reuse into two-row reuse,
preserving each row's column accumulation order, precision and predicates.
The change follows completed160 whole-solve regression and161 local slowdown.
Main numerical source052 and its accepted artifact remain unchanged.

Actual task163 on cn19480 passed configure/build/codegen,32 selected CTest
checks, dense double oracle/tails/sentinels at16/32/64-byte SVE and independent
nativeMPI2 oracle at each of those actual per-rank vector lengths. All children
cleaned. Actual target library:
fa18ca4e2c42e731f12b837825afb80ef534fce73856e60e18364cab077bb71b.
Static reused body332instructions/36ld1w, no observed vector stack spills;
the main local caller frame remains0x210bytes.

Task164 then repeated the same bounded one-core microprobe with exact target
flags and independent double oracle. Five repeats,30000calls each:

| Block sites | Off opening median | Pair reuse median | Off closing median |
| --- | ---: | ---: | ---: |
| 432 | 0.121345284s | 0.128161567s | 0.122004402s |
| 864 | 0.288946365s | 0.297735416s | 0.354524369s |

The432case reduces the first variant's about60percent slowdown to about5percent.
The864case controls drift substantially and do not establish a gain. Both
absolute oracle errors remain about1e-7. This is local diagnosis, never a full12
score or adoption. New ordinary165 uses four fresh process groups with old052
opening/closing controls and all12 scalar/reference verification. It was still
running when this closed qualification archive was created.

`archive-files.json` maps48 exact exported logs, reports, source helper scripts,
plans and codegen records to original paths and SHA256. No165 result inferred.
