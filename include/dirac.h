#pragma once
#include "gauge.h"

// A = Clover - kappa * hopping; no even/odd preconditioning.
void apply_dirac(const Gauge &g, const Field &in, Field &out, int nr, double mass = -.277);
