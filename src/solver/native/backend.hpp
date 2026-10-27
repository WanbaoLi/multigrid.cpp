#pragma once
#include "../../runtime/backend.hpp"
namespace lqcd {
std::unique_ptr<Backend> make_native(const lqcd_config &, const Geometry &, MPI_Comm);
}
