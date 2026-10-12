#pragma once
#include "gauge.h"

struct Multigrid
{
    Options o;
    int cx, cy, cz, ct, block_volume;
    int coarse_dof = 12;
    size_t n_fine, n_coarse;
    Field basis;   // [coarse block][fine site_index in block][fine component][coarse component]
    Field stencil; // [coarse site_index][onsite,+x,-x,+y,-y,+z,-z,+t,-t][row][column]
};

size_t coarse_site_index(int x, int y, int z, int t, const Multigrid &m);
int local_site(int x, int y, int z, int t, const Multigrid &m);
size_t basis_index(size_t cb, int ls, int a, int d, const Multigrid &m);
void build_coarse_operator(const Gauge &g, Multigrid &m);
void prolong_field(const Multigrid &m, const Field &coarse, Field &fine, int nr);
void restrict_field(const Multigrid &m, const Field &fine, Field &coarse, int nr);
void apply_coarse_matrixfree(const Gauge &g, const Multigrid &m, const Field &x, Field &y, int nr);
void apply_coarse(const Gauge &g, const Multigrid &m, const Field &x, Field &y, int nr);
void vcycle(const Gauge &g, const Multigrid &m, Field &x, const Field &b, int nr);
