#pragma once
#include "core/gauge.h"

void build_clover(const Gauge &g, Field &all);
void build_clover(const Gauge &g, CoefficientField &all, int first_t = 0, int end_t = -1);
void apply_clover_only(const Gauge &g, const Field &in, Field &out, int nr);
