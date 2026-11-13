#include "shared_coefficient.hpp"
#include <stdexcept>

namespace lqcd_native {
SharedCoefficientMemory::SharedCoefficientMemory(MPI_Comm parent) {
    if (MPI_Comm_split_type(parent, MPI_COMM_TYPE_SHARED, 0, MPI_INFO_NULL, &local_comm) !=
        MPI_SUCCESS)
        throw std::runtime_error("MPI shared-memory communicator creation failed");
    int local_size = 0, parent_size = 0;
    MPI_Comm_size(local_comm, &local_size);
    MPI_Comm_size(parent, &parent_size);
    if (local_size != parent_size) {
        MPI_Comm_free(&local_comm);
        throw std::runtime_error("shared coefficients currently require one physical host");
    }
}

SharedCoefficientMemory::~SharedCoefficientMemory() {
    for (auto &window : windows) {
        MPI_Win_unlock_all(window);
        MPI_Win_free(&window);
    }
    if (local_comm != MPI_COMM_NULL)
        MPI_Comm_free(&local_comm);
}

void *SharedCoefficientMemory::allocate(std::size_t bytes) {
    int local_rank = 0;
    MPI_Comm_rank(local_comm, &local_rank);
    void *local_base = nullptr;
    MPI_Win window = MPI_WIN_NULL;
    const MPI_Aint owned = local_rank == 0 ? static_cast<MPI_Aint>(bytes) : 0;
    if (MPI_Win_allocate_shared(owned, 1, MPI_INFO_NULL, local_comm, &local_base, &window) !=
        MPI_SUCCESS)
        throw std::runtime_error("MPI shared coefficient allocation failed");
    MPI_Aint queried_size = 0;
    int queried_disp = 0;
    void *root_base = nullptr;
    if (MPI_Win_shared_query(window, 0, &queried_size, &queried_disp, &root_base) != MPI_SUCCESS ||
        queried_size < static_cast<MPI_Aint>(bytes) || !root_base) {
        MPI_Win_free(&window);
        throw std::runtime_error("MPI shared coefficient query failed");
    }
    windows.push_back(window);
    MPI_Win_lock_all(0, window);
    return root_base;
}

void SharedCoefficientMemory::synchronize() {
    for (auto window : windows)
        if (MPI_Win_sync(window) != MPI_SUCCESS)
            throw std::runtime_error("MPI shared coefficient synchronization failed");
    MPI_Barrier(local_comm);
    for (auto window : windows)
        MPI_Win_sync(window);
}

std::shared_ptr<SharedCoefficientMemory> make_shared_coefficient_memory(MPI_Comm parent) {
    return std::make_shared<SharedCoefficientMemory>(parent);
}
}
