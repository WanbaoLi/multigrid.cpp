#pragma once
#include "lqcd/core/field.h"
#include <string>

struct Options : Lattice {
    int nrhs = 1, maxit = 100;
    double tol = 1e-12;
    double mass = -.277, csw = 1.;
    int bx = 6, by = 6, bz = 6, bt = 4;
    bool operator_probe = false;
    bool check_ac = false;
    bool plain = false, check_only = false;
    int restart = 8;
    int repeat = 1;
    bool benchmark = false;
    std::string trace, coarse_source, validate_solution;
    bool diagnose_ac = false;
    std::string gauge, source, out = "cpu_mg_solution.bin";
    std::string basis = "canonical";
    std::string basis_file = "basis.bin";
};
