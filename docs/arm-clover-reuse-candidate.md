# ARM Clover input reuse candidate

Unaccepted experiment, based exactly on accepted052 source5fe1b5f. The separate
haloV1/V2 and source-owned setup changes are absent. The accepted binary and
main campaign best are unchanged. Enable only in a fresh process through
`LQCD_ARM_SVE_CLOVER_REUSE=1`; default is off.

The completed143 solve profile independently passed all12 scalar/reference
checks. At two representative ranks, exact sampled user-cycle fractions were
54.14/54.77% native code and41.20/40.75% GOMP. Individual native leaf costs
included local_range8.58/8.17%, fine_apply_batch9.03/9.18%, and standalone
clover_range about2.6-2.8%. Clover also runs inside some local/global fine
paths. The standalone cost alone does not establish enough end-to-end gain;
whole-solve measurement remains necessary. Samples describe final diagnostic
execution at ranks0/8, not elapsed-time proportions for the whole node.

The legacy Clover loop visits an output component first, then every site tile.
Its six rows in each chirality reload the same six complex source components.
The experiment visits a chirality and site tile first, loads those inputs once
into three SVE tuples, and reuses them for six output rows. Matrix coefficients
already use contiguous SoA loads; this is not a coefficient-gather replacement.
Coefficient storage, column accumulation order, multiply/add/subtract sequence,
tail predicates and distinct source/output contract are retained. No packing,
allocation, extra thread pool, precision reduction or algorithm change is added.

The optional body is a separate noinline function to keep its input-register
requirements out of the old arithmetic loop. That is a hypothesis about code
layout, not a nonregression proof. Actual target assembly must show whether the
inputs stay in registers, whether SVE spill/reload traffic appears, and whether
the default-off caller changes its frame/code enough to matter. Prior haloV1
showed why a same-binary on/off win is insufficient without an old-binary
bracket and a default-off whole-version check.

Required qualification: existing dense independent double Clover oracle,
sentinel/range/tail checks and Wilson local/global tests; actual16/32/64-byte
SVE runs, complete configured CTest including MPI/runtime tests with the option
enabled, then full12 independent scalar residual<=1e-8 and reference error<=1e-6
for every ordinary comparison. The added test directly exercises the new body
regardless of the process dispatch flag and also enables it through the public
ARM dispatch in another CTest instance. Non-ARM skips do not qualify SVE.

Run old control, new off, new on, and old closing control as separate processes,
each with its own hierarchy, one full12 warmup and at least three steady rounds.
Use identical current best runtime, placement, setup/solve teams and physical
input on one exclusive allocation. Reject adoption if control drift/noise is
too large, if any accuracy check fails, or if the new on version fails the
existing >=3% two-sided gain and disjoint-range gates. Retain all failures.
If this first layout fails, inspect codegen and native microbench evidence;
changes to register grouping or arithmetic predicates require a separately
recorded next round, followed by the same whole-solve gates.

No target build, target numerical pass or speedup is claimed by this proposal.
