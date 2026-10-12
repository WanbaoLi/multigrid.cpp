#pragma once
#include <chrono>
#ifdef _OPENMP
#include <omp.h>
#endif

inline int thread_count() {
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}
inline double wall_seconds() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
