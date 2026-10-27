#include "../../solver/native/backend.hpp"
namespace lqcd {
std::unique_ptr<Backend> make_x86(const lqcd_config &c, const Geometry &g, MPI_Comm comm) {
    return make_native(c, g, comm);
}
} // namespace lqcd
