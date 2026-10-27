# node5005：perf 与强扩展诊断（2026-10-22）

此文保存优化前基线。后续修复及重新测量见 [优化与 perf 复测](node5005-optimization.md)。

当前实现的强扩展确实存在瓶颈。同一 AMD EPYC 9755 节点、同一个 znver5 二进制上，128 核比 256 核快约 7%。增加核数时，浮点 MG 的一部分工作被分摊，但完整双精度场的可靠更新和最终算子验算仍被每个 rank 重复执行，并伴随大规模 Allgather。

## 同机强扩展

全部使用同一真实 24³×64 fixture、两层 MG、细层和粗层 EO、seed=1024、相同容差。每次零初值，复用自行生成的 hierarchy；表中为完整 host API，排除 setup、导出和独立验算。每配置 5 次，稳态中位数取后 4 次。所有样本均为 **17 次累计外迭代**，完整残差小于 1e-8，算子和解均对照 QUDA fixture。

| MPI × 线程 | 总核数 | NUMA 域 | 第二次 / s | 稳态中位数 / s | 相对 32 核加速 | 强扩展效率 |
|---|---:|---|---:|---:|---:|---:|
| 1×32 | 32 | 0 | 3.659507 | 3.657776 | 1.00× | 100% |
| 2×32 | 64 | 0、4 | 2.170239 | 2.171781 | 1.68× | 84.2% |
| **4×32** | **128** | **0、2、4、6** | **1.772387** | **1.773196** | **2.06×** | **51.6%** |
| 8×32 | 256 | 全部 8 域 | 1.942222 | 1.899313 | 1.93× | 24.1% |

效率以同机 32 核为基准：`(T32/Tn)/(n/32)`。这是一组有限顺序扫描，不是最优值证明。128 核解另经独立 C++ 完整算子验算通过。

固定 8 个 rank、同一个 hierarchy，仅修改线程资源：

| 每 rank 线程 | 总核数 | 第二次 / s | 稳态中位数 / s |
|---:|---:|---:|---:|
| 8 | 64 | 2.6988 | 2.6959 |
| 16 | 128 | 2.0266 | 2.0091 |
| 24 | 192 | 1.8717 | 1.8711 |
| 32 | 256 | 1.9422 | 1.8993 |

24→32 线程已饱和；1–2% 的差距接近这组运行的波动，不能据此宣称 24 线程显著优于 32。相同 128 核下，4×32 又快于 8×16，说明 MPI 分解和工作粒度确实影响结果。

## perf：线程在做什么

在 setup、普通计时和字段导出完成后，benchmark 发布 PID 并等待外部 `go` 文件。随后执行 10 次额外零初值求解，仅用于 profiling，不用于上面的性能表。

`perf record -e cycles:u -F 49 --call-graph dwarf,4096` 采集 rank 0 和 rank 4（两个 socket 各一个）；两个 rank 各有 34 个线程出现在记录中，覆盖动态增加的 OpenMP worker。共 32,233 个样本、0 lost samples。主要采用 flat self-symbol 统计：

| 符号 | 采样用户态 cycles 占比 |
|---|---:|
| libgomp `do_wait` | **37.33%** |
| 标量双精度 `add_dslash` | **10.76%** |
| 标量双精度 `apply_clover_only` | **6.81%** |
| SAP `local_range` | 7.91% |
| 全局浮点 Wilson 核 | 7.82% |
| 块内浮点 Wilson 核 | 5.54% |
| restriction / prolongation | 4.95% / 4.41% |
| 粗层矩阵乘核 | 0.72% |

`do_wait` 的辅助调用栈包括 OpenMP 团队结束等待及 `fine_apply` 内部屏障。占比是 **CPU-cycle 样本比例，不能当作整次求解墙时比例**。部分旧版 perf/BFD 的 DWARF 调用链解码报错，因此不使用不完整调用树作精确父子归因；flat symbol 报告成功且无该类报错。

同时对全部 8 个 rank 做 `perf stat`：用户态 task-clock 等效约 128 个 CPU，IPC 1.83，generic cache miss/reference 比约 7.78%。task-clock 包含忙等；这些计数不能直接证明 DRAM 带宽饱和，也不能当作有效数值计算利用率。

## MPI：全场 Allgather 比标量归约更突出

另一轮单独诊断运行用 PMPI 包装器，仅在 `MPI_Pcontrol(1)` 到 `MPI_Pcontrol(0)` 的 5 次额外求解内计数；setup 和普通样本不计入。按每列、每 rank 归一化：

| MPI 操作 | 次数 / 列 | 8 rank 平均调用墙时 / 列 |
|---|---:|---:|
| **Allgather** | **9** | **0.500 s** |
| Allreduce | 477 | 0.073 s |
| Waitall | 292 | 0.080 s |
| Barrier | 2 | 0.002 s |

9 次 Allgather 中包含 **5 次完整 spinor** 和少量 Python/API 元数据交换。一个完整 complex128 spinor 为 `884736×12×16 = 162 MiB`，每 rank 每列累计接收约 **810 MiB** 完整场，8 rank 合计约 6.33 GiB。这是 MPI 接收缓冲规模，不等于实际物理链路流量。Allgather 的平均调用墙时约 0.50 秒，rank 间为 0.47–0.53 秒；包含到达不齐和等待，不能全归因于链路传输。

来源可直接追到代码：

- `src/backends/x86/backend.cpp` 的 `gather()`：输入源一次、最终完整算子验证输入一次。
- `src/backends/x86/fine_operator.cpp` 的 `decode_fine()`：3 次可靠更新各 Allgather 一次完整修正。
- `src/backends/x86/solver.cpp` 的可靠更新：对完整 `x/r/dx` 做 AXPY、复制和算子应用。
- `src/backends/x86/cycle.cpp` 的 `NativeMG::apply()`：调用标量 double `apply_dirac()`；该算子的 Clover 和 Dslash 循环遍历完整 884736 个 site。

因此，双精度算子部分在 8×32 配置中实际是 **8 个进程各用 32 线程重复相同的全场工作**。它没有像浮点 owned slab 那样被 256 核共同分摊。典型一列包含 3 次可靠更新算子和 1 次 API 最终算子验证，每个 rank 都执行这些完整算子。MPI 调用墙时不可跨 rank 相加，Waitall 还可能与其他 worker 重叠，不能把本表与 perf 或 halo 字段相加构成求解时间分解。

## halo、粗层和 NUMA

1024 个 aggregate 分给 8 个 rank，每 rank 128 个；时间粗格点 16/8=2 个平面。当前实现把首尾两个 aggregate 平面都归为 boundary，所以 **interior aggregate 数为 0**。细层和粗层 halo 诊断都确认 interior 仅有空循环的计时量级。

每列实测 88 次 fine halo、204 次 coarse halo，合计 292 次 Waitall；每 rank 双向发送约 222.75 MiB fine 数据和 9.56 MiB coarse 数据。halo profile 的各字段是各 rank 局部累计量的独立最大值，不可直接相加。

粗层 EO 每次仅 64 个 active site，32 线程平均 2 个 site；但仍频繁进入 OpenMP parallel region。粗向量的 norm/dot/AXPY 采用 `size>100000` 才并行，而此格点单 rank 完整粗向量也仅 98304 个 float，8 rank 时仅 12288。由此可见需要独立设计粗层线程粒度。**477 次 Allreduce 是实测总数；没有证据把 Allreduce 当成此次最大的耗时项。**

`numastat -p` 在 rank 0 和 rank 4 的驻留内存中分别约 99.84%、99.85% 位于其所属 NUMA 域，当前没有大量页错放的证据。驻留页分布不是远端访问流量测量。每 rank 约 17 GiB 的驻留量也包含只用于 setup 的资产，不能把所有副本都算作稳态带宽。

## 因果对照与修复优先级

8×32 的单独 5 次计时对照：

| 配置 | 第二次 / s | 稳态中位数 / s |
|---|---:|---:|
| 默认 overlap、默认等待 | 1.942 | 1.899 |
| 关闭 halo overlap | 1.882 | 1.876 |
| `OMP_WAIT_POLICY=PASSIVE` | 1.932 | 2.032 |

关闭 overlap 没有明显改善，被动等待更慢。单纯换等待方式不能消除产生等待的重复工作和同步依赖。

优先顺序：

1. **将生产可靠更新、最终 `D*x` 和场运算改成 rank-local double + halo，移除这些完整 spinor Allgather。** 独立标量参考算子继续留作离线验算。保持完整双精度残差门，不能通过少做验算来加速。
2. 把 fine 工作场从全局尺寸工作区改为 owned sites + ghosts，避免全局初始化/复制；继续验证 NUMA first-touch。
3. 为粗层选择独立线程组或进程聚合，减少小数组上的 OpenMP 启动和屏障；用实测决定是否批量归约，不能机械改变有依赖的 MGS。
4. 将细层 boundary 细化到物理时间 face：8 个本地时间切片仍有 6 个不依赖远端，当前按 aggregate 粒度等待过于保守。再推广空间/时间多维分解，避免未来更多 NUMA 下的薄域。

这轮全部使用此前相同 AMD 求解二进制，只新增 benchmark 的外部 profiling gate 和 MPI_Pcontrol 标记。没有把改变算法、放宽精度或计时范围得到的数字列为强扩展收益。

## 证据与复现

机器可读全部样本、per-rank PMPI 时间、perf 符号统计、NUMA 数据和源码/二进制哈希见 [node5005-perf.json](node5005-perf.json)。原始数据在工作区 `.cache/node5005-perf-20261022/`：

- `run_scaling.sh`：同机扫描；`rank1/2/4/8/result.json` 及各线程 case 保存完整样本。
- `collect_perf.py`、`perf-metadata.json`：PID、命令、采样范围、线程覆盖。perf 由 SIGINT 正常停止；Python returncode 为 -2，record/stat 已成功刷出结果。
- `perf.data`、`perf-flat.csv`、`perf-stat.txt`：原始采样、flat 符号表和计数器。
- `mpi_counters.c/.so`、`run_controls.sh`、`mpi-counters/rank*.json`：PMPI 包装器、对照命令和每 rank 统计。
- `diagnostic8.log`、`blocking8/result.json`、`passive8/result.json`：halo 诊断及控制实验。
- `numastat-rank0/4.txt`、`numa-maps-rank0/4.txt`：NUMA 驻留页证据。

profiling gate 需使用新目录。各 rank 写好 `rankN.ready.json` 后，先启动外部 perf，再创建 `go` 文件；300 秒内未创建会超时。`profile_samples` 与正常 `samples` 分开保存。
