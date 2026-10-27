#include <Grid/Grid.h>
#include <fstream>
#include <iomanip>
#include <chrono>
using namespace Grid;
using MixedSolver=MixedPrecisionBiCGSTAB<LatticeFermionD,LatticeFermionF>;
struct MixedAdapter : OperatorFunction<LatticeFermionD> {
    MixedSolver &solver;
    explicit MixedAdapter(MixedSolver &s):solver(s){}
    void operator()(LinearOperatorBase<LatticeFermionD> &,const LatticeFermionD &b,LatticeFermionD &x) override {solver(b,x);}
};
static double now(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
template<class Field> void load_field(const std::string &path,Field &out) {
    using Site=typename Field::scalar_object;
    std::vector<Site> a(out.Grid()->lSites());
    auto *g=out.Grid();size_t offset=(size_t)g->_processor_coor[3]*a.size()*sizeof(Site);
    std::ifstream f(path,std::ios::binary);f.seekg(offset);f.read((char*)a.data(),a.size()*sizeof(Site));
    if(!f)throw std::runtime_error("read failed: "+path);
    vectorizeFromLexOrdArray(a,out);
}
int main(int argc,char **argv) {
    if(argc<3){std::cerr<<"usage: grid_bench INPUT_DIR OUTPUT_PREFIX [Grid options]"<<std::endl;return 2;}
    std::string input=argv[1],output=argv[2];
    Grid_init(&argc,&argv);
    bool mixed=GridCmdOptionExists(argv,argv+argc,"--mixed");
    auto grid=SpaceTimeGrid::makeFourDimGrid(GridDefaultLatt(),GridDefaultSimd(Nd,vComplexD::Nsimd()),GridDefaultMpi());
    auto rb=SpaceTimeGrid::makeFourDimRedBlackGrid(grid);
    LatticeGaugeFieldD U(grid);LatticeFermionD b(grid),x(grid),probe(grid),expected(grid),image(grid);
    load_field(input+"/gauge.bin",U);load_field(input+"/b.bin",b);
    load_field(input+"/probe.bin",probe);load_field(input+"/D_probe.bin",expected);
    const double kappa=1/(2*(4-.277));b=(1/(2*kappa))*b;expected=(1/(2*kappa))*expected;
    WilsonImplD::ImplParams params;for(int mu=0;mu<4;mu++)params.boundary_phases[mu]=(mu==3?-1.:1.);
    grid->Barrier();double setup=now();
    WilsonCloverFermionD D(U,*grid,*rb,-.277,1.,1.,WilsonAnisotropyCoefficients(),params);
    grid->Barrier();setup=now()-setup;
    D.M(probe,image);double error=sqrt(norm2(image-expected)/norm2(expected));
    if(grid->IsBoss())std::cout<<"OPERATOR_ERROR "<<std::setprecision(17)<<error<<std::endl;
    if(!std::isfinite(error)||error>1e-11)throw std::runtime_error("operator mismatch");
    double times[2],residuals[2];int iterations[2],refinements[2]={0,0},inner[2]={0,0},final_steps[2]={0,0};
    BiCGSTAB<LatticeFermionD> bicg(1e-9,2000);
    double extra_setup=now();
    auto gf=SpaceTimeGrid::makeFourDimGrid(GridDefaultLatt(),GridDefaultSimd(Nd,vComplexF::Nsimd()),GridDefaultMpi());
    auto rbf=SpaceTimeGrid::makeFourDimRedBlackGrid(gf);
    LatticeGaugeFieldF uf(gf);precisionChange(uf,U);
    WilsonImplF::ImplParams pf;for(int mu=0;mu<4;mu++)pf.boundary_phases[mu]=(mu==3?-1.:1.);
    WilsonCloverFermionF Df(uf,*gf,*rbf,-.277,1.,1.,WilsonAnisotropyCoefficients(),pf);
    NonHermitianSchurDiagMooeeOperator<WilsonCloverFermionD,LatticeFermionD> opD(D);
    NonHermitianSchurDiagMooeeOperator<WilsonCloverFermionF,LatticeFermionF> opF(Df);
    MixedSolver mixedSolver(1e-9,2000,50,rbf,opF,opD);mixedSolver.InnerTolerance=.01;
    MixedAdapter adapter(mixedSolver);
    NonHermitianSchurRedBlackDiagMooeeSolve<LatticeFermionD> solve(bicg);
    NonHermitianSchurRedBlackDiagMooeeSolve<LatticeFermionD> mixedSolve(adapter);
    setup+=now()-extra_setup;
    for(int run=0;run<2;run++) {
        x=Zero();grid->Barrier();double start=now();if(mixed)mixedSolve(D,b,x);else solve(D,b,x);grid->Barrier();times[run]=now()-start;
        iterations[run]=mixed?(mixedSolver.TotalInnerIterations+mixedSolver.TotalFinalStepIterations):bicg.IterationsToComplete;D.M(x,image);residuals[run]=sqrt(norm2(image-b)/norm2(b));
        if(mixed){refinements[run]=mixedSolver.TotalOuterIterations;inner[run]=mixedSolver.TotalInnerIterations;final_steps[run]=mixedSolver.TotalFinalStepIterations;}
        if(grid->IsBoss())std::cout<<"SOLVE "<<run+1<<" seconds "<<times[run]<<" iterations "<<iterations[run]<<" residual "<<residuals[run]<<std::endl;
        if(!std::isfinite(residuals[run])||residuals[run]>1e-8)throw std::runtime_error("true residual failure");
    }
    std::vector<LatticeFermionD::scalar_object> saved(grid->lSites());unvectorizeToLexOrdArray(saved,x);
    std::ofstream f(output+".rank"+std::to_string(grid->_processor_coor[3])+".bin",std::ios::binary);f.write((char*)saved.data(),saved.size()*sizeof(saved[0]));f.close();
    if(grid->IsBoss()) {
        std::ofstream j(output+".json");j<<std::setprecision(17)
          <<"{\"library\":\"Grid\",\"solver\":\"even-odd BiCGStab "<<(mixed?"mixed refinement":"double")<<"\",\"ranks\":"<<grid->_Nprocessors
          <<",\"threads_per_rank\":"<<omp_get_max_threads()<<",\"setup_seconds\":"<<setup<<",\"operator_error\":"<<error
          <<",\"solve_seconds\":["<<times[0]<<","<<times[1]<<"],\"iterations\":["<<iterations[0]<<","<<iterations[1]
          <<"],\"true_residual\":["<<residuals[0]<<","<<residuals[1]<<"],\"refinement_steps\":["<<refinements[0]<<","<<refinements[1]
          <<"],\"inner_iterations\":["<<inner[0]<<","<<inner[1]<<"],\"final_double_iterations\":["<<final_steps[0]<<","<<final_steps[1]<<"]}\n";
    }
    Grid_finalize();
}
