# 从 LIME 求解完整点源传播子

`tools/solve_propagator.py` 提供纯 CPU 流程：读取单文件 SciDAC/ILDG LIME、验证原始字节的 SciDAC 校验、可选 stout、构建 Clover 和自研 MG、求解同一点的12个 spin/color 源，输出可由 PyQUDA 直接加载的全局传播子。运行不需要 PyTorch、PyQCU、QUDA 或 GPU。需要 NumPy、mpi4py 和本项目编译好的 CPU 库；HDF5 不是生产入口的依赖。

先按 [运行说明](native-runtime-usage.md) 编译最新库；文件读取与 smearing 都在 setup 前，重复求解复用同一 hierarchy，但所有12列每次都从零初值开始。

```bash
conda activate pyquda
export LQCD_CPU_LIBRARY=$PWD/multigrid.cpp/build/runtime/liblqcd_cpu.so
python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/tools/solve_propagator.py \
  --gauge beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime \
  --mass -0.277 --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --source 0 0 0 0 --repeats 3 --output results/point-0000
```

输出目录必须不存在，不会覆盖已有结果。单进程可直接运行 `python tools/solve_propagator.py ...`；多进程也可 `mpirun --bind-to none -n N python ... --threads T`。当前 solver 仍只支持等长 t-slab、两个 MG level、各向同性和费米子时间反周期。`run_numa.py` 的格点/块默认24³×64、6×6×6×4；其他尺寸需同时设置 launcher 的 `--lattice`/`--block` 和求解入口的 `--block`。

## NUMA 拓扑与求解参数

`run_numa.py --ranks-per-numa N` 在每个NUMA域内划分N组互不重叠的物理核，
`--threads` 指每个MPI进程的OpenMP线程数。默认N=1；不指定线程数时均分允许
使用的物理核。进程数仍必须满足t-slab的偶数局部时间长度和完整aggregate限制。
可先加 `--dry-run` 查看映射。以每NUMA有32个可用物理核的EPYC9755配置为例：

```bash
source multigrid.cpp/profiles/epyc9755_physical.env
python multigrid.cpp/tools/run_numa.py --ranks-per-numa 2 --threads 16 -- \
  python -u multigrid.cpp/tools/solve_propagator.py \
  --gauge beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime --mass -0.277 \
  --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --solver-options multigrid.cpp/profiles/epyc9755_physical_solver.json \
  --source 0 0 0 0 --repeats 3 --output results/epyc-physical
```

`--solver-options` 只在hierarchy setup完成后应用求解参数，不改变mass、csw、
源幅度、边界或stout，也不改变构建好的hierarchy。该profile是已选定机器/物理
参数下的数值求解设置，不能替代其他机器和配置上的正确性检查与测量。
性能范围与证据见 [x86性能记录](x86-performance.md)。

`LQCD_RHS_BATCH=1` 为默认兼容路径；设为 `2` 时 `solve_many`/完整传播子按两列
调用新增batch接口，每列仍从零初值开始，保留独立迭代数、收敛状态和完整残差。
奇数尾列使用scalar调用。所有rank必须设置相同值，且只接受1或2。
旧库可继续以默认1运行；选择2但库没有新符号时明确报不支持。

批量统计中的 `batch_size=2`、`timing_scope="shared_batch"` 表示两列共享整批
`solver_seconds`/`api_seconds`：**不能将这两个字段逐列相加，也不能除以2冒充
实测单列时间**。完整传播子性能应使用各轮实际 `wall_seconds`，继续保留所有列的
真实残差门。示例前加 `LQCD_RHS_BATCH=2` 可试验两列路径，不表示其必然更快。

## 参数和物理约定

- `--mass`、`--csw`：显式值覆盖 LIME 元数据。没有显式值时，只采用唯一、无歧义的文件值；元数据缺失或包含多个动作参数时要求显式指定。该真实文件包含多个 mass，因此示例显式给 valence mass。文件中的 Clover 系数为 **1.160920226**；省略 `--csw` 使用它，额外加 `--csw 1` 才匹配此前的性能 fixture。一般有限 csw（包括0）已通过公共 config 接入 Clover 构造。
- `--stout-steps` 默认为 **0**，不会自动改变规范场。`--stout-dir-ignore 4` 表示全部四方向；`3` 表示仅空间方向，时间链接与时间 staples 均不参与。rho 乘 staple 总和。每一步使用上一步的全部旧链接，MPI halo 每步更新。
- stout 用周期、未扭曲 gauge；反周期符号仅由 Dirac hopping 在全局时间边界应用一次。Clover 使用预处理后的同一 gauge。
- 默认 `--normalization mass --source-scale 1` 解 **M S=δ**，即单位点源传播子。`kappa` 解 **(2κM) S=δ**，κ=1/[2(m+4)]。输出幅度由方程决定，不在加载/保存时暗中重缩放。
- `--source X Y Z T` 是全局坐标。12列顺序为 `source_spin*3+source_color`，sink/source spin/color 轴按 PyQUDA 约定保存。
- F/D 输入保留存储值、转换为 complex128，不自动重新投影到 SU(3)。PyQUDA 某些 F 精度读取器默认会 reunitarize；这种额外预处理必须在物理对照中明确匹配。当前真实 D 精度文件没有此区别。

此前基准使用幅度 **1/(2κ)=m+4** 的 mass 点源，而此入口默认单位幅度；同一 gauge/mass/csw 下，新单位源解等于此前保存解乘 **2κ**。不能直接把二者差异判作算法错误。可显式设置 `--source-scale 3.723` 重现 mass=-0.277 时的旧源幅度。

## 输出及 PyQUDA 读取

`propagator.npy` 是标准 NumPy 文件，complex128、全局字典序 `[T,Z,Y,X,sink_spin,source_spin,sink_color,source_color]`。各 MPI rank 直接写互不重叠的 t slab，不聚合全场到 rank0；因此需要所有 rank 可见的同一共享文件系统。文件写出时间不计入求解时间。发生失败时不生成 `complete=true` 的结果清单。

```python
from pyquda_comm import initGrid
from pyquda.field import LatticePropagator

initGrid(grid_size=[1, 1, 1, 8])  # 与当前 MPI rank 数匹配
prop = LatticePropagator.load("results/point-0000/propagator.npy")
column = prop.getFermion(0, 0)
```

PyQUDA 的文件 loader 从形状恢复格点及 EO-x 存储；mass、边界和源幅度不存于 `.npy` 头，必须从 `result.json` 获取，并为后续物理计算设置相同边界约定。输出可以按另一合法 MPI 分区由 PyQUDA 重新加载。

`result.json` 保存输入 SHA256、LIME 元数据、实际 mass/csw 及其来源、stout 设置、源位置/幅度、归一化、时间边界、rank/线程绑定、每列迭代数和完整 double 残差。计时分开列出 LIME 读取、stout、gauge/Clover 加载、setup、第一次/第二次/后续中位数完整12列 API 和文件输出。完整传播子性能包括生成源和整理传播子轴序，不能与旧单列或纯 solver 时间混用。

可选 `--save-gauge` 保存每 rank 预处理后的 `gauge_rank00000.npy`，布局 `[localT,Z,Y,X,4,3,3]`，便于独立数值验算。

## Python 接口

已有 ready solver 可直接求解点源传播子：

```python
prop_eo, column_stats = solver.solve_propagator(
    point=(0, 0, 0, 0), tol=1e-8, source_scale=1., layout="pyquda")
# prop_eo: [p,t,z,y,x/2,s,S,c,C]
```

完整文件工作流为：

```python
from lqcd_cpu.propagator import solve_lime_propagator
report = solve_lime_propagator(
    "configuration.lime", "results/new-run", mass=-0.277,
    stout_steps=1, stout_rho=.125, repeats=3)
```

独立 LIME/stout API 分别位于 `lqcd_cpu.io` 和 `lqcd_cpu.smearing`；它们没有 GPU 或 QUDA 运行时依赖。NumPy stout 采用批量3×3 Hermitian `eigh`，优先数值清晰和跨 CPU 可用；尚不是原生 SIMD smearing 核。

真实24³×64的两种Clover系数、三轮完整传播子、全部列独立残差和PyQUDA实际加载验收见 [完整流程结果](propagator-results.md)。
