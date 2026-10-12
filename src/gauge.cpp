#include "gauge.h"

void unit_gauge(Gauge &g)
{
    size_t n = (size_t)g.o.nx * g.o.ny * g.o.nz * g.o.nt;
    g.u.assign(n * 4 * 9, Complex{});
    for (size_t s = 0; s < n; s++)
        for (int m = 0; m < 4; m++)
            for (int c = 0; c < 3; c++)
                g.at(s, m, c, c) = 1.;
}
void load_gauge(Gauge &g)
{
    size_t n = (size_t)g.o.nx * g.o.ny * g.o.nz * g.o.nt;
    g.u.resize(n * 4 * 9);
    if (g.o.gauge.empty())
    {
        unit_gauge(g);
        return;
    }
    read_binary(g.o.gauge, g.u);
    g.loaded = true;
}
