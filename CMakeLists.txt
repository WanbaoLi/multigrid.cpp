cmake_minimum_required(VERSION 3.16)
project(multigrid_cpp VERSION 0.2.0 LANGUAGES C CXX)

option(LQCD_BUILD_RUNTIME "Build the PyQUDA-compatible MPI runtime" OFF)
option(LQCD_DD_REFERENCE "Build the optional DDalphaAMG reference adapter" OFF)
option(LQCD_BUILD_NATIVE_BENCH "Build the native component benchmark" OFF)
option(MULTIGRID_OPENMP "Enable OpenMP in the core library" ON)
option(MULTIGRID_NATIVE "Tune the build for the host CPU" OFF)
option(LQCD_KUPL_HBW "Enable optional Kunpeng KUPL HBW allocation" OFF)
set(LQCD_KUPL_ROOT "" CACHE PATH "KUPL prefix containing include/kupl.h and lib/libkupl")

if(LQCD_KUPL_HBW)
    find_path(LQCD_KUPL_INCLUDE_DIR kupl.h HINTS "${LQCD_KUPL_ROOT}" "$ENV{KUPL_ROOT}" PATH_SUFFIXES include)
    find_library(LQCD_KUPL_LIBRARY kupl HINTS "${LQCD_KUPL_ROOT}" "$ENV{KUPL_ROOT}" PATH_SUFFIXES lib lib64)
    if(NOT LQCD_KUPL_INCLUDE_DIR OR NOT LQCD_KUPL_LIBRARY)
        message(FATAL_ERROR "LQCD_KUPL_HBW requires kupl.h and libkupl; set LQCD_KUPL_ROOT")
    endif()
endif()

function(lqcd_link_kupl target)
    if(LQCD_KUPL_HBW)
        target_compile_definitions(${target} PRIVATE LQCD_HAVE_KUPL=1)
        target_include_directories(${target} PRIVATE "${LQCD_KUPL_INCLUDE_DIR}")
        target_link_libraries(${target} PRIVATE "${LQCD_KUPL_LIBRARY}")
    endif()
endfunction()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(LQCD_CORE_SOURCES
    src/core/field.cpp src/core/gauge.cpp src/core/clover.cpp
    src/core/dslash.cpp src/core/dirac.cpp src/core/gcr.cpp src/core/multigrid.cpp)
add_library(multigrid_core ${LQCD_CORE_SOURCES})
set_target_properties(multigrid_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(multigrid_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(MULTIGRID_OPENMP)
    find_package(OpenMP QUIET)
    if(OpenMP_CXX_FOUND)
        target_link_libraries(multigrid_core PUBLIC OpenMP::OpenMP_CXX)
    endif()
endif()
if(MULTIGRID_NATIVE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(multigrid_core PUBLIC -march=native -mtune=native)
endif()

# Independent scalar/reference executable used by the correctness oracle.
add_executable(multigrid src/reference/main.cpp src/reference/validation.cpp)
target_include_directories(multigrid PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/reference)
target_link_libraries(multigrid PRIVATE multigrid_core)

if(LQCD_BUILD_RUNTIME OR LQCD_BUILD_NATIVE_BENCH)
    find_package(MPI REQUIRED COMPONENTS C CXX)
    find_package(OpenMP REQUIRED COMPONENTS C CXX)
    set(LQCD_NATIVE_SOURCES
        src/solver/native/hbw_assets.cpp
        src/solver/native/environment.cpp
        src/solver/native/hierarchy.cpp
        src/solver/native/fine_operator.cpp
        src/solver/native/double_operator.cpp
        src/solver/native/sap.cpp
        src/solver/native/coarse.cpp
        src/solver/native/cycle.cpp
        src/solver/native/setup.cpp
        src/solver/native/solver.cpp
        src/solver/native/batched_solver.cpp
        src/solver/native/batched_fine_operator.cpp
        src/solver/native/batched_cycle.cpp
        src/solver/native/batched_sap.cpp
        src/solver/native/validation.cpp
        src/solver/native/memory_placement.cpp
        src/support/hbw_buffer.cpp
        src/solver/native/halo_profile.cpp)
endif()

if(LQCD_BUILD_NATIVE_BENCH)
    add_executable(bench_native benchmarks/native/bench_native.cpp ${LQCD_NATIVE_SOURCES})
    target_include_directories(bench_native PRIVATE src/solver/native)
    target_link_libraries(bench_native PRIVATE multigrid_core MPI::MPI_CXX OpenMP::OpenMP_CXX)
    lqcd_link_kupl(bench_native)
endif()

if(LQCD_BUILD_RUNTIME)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64|i.86)$")
        set(LQCD_HARDWARE_BACKEND x86)
        set(LQCD_HARDWARE_DEFINE LQCD_BACKEND_X86=1)
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|AARCH64|arm64|ARM64)$")
        set(LQCD_HARDWARE_BACKEND arm)
        set(LQCD_HARDWARE_DEFINE LQCD_BACKEND_ARM=1)
    else()
        message(FATAL_ERROR "Supported CPU backends are x86 and AArch64 ARM")
    endif()
    add_library(lqcd_cpu SHARED
        src/runtime/context.cpp src/runtime/layout.cpp src/runtime/registry.cpp
        ${LQCD_NATIVE_SOURCES}
        src/solver/native/backend.cpp
        src/backends/${LQCD_HARDWARE_BACKEND}/backend.cpp)
    target_include_directories(lqcd_cpu PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/runtime)
    target_compile_definitions(lqcd_cpu PRIVATE ${LQCD_HARDWARE_DEFINE})
    target_link_libraries(lqcd_cpu PRIVATE multigrid_core MPI::MPI_CXX OpenMP::OpenMP_CXX m)
    lqcd_link_kupl(lqcd_cpu)
    if(LQCD_DD_REFERENCE)
        include(cmake/DDalphaAMG.cmake)
        target_sources(lqcd_cpu PRIVATE src/references/ddalphaamg/adapter.cpp)
        target_compile_definitions(lqcd_cpu PRIVATE LQCD_DD_REFERENCE=1)
        target_link_libraries(lqcd_cpu PRIVATE ddalphaamg)
    endif()
    target_link_options(lqcd_cpu PRIVATE "-Wl,--exclude-libs,ALL")
    set_target_properties(lqcd_cpu PROPERTIES CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN YES VERSION 0.2.0 SOVERSION 0)
    install(TARGETS lqcd_cpu LIBRARY DESTINATION lib)
    install(FILES include/lqcd/lqcd.h DESTINATION include/lqcd)
    set(LQCD_TEST_PYTHON "" CACHE FILEPATH "Python with mpi4py, numpy and PyQUDA fields")
endif()

include(cmake/Tests.cmake)
