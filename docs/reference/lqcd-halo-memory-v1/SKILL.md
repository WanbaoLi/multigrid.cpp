---
name: lqcd-halo-memory-v1
description: Apply frozen Linux mmap and memfd constraints when bounding resident halo memory in the multigrid.cpp distributed CPU solver. Keep measurements and experimental code outside this reference.
---

# LQCD halo memory reference v1

Frozen 2026-11-14. Do not edit this reference during experiments; create a new
version if the kernel API assumptions change. Verify `manifest.json` before use.

Use these primary Linux man-pages for shared scratch mappings:

- [mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html): file offsets and
  mapping addresses must meet the actual system page alignment. Shared mappings
  of the same file offset refer to the same storage. A mapping remains valid
  after its file descriptor is closed. `MAP_FIXED` replaces existing mappings;
  use it only inside the caller's existing large workspace reservation.
- [memfd_create(2)](https://man7.org/linux/man-pages/man2/memfd_create.2.html): the
  anonymous file has RAM backing, starts with length zero, needs `ftruncate`,
  and is released when the last descriptor/mapping reference disappears. It is
  not a disk checkpoint or a filesystem quota workaround.

Distinguish transmitted face bytes from resident pages. In aggregate-major,
component-major spinors, a thin face can touch every page of an unowned aggregate.
Count actual pages, not just communicated scalar elements. Use runtime
`sysconf(_SC_PAGESIZE)`; do not assume 4 KiB or infer pages from the login host.

Numerical state is the owned portion of each spinor. Its received halo is
scratch, valid only for the current operator application. Reusing physical halo
pages across vectors is valid only while owned values remain private, no caller
expects old halo values, and no two simultaneous RHS columns share the same
scratch slot. Each active RHS needs a separate slot. Keep sends in separate
buffers until MPI completes. Map only full pages wholly inside unowned regions;
leave boundary pages that also contain owned values private.

Do not cache mappings by pointer alone: an allocator can reuse an address after
deallocation. Either track allocation lifetime or rebind before each operator.
Small `posix_memalign` allocations are not `mmap` reservations and must not be
replaced with `MAP_FIXED`. Closing the scratch owner does not remove mappings
held by surviving setup vectors; include that overlap in the lifetime budget.

Validate independent full-operator residuals, repeated and batched solves,
coincident periodic neighbors and preserved owned values. Compare summed PSS
and kernel/scheduler peaks; RSS counts aliases repeatedly. Keep source hashes,
page size, MPI transport and all failure evidence in the experiment record.
