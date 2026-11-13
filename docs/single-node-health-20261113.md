# 单节点真实组态健康检查（2026-11-13）

本次正式比较统一使用 GitHub `develop` 提交 `efe57de52223a6f7f5177ac731c33e762070b327`。两台机器均固定 **16 个 MPI 进程**，时间方向切分为 `grid=1,1,1,16`，零初值，12 列按每批 2 列求解，停止条件为真相对残差不大于 `1e-8`。每个格子只建一次层次，然后测 3 次单列和 3 次完整 12 列。“预热后”是第 2、3 次的中位数。stout、规范场转换/Clover 构造和 setup 均不计入求解时间。

| 机器 | 格子 | setup / solve 线程（每 MPI） | 分块 | stout | setup | 预热后单列 | 预热后12列 | 最大独立残差 |
|---|---|---|---|---:|---:|---:|---:|---:|
| node5005 | 24³×64 | 16 / 12 | 6×6×6×4 | 0.671 s | 129.368 s | **0.688 s** | **6.216 s** | 9.170×10⁻⁹ |
| node5005 | 32³×64 | 16 / 12 | 8×8×8×4 | 1.644 s | 300.843 s | **2.846 s** | **29.989 s** | 1.844×10⁻⁹ |
| 灵晟 | 24³×64 | 37 / 32 | 6×6×6×4 | 3.825 s | 224.591 s | **1.274 s** | **14.853 s** | 4.819×10⁻⁹ |
| 灵晟 | 32³×64 | 37 / 32 | 8×8×8×4 | 8.811 s | 487.831 s | **5.297 s** | **63.850 s** | 4.876×10⁻⁹ |

灵晟每 NUMA 域一个 MPI，使用全部 16 个 NUMA 域，每进程绑定 37 个可用物理核；求解时队伍缩为 32 线程，不重建层次。node5005 每 NUMA 域两个 MPI，8 个 NUMA 域共 16 MPI，每进程绑定 16 核，求解时使用 12 线程。

## 正确性和计时范围

每次测量都通过运行库的真残差门限；每组最后一次单列与最后一次 12 列输出，另外使用独立标量 `multigrid` 程序逐列验证，一组共 13 次独立算子检查。四组均通过，单列与 12 列第一列相对差为 0，所有测量均无额外 correction/refinement。精度是混合精度：MG/SAP 热路径采用 FP32，外部场及完整真残差检查采用 FP64；这不是“全双精度热算子”的结果。

两台机器分别通过 30/30 CTest，包括普通 MPI、shared MPI、context 生命周期和 batch12。node5005 用 GCC 14.4/Open MPI 5.0.10；灵晟用站点 GCC 10.3.1/HPCKit 25.1 HMPI（MPI 库报告 Open MPI 4.1.6rc4）。

首次、第二次、预热后数据（秒）：

| 机器/格子 | 单列：首次 / 第二次 / 预热后 | 12列：首次 / 第二次 / 预热后 | 本轮最快12列 |
|---|---|---|---:|
| node5005 C24 | 0.716 / 0.685 / 0.688 | 6.299 / 6.226 / 6.216 | 6.205 |
| node5005 C32 | 2.996 / 2.846 / 2.846 | 30.240 / 29.995 / 29.989 | 29.983 |
| 灵晟 C24 | 1.722 / 1.290 / 1.274 | 15.340 / 14.914 / 14.853 | 14.792 |
| 灵晟 C32 | 6.047 / 5.304 / 5.297 | 64.595 / 63.923 / 63.850 | 63.777 |

C24 参数：mass `-0.277`，Clover 系数 `1.160920226`；C32：mass `-0.279`，Clover 系数 `1.1606789224`。两格均一次 stout，`rho=0.125`，四个方向均参与，时间反周期边界，seed `1024`。这些参数已逐项写入结果 JSON。

## 恢复原来的灵晟 16 MPI 路径

目录整理后的代码缺少旧 `73531ac` / `a35c3a4` 的共享系数实现。新提交 `efe57de` 按当前 `src/` 内部头文件结构迁回它，未恢复旧目录。灵晟 profile 显式使用 `LQCD_SHARED_COEFFICIENTS=1`；普通 runtime 默认关闭，x86 本轮保持原私有存储路径。

共享对象是不可变的双精度规范场、Clover、setup basis 和 coarse stencil，spinor、Krylov、halo、FP32/packed 热数据仍是每个 MPI 私有。代码为 `src/core/coefficient_field.h`、`src/support/shared_coefficient.*`、`src/solver/native/backend.cpp` 和 `setup.cpp`。写者分片写规范场/Clover/basis，随后 `MPI_Win_sync → MPI_Barrier → MPI_Win_sync`；粗算子由 rank 0 装配，避免 scatter-add 的并发写冲突。该模式目前只支持单物理节点。

C32 的这四类双精度系数每份为 23.9414 GiB，原 16 份合计 383.0625 GiB；共享后只保留一份。这是静态系数容量，不是进程峰值内存。灵晟作业 `2117750` 在 `cn12118` 成功结束，分配 592 CPU、480000 MB；调度器报告每节点 `memMax=420658 MB`，汇总计数 `memMaxTotal=301664 MB`，两项均保留其原口径，无交换和 OOM。KUPL 热数据分配确认 `fallback=0`、`sdk_verify=1`。

此前的 8 MPI C32 记录改名为 `lingsheng-L32-8mpi-diagnostic.json`，只作诊断，正式表格全部为 16 MPI。本轮 C32 预热后 63.850 s，与旧 16 MPI recipe 的约 64.897 s 接近，不能将与 8 MPI 诊断值的差异单独归因于某个内核优化。

## 编译和复现命令

从干净 GitHub checkout 的项目根目录执行。脚本自动在输出目录编译 runtime 和独立参考、运行选定 CTest，再检查真实输入。输出目录必须是尚不存在的新目录，不能位于源码目录内部。

node5005：先 `ssh itp`，再 `ssh node5005`，然后运行：

```bash
bash tools/health/run_single_node.sh x86 \
  "$HOME/.cache/mg-health-replay-NEW" \
  /public2/home/lwb_720/lqcd/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime \
  /public2/home/lwb_720/.cache/mg-health-20261113/inputs/beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime
```

灵晟：先 `ssh ls`，在登录节点提交，编译与计时发生在选出的空闲计算节点：

```bash
bash tools/health/submit_ls.sh \
  "$HOME/lqcd-run/health-replay-NEW" \
  "$HOME/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime" \
  "$HOME/multigrid.cpp/data/C32P23/beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime"
```

默认 ARM profile 为 `profiles/optimization/lingsheng-shared-uniform.json`，x86 为 `profiles/optimization/node5005-833-full12.json`。两格强制 16 MPI，脚本拒绝旧的 8 MPI override。只运行一个格子可在命令前加 `LQCD_HEALTH_GEOMETRIES=24` 或 `=32`。结果在 `L24/result.json`、`L32/result.json` 和各自的 `verification.json`；只有全部 13 次独立检查通过后才删除临时大数组。

输入完整性：

- C24：`beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime`，SHA256 `47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30`。
- C32：`beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime`，SHA256 `bc2918403eee5d1e10a409fc0e69ac03b22cc7f0cf71be760b44a593ff0d0828`。

本轮远程源码与输出：

- node5005 源码：`/public2/home/lwb_720/.cache/mg-health-efe57de-source-20261113`；输出：`/public2/home/lwb_720/.cache/mg-health-16mpi-efe57de-20261113`。
- 灵晟源码：`/home/share/nsls_lwb/lqcd-run/health-20261113/source`；输出：`/home/share/nsls_lwb/lqcd-run/health-20261113/run-16mpi-shared-01`。

结果 JSON 在 `experiments/single-node-health-20261113/`；原始日志和 CTest 日志另备份在本机 `C:\Users\lwb\AppData\Local\Temp\mg-health-16mpi-efe57de-results-20261113` 与 `C:\Users\lwb\AppData\Local\Temp\ls-health-16mpi-efe57de-results-20261113`，没有将原始测试日志、二进制或大数组放入 Git。

## 最后一次性能检查

node5005 的 C32/C24 完整时间比约为 `29.989/6.216=4.82`。体积比约为 `(32/24)^3=2.37`，平均外层迭代从 21.42 次增加到 41.83 次，迭代比约 1.95，二者乘积约 4.63，已解释大部分差异。灵晟的时间比约 4.30，平均外层迭代为 24.08 和 43.58 次。C32 的收敛质量值得优先检查。

旧 node5005 诊断的 rank 0 局部累计计时中，C32 的 SAP 为 2.711 s，restriction 为 0.426 s，prolongation 为 0.352 s，coarse 为 0.311 s；它们不是 MPI 墙钟分解，不能直接换算整体占比。以下是有代码依据的后续候选，不是已经测得的加速：

1. **SAP 块内两列融合。** `src/solver/native/batched_sap.cpp` 在每个 cycle/颜色建立并行区，并在一个块内顺序处理两列；`sap.cpp` 对两列重复执行局部 Wilson/Clover 操作。先拆 profile，再尝试重用系数和减少并行区开销。两种格子在 16 MPI 下每进程每色都是 32 个块，恰好对应 32 线程，单纯改调度没有明显的任务数量收益。融合可能增加寄存器和缓存压力，需完整验证。
2. **改善 C32 收敛。** 灵晟当前粗解容差默认为 `0.1`；可有限比较 `0.05` 或更强 setup，以完整 12 列时间决定。更准的粗解可能减少外迭代，也可能使每次 V-cycle 更贵，不能只比较迭代数。
3. **释放建层向量，局部化剩余全局 FP32 副本。** `setup.cpp` 最终保留 24 条 setup 测试向量，C32 共约 72 GiB/节点，后续求解不再读取它们。`hierarchy.cpp` 和 `hbw_assets.cpp` 还保留全局 FP32/packed 原始副本。可先释放建层向量，再将只读系数改为 owned block 加所需 halo；共享全局浮点数据也要考虑 NUMA 远端访问。这些目前是容量和代码证据，尚无纯求解加速数据。

上述候选继续固定 16 MPI，以完整 12 列墙钟时间和 `1e-8` 真残差验收。保留本轮已通过版本，不能用局部算子加速替代最终指标。
