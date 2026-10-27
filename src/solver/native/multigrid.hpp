#pragma once
#include "lqcd/core/multigrid.h"
#include <memory>
#include <mpi.h>
// Project-owned mixed-precision aggregation MG. No external solver calls.
class NativeMG {
    struct Impl;
    std::unique_ptr<Impl> impl;

  public:
    NativeMG(const Gauge &, const Multigrid &, MPI_Comm = MPI_COMM_SELF, unsigned seed = 1024);
    ~NativeMG();
    // Double fields contain only the rank-owned lexical t slab.
    void apply(const Field &, Field &) const;
    void precondition(const Field &, Field &);
    void solve(const Field &, Field &, double tol, int maxiter, int restart);
    std::vector<int> solve_batch(const std::vector<Field> &b, std::vector<Field> &x,
                                 double tol, int maxiter, int restart);
    void generate_basis(Multigrid &, int homogeneous_cycles, int adaptive_steps);
    void verify() const;
    // Optional NUMA policy for immutable rank-owned coefficient pages.
    // Called collectively after the final hierarchy has passed its gates.
    void place_hot_data();
    int iterations = 0;
};
