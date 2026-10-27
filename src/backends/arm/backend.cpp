#include "../../solver/native/backend.hpp"
namespace lqcd {
std::unique_ptr<Backend> make_arm(const lqcd_config &c, const Geometry &g, MPI_Comm comm) {
    return make_native(c, g, comm);
}
} // namespace lqcd
