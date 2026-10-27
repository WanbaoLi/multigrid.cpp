#pragma once
#include "lqcd/core/gauge.h"

// A = Clover - kappa * hopping; no even/odd preconditioning.
void apply_dirac(const Gauge &g, const Field &in, Field &out, int nr, double mass);
inline void apply_dirac(const Gauge &g, const Field &in, Field &out, int nr) {
    apply_dirac(g, in, out, nr, g.o.mass);
}
