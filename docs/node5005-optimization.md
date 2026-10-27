# node5005：按 perf 优化与复测（2026-10-22）

256 核单列第二次完整 host API 从 **1.942222 s 降到 0.568291 s**；后四次中位数从 **1.899313 s 降到 0.567611 s**，稳态加速 **3.346×**。相同机器、真实 24³×64 fixture、相同 MG 参数与 17 次累计迭代，保持完整 double 残差门。256 核现在比 128 核快约 **1.83×**。

## 实现改动

- `src/backends/x86/backend.cpp`：生产 apply/solve 直接使用 rank-local 词典序 double 场，移除源和最终验证输入的全场 gather；保留 mass/kappa 缩放。
- `double_operator.cpp`：double Wilson-Clover 只算本地 t slab，使用 double 6×6 clover、half-spin 投影、相邻时间面非阻塞 halo；MPI 主线程推进通信，worker 计算内部站点。反周期只在全局时间边界应用一次。
- `fine_operator.cpp`、`environment.cpp`、`solver.cpp`：可靠修正 decode 不再 Allgather；double norm/dot 对所有本地元素求和再全局归约；float 解只初始化 owned 区间。源保持只读，每次求解零初值。
- `fine_operator.cpp`、`wilson_kernel.hpp`：细层 halo 计算按物理 t 面拆分。在 8 rank、每 rank 两个 bt=4 aggregate 时，6/8 时间片可在通信期间计算；通信完成后再算首尾两面。
- `validation.cpp`：setup 保留原始全格点 scalar 算子，额外检查新 double 算子相对误差 <2e-13。独立 reference executable 不使用新生产核。公共 C ABI、PyQUDA EO-x 输入输出、两层默认 EO 均保持原契约。

## 同机强扩展

AMD EPYC 9755 双路 256 物理核，8 NUMA，每域 32 核；一个 NUMA 一个 MPI，每 rank 32 OpenMP。Release、GCC 14.4、`-march=native -mtune=native`（znver5），不使用 fast-math。每配置自行 setup、五次零初值求解，排除 setup/I/O，包含布局转换、可靠更新和 API 最终完整残差验证。稳态为后四次中位数。

| MPI×线程 | 核数 | 原第二次 / s | 新第二次 / s | 原稳态 / s | 新稳态 / s | 稳态收益 |
|---|---:|---:|---:|---:|---:|---:|
| 1×32 | 32 | 3.659507 | 3.553219 | 3.657776 | 3.557254 | 1.028× |
| 2×32 | 64 | 2.170239 | 1.786701 | 2.171781 | 1.786554 | 1.216× |
| 4×32 | 128 | 1.772387 | 1.036659 | 1.773196 | 1.038166 | 1.708× |
| 8×32 | 256 | 1.942222 | **0.568291** | 1.899313 | **0.567611** | **3.346×** |

同机 32→256 核加速 **6.267×**，效率 **78.34%**，此前为 1.926×、24.07%。这是一组有限顺序扫描。256 核五次样本为 0.591138、0.568291、0.566757、0.670401、0.566931 s，包含一个明显慢样本。另一次独立 context 在 perf 启动前的普通第二次为 0.569719 s；12 列回归 context 的普通第二次为 0.595887 s。所有样本均保留，不能宣称每次固定 0.568 s。

## 优化后 perf

沿用此前采集范围：setup、普通计时和导出之后，十次额外零初值求解；`cycles:u -F 49 --call-graph dwarf,4096` 采样两个 socket 的 rank 0/4，stat 覆盖全部 8 rank。attach 时每 rank 34 个线程（32 OpenMP 加环境线程）。新记录 20,928 samples、0 lost；两项 perf 通过 SIGINT 正常刷出数据。flat self-symbol 报告避免旧 perf/BFD 的 DWARF 调用树解码问题。

| 热点 | 原采样 cycles 占比 | 新占比 |
|---|---:|---:|
| OpenMP `do_wait` | 37.33% | 38.25% |
| 旧 scalar Clover + Dslash / 新 distributed double | 17.57% | 2.31% |
| 全场 float Wilson 核 | 7.82% | 14.49% |
| SAP `local_range` | 7.91% | 11.69% |
| 块内 float Wilson 核 | 5.54% | 8.40% |
| restriction / prolongation | 4.95% / 4.41% | 6.84% / 6.09% |

相同十列 profiling，全部 rank 的 instructions 从 15.668×10¹² 降到 7.317×10¹²（**减少 53.30%**），cycles 从 8.576×10¹² 降到 5.547×10¹²（减少 35.32%）。IPC 为 1.83→1.32；generic miss/reference 为 7.78%→10.71%。这些计数包含忙等，miss 比不等于 DRAM 带宽；占比也不是整次求解墙时比例。热点占比上升不能直接解释为该核变慢。

DWARF profiling 对这个不足一秒的 workload 有明显扰动：十次 profiling 样本约 0.569–0.980 s。因此性能收益只使用不带 profiler 的普通样本，不使用 profiling 墙时。OpenMP 等待仍是最大周期热点，后续应检查 SAP/细核工作粒度与 parallel region/屏障，不能因为这次加速就认为已经全局最优。

## MPI 与 overlap 的实测

单独 context、五次额外求解由 MPI_Pcontrol 包围；表中是每列每 rank 的次数和 8 rank 平均调用墙时。

| 操作 | 原次数 | 新次数 | 原时间 / s | 新时间 / s |
|---|---:|---:|---:|---:|
| Allgather | 9 | **4** | 0.500108 | **0.00002715** |
| Allreduce | 477 | 481 | 0.072520 | 0.033617 |
| Waitall | 292 | 296 | 0.080219 | 0.071632 |
| Barrier | 2 | 2 | 0.002229 | 0.000444 |

**原来五次完整 spinor Allgather 全部移除。** 每 rank 每列 Allgather 接收缓冲总量由 **849,346,816 B（810 MiB 全场加 256 B 元数据）降为 256 B**。四次 double 算子现在各进行一次双面 halo，表现为 Waitall 增加四次；四次输入一致性检查使 Allreduce 增加四次。源码保留完整最终验证，不是少算残差获得的收益。

这些是调用墙时，含到达不齐和等待；不可跨 rank 相加，也不可与 perf 周期、重叠计算计时相加。PMPI 包装器仅统计这四类操作，halo profile 使用的 MPI_Reduce 等不在表中。buffer_bytes 是接收缓冲规模，不是物理链路流量。

细层 profile 的每列 interior 字段中位数由空循环量级约 0.000020 s 变为 **0.113351 s**，boundary 从 0.097064 s 变为 **0.031357 s**：物理内部时间片已在 halo 等待阶段计算。fine/coarse 的消息数量和字节未改变。各 profile 字段是 rank 局部累计量的独立最大值，不能相加；double halo 不包含在这两个 float-level profile 中，但已计入 PMPI Waitall。

## 数值与完整传播子

- **13/13 CTest 通过**，包括 serial、MPI2/4、阻塞/异步 halo、非均匀线程数、两层 EO/legacy 组合、奇数非 x 块与 SIMD 尾部、线程动态调整和 source preservation。
- 真实 fixture 对照 PyQUDA：double 算子误差约 **3.99e-16**，单列解相对误差约 **1.49e-7**（门为 1e-6）。32/64/128/256 核均为 **17 次累计迭代**，API 额外 refinement_steps=0，独立旧标量完整残差约 **3.75e-9**。
- 独立的 8×32 context 跑完整 **12 列传播子为 8.106245 s**；12 列都为 17 次迭代，全部用冻结的旧独立 scalar executable 重新验证，最大残差 **3.748522e-9**。这是一轮完整传播子回归，含 0.9 s 的慢列；不冒充第二次/稳态完整传播子成绩。单列 <5 s 已满足，完整 12 列 <5 s 尚未达到。
- setup 约 74 s，不进入上述求解成绩。没有导入外部 basis、预存解或非零初值。

## 证据与限制

[机器可读记录](node5005-optimization.json) 包含全样本、哈希、MPI、perf、halo 和 12 列独立残差。原始输出在工作区 `.cache/node5005-optimized-20261022/`；旧 `.cache/node5005-perf-20261022/` 保持只读。

- `build-manifest.json`、`sources-before-build.json`、`optimized.so`：源码、fixture、编译库、冻结旧 reference 和编译环境；后续阶段拒绝源码或二进制变更。
- `run_comparison.py`：build→scaling→perf→pmpi→compare 顺序执行，拒绝覆盖；`run_propagator.py`：额外 12 列回归。复现需换新输出/build 路径。
- `rank1/2/4/8/`、`comparison.json`：普通性能与各配置独立验算；`propagator8/`：12 列及独立完整残差。
- `perf.data`、`perf-flat.csv/txt`、`perf-stat.txt`、`perf-metadata.json`、`perf8/`：原始采样与普通/profile 分离样本。
- `mpi-counters/rank*.json`、`diagnostic8.log`：MPI 和 float halo 原始诊断；`ctest.log`：测试结果。

AMD 独立 build 为 `build/node5005-optimized`，没有覆盖 Intel/旧 AMD 基线库。生产 double 场已本地化，但 gauge/clover/setup basis 仍复制，float 细场仍用全局编号工作区；目前仅 t-slab 分解，尚不能宣称多节点内存扩展性或 ARM/神威硬件性能。下一步热点是浮点 Wilson/SAP 和 OpenMP 同步，而不是已移除的全场 Allgather。
