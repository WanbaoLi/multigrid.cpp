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
| Batch2 GCR directions/images at restart24, including halos | up to 216 GiB |

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
