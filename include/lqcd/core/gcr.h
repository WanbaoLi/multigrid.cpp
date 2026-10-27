#pragma once
#include "lqcd/core/field.h"
#include <functional>

using LinearOperator = std::function<void(const Field &input, Field &output)>;
struct GcrOptions {
    int maxit = 100;
    double tol = 1e-12;
    int restart = 8;
    std::string out = "solution.bin";
};
// An empty preconditioner means plain GCR. No operator-specific knowledge.
void solve_gcr(const LinearOperator &apply, const LinearOperator &precondition, const Field &b,
               Field &x, const GcrOptions &options);
