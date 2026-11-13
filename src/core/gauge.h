#pragma once
#include "core/field.h"
#include "core/coefficient_field.h"
#include "core/options.h"

struct Gauge {
    Options o;
    CoefficientField u;
    CoefficientField clover;
    bool loaded = false;
    Complex &at(size_t s, int mu, int r, int c) { return u[((s * 4 + mu) * 3 + r) * 3 + c]; }
    const Complex &at(size_t s, int mu, int r, int c) const {
        return u[((s * 4 + mu) * 3 + r) * 3 + c];
    }
};

void unit_gauge(Gauge &g);
void load_gauge(Gauge &g);
