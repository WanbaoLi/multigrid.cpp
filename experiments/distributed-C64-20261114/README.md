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
