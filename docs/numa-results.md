# NUMA、SIMD 与奇偶预处理重构验收（2026-10-21批次）

默认生产路径已启用 **细层 SAP 块内 EO-Schur MR + 粗层 EO-Schur GCR**。
程序不链接或调用 DDalphaAMG、Grid、openQCD 或 QUDA 求解器；这些库只用于参考和独立对照。
外层仍解完整 Wilson–Clover 方程，外部 PyQUDA EO-x / lex-tzyx、complex128、DR 基不变。

## 最终实测

同一真实 LIME 派生的 24³×64 规范场，一次 stout(rho=.125)，mass=-.277、csw=1、时间反周期。
每次零初值，共用各自独立生成的 hierarchy。表中为**完整主机 API**，包括 CPU 布局转换或 GPU 上传/下载、同步和完整双精度残差检查；排除 setup 和文件 I/O。
MPI 取各 rank 最大时间。节点非独占，没有并行运行本项目的 CPU/GPU 性能任务来取得下表。

| 实现 | 资源 | 第二次 API | 后续4次中位数 | 完整残差 |
|---|---|---:|---:|---:|
| 自研 multigrid.cpp | 自动2 NUMA × 1 MPI，每rank44线程，共88核 | **2.302160 s** | **2.345241 s** | 3.749e-09 |
| PyQUDA | 8 H20，8 MPI | **0.232309 s** | **0.232213 s** | 7.829e-09 |

第二次 CPU/GPU 比值 **9.910**，CPU 同时满足 <5秒。
稳态中位数比值为 **10.100**，略高于10；这是接近门槛的结果，
不能声称每次运行都低于10倍。CPU后续样本范围
2.270321–2.431209秒。
第一轮 CPU API 为 2.362172秒；原生 setup 为 71.678019秒。
GPU本轮使用已暖的 kernel tuning cache，setup为 1.676526秒；setup不参与上述门槛。

完整12列传播子顺序实测 **28.041402秒**，使用2×44线程；这不是把单列时间乘12。
12列全部由独立旧 C++ 算子验算，最大相对残差 **3.748515037599e-09**。
随机算子与 QUDA probe 的相对差为 3.890e-16，点源解与QUDA参考解的相对差为
1.489e-07。最终点源场与实时 QUDA 算子验算过的场逐位相同；
该 QUDA 算子给出的 CPU 解残差为 3.749e-09。
解差和方程残差是不同指标，最终验收始终要求完整方程残差≤1e-8。

## 实际改动

- `tools/run_numa.py` 按允许的物理核集合发现 NUMA，去除 SMT 重复核，每域启动一个 MPI。
  核数不写死；线程数可独立配置，Ready 后可用 `Solver.set_threads()` 集体调整，无需重建 hierarchy。
- 细层只发送物理时间面，当前 bt=4 时每次 matvec 的 halo 发送字节为原来的1/4。
  细、粗两层均使用非阻塞邻居交换；MPI主线程推进通信，OpenMP工作线程计算内部块，完成后计算边界。
  边界循环使用紧凑索引，避免静态调度只让少量线程承担边界工作。
- 粗层 Krylov 向量按 rank 本地存储，删除每次粗迭代的全向量 Allgather，使用邻居 halo 和全局标量归约。
- SAP 每个颜色步骤只计算需要的算子 image。块内构造 clover 逆并做 Schur MR4，随后重建 odd；
  粗层执行带 onsite 逆预条件的 Schur GCR，停止尺度为原完整粗 RHS 范数的0.1。
- 预计算邻居地址偏移，热循环无整数除法；局部32位、全场指针宽度 gather。
  半旋量 scratch 每线程复用；内部系数、索引和工作区64字节对齐，未对不满足条件的单独行强加对齐假设。
- 内层修正目标为 clamp(0.5×tol/current_full_residual, 1e-3, 0.1)，最终仍重新计算双精度完整残差。
  当前点源累计细层迭代 **17次**；无初值复用和源修改。
- 自适应 setup 复用上一轮 test vectors，删除随后会被覆盖的随机初始化，不改变初始随机流。

## 对照与选择

| 对照 | 第二次完整 API | 结论 |
|---|---:|---|
| 原阶段1二进制，同一2×44绑定 | 8.234663s | 本轮旧版对照；不能直接拿不同负载下的10月14日数字作加速比 |
| 重构但未启用 EO，2×44 | 4.354076s | 中间版本 |
| 同一中间版本，2×32重叠 | 3.008678s | 有界线程扫描 |
| 对应2×32阻塞 | 3.033114s | 本机重叠净收益很小，不夸大 |
| 原论文 vector update，旧full-MR、2×22 | 3.829288s | 对照inverse约3.713s，未证明更快，保留inverse默认 |
| 512位偏好，旧full-MR、2×32 | 3.134737s | 未优于当时256位，未切换默认构建 |

这些是本轮有限实验，不是全参数全局最优证明。细粒度 profiling 只用于诊断，正式性能数据关闭它。
早期测试超时来自 OpenMPI5/PRTE 将多线程 rank 绑在单核；CTest现显式使用 `--bind-to none`。
最终 **13项 CTest 全通过**，包括 fine/coarse EO四组合、奇数by及SIMD尾部、MPI不等线程数、
动态线程调整、外部布局、源保持、零源、错误路径和对齐 allocator。

## 复现

在 `lqcd` 根目录、conda pyquda 环境中：

```bash
MPI_PREFIX="$CONDA_PREFIX" LQCD_TEST_PYTHON="$CONDA_PREFIX/bin/python" \
bash multigrid.cpp/tools/build_runtime.sh
ctest --test-dir multigrid.cpp/build/runtime -j 2 --output-on-failure
export LQCD_CPU_LIBRARY="$PWD/multigrid.cpp/build/runtime/liblqcd_cpu.so"
LQCD_HALO_PROFILE=0 python multigrid.cpp/tools/run_numa.py -- \
  python -u multigrid.cpp/benchmarks/runtime/benchmark_runtime.py --repeats 5 --twelve-rhs \
  --output .cache/native-mg/reproduce-numa
python multigrid.cpp/benchmarks/runtime/verify_runtime_columns.py .cache/native-mg/reproduce-numa
```

命令没有写死 MPI ranks 或线程数。GPU对照使用 `benchmarks/runtime/benchmark_pyquda_runtime.py`，
`mpirun -n 8 --bind-to core` 配合 `--grid 1 1 1 8 --repeats 5`；可通过
`--cpu-solution-dir .cache/native-mg/reproduce-numa` 用实时QUDA算子验证CPU解。
执行性能任务时不要同时运行本项目的CPU验算或其他性能任务。

## 边界与证据

只验收本机x86；ARM/灵晟、SW后端尚未实现。NUMA启动器目前单机，runtime只支持t-slab。
setup/gauge/basis/stencil及double参考场仍有全局副本，不能宣称多节点内存或强扩展已完成。
薄子域可能没有可重叠的内部aggregate。当前限定两层、csw=1、时间反周期、偶数bx、单活context。

- 最终CPU：`../../.cache/numa-mg-20261021/final_aligned/result.json`
- 12列独立验算：`../../.cache/numa-mg-20261021/final_aligned/independent_columns.json`
- GPU及实时CPU解验算：`../../.cache/numa-mg-20261021/quda8_final/result.json`
- 最终测试：`../../.cache/numa-mg-20261021/ctest-aligned.log`
- 机器可读数据、源码/二进制/输入SHA256：[numa-results.json](numa-results.json)
- 原论文及算法差异审查：[ddalphaamg-review.md](ddalphaamg-review.md)
- 构建/API/资源说明：[native-runtime-usage.md](native-runtime-usage.md)



## 目录重构后的版本

最新拆分版本、当前源码哈希及独立 12 列回归见 [项目整理与回归](refactor-results.md)。本报告上方的 CPU/GPU 比较和同名 JSON 保留 10 月 21 日实测及当时的源码路径，不代表 10 月 22 日重新进行了 GPU 比较。
