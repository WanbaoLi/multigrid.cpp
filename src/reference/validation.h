#pragma once
#include "lqcd/core/multigrid.h"

void check_coarse_operator(const Gauge &g, const Multigrid &m);
void diagnose_one_coarse_site(const Gauge &g, const Multigrid &m);
