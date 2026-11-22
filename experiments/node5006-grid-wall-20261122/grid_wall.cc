#include <Grid/Grid.h>
#include <Test_multigrid_common.h>

#include <array>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

using namespace Grid;

int main(int argc, char **argv)
{
  if (argc < 3) {
    std::cerr << "Usage: grid_wall GAUGE.lime SAMPLES.jsonl [Grid options]\n";
    return 2;
  }
  const std::string input = argv[1];
  const std::string output = argv[2];
  Grid_init(&argc, &argv);

  const int status = [&]() {
    constexpr int columns = Ns * Nc;
    constexpr RealD mass = -0.279;
    constexpr RealD csw = 1.160678675188;
    constexpr RealD fullTolerance = 1e-8;
    constexpr RealD normalTolerance = 1e-10;
    constexpr int basis = 40;
    using Clock = std::chrono::steady_clock;

    const Coordinate lattice(std::vector<int>{24, 24, 24, 64});
    GRID_ASSERT(GridDefaultLatt() == lattice);
    auto *gridD = SpaceTimeGrid::makeFourDimGrid(
        lattice, GridDefaultSimd(Nd, vComplexD::Nsimd()), GridDefaultMpi());
    auto *gridF = SpaceTimeGrid::makeFourDimGrid(
        lattice, GridDefaultSimd(Nd, vComplexF::Nsimd()), GridDefaultMpi());
    auto *rbD = SpaceTimeGrid::makeFourDimRedBlackGrid(gridD);
    auto *rbF = SpaceTimeGrid::makeFourDimRedBlackGrid(gridF);

    LatticeGaugeFieldD raw(gridD), gaugeD(gridD);
    FieldMetaData metadata;
    IldgReader reader;
    reader.open(input);
    reader.readConfiguration(raw, metadata);
    reader.close();
    Smear_Stout<PeriodicGimplD> stout(0.125);
    stout.smear(gaugeD, raw);

    LatticeGaugeFieldF gaugeF(gridF);
    precisionChange(gaugeF, gaugeD);
    WilsonImplD::ImplParams paramsD;
    WilsonImplF::ImplParams paramsF;
    for (int mu = 0; mu < Nd; ++mu) {
      paramsD.boundary_phases[mu] = mu == 3 ? -1.0 : 1.0;
      paramsF.boundary_phases[mu] = mu == 3 ? -1.0 : 1.0;
    }
    WilsonCloverFermionD diracD(gaugeD, *gridD, *rbD, mass, csw, csw,
                               WilsonAnisotropyCoefficients(), paramsD);
    WilsonCloverFermionF diracF(gaugeF, *gridF, *rbF, mass, csw, csw,
                               WilsonAnisotropyCoefficients(), paramsF);

    WilsonMGParams params;
    params.blockSizes = {{3, 6, 6, 2}};
    checkParameterValidity(params);
    LevelInfo levels(gridF, params);
    NLevelMGPreconditioner<vSpinColourVectorF, vTComplexF, basis, 2, WilsonCloverFermionF> mg(
        params, levels, diracF, diracF);
    mg.setup();
    MdagMLinearOperator<WilsonCloverFermionD, LatticeFermionD> normal(diracD);
    MixedPrecisionFlexibleGeneralisedMinimalResidual<LatticeFermionD, LatticeFermionF>
        solve(normalTolerance, 1000, gridF, mg, 32);

    LatticeInteger t(gridD);
    LatticeCoordinate(t, 3);
    LatticeFermionD constant(gridD), zeroSource(gridD), image(gridD);
    zeroSource = Zero();
    std::vector<LatticeFermionD> rhs(columns, gridD);
    std::vector<LatticeFermionD> normalRhs(columns, gridD);
    std::vector<LatticeFermionD> solution(columns, gridD);
    for (int column = 0; column < columns; ++column) {
      LatticeFermionD::scalar_object component;
      component = Zero();
      component()(column / Nc)(column % Nc) = ComplexD(1.0, 0.0);
      constant = component;
      rhs[column] = where(t == Integer(0), constant, zeroSource);
      GRID_ASSERT(norm2(rhs[column]) == 24 * 24 * 24);
      diracD.Mdag(rhs[column], normalRhs[column]);
    }

    std::ofstream samples;
    if (gridD->IsBoss()) {
      samples.open(output);
      if (!samples) throw std::runtime_error("cannot open samples: " + output);
      samples << std::setprecision(17);
    }
    bool passed = true;
    for (int count : {1, columns}) {
      for (int run = 1; run <= 3; ++run) {
        std::array<int, columns> iterations{};
        std::array<double, columns> residuals{};
        for (int column = 0; column < count; ++column) solution[column] = Zero();
        gridD->Barrier();
        const auto start = Clock::now();
        for (int column = 0; column < count; ++column) {
          solve(normal, normalRhs[column], solution[column]);
          iterations[column] = solve.IterationCount;
        }
        double seconds = std::chrono::duration<double>(Clock::now() - start).count();
        gridD->GlobalMax(seconds);
        for (int column = 0; column < count; ++column) {
          diracD.M(solution[column], image);
          image = rhs[column] - image;
          residuals[column] = std::sqrt(norm2(image) / norm2(rhs[column]));
          passed &= std::isfinite(residuals[column]) && residuals[column] <= fullTolerance;
        }
        if (gridD->IsBoss()) {
          samples << "{\"rhs\":" << count << ",\"run\":" << run
                  << ",\"warmup\":" << (run == 1 ? "true" : "false")
                  << ",\"solver_seconds\":" << seconds
                  << ",\"ranks\":" << gridD->_Nprocessors
                  << ",\"threads_per_rank\":" << GridThread::GetThreads()
                  << ",\"iterations\":[";
          for (int column = 0; column < count; ++column) {
            if (column) samples << ',';
            samples << iterations[column];
          }
          samples << "],\"full_relative_residuals\":[";
          for (int column = 0; column < count; ++column) {
            if (column) samples << ',';
            if (std::isfinite(residuals[column])) samples << residuals[column];
            else samples << "null";
          }
          samples << "]}" << std::endl;
          std::cout << "GRID_WALL " << count << " RHS run " << run << ": "
                    << std::fixed << std::setprecision(6) << seconds << " s" << std::endl;
        }
      }
    }
    return passed ? 0 : 1;
  }();
  Grid_finalize();
  return status;
}
