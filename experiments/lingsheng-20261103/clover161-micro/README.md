# First Clover reuse local diagnosis

Auxiliary task161 ran only after the ordinary full12 group160 closed. The exact
qualified861 header was compiled with actual target flags from its build. One
physical core was pinned; each off/on/off process runs30000calls per repeat,
five repeats, and an independent double-precision dense oracle. All passed.

| Block sites | Off opening median | Reuse-on median | Off closing median |
| --- | ---: | ---: | ---: |
| 432 | 0.122301992s | 0.195880472s | 0.122207170s |
| 864 | 0.310712288s | 0.371074199s | 0.276256773s |

These are30000-call local totals, not complete propagator times.432site controls
are stable and show about60percent slowdown.864site controls drift, but the
reuse path is slower than both. Max absolute oracle errors1.046e-7/1.137e-7.

Together with actual codegen showing no vector spills and unchanged caller
frames, this supports reducing six-row coefficient stream fanout and exposing
more independent accumulation chains in a separate candidate. It does not
prove cache behavior without further counters or isolate all causes. The new
pair-row candidate receives its own dense/tail/three-vector-length tests,
MPI checks and full12 verification; a microbenchmark cannot promote it.
