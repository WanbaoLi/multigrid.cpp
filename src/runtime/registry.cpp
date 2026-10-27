#include "backend.hpp"
namespace lqcd {
#ifdef LQCD_BACKEND_X86
std::unique_ptr<Backend> make_x86(const lqcd_config &, const Geometry &, MPI_Comm);
#endif
#ifdef LQCD_BACKEND_ARM
std::unique_ptr<Backend> make_arm(const lqcd_config &, const Geometry &, MPI_Comm);
#endif
std::unique_ptr<Backend> make_backend(const std::string &name, const lqcd_config &c,
                                      const Geometry &g, MPI_Comm comm) {
#ifdef LQCD_BACKEND_X86
    if (name == "x86")
        return make_x86(c, g, comm);
#endif
#ifdef LQCD_BACKEND_ARM
    if (name == "arm")
        return make_arm(c, g, comm);
#endif
#ifdef LQCD_DD_REFERENCE
    if (name == "reference-ddalphaamg")
        return make_ddalphaamg(c, g, comm);
#endif
    throw Error(LQCD_UNSUPPORTED, "backend not built: " + name);
}
} // namespace lqcd
