#pragma once
#include "environment.hpp"

// One RHS's persistent allocation only: all numerical state is reset at the
// start of solve_batch. No cross-RHS or cross-call initial guesses are kept.
struct BatchKrylovWorkspace {
    Field residual, image, delta;
    double bn = 0, relative = 1, float_bn = 0, target = 0;
    lqcd_native::detail::FloatField b, x, r, float_image;
    std::vector<lqcd_native::detail::FloatField> images, directions;
    size_t active = 0;
    int iterations = 0;
    bool converged = false, correction_done = false;
};
