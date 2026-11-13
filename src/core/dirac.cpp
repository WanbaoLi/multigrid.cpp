#include "core/dirac.h"
#include "core/clover.h"
#include "core/dslash.h"

void apply_dirac(const Gauge &g, const Field &in, Field &out, int nr, double mass) {
    apply_clover_only(g, in, out, nr);
    add_dslash(g, in, out, nr, mass);
}
