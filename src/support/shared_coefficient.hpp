#pragma once
#include <cstddef>
#include <memory>
#include <mpi.h>
#include <vector>

namespace lqcd_native {
class SharedCoefficientMemory {
    MPI_Comm local_comm = MPI_COMM_NULL;
    std::vector<MPI_Win> windows;

  public:
    explicit SharedCoefficientMemory(MPI_Comm parent);
    ~SharedCoefficientMemory();
    SharedCoefficientMemory(const SharedCoefficientMemory &) = delete;
    SharedCoefficientMemory &operator=(const SharedCoefficientMemory &) = delete;
    void *allocate(std::size_t bytes);
    void synchronize();
};

std::shared_ptr<SharedCoefficientMemory> make_shared_coefficient_memory(MPI_Comm parent);
}
