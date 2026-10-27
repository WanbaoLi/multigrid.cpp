#ifndef LQCD_CPU_API_H
#define LQCD_CPU_API_H
#include <stddef.h>
#include <stdint.h>
#if defined(_WIN32)
#define LQCD_API __declspec(dllexport)
#else
#define LQCD_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef struct lqcd_context lqcd_context;
enum { LQCD_ABI_VERSION = 1 };
enum {
    LQCD_SUCCESS = 0,
    LQCD_INVALID_ARGUMENT = 1,
    LQCD_INVALID_STATE = 2,
    LQCD_UNSUPPORTED = 3,
    LQCD_NOT_CONVERGED = 4,
    LQCD_INTERNAL_ERROR = 5
};
enum { LQCD_LEX_TZYX = 0, LQCD_PYQUDA_EO_X = 1 };
enum { LQCD_COMPLEX128 = 0 };
enum { LQCD_MASS_NORMALIZATION = 0, LQCD_KAPPA_NORMALIZATION = 1 };
typedef struct {
    uint32_t abi_version, struct_size;
    int32_t lattice[4];      /* global x,y,z,t */
    int32_t process_grid[4]; /* parent communicator rank order: t fastest */
    int32_t block[4];
    int32_t threads, levels, t_boundary, normalization; /* threads >=1, rank-local */
    double mass, csw;
    uint32_t seed;
    int64_t mpi_comm_f; /* MPI_Comm_c2f; caller owns MPI initialization */
} lqcd_config;
typedef struct {
    void *data; /* interleaved real/imag float64, contiguous */
    uint64_t complex_elements;
    int32_t layout, precision;
} lqcd_field_view;
typedef struct {
    uint32_t struct_size;
    int32_t converged, iterations, refinement_steps;
    double solver_seconds, api_seconds, true_residual;
} lqcd_solve_result;

/* All context operations are collective on config.mpi_comm_f, on the MPI
   main thread. Initialize MPI with at least MPI_THREAD_FUNNELED when threads>1.
   One live runtime context/process; no concurrent solves.
   Gauge is untwisted. API applies t_boundary; do not twist links twice.
   PyQUDA gauge: [4,2,T,Z,Y,X/2,3,3]; spinor: [2,T,Z,Y,X/2,4,3].
   Lex gauge: [T,Z,Y,X,4,3,3]; spinor: [T,Z,Y,X,4,3].
   MASS: Mx=b, M=(m+4)I - H/2 + clover; KAPPA: (2*kappa*M)x=b. */
LQCD_API const char *lqcd_last_error(void);
LQCD_API const char *lqcd_backend_capabilities(const char *backend);
LQCD_API int lqcd_create(const char *backend, const lqcd_config *config, lqcd_context **out);
LQCD_API int lqcd_load_gauge(lqcd_context *, const lqcd_field_view *gauge);
LQCD_API int lqcd_setup(lqcd_context *, double *seconds);
/* Ready-context resource update; collective, but counts may differ per rank.
   Does not rebuild the hierarchy or change the numerical operator. Supported
   by the native x86 backend; external reference adapters may reject it. */
LQCD_API int lqcd_set_threads(lqcd_context *, int32_t threads);
LQCD_API int lqcd_apply(lqcd_context *, const lqcd_field_view *in, lqcd_field_view *out);
LQCD_API int lqcd_solve(lqcd_context *, const lqcd_field_view *rhs, lqcd_field_view *out,
                        double tol, lqcd_solve_result *result);
/* count is collectively identical, 1 through 12. Each result retains per-column
   convergence/iterations; api_seconds and solver_seconds describe shared batch
   wall time and must not be summed as independent column times. */
LQCD_API int lqcd_solve_batch(lqcd_context *, const lqcd_field_view *inputs,
                              lqcd_field_view *outputs, int count, double tol,
                              lqcd_solve_result *results);
LQCD_API int lqcd_destroy(lqcd_context *);
#ifdef __cplusplus
}
#endif
#endif
