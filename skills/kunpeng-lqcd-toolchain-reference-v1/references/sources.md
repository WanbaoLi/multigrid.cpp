# Official references inspected2026-11-04

These are short paraphrases. Public upstream manuals/source do not identify
the complete implementation of a vendor build.

1. [GCC12 changes](https://gcc.gnu.org/gcc-12/changes.html): AArch64/Arm improvements
   include additional architecture/CPU targeting, signed-difference dot-product
   vectorization and changes to Advanced SIMD intrinsics. The release also
   changes-O2 vectorization policy. Our baseline already uses-O3, so that-O2
   change cannot by itself explain a speedup. None of these entries promises a
   faster Wilson–Clover solve on the observed CPU.
2. [GCC12.3 AArch64 options](https://gcc.gnu.org/onlinedocs/gcc-12.3.0/gcc/AArch64-Options.html):
   native targeting depends on the compilation host. Scalable SVE is the
   vector-length-independent default; explicit fixed lengths allow assumptions
   that limit portability. LP64/ILP32 library interfaces must match. Keep the
   existing native/scalable policy when first isolating a compiler change.
3. [LLVM OpenMP runtime](https://openmp.llvm.org/design/Runtimes.html): libomp is
   the host runtime. Its wait controls differ from GNU's: the documented default
   policy can still spin for KMP_BLOCKTIME unless the policy is explicitly set.
   The upstream documented default blocktime is200ms. This is not a measurement
   of the installed BiSheng runtime or justification to scan arbitrary values.
4. [LLVM17 GOMP bridge source](https://raw.githubusercontent.com/llvm/llvm-project/release/17.x/openmp/runtime/src/kmp_gsupport.cpp):
   upstream implements GOMP entry points through its host runtime. That makes a
   compatibility investigation plausible. A vendor build may expose a different
   symbol/version set; check the actual native library and KUPL dependencies.

The installed-version observations in site-evidence.json come from login-only
version queries and existing project history. They establish availability and
prior failure mechanisms, not compute-node correctness, target flags or speed.
