#pragma once
#include "gauge.h"

void build_clover(const Gauge &g, Field &all);
void apply_clover_only(const Gauge &g, const Field &in, Field &out, int nr);
