#pragma once
#include "gauge.h"

// DeGrand-Rossi Euclidean gamma matrices, directions X,Y,Z,T.
extern Complex gamma_matrix[4][4][4];
void gamma_init();
// Add normalized hopping to an already initialized output. This preserves
// the original clover-first accumulation order in apply_dirac().
void add_dslash(const Gauge &g, const Field &in, Field &out, int nr, double mass = -.277);
void apply_dslash(const Gauge &g, const Field &in, Field &out, int nr);
