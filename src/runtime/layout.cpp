#include "backend.hpp"
namespace lqcd {
static size_t parity_index(size_t site, const Geometry &g) {
    size_t a = site;
    int p = 0;
    for (int d = 0; d < 4; d++) {
        p += (int)(a % g.local[d]) + g.coords[d] * g.local[d];
        a /= g.local[d];
    }
    return (size_t)(p & 1) * (g.volume / 2) + site / 2;
}
static Complex get(const double *p, size_t i) {
    return {p[2 * i], p[2 * i + 1]};
}
static void put(double *p, size_t i, Complex z) {
    p[2 * i] = z.real();
    p[2 * i + 1] = z.imag();
}
void unpack_gauge(const lqcd_field_view &in, const Geometry &g, Vector &out) {
    out.resize(g.volume * 36);
    auto p = static_cast<const double *>(in.data);
#pragma omp parallel for schedule(static)
    for (size_t s = 0; s < g.volume; s++)
        for (int mu = 0; mu < 4; mu++)
            for (int c = 0; c < 9; c++) {
                size_t idx = in.layout == LQCD_LEX_TZYX
                                 ? (s * 4 + mu) * 9 + c
                                 : ((size_t)mu * g.volume + parity_index(s, g)) * 9 + c;
                out[(s * 4 + mu) * 9 + c] = get(p, idx);
            }
}
void unpack_spinor(const lqcd_field_view &in, const Geometry &g, Vector &out) {
    out.resize(g.volume * 12);
    auto p = static_cast<const double *>(in.data);
#pragma omp parallel for schedule(static)
    for (size_t s = 0; s < g.volume; s++) {
        size_t idx = in.layout == LQCD_LEX_TZYX ? s : parity_index(s, g);
        for (int c = 0; c < 12; c++)
            out[s * 12 + c] = get(p, idx * 12 + c);
    }
}
void pack_spinor(const Vector &in, const Geometry &g, lqcd_field_view &out) {
    auto p = static_cast<double *>(out.data);
#pragma omp parallel for schedule(static)
    for (size_t s = 0; s < g.volume; s++) {
        size_t idx = out.layout == LQCD_LEX_TZYX ? s : parity_index(s, g);
        for (int c = 0; c < 12; c++)
            put(p, idx * 12 + c, in[s * 12 + c]);
    }
}
} // namespace lqcd
