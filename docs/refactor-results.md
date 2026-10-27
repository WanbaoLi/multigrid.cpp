# 项目整理与回归（2026-10-22）

本次将源码、测试、基准和构建产物分开，并拆开生产 MG 长文件。PyQUDA 字段布局、C ABI、细层/粗层 EO、零初值与最终完整残差要求均保留。

## 源码结构

- `src/core/`：可移植的场、Wilson-Clover 算子和独立参考 GCR/MG。
- `src/runtime/`：C ABI、MPI 集体校验、布局转换和硬件后端注册。
- `src/backends/x86/`：按 `hierarchy`、`fine_operator`、`sap`、`coarse`、`cycle`、`setup`、`solver`、`validation` 拆分。最长实现文件约 300 行；主 V-cycle 在 `cycle.cpp` 中可直接阅读。
- `src/support/`：内部对齐分配器。`src/references/`：显式选择的外部参考适配器。
- `tests/unit`、`tests/runtime`、`tests/oracle`：基础测试、MPI/API 测试和独立验证。
- `benchmarks/runtime`、`benchmarks/native`、`benchmarks/reference-libraries`：生产基准、组件实验和外部库比较。
- `tools/`：唯一的构建与 NUMA 启动入口。所有常规构建产物统一到 `build/`，不再混杂多个 `build-*` 目录。

删除了旧构建目录、字节码缓存、无效图片引用、重复的历史阶段文档/配置、旧调参入口、重复的示例入口，以及两个从未读取的全场 float 工作缓冲区。独立 oracle 和有用途的外部参考基准保留。

关键尺寸改为 `block_sites`、`coarse_dof`、`fine_sites`；局部所有权改为 `first_aggregate`、`end_aggregate`。`restrict_to_coarse`、`prolongate_add`、`apply_vcycle` 和 `solve_float_gcr` 直接说明步骤用途。C++ 与 Python 格式已统一，中文阅读指南见 [code-guide.md](code-guide.md)。

## 重构版本实测

同一真实 `24³×64` LIME 派生输入，mass=-0.277、csw=1、时间反周期，自动 2 MPI ×44 OpenMP 线程。每次零初值，复用自行生成的 hierarchy；以下求解时间包含完整 host API，排除 setup 和文件 I/O。

| 项目 | 结果 |
|---|---:|
| Setup | 73.348 s |
| 第二次单列完整 API | **1.884575 s** |
| 后续 4 次稳态中位数 | **1.905824 s** |
| 完整 12 列实际求解 | **24.528831 s** |
| 算子误差（对 QUDA probe） | 3.8903×10⁻¹⁶ |
| 单列解相对 QUDA 差异 | 1.4890×10⁻⁷ |
| 12 列独立完整残差最大值 | **3.75×10⁻⁹** |

单列为 17 次累计外迭代。第二次仍低于 5 秒；节点非独占，本次时间不证明仅靠重构获得了加速。GPU 未在本次重测，原 8 卡对照保留在 [NUMA 实测报告](numa-results.md)。

随后仅删除未使用工作缓冲和整理 CMake；最终源码树上的 MPI/API CTest **13/13** 通过。无 OpenMP 的参考程序 CTest **4/4** 通过；可选原生组件 benchmark 单独编译成功。12 列由新的参考可执行程序逐列重新应用完整算子验算。

## 复现与记录

从项目目录执行：

```bash
MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda \
LQCD_TEST_PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
bash tools/build_runtime.sh
ctest --test-dir build/runtime -j 2 --output-on-failure

LQCD_CPU_LIBRARY=$PWD/build/runtime/liblqcd_cpu.so \
python tools/run_numa.py -- \
  python -u benchmarks/runtime/benchmark_runtime.py --repeats 5 --twelve-rhs \
  --output ../.cache/project-refactor-20261022/reproduction
python benchmarks/runtime/verify_runtime_columns.py \
  ../.cache/project-refactor-20261022/reproduction --threads 8
```

使用与 C++ MPI 相同安装的 conda `pyquda` 环境运行 Python 和 mpirun。源码/二进制 SHA256、全部原始样本、12 列残差和日志路径在 [refactor-results.json](refactor-results.json)。10月21日的 [numa-results.json](numa-results.json) 保留当时的源路径和哈希，不能当作当前源码 manifest。
