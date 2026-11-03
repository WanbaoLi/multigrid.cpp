// Real installed KUPL availability/allocation/verification on each NUMA rank.
#include "../../src/support/hbw_buffer.hpp"
#include <kupl.h>
#include <mpi.h>
#include <omp.h>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char **argv) {
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    const std::size_t bytes = 64ull << 20;
    const int available = kupl_hbw_check_available();
    lqcd_native::hbm::HbwBuffer buffer(bytes, 64, lqcd_native::hbm::Policy::Require);
    int verified = -2;
    if (buffer) {
        auto *values = static_cast<unsigned char *>(buffer.data());
#pragma omp parallel for schedule(static)
        for (std::size_t i=0; i<bytes; ++i) values[i] = static_cast<unsigned char>(i);
        verified = buffer.verify_hbw();
    }
    const auto pages = buffer.sample_pages();
    std::string mems;
    std::ifstream status("/proc/self/status");
    for (std::string line; std::getline(status,line);)
        if (line.rfind("Mems_allowed_list:",0)==0) mems=line.substr(line.find(':')+1);
    // Serialize log lines; this is a capability probe, never a speed metric.
    int size;
    MPI_Comm_size(MPI_COMM_WORLD,&size);
    for (int owner=0;owner<size;++owner) {
        MPI_Barrier(MPI_COMM_WORLD);
        if (rank==owner) {
            std::cout << "HBW_PROBE {\"rank\":"<<rank<<",\"available\":"<<available
                <<",\"allocated\":"<<(buffer?"true":"false")<<",\"bytes\":"<<bytes
                <<",\"sdk_verify\":"<<verified<<",\"allowed_mems\":\""<<mems
                <<"\",\"query_rc\":"<<pages.query_rc<<",\"query_errno\":"<<pages.query_errno
                <<",\"nodes\":[";
            for (std::size_t i=0;i<pages.nodes.size();++i) {
                if (i) std::cout<<',';
                std::cout<<pages.nodes[i];
            }
            std::cout<<"],\"error\":\""<<buffer.error()<<"\"}"<<std::endl;
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
    MPI_Finalize();
}
