#pragma once
// Compile-time hardware selection: algorithm/MPI code never includes a second
// copy of the solver. ISA-specific headers remain in their hardware backend.
#if defined(LQCD_BACKEND_ARM) || defined(__aarch64__)
#define LQCD_NATIVE_ARM_WILSON 1
#include "../../backends/arm/wilson_kernel.hpp"
#include "../../backends/arm/clover_neon.hpp"
#include "../../backends/arm/transfer_sve.hpp"
#include "../../backends/arm/coarse_sve.hpp"
#if defined(__ARM_FEATURE_SVE)
#define LQCD_NATIVE_SVE_TRANSFER 1
#define LQCD_NATIVE_SVE_COARSE 1
#endif
#if defined(__aarch64__)
#define LQCD_NATIVE_NEON_CLOVER 1
#endif
namespace lqcd_native { namespace kernels = arm; }
#else
#include "../../backends/x86/wilson_kernel.hpp"
#include "../../backends/x86/transfer_avx512.hpp"
namespace lqcd_native { namespace kernels = x86; }
#if defined(__AVX512F__)
#define LQCD_NATIVE_AVX512_TRANSFER 1
#if !defined(LQCD_DISABLE_LOCAL_AVX512)
#define LQCD_NATIVE_PACKED_WILSON 1
#endif
#endif
#endif
