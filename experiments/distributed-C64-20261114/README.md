# Distributed C64 preparation

User target: real F64P14 64^3x128, 16 MPI per node, 32 solve threads/rank,
zero-start single and full12 after hierarchy reuse, true relative residual 1e-8.
Reference skill and old shared-uniform / current C24-C32 experience read first.

Problem: global FP64 basis is 288 GiB per replica; private global FP32 basis is
72 GiB per rank. Merely turning off single-host sharing cannot fit this job.

Attempt 1: opt-in LQCD_DISTRIBUTED_STORAGE=1. Preserve global virtual indices,
but demand-map and touch only owned coefficient rows, spinors and received halos.
FP64 gauge exchanges one physical t-face; FP64 basis exchanges coarse t-planes.
Galerkin assembly computes owned rows from local and adjacent source blocks.
Private FP32 constructor loops visit owned blocks only. Setup test vectors avoid
Allgather; a deterministic counter probe supplies owned values independently of
rank count. This changes the setup seed sequence in distributed mode, not the
operator. Release all 24 test vectors after final setup. Ordinary mode remains
the reference path. Sparse virtual space is not a claim of zero memory cost:
resident bytes, RSS/PSS and scheduler peaks must be measured.

Initial estimate: 4 nodes x 16 MPI, block 8,8,8,2; global time slabs give local
64^3x2. FP64 basis owners+two coarse halos: 216 GiB/node. Gauge+Clover owner/halo:
about 31.5 GiB/node. FP32 coefficients about 32 GiB/node per Impl generation;
24 setup vectors 18 GiB/node. Include two generations, workspace halos, assembly
temporaries and Python arrays: initially budget 350--440 GiB/node (estimate,
not measured). Two nodes have insufficient comfortable setup-peak margin with
full coarse basis halos. Four is the initial feasible candidate, not an optimum.

Before real input: ordinary/shared CTest regression, distributed MPI2 gates and
cross-host small geometry validation. Independent scalar slab oracle checks
local outputs with a padded lattice and global temporal wrap twist. Record
first/second/steady, pure solver/API timings, correction activity and all12
independent residuals. No result or performance claim yet.

## Attempt 2: fit the actual two-node account limit

Donau `dlimit -s testusers_rebuild` reports 1216 CPUs, with 608 charged per
exclusive 592-application-CPU node. A four-node probe was PENDING with reason
20618 (account limit); it was cancelled. Do not describe this as unavailable
hardware or a completed four-node run.

Use two nodes, 32 MPI total, 16 per node, 32 threads/rank, block 8,8,8,4,
local 64^3x4. Pack FP64 basis's exact chiral zeros, preserving logical indexing
for scalar assembly; owner plus two coarse halos becomes 216 GiB/node rather
than 432. Drop stale basis halos before adaptive work, move cached setup vectors,
destroy the old Impl before exchanging new basis halos, and release setup-only
FP64 basis/stencil after verification. Release scalar warmup Krylov capacity
before the batch2 measurement. These changes address a live-buffer peak, not
just a logical field-size estimate. FP64 gauge/Clover remain for reliable updates.

Estimated principal resident data on each of two nodes:

| Storage | Estimate |
|---|---:|
| Compact FP64 basis, owned plus two coarse halos (setup only) | 216 GiB |
| FP64 gauge, owned plus physical faces, and owned Clover | 54 GiB |
| Owned FP32 links/diag/inverse/basis, one Impl | 63 GiB |
| 24 setup test vectors, owned plus physical faces | 54 GiB |
| Batch2 GCR directions/images at restart16, including halos | up to 144 GiB |

These rows have different lifetimes and must not simply be summed. Setup-only
FP64 basis and test vectors are gone before batch2 GCR capacity is allocated.
Estimate 350--440 GiB/node peak with temporary assembly and Python arrays;
allocation is 480000 MB/node (~458 GiB), so measured PSS/cgroup peaks are required.
No swap/OOM is acceptable. Keep the known correct C24/C32 ordinary path available.

Attempt 1 compute gate (library from 966cb2f, storage implementation 65b593c)
has passed ordinary and shared MPI2, distributed CPU/batch12, and distributed
halo tests. Compact basis and lifetime changes require a fresh build/gate.
Two-node campaign job 2124786 uses commit 891b232, after the one-node gate exits.
The launcher reserves two whole nodes, then explicitly maps 16 ranks per host;
`--oversubscribe` overrides Donau's one task-slot per whole-node reservation,
not the granted physical CPU masks (rank_exec assigns disjoint 32-core masks).

Two-node regression job 2124786 passed all 10 selected CTests in 725.06 s,
including compact basis, ordinary/shared CPU, shared full12, distributed CPU,
full12, halo and SAP EO. Its campaign script was updated while bash was waiting
inside the gate child; the running shell reached EOF after the gate instead of
dispatching the newly added continuation. The job ended SUCCEEDED without any
real-input measurement. This is an orchestration failure, not a numerical result.
Do not edit a running campaign script again. A fresh frozen campaign invocation
can reuse the completed build via its third argument, rebuilding and rerunning
the compact/distributed solve gates before the cross-host and real-input stages.

## Actual two-node communication and real-input attempt

Jobs 2124930/2124986 exposed a 32-rank startup stall before gauge I/O. Python
tracebacks placed all ranks in the placement metadata Allgather. Selecting
portable collectives alone (2125012), then ob1/vader/TCP (2125036), did not solve
startup. Requesting 32 task slots with explicit Donau NUMA affinity produced a
rankfile conflict (2125063), then a launcher allocator abort without manual
mapping (2125080). None of these are numerical performance results.

Job 2125108, measured source 88e8bbe, requested two nodes, 32 tasks, 16/host,
37 CPUs and 30000 MB/task, exclusive host, without Donau `-a`. The project NUMA
launcher bound 32 disjoint cores per MPI. Explicit ob1/self,vader,tcp, portable
collectives and the observed 10.36.0.0/16 network passed shared communicator,
object collectives, typed reductions and an 8 MiB ring. This combination works;
the individual root cause among allocation/network/default components is not
yet isolated. Do not claim that disabling one specific component fixed it.

Real C24 gate: setup 58.2773 s, warmed pure single 4.08987 s, full12 34.86493 s;
all 13 outputs passed the independent scalar oracle. These are two-node C24
gate timings with 6,6,6,2 blocks, not a replacement for the previous tuned
single-node C24 result. See `c24-gate.json` for every sample and residual.

C64 completed read (13.7126 s), stout (67.8867 s), gauge/Clover load (1.41994 s),
and the initial 24 homogeneous setup vectors. PSS after gauge load was
50.5608 / 50.6097 GiB. During the first basis/coarse construction, live scheduler
memMax reached 406706 / 412415 in scheduler MB units; final surviving-host
memMax was 472932. ORTE then reported losing its remote daemon; Donau marked
the job FAILED at 14:56:56. There is no explicit OOM message and no C64 setup or
solve result. High memory pressure is a hypothesis supported by the peak, not
an independently confirmed kernel OOM diagnosis.

## Attempt 3: reuse resident halo pages

The original budget above counted physical face elements as resident vector
bytes. That is too optimistic for blocked component-major EO storage: writing
both parity faces touches pages throughout each unowned aggregate. At C64's
block 8,8,8,4 and one owned time aggregate/rank, a fine vector can commit one
owned plus two complete ghost aggregate planes. The 24 setup vectors can then
occupy about 108 GiB/node, not 54. Batch2 restart16 directions plus owned-only
images can occupy about 192 GiB/node, not the earlier 144 estimate.

Hypothesis: owned spinors are persistent numerical state, but received halos
are only scratch for the current operator application. Map fully unowned pages
of every large workspace onto a reusable per-rank memfd, with distinct slots
for simultaneous RHS columns. Keep original virtual indices, kernels and MPI
face messages. Never map pages containing owned values. Rebind on every operator
call to avoid stale pointer-lifetime caches. Small non-mmap allocations retain
the old path. Frozen Linux API constraints: `docs/reference/lqcd-halo-memory-v1`.

This should reduce 24-vector setup residency toward 36 GiB owned + 3 GiB scratch
per node, and batch2 restart16 GCR residency toward 96 GiB owned + 6 GiB scratch,
plus small private partial pages and lifetime overlap. These are predictions;
the new implementation still needs unit/MPI gates, real C24 independent residuals
and an actual C64 run. Ordinary/shared modes and the prior C24-correct revision
remain recoverable from Git.

## Resource stop requested by the user

After the first real C64 failure, the user asked to stop if more nodes are needed
and offered to request resources. No new job was submitted after 2125108. The
conservative next allocation is four whole nodes, 16 MPI/node, 32 threads/MPI,
64 ranks total, time grid 1,1,1,64, local lattice 64^3x2, block 8,8,8,2. Three
nodes are incompatible with the current equal t-slab contract because 48 ranks
do not divide 128. Request 480000 scheduler MB/node and about 2432 exclusive-node
charged CPUs. The 250--320 GiB/node memory budget is a prediction, not acceptance.

The halo-page implementation was prepared locally but has not been compiled or
run on target hardware. Preserve it on `codex/c64-halo-pages`, separate from the
last C24-validated baseline. Its Python and shell syntax checks passed; these do
not establish C++ correctness, memory use or C64 performance. No C64 warmed
single/full12 time exists yet. The frozen reference and all experiment sources
are published, and further jobs wait for the user's resource update.
