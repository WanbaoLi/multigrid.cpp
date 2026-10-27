# 灵晟单节点8/16 NUMA测试

目标硬件由用户提供：单节点2×304核，共16个CPU NUMA，每域38核、4GB HBM和32GB
DDR。具体指令集、HBM的Linux内存节点编号、编译器、MPI和调度分区必须在分配到的
真实计算节点重新检查；不能用登录节点的硬件探测代替。

## 实测结果（2026-10-26）

Donau作业1963160在真实计算节点`cn05131`原生编译并完成8/16 NUMA测试。站点队列
为`q_hpcapp`、账户`common`。节点有608物理核；每个NUMA的最后一核保留给系统，
作业cpuset实际允许592核，因此正式比较使用8×37=296核与16×37=592核。
CPU+DDR为Linux NUMA0–15，HBM为纯内存节点16–31；本次作业的`Mems_allowed_list`
仅为0–15，**本次结果使用DDR，没有使用HBM**。HWCAP实测SVE/SVE2/SME可见，
prctl报告SVE/SME向量长度64字节；未测试SME算术内核。

最终使用GCC10.3.1、`-O3 -march=native -mtune=native -fopenmp`、HMPI/OpenMPI
4.1.6rc4、NumPy2.0.2/mpi4py4.1.1。两组使用同一库SHA256
`9fc1af9eac470afdb278b8504df0485c015973c3b23c14da4160d6f18a09a658`。
GCC的native宏包含SVE2，本次未新增手写SVE/SME内核；ARM手写内核仍为NEON Clover，
Wilson为portable路径，是否向量化由编译器决定。这是原生构建成绩，不能表述为已完成
专门的512-bit SVE优化。

| 阶段（秒） | 前8 NUMA，296核 | 全16 NUMA，592核 |
|---|---:|---:|
| MG setup，单独记录 | 200.083 | 190.693 |
| 第一轮完整12列API | 45.859 | 29.181 |
| **第二轮完整12列API** | **45.386** | **28.576** |
| 第三轮完整12列API | 45.439 | 28.516 |
| 后两轮API中位数 | 45.412 | 28.546 |
| **第二轮纯求解** | **44.915** | **27.815** |

第二轮API加速比1.588263、并行效率79.413%；纯求解加速比1.614773、效率80.739%。
setup、LIME读取、stout、clover构造和文件写出均不计入第二轮求解。两组均为每列
24–25次迭代，refinement为0，每列每轮零初值，保留EO SAP/粗层EO及原真残差门。
这只是当前实现的同机强扩展基线，未达到5秒性能目标，也不是该节点的最优成绩。

GCC构建的13项相关CTest全部通过。完整传播子的12列逐一经独立scalar C++算子
复核：8 NUMA最大相对残差`4.818817327953574e-9`，16 NUMA为
`4.8188226395506315e-9`。正式二进制/输入/输出SHA256、线程亲和性、资源和逐列
数值门在JSON中保存。本地证据根目录为`.cache/lingsheng-scaling-20261026/`，
主要文件为`scaling.json`、`numa8-result.json`、`numa16-result.json`及
`verification-gcc/numa{8,16}/verification.json`。

远端工作目录：`/home/share/nsls_lwb/.cache/multigrid-lingsheng-20261026/`。
完整传播子分别为`results-gcc/numa8/propagator.npy`和
`results-gcc/numa16/propagator.npy`。共享工作目录没有复制约4GiB的传播子到本机。

调度器最终将作业记为`FAILED/124`：交互编排用的临时controller在所有任务完成后
触及自设3400秒等待期限。**GCC编译/13项测试、8/16 NUMA性能任务、独立复核任务
均返回0**，性能与复核报告的`complete`均为true。这个控制脚本退出码不能当作求解
失败。下述正式Donau脚本直接完成构建、测试、测量后退出，不使用该临时等待循环。

## 比较口径

| 配置 | NUMA选择 | MPI进程 | OpenMP/进程 | 总物理核 |
|---|---|---:|---:|---:|
| 半节点 | 允许cpuset中按编号排序的前8个CPU NUMA | 8 | 37 | 296 |
| 完整节点 | 全部16个CPU NUMA | 16 | 37 | 592 |

两组在同一次单节点独占分配中串行运行，使用同一库文件、原始24³×64 LIME、
mass=-.277、csw=1.160920226、一步四方向stout/rho=.125、原点单位源和时间反周期。
保持相同MG块6×6×6×4、双RHS batch、奇偶预处理和残差门1e-8。每组完成3轮12列
传播子求解，每列每轮从零初值开始。报告setup、第一轮、第二轮、后两轮中位数；
强扩展加速比取T8/T16，效率取T8/(2*T16)。MPI最大wall与内部batch计时分别统计，
共享batch计时只计一次。

16 rank的local t=4，8 rank的local t=8，几何均合法。前者只有一个时间aggregate，
通信/全局归约占比可能上升。当前hierarchy仍有全局副本，单rank仅basis就约8.2GB，
因此不能将整个进程强制`membind`到4GB HBM。先记录默认内存策略和实际页放置，再
考虑只把热点工作区放入HBM；HBM优化需单独验证，不能混入8/16核数对比。

## 工具

- `tools/benchmark_numa_scaling.py`：发现可用物理核、按NUMA顺序选择、检查等宽rank，
  调用生产LIME→stout→传播子路径。每组保留`.npy`、gauge分片、逐列残差与日志。
  `scaling.json`记录输入/库SHA256、亲和性、资源分配、内存策略、计时和扩展效率；
  任何一列不收敛或真残差超限会终止，报告保持`complete=false`。
- `tools/slurm_lingsheng_scaling.sh`：申请单节点608核独占的提交模板，原生构建和
  小型C++/启动器测试后执行8/16 NUMA比较；保留给实际使用Slurm的站点。
- `tools/donau_lingsheng_scaling.sh`：本次站点的正式模板，使用已验证的HPCKit/HMPI
  和GCC路径。NUMA线程数从允许cpuset发现，不使用保留的系统核。

本次站点使用Donau，已验证的提交参数为：

```bash
export LQCD_SOURCE_DIR="$PWD"
export LQCD_GAUGE="$HOME/.cache/multigrid-arm-20261025/configuration24.lime"
export LQCD_TOOLCHAIN_ENV=/home/share/test_mpi/my_software/hpckit/HPCKit/latest/setvars.sh
dsub -q q_hpcapp -A common -nn 1 -N 1 -x job \
  -R 'cpu=592,mem=480000MB' -T 3600 --cwd "$PWD" \
  -o "$HOME/Job_Output/lqcd-scaling.log" /bin/bash tools/donau_lingsheng_scaling.sh
```

SDK路径/访问权限应在下次运行时复核。单Donau replica向HMPI只提供1个slot，模板
对这个单节点启动器设置`OMPI_MCA_ras=^donau`、`OMPI_MCA_plm=isolated`，并使用明确
localhost slots和亲和性。该配置不能直接作为多节点MPI启动方式。

毕昇17另行完成过原生构建和数值测试，但setup随机数生成出现软件long-double
热点：相同10万次标准正态抽样，校验和一致，毕昇约.219s、GCC约.0049s。因此最终
两组统一使用GCC；毕昇未完成setup的尝试保留在`results/`，不纳入性能比较。

恢复连接并确认Slurm分区/账户后，从远端`multigrid.cpp/`目录提交，例如：

```bash
export LQCD_SOURCE_DIR="$PWD"
export LQCD_GAUGE="$HOME/.cache/multigrid-arm-20261025/configuration24.lime"
export LQCD_MPI_LIBRARY_PATH=/usr/local/lib
export LQCD_MPIRUN=/usr/local/bin/mpiexec
# 先按实际计算节点加载compiler/MPI模块，并确认mpi4py与C++链接同一MPI。
# --partition和--account使用站点查询得到的值，不猜测队列名称。
sbatch --partition="$PARTITION" --account="$ACCOUNT" tools/slurm_lingsheng_scaling.sh
```

模板使用隔离venv的Python/CMake，支持`LQCD_PYTHON`、`LQCD_CMAKE`、`LQCD_CTEST`、
`LQCD_MPIRUN`、`CC`和`CXX`覆盖。默认使用计算节点的`-march=native`；编译器不能
识别该CPU时会明确失败，再根据实测HWCAP和站点编译器选择经过验证的ISA参数。
模板不会自动强制HBM绑定，也不会沿用登录节点的二进制。

## 已完成的本地验证

`bash -n`、Python编译和启动计划检查通过。新驱动在本机8⁴非平凡LIME上，以
1 MPI×2线程、2 MPI×2线程各完成两轮完整12列，残差均小于1e-8，生成扩展统计。
这是测试工具的端到端检查，不是灵晟的性能结果。
证据位于`.cache/lingsheng-scaling-20261026/local-workflow-check2/`。
