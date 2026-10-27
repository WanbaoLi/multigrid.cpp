# multigrid.cpp

面向 Wilson-Clover 的 CPU、MPI、SIMD 自研多重网格求解器，提供稳定的 C ABI 和 PyQUDA 兼容的 host field 接口。

项目按硬件后端组织：已实现 `x86` 和 AArch64 `arm`，`sw` 待移植。DDalphaAMG、Grid 和 openQCD 只放在参考基准或可选适配器中，不属于生产后端。

## 目录

```text
include/lqcd/                 公共 C/C++ 头文件
src/core/                     可移植 Wilson-Clover、GCR、参考 MG
src/solver/native/            共享 MG、SAP、Krylov 和 MPI 算法
src/backends/x86/             x86 AVX512 内核和硬件工厂
src/backends/arm/             AArch64 NEON 内核和硬件工厂
src/backends/portable/        通用 Wilson 数学与 OpenMP SIMD 循环
src/runtime/                  C ABI、布局转换、生命周期和后端注册
src/reference/                独立数值参考程序和验算 CLI
src/references/               可选外部求解器适配器
src/support/                  内部内存和通用工具
python/lqcd_cpu/              ctypes + mpi4py 的 PyQUDA host wrapper
benchmarks/                   性能程序；reference-libraries 是可选外部库比较
tests/runtime/               MPI、halo、奇偶和线程契约测试
tests/unit/                   不依赖 MPI 的 C++ 单元测试
tests/oracle/                 独立算子、P/R、RAP 和解验证脚本
tools/                       构建和 NUMA 启动工具
docs/                        算法、接口、结果和移植说明
```

## 构建

纯 C++ 参考程序：

```bash
cmake -S . -B build/reference -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON
cmake --build build/reference -j8
ctest --test-dir build/reference --output-on-failure
```

PyQUDA-compatible 生产运行库：

```bash
MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda \
LQCD_TEST_PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
bash tools/build_runtime.sh
ctest --test-dir build/runtime --output-on-failure
```

默认按构建主机选择项目自己的 x86 或 ARM MG。设置 `LQCD_DD_REFERENCE=ON` 才会加入 DDalphaAMG 参考适配器。

## 运行

Python wrapper 需要把 `python` 放入 `PYTHONPATH`，并由调用方先初始化 MPI：

```python
from lqcd_cpu import Solver

with Solver([24, 24, 24, 64], [1, 1, 1, 8],
            mass=-0.277, csw=1.0, block=[6, 6, 6, 4]) as solver:
    solver.load_pyquda_gauge(gauge)
    solver.setup()
    solution = solver.solve_pyquda(source, tol=1e-8)
```

`tools/run_numa.py` 默认每个 NUMA 域一个 MPI rank，自动发现物理核并在域内设置 OpenMP；`--ranks-per-numa N` 可划分多个互不重叠的进程核组：

```bash
LQCD_CPU_LIBRARY=$PWD/build/runtime/liblqcd_cpu.so \
python tools/run_numa.py -- \
  python benchmarks/runtime/benchmark_runtime.py --repeats 5 --twelve-rhs \
  --output .cache/native-mg/run
```

完整接口、字段布局、归一化、线程修改和复现命令见 [运行说明](docs/native-runtime-usage.md)。

直接输入 LIME 求解12列点源传播子（纯 CPU，可选 stout）：

```bash
python tools/run_numa.py -- python -u tools/solve_propagator.py \
  --gauge /path/configuration.lime --mass -0.277 \
  --stout-steps 1 --stout-rho 0.125 --repeats 3 --output results/point-0000
```

输出 `propagator.npy` 可由 PyQUDA `LatticePropagator.load()` 直接读取；方程、参数来源、逐列残差及分阶段计时写入 `result.json`。见 [完整传播子流程](docs/propagator.md)。

对于每NUMA32核的EPYC9755，可使用每域两个MPI、每进程16线程，并在setup后
应用指定求解参数（项目目录内运行）：

```bash
source profiles/epyc9755_physical.env
python tools/run_numa.py --ranks-per-numa 2 --threads 16 -- \
  python -u tools/solve_propagator.py --gauge /path/configuration.lime \
  --mass -0.277 --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --solver-options profiles/epyc9755_physical_solver.json \
  --repeats 3 --output results/epyc-physical
```

solver profile不修改物理参数或已构建的hierarchy。`LQCD_RHS_BATCH=1` 默认兼容
旧库；可选2启用两列batch接口，旧库缺少接口时明确拒绝。每列仍独立检查完整残差；
标记 `timing_scope="shared_batch"` 的时间是整批共享墙时，不能按列相加或伪均摊。
以完整传播子每轮wall比较性能，详见 [x86性能记录](docs/x86-performance.md)。

## 算法和验证

完整中文导读见 [项目结构、Multigrid算法与CPU后端](docs/project-algorithm-guide.md)，
包含P/R与粗细格映射、三层奇偶/红黑关系、通信重叠、x86和灵晟实现，以及逐节源码定位。

生产路径包含细层块内奇偶 Schur SAP、粗层奇偶 Schur GCR、RAP 粗化、异步 t-slab halo 和 flexible GCR。算法参考 DDalphaAMG 原论文的自适应聚合思想重写；x86/ARM 共用同一算法，硬件内核分别实现。Kunpeng-920 的移植与验证见 [ARM 后端](docs/arm-backend.md)，灵晟真实计算节点的测试见 [8/16 NUMA 强扩展](docs/lingsheng-scaling.md)。

- [鲲鹏HPC手册驱动的SVE/NUMA优化与skill](docs/kunpeng-hpc-optimization.md)
- [代码阅读顺序](docs/code-guide.md)
- [算法说明](docs/native-algorithm.md)
- [后端架构和移植边界](docs/backend-architecture.md)
- [重构后的性能与数值回归](docs/refactor-results.md)
- [EPYC 9755 / 8 NUMA / 256 核实测](docs/node5005-results.md) · [perf 与强扩展瓶颈](docs/node5005-perf.md) · [优化后 0.568 秒与 perf 复测](docs/node5005-optimization.md)
- [AVX512、packed 系数与 GCR 归约优化实测](docs/node5005-simd-optimization.md)
- [NUMA 与 8 卡 PyQUDA 对照](docs/numa-results.md)
- [原论文和 DDalphaAMG 代码审查](docs/ddalphaamg-review.md)
- [当前接口限制](docs/native-backend-status.md)
- [阶段路线图](docs/roadmap.md)
- [第三方许可证](THIRD_PARTY.md)

独立 oracle 流程位于 `tests/oracle/`，不会参与生产运行库。外部库比较位于 `benchmarks/reference-libraries/`，需要预先准备其源码和依赖。
