# AMD EPYC 9755 默认编译和测试

这套入口用于 AMD EPYC 9755（node5005）上的项目自有 x86 Wilson-Clover CPU 后端。默认配置是：

- 24×24×24×64 格子；
- 聚合块 `6 6 6 4`；
- 每个 CPU NUMA 域一个 MPI 进程；
- 每个 MPI 进程 32 个 OpenMP 线程；
- EPYC 9755 的典型单节点配置是 8 个 NUMA 域，因此默认是 8 MPI×32 线程；
- `mass=-0.277`、`csw=1.160920226`、质量归一化；
- 原点单位点源，完整12列，目标真相对残差 `1e-8`；
- 默认做一次 stout（`rho=0.125`，忽略时间方向），然后建层并重复求解；
- 不使用 DDalphaAMG、QUDA 或 GPU。

## 准备 24×64 组态

`test.sh` 直接读取一个原始 `.lime` 文件。建议放在 AMD 节点个人目录下：

```bash
mkdir -p "$HOME/lqcd-inputs"
```

默认文件名是：

```text
beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
```

默认完整路径为：

```text
$HOME/lqcd-inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
```

也可以把文件放在用户指定位置，再通过 `GAUGE` 覆盖。此前常用的共享路径是：

```text
/public2/home/lwb_720/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
```

但不同 AMD 节点的共享目录挂载可能不同；运行前必须用 `test -f` 确认文件确实可读。当前脚本要求原始 LIME 文件，不能把 post-stout fixture 目录直接作为 `--gauge` 参数。

## 编译

在项目根目录执行：

```bash
bash tools/x86/build.sh
```

脚本默认使用 `build/amd9755`，Release、`MULTIGRID_NATIVE=ON`、项目 x86 后端、MPI 和 OpenMP。`MULTIGRID_NATIVE=ON` 会启用编译器的本机优化（包括 `-march=native -mtune=native`）；没有启用 fast-math。

如果节点上的 Python/MPI 不在默认 PATH 中，可以这样指定：

```bash
PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda \
BUILD_JOBS=16 bash tools/x86/build.sh
```

## 测试和一次真实求解

最简单的完整测试：

```bash
bash tools/x86/test.sh
```

它依次运行 CTest，然后用 `tools/run_numa.py` 启动真实 LIME 流程。`solve_propagator.py` 在一次进程中完成：读入、一次 stout、Clover 生成、一次 `setup()`，然后执行 `REPEATS` 轮完整12列求解。每轮列求解都从零初值开始，层次在轮次之间复用。

指定组态和输出目录：

```bash
GAUGE=/public2/home/lwb_720/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime \
OUTPUT=$HOME/lqcd-results/amd9755-c24 \
bash tools/x86/test.sh
```

脚本输出目录必须不存在，否则会拒绝覆盖。结果写入 `result.json`，其中可直接查看：

- `stout_seconds`：一次 stout 时间；
- `gauge_load_clover_seconds`：规范场加载和 Clover 生成；
- `setup_seconds`：多重网格建层；
- `first_seconds`、`second_seconds`、`steady_median_seconds`：完整12列求解时间；
- `max_true_residual`：所有列中的最大真相对残差。

## `test.sh` 参数

可以用位置参数，也可以用环境变量。位置参数是：

```bash
bash tools/x86/test.sh /path/to/configuration.lime /path/to/new-output
```

常用环境变量如下：

| 变量 | 默认值 | 作用 |
|---|---:|---|
| `GAUGE` | `$HOME/lqcd-inputs/<filename>.lime` | 原始 LIME 组态 |
| `OUTPUT` | `results/amd9755-c24` | 新结果目录 |
| `BUILD_DIR` | `build/amd9755` | 编译目录 |
| `RANKS_PER_NUMA` | `1` | 每个 NUMA 域的 MPI 进程数 |
| `THREADS` | `32` | 每个 MPI 进程的 OpenMP 线程数 |
| `BLOCK_X/Y/Z/T` | `6/6/6/4` | 聚合块大小 |
| `MASS` | `-0.277` | Wilson 质量参数 |
| `CSW` | `1.160920226` | Clover 系数 |
| `STOUT_STEPS` | `1` | stout 次数；已经 stout 的输入设为 `0` |
| `STOUT_RHO` | `0.125` | stout 参数 |
| `STOUT_DIR_IGNORE` | `4` | 忽略时间方向 |
| `TOL` | `1e-8` | 完整真残差阈值 |
| `REPEATS` | `3` | 完整12列重复次数 |
| `RHS_BATCH` | `1` | `2` 可启用两列批量接口 |
| `RUN_CTEST` | `1` | 设为 `0` 跳过 CTest |

例如使用 16 MPI×16 线程的历史 AMD 配置：

```bash
RANKS_PER_NUMA=2 THREADS=16 RHS_BATCH=2 \
GAUGE=/path/to/configuration.lime \
OUTPUT=$HOME/lqcd-results/amd9755-16x16 \
bash tools/x86/test.sh
```

单次执行只改变 `RANKS_PER_NUMA` 和 `THREADS` 不会改变物理参数；但它会改变 MPI/线程拓扑，结果应单独记录，不能和默认配置直接混合比较。

## 结果解释

smear 只需要对每个组态做一次。当前 `test.sh` 的一次进程内，smear 在 setup 前执行一次；之后重复轮次复用同一份规范场和多重网格层次。若只想测已经 stout 的组态，把 `STOUT_STEPS=0`，并在报告中注明输入已经预处理。

默认测试包含 setup 和求解，但结果字段分开记录。比较求解性能时使用 `second_seconds` 或 `steady_median_seconds`，不要把 setup 或 stout 加到重复求解时间中；如果比较端到端首次运行，则使用 `total_wall_seconds` 并明确说明口径。
