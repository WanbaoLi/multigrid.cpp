# Two-row Clover reuse: second candidate

Unaccepted, isolated from accepted052 and the active first variant. The first
variant861 reuses twelve source vectors across six output rows. Actual target
assembly shows no SVE spills and unchanged main caller frames. Preliminary
ordinary160 on samples are slower than off; the full closed bracket and all12
precision are still required before that is a final result.

This second candidate reduces reuse groups to two output rows. Each source
vector feeds two independent complex accumulators; each output row retains
the same column order and separate multiply/add/subtract operations. Six-row
reuse loads sources less often, but visits more coefficient streams per site
tile. Two-row reuse tests that cache/prefetch and instruction-pipeline tradeoff.
No coefficient packing, extra allocation, new precision or solver tuning.

Existing dense Clover double oracle, sentinel and tail tests call the reused
function directly for varied extents/ranges. Native ARM compile, actual SVE
16/32/64 tests and full MPI/real12 validation remain required. First run the
closed first variant's local microbenchmark, then compare this row grouping
with matched old/new-off/new-on micro controls. Local timing cannot promote it.

Only after that evidence justifies a whole-solve trial may it enter a new
ordinary old052/new-off/new-on/old052 bracket with all12 independent validation,
the unchanged3percent adoption gate and5percent control-drift bound. The flag
remains cached per process and default-off. No speedup or target pass claimed.
