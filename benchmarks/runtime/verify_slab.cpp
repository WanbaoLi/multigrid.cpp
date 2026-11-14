// Independent scalar full-spin Wilson/Clover oracle on padded local t slabs.
// No production native headers or half-spin/SIMD kernels are used here.
#include "core/dirac.h"
#include "core/clover.h"
#include "core/dslash.h"
#include <mpi.h>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

static void read(const std::string &path, Field &v) {
    std::ifstream f(path,std::ios::binary);
    if (!f.read(reinterpret_cast<char*>(v.data()),v.size()*sizeof(Complex)))
        throw std::runtime_error("short scalar oracle input: "+path);
}
int main(int argc,char **argv) {
    MPI_Init(&argc,&argv);
    int rank,ranks; MPI_Comm_rank(MPI_COMM_WORLD,&rank); MPI_Comm_size(MPI_COMM_WORLD,&ranks);
    try {
        if(argc!=9) throw std::runtime_error("usage: verify_slab ROOT L T MASS CSW TOL SOURCE_T COLUMNS");
        std::string root=argv[1];
        int L=std::stoi(argv[2]), T=std::stoi(argv[3]), lt=T/ranks;
        double mass=std::stod(argv[4]),csw=std::stod(argv[5]),tol=std::stod(argv[6]);
        int source_t=std::stoi(argv[7]), columns=std::stoi(argv[8]);
        size_t spatial=(size_t)L*L*L, sites=spatial*lt;
        if(T%ranks || lt<2) throw std::runtime_error("invalid scalar slab topology");
        Gauge g; g.o.nx=g.o.ny=g.o.nz=L; g.o.nt=lt+2; g.o.mass=mass;g.o.csw=csw;
        Field gauge(sites*36); read(root+"/gauge-"+std::to_string(rank)+".bin",gauge);
        g.u.resize(spatial*(lt+2)*36);
        std::copy(gauge.begin(),gauge.end(),g.u.begin()+spatial*36);
        int prev=(rank+ranks-1)%ranks,next=(rank+1)%ranks;
        MPI_Sendrecv(gauge.data(),spatial*72,MPI_DOUBLE,prev,70,
                     g.u.data()+spatial*(lt+1)*36,spatial*72,MPI_DOUBLE,next,70,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
        MPI_Sendrecv(gauge.data()+spatial*(lt-1)*36,spatial*72,MPI_DOUBLE,next,71,
                     g.u.data(),spatial*72,MPI_DOUBLE,prev,71,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
        // Place physical antiperiodicity on U_t at the global wrap. Scalar
        // periodic-coordinate wrapping at padded edges cannot affect owned rows.
        for(int t=0;t<lt+2;++t)
            if((rank*lt+t-1+T)%T==T-1)
                for(size_t s=0;s<spatial;++s)
                    for(int j=0;j<9;++j) g.u[((size_t)t*spatial+s)*36+27+j]*=-1.;
        build_clover(g,g.clover); gamma_init();
        Field owned(sites*12), padded(spatial*(lt+2)*12), image;
        for(int col=0;col<columns;++col) {
            read(root+"/solution-"+std::to_string(rank)+"-"+std::to_string(col)+".bin",owned);
            std::copy(owned.begin(),owned.end(),padded.begin()+spatial*12);
            MPI_Sendrecv(owned.data(),spatial*24,MPI_DOUBLE,prev,72,
                         padded.data()+spatial*(lt+1)*12,spatial*24,MPI_DOUBLE,next,72,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Sendrecv(owned.data()+spatial*(lt-1)*12,spatial*24,MPI_DOUBLE,next,73,
                         padded.data(),spatial*24,MPI_DOUBLE,prev,73,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            apply_dirac(g,padded,image,1,mass);
            double sum=0;
            for(size_t i=0;i<owned.size();++i) {
                Complex b{};
                const int source_col=col==0?0:col-1;
                if(rank*lt<=source_t && source_t<(rank+1)*lt &&
                   i==((size_t)(source_t-rank*lt)*spatial*12+source_col)) b=1./(4+mass);
                sum+=std::norm(image[spatial*12+i]-b);
            }
            MPI_Allreduce(MPI_IN_PLACE,&sum,1,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);
            double rel=std::sqrt(sum)*std::abs(4+mass);
            if(rank==0) std::cout<<"SCALAR_COLUMN "<<col<<" "<<std::scientific<<rel<<std::endl;
            if(!std::isfinite(rel)||rel>tol) throw std::runtime_error("independent scalar residual failed");
        }
        if(rank==0) std::cout<<"SCALAR_ALL_PASSED"<<std::endl;
    } catch(const std::exception &e) {
        std::cerr<<"rank="<<rank<<" scalar oracle: "<<e.what()<<std::endl;
        MPI_Abort(MPI_COMM_WORLD,1);
    }
    MPI_Finalize();
}
