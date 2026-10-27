#include "backend.hpp"
#include <climits>
#include <cmath>
#include <cstring>
#include <limits>
#include <omp.h>
#include <sstream>
using namespace lqcd;
struct lqcd_context {
    lqcd_config config{};
    Geometry geometry;
    MPI_Comm comm = MPI_COMM_NULL;
    enum Stage { Created, Loaded, Ready } stage = Created;
    std::unique_ptr<Backend> backend;
    bool mutable_threads = false;
    Vector b, x, image, correction, delta;
    std::vector<Vector> batch_b, batch_x, batch_image, batch_correction, batch_delta;
    ~lqcd_context() {
        backend.reset();
        if (comm != MPI_COMM_NULL)
            MPI_Comm_free(&comm);
    }
};
namespace {
thread_local std::string last_error;
bool active = false;
template <class F> int guard(F f) {
    try {
        last_error.clear();
        f();
        return LQCD_SUCCESS;
    } catch (const Error &e) {
        last_error = e.what();
        return e.code;
    } catch (const std::exception &e) {
        last_error = e.what();
        return LQCD_INTERNAL_ERROR;
    }
}
void collective(MPI_Comm comm, int code, const char *message) {
    int failure = 0;
    MPI_Allreduce(&code, &failure, 1, MPI_INT, MPI_MAX, comm);
    if (failure)
        throw Error(failure, code ? message : "another rank rejected this collective operation");
}
void same(MPI_Comm comm, uint64_t value) {
    uint64_t lo, hi;
    MPI_Allreduce(&value, &lo, 1, MPI_UINT64_T, MPI_MIN, comm);
    MPI_Allreduce(&value, &hi, 1, MPI_UINT64_T, MPI_MAX, comm);
    if (lo != hi)
        throw Error(LQCD_INVALID_ARGUMENT,
                    "collective configuration/operation differs across ranks");
}
uint64_t config_hash(const lqcd_config &c, const char *name) {
    uint64_t h = 1469598103934665603ULL;
    auto add = [&](const void *p, size_t n) {
        auto q = static_cast<const unsigned char *>(p);
        for (size_t i = 0; i < n; i++) {
            h ^= q[i];
            h *= 1099511628211ULL;
        }
    };
    add(c.lattice, sizeof(c.lattice));
    add(c.process_grid, sizeof(c.process_grid));
    add(c.block, sizeof(c.block));
    // Threads are rank-local resources, not a collective numerical parameter.
    // Different NUMA domains/cpusets may expose different numbers of cores.
    add(&c.levels, sizeof(c.levels));
    add(&c.t_boundary, sizeof(c.t_boundary));
    add(&c.normalization, sizeof(c.normalization));
    add(&c.mass, sizeof(c.mass));
    add(&c.csw, sizeof(c.csw));
    add(&c.seed, sizeof(c.seed));
    add(name, std::strlen(name));
    return h;
}
void enter(lqcd_context *c, int operation, lqcd_context::Stage expected) {
    if (!c)
        throw Error(LQCD_INVALID_STATE, "null/closed context");
    int main = 0;
    MPI_Is_thread_main(&main);
    if (!main)
        throw Error(LQCD_INVALID_STATE, "collective API must run on the MPI main thread");
    same(c->comm, (uint64_t)operation);
    collective(c->comm, c->stage == expected ? 0 : LQCD_INVALID_STATE,
               "invalid context lifecycle state");
    omp_set_dynamic(0);
    omp_set_num_threads(c->config.threads);
}
void view(lqcd_context *c, const lqcd_field_view *f, size_t elements) {
    int err = (!f || !f->data || f->complex_elements != elements) ? LQCD_INVALID_ARGUMENT : 0;
    if (!err && (f->precision != LQCD_COMPLEX128 ||
                 (f->layout != LQCD_LEX_TZYX && f->layout != LQCD_PYQUDA_EO_X)))
        err = LQCD_UNSUPPORTED;
    collective(c->comm, err,
               "field must be contiguous complex128 with declared layout and local element count");
}
double global_norm2(const Vector &x, MPI_Comm comm) {
    double local = 0, total = 0;
#pragma omp parallel for reduction(+ : local) schedule(static)
    for (size_t i = 0; i < x.size(); i++)
        local += std::norm(x[i]);
    MPI_Allreduce(&local, &total, 1, MPI_DOUBLE, MPI_SUM, comm);
    return total;
}
double max_time(MPI_Comm comm, double begin) {
    double elapsed = MPI_Wtime() - begin, maximum;
    MPI_Allreduce(&elapsed, &maximum, 1, MPI_DOUBLE, MPI_MAX, comm);
    return maximum;
}
} // namespace
extern "C" {
const char *lqcd_last_error() {
    return last_error.c_str();
}
const char *lqcd_backend_capabilities(const char *name) {
#ifdef LQCD_BACKEND_X86
    if (name && !std::strcmp(name, "x86"))
        return "{\"backend\":\"x86\",\"algorithm\":\"project-owned adaptive aggregation MG + SAP + "
               "flexible "
               "GCR\",\"mpi\":true,\"mpi_decomposition\":\"t-slab\",\"levels\":[2],\"setup\":"
               "\"native homogeneous SAP and inverse "
               "iteration\",\"max_active_contexts_per_process\":1,\"device\":\"cpu\",\"openmp\":"
               "true}";
#endif
#ifdef LQCD_BACKEND_ARM
    if (name && !std::strcmp(name, "arm"))
        return "{\"backend\":\"arm\",\"algorithm\":\"project-owned adaptive aggregation MG + SAP + "
               "flexible "
               "GCR\",\"mpi\":true,\"mpi_decomposition\":\"t-slab\",\"levels\":[2],\"setup\":"
               "\"native homogeneous SAP and inverse "
               "iteration\",\"max_active_contexts_per_process\":1,\"device\":\"cpu\",\"openmp\":"
               "true}";
#endif
#ifndef LQCD_DD_REFERENCE
    return "{}";
#else
    if (!name || std::strcmp(name, "reference-ddalphaamg"))
        return "{}";
    return "{\"backend\":\"ddalphaamg\",\"abi\":1,\"device\":\"cpu\",\"mpi\":true,\"openmp\":true,"
           "\"io_precision\":[\"complex128\"],\"layouts\":[\"lex_tzyx\",\"pyquda_eo_x\"],\"max_"
           "active_contexts_per_process\":1,\"concurrent_solves\":false}";
#endif
}
int lqcd_create(const char *name, const lqcd_config *cfg, lqcd_context **out) {
    return guard([&] {
        if (!cfg || !name || !out)
            throw Error(LQCD_INVALID_ARGUMENT, "null create argument");
        *out = nullptr;
        int initialized = 0, finalized = 0, main = 0;
        MPI_Initialized(&initialized);
        MPI_Finalized(&finalized);
        if (!initialized || finalized)
            throw Error(LQCD_INVALID_STATE, "caller must initialize MPI and keep it alive");
        MPI_Is_thread_main(&main);
        if (!main)
            throw Error(LQCD_INVALID_STATE, "create requires MPI main thread");
        MPI_Comm parent = MPI_Comm_f2c(static_cast<MPI_Fint>(cfg->mpi_comm_f));
        if (parent == MPI_COMM_NULL)
            throw Error(LQCD_INVALID_ARGUMENT, "null MPI communicator");
        collective(
            parent,
            cfg->abi_version == 1 && cfg->struct_size == sizeof(*cfg) ? 0 : LQCD_INVALID_ARGUMENT,
            "ABI/struct size mismatch");
        same(parent, config_hash(*cfg, name));
        collective(parent, active ? LQCD_INVALID_STATE : 0,
                   "runtime currently supports one live context per process");
        collective(parent,
                   std::strcmp(lqcd_backend_capabilities(name), "{}") ? 0 : LQCD_UNSUPPORTED,
                   "backend is not built");
        auto c = std::make_unique<lqcd_context>();
        c->config = *cfg;
        c->mutable_threads = std::strcmp(name, "x86") == 0 || std::strcmp(name, "arm") == 0;
        int rank, size;
        MPI_Comm_rank(parent, &rank);
        MPI_Comm_size(parent, &size);
        int thread_support;
        MPI_Query_thread(&thread_support);
        collective(parent,
                   cfg->threads > 1 && thread_support < MPI_THREAD_FUNNELED ? LQCD_UNSUPPORTED : 0,
                   "MPI must be initialized with at least MPI_THREAD_FUNNELED for OpenMP workers");
        int error = 0;
        uint64_t product = 1, volume = 1, block_volume = 1;
        if (cfg->threads < 1 || cfg->levels < 2 || cfg->levels > 3 ||
            (cfg->t_boundary != 1 && cfg->t_boundary != -1) || cfg->normalization < 0 ||
            cfg->normalization > 1 || !std::isfinite(cfg->mass) || cfg->mass <= -4 ||
            !std::isfinite(cfg->csw))
            error = 1;
        for (int d = 0; d < 4; d++) {
            int n = cfg->lattice[d], p = cfg->process_grid[d], b = cfg->block[d];
            if (n <= 0 || p <= 0 || b <= 0 || n % 2 || n % p) {
                error = 1;
                continue;
            }
            c->geometry.local[d] = n / p;
            product *= p;
            volume *= n / p;
            block_volume *= b;
            if ((n / p) % 2 || (n / p) % b || n / b < (cfg->levels == 3 ? 4 : 2))
                error = 1;
        }
        if (product != (uint64_t)size || volume > INT_MAX / 72 || block_volume < 4)
            error = 1;
        collective(parent, error ? LQCD_INVALID_ARGUMENT : 0,
                   "invalid geometry, process grid, block, physics or thread settings");
        /* Public rank order is xyzt with t fastest, matching PyQUDA. */
        for (int d = 3; d >= 0; d--) {
            c->geometry.coords[d] = rank % cfg->process_grid[d];
            rank /= cfg->process_grid[d];
        }
        c->geometry.volume = volume;
        MPI_Comm_dup(parent, &c->comm);
        omp_set_dynamic(0);
        omp_set_num_threads(cfg->threads);
        c->backend = make_backend(name, *cfg, c->geometry, c->comm);
        active = true;
        *out = c.release();
    });
}
int lqcd_load_gauge(lqcd_context *c, const lqcd_field_view *g) {
    return guard([&] {
        enter(c, 1, lqcd_context::Created);
        view(c, g, c->geometry.volume * 36);
        Vector gauge;
        unpack_gauge(*g, c->geometry, gauge);
        collective(c->comm, std::isfinite(global_norm2(gauge, c->comm)) ? 0 : LQCD_INVALID_ARGUMENT,
                   "nonfinite gauge");
        c->backend->load_gauge(gauge);
        c->stage = lqcd_context::Loaded;
    });
}
int lqcd_setup(lqcd_context *c, double *seconds) {
    return guard([&] {
        enter(c, 2, lqcd_context::Loaded);
        collective(c->comm, seconds ? 0 : LQCD_INVALID_ARGUMENT, "null setup result");
        MPI_Barrier(c->comm);
        double begin = MPI_Wtime();
        c->backend->setup();
        *seconds = max_time(c->comm, begin);
        c->stage = lqcd_context::Ready;
    });
}
int lqcd_set_threads(lqcd_context *c, int32_t threads) {
    return guard([&] {
        enter(c, 6, lqcd_context::Ready);
        collective(c->comm, c->mutable_threads ? 0 : LQCD_UNSUPPORTED,
                   "backend does not support changing thread resources after setup");
        collective(c->comm, threads > 0 ? 0 : LQCD_INVALID_ARGUMENT, "threads must be positive");
        int support;
        MPI_Query_thread(&support);
        collective(c->comm, threads > 1 && support < MPI_THREAD_FUNNELED ? LQCD_UNSUPPORTED : 0,
                   "MPI must be initialized with at least MPI_THREAD_FUNNELED for OpenMP workers");
        // All validation is collective and precedes mutation, so a bad request
        // on one rank leaves every rank's context resource count unchanged.
        c->config.threads = threads;
        omp_set_dynamic(0);
        omp_set_num_threads(threads);
    });
}
int lqcd_apply(lqcd_context *c, const lqcd_field_view *in, lqcd_field_view *out) {
    return guard([&] {
        enter(c, 3, lqcd_context::Ready);
        view(c, in, c->geometry.volume * 12);
        view(c, out, c->geometry.volume * 12);
        unpack_spinor(*in, c->geometry, c->b);
        c->backend->apply(c->b, c->x);
        if (c->config.normalization == LQCD_KAPPA_NORMALIZATION) {
            double scale = 1 / (4 + c->config.mass);
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < c->x.size(); i++)
                c->x[i] *= scale;
        }
        pack_spinor(c->x, c->geometry, *out);
    });
}
int lqcd_solve(lqcd_context *c, const lqcd_field_view *in, lqcd_field_view *out, double tol,
               lqcd_solve_result *r) {
    return guard([&] {
        double begin = MPI_Wtime();
        enter(c, 4, lqcd_context::Ready);
        collective(c->comm,
                   r && r->struct_size == sizeof(*r) && std::isfinite(tol) && tol > 0 && tol < 1
                       ? 0
                       : LQCD_INVALID_ARGUMENT,
                   "invalid tolerance or result structure");
        uint64_t bits;
        std::memcpy(&bits, &tol, sizeof(bits));
        same(c->comm, bits);
        view(c, in, c->geometry.volume * 12);
        view(c, out, c->geometry.volume * 12);
        unpack_spinor(*in, c->geometry, c->b);
        if (c->config.normalization == LQCD_KAPPA_NORMALIZATION) {
            double scale = 4 + c->config.mass;
#pragma omp parallel for schedule(static)
            for (size_t i = 0; i < c->b.size(); i++)
                c->b[i] *= scale;
        }
        double bn = global_norm2(c->b, c->comm);
        collective(c->comm, std::isfinite(bn) ? 0 : LQCD_INVALID_ARGUMENT, "nonfinite source");
        r->iterations = 0;
        r->refinement_steps = 0;
        r->solver_seconds = 0;
        r->true_residual = 0;
        r->converged = 1;
        if (bn == 0)
            c->x.assign(c->b.size(), Complex{});
        else {
            auto info = c->backend->solve(c->b, c->x, tol);
            r->iterations = info.iterations;
            r->solver_seconds = info.seconds;
            auto verify = [&] {
                c->backend->apply(c->x, c->image);
#pragma omp parallel for schedule(static)
                for (size_t i = 0; i < c->image.size(); i++)
                    c->image[i] -= c->b[i];
                r->true_residual = std::sqrt(global_norm2(c->image, c->comm) / bn);
                r->converged = std::isfinite(r->true_residual) && r->true_residual <= tol;
            };
            verify();
            // Mixed-precision recurrences can understate the final full residual.
            // Correct only failed solves, with the same hierarchy and an explicit
            // double-precision defect. Never relax the caller's residual gate.
            while (!r->converged && std::isfinite(r->true_residual) && r->refinement_steps < 2) {
                c->correction = c->image;
#pragma omp parallel for schedule(static)
                for (size_t i = 0; i < c->correction.size(); i++)
                    c->correction[i] = -c->correction[i];
                double inner_tol = std::min(.1, .25 * tol / r->true_residual);
                auto fix = c->backend->solve(c->correction, c->delta, inner_tol);
                r->iterations += fix.iterations;
                r->solver_seconds += fix.seconds;
                r->refinement_steps++;
#pragma omp parallel for schedule(static)
                for (size_t i = 0; i < c->x.size(); i++)
                    c->x[i] += c->delta[i];
                verify();
            }
        }
        pack_spinor(c->x, c->geometry, *out);
        r->api_seconds = max_time(c->comm, begin);
        if (!r->converged) {
            std::ostringstream message;
            message << "full-operator residual " << r->true_residual << " exceeds tolerance " << tol
                    << " or backend did not converge";
            throw Error(LQCD_NOT_CONVERGED, message.str());
        }
    });
}
int lqcd_solve_batch(lqcd_context *c, const lqcd_field_view *inputs, lqcd_field_view *outputs,
                     int count, double tol, lqcd_solve_result *results) {
    return guard([&] {
        const double begin = MPI_Wtime();
        enter(c, 7, lqcd_context::Ready);
        same(c->comm, static_cast<uint64_t>(count));
        collective(c->comm,
                   count >= 1 && count <= 12 && inputs && outputs && results && std::isfinite(tol) &&
                           tol > 0 && tol < 1
                       ? 0
                       : LQCD_INVALID_ARGUMENT,
                   "batch requires count1..12, field arrays, result array and valid tolerance");
        uint64_t bits;
        std::memcpy(&bits, &tol, sizeof(bits));
        same(c->comm, bits);
        c->batch_b.resize(count);
        c->batch_x.resize(count);
        c->batch_image.resize(count);
        c->batch_correction.resize(count);
        c->batch_delta.resize(count);
        std::vector<double> norms(count);
        bool any_nonzero = false;
        // Unpack every input before writing any output, preserving valid aliasing.
        for (int j = 0; j < count; ++j) {
            collective(c->comm,
                       results[j].struct_size == sizeof(results[j]) ? 0 : LQCD_INVALID_ARGUMENT,
                       "invalid batch result structure");
            view(c, &inputs[j], c->geometry.volume * 12);
            view(c, &outputs[j], c->geometry.volume * 12);
            unpack_spinor(inputs[j], c->geometry, c->batch_b[j]);
            auto &b = c->batch_b[j];
            if (c->config.normalization == LQCD_KAPPA_NORMALIZATION) {
                const double factor = 4 + c->config.mass;
#pragma omp parallel for schedule(static)
                for (size_t i = 0; i < b.size(); ++i)
                    b[i] *= factor;
            }
            norms[j] = global_norm2(b, c->comm);
            collective(c->comm, std::isfinite(norms[j]) ? 0 : LQCD_INVALID_ARGUMENT,
                       "nonfinite batch source");
            any_nonzero = any_nonzero || norms[j] != 0;
            auto &r = results[j];
            r.iterations = r.refinement_steps = 0;
            r.converged = 1;
            r.solver_seconds = r.api_seconds = r.true_residual = 0;
            c->batch_x[j].assign(b.size(), Complex{});
        }
        double solver_wall = 0;
        if (any_nonzero) {
            const double start = MPI_Wtime();
            auto info = c->backend->solve_batch(c->batch_b, c->batch_x, tol);
            solver_wall = max_time(c->comm, start);
            collective(c->comm, info.size() == static_cast<size_t>(count) ? 0 : LQCD_INTERNAL_ERROR,
                       "backend returned invalid batch result count");
            for (int j = 0; j < count; ++j)
                results[j].iterations = info[j].iterations;
        }
        int failed = -1;
        for (int j = 0; j < count; ++j) {
            auto &r = results[j];
            auto &x = c->batch_x[j];
            auto &b = c->batch_b[j];
            auto &image = c->batch_image[j];
            if (norms[j] == 0) {
                x.assign(b.size(), Complex{});
                r.iterations = 0;
            } else {
                auto verify = [&] {
                    c->backend->apply(x, image);
#pragma omp parallel for schedule(static)
                    for (size_t i = 0; i < image.size(); ++i)
                        image[i] -= b[i];
                    r.true_residual = std::sqrt(global_norm2(image, c->comm) / norms[j]);
                    r.converged = std::isfinite(r.true_residual) && r.true_residual <= tol;
                };
                verify();
                while (!r.converged && std::isfinite(r.true_residual) && r.refinement_steps < 2) {
                    auto &correction = c->batch_correction[j];
                    auto &delta = c->batch_delta[j];
                    correction = image;
#pragma omp parallel for schedule(static)
                    for (size_t i = 0; i < correction.size(); ++i)
                        correction[i] = -correction[i];
                    const double start = MPI_Wtime();
                    auto fix = c->backend->solve(correction, delta,
                                                 std::min(.1, .25 * tol / r.true_residual));
                    solver_wall += max_time(c->comm, start);
                    r.iterations += fix.iterations;
                    ++r.refinement_steps;
#pragma omp parallel for schedule(static)
                    for (size_t i = 0; i < x.size(); ++i)
                        x[i] += delta[i];
                    verify();
                }
            }
            if (!r.converged && failed < 0)
                failed = j;
        }
        for (int j = 0; j < count; ++j)
            pack_spinor(c->batch_x[j], c->geometry, outputs[j]);
        const double api_wall = max_time(c->comm, begin);
        for (int j = 0; j < count; ++j) {
            results[j].solver_seconds = solver_wall;
            results[j].api_seconds = api_wall;
        }
        if (failed >= 0) {
            std::ostringstream error;
            error << "batch RHS " << failed << " full residual " << results[failed].true_residual
                  << " exceeds tolerance " << tol;
            throw Error(LQCD_NOT_CONVERGED, error.str());
        }
    });
}
int lqcd_destroy(lqcd_context *c) {
    return guard([&] {
        if (!c)
            return;
        same(c->comm, 5);
        delete c;
        active = false;
    });
}
}
