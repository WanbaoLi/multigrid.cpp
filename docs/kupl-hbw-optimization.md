# KUPL HBW：真实分配探针与集成边界（2026-10-26）

本轮确实调用了SDK的 `kupl_hbw_check_available()` 和 `kupl_hbw_malloc()`，但
**所有rank返回不可用/null，没有成功分配HBM，也没有HBM加速证据**。不能把这次
失败解释为已证明SDK不识别新芯片。296核完整12列的速度验收另行记录，此处不发布
未完成的性能数字。

## 可复核探针

Donau作业 **1966770**，节点 **cn05137**，前8个CPU NUMA各37个应用核，共296核。
8个MPI rank分别请求 **64MiB（67108864 bytes）** HBW内存。

| 检查 | 结果 |
|---|---|
| `kupl_hbw_check_available` | 8/8为0 |
| `kupl_hbw_malloc` | 8/8为null |
| SDK诊断 | High Band-width memory undetected |
| 作业允许内存节点 | 0–15（DDR） |
| 已知物理HBM节点 | 16–31，当前不在作业允许集合 |
| memlock限制 | soft/hard均unlimited，非本次不可用的首要原因 |
| 后续verify/move_pages | 没有指针，因此未执行；日志-2是探针未执行标记，不是SDK返回值 |

日志中`cpus`来自调用线程的affinity，初始化OpenMP后主线程显示单核；完整团队绑定
以同一日志前部的placement/OMP_PLACES为准，不能据主线程单核认定只申请了8核。

已从远端本任务目录下载完整日志，未改写旧日志：

- `.cache/kupl-hbw-20261026/evidence/001-probe.log`、`.exit`：首次链接失败。
- `002-probe-runtime.log`、`.exit`：修正运行库后的真实8rank分配探针。
- `manifest.json`：下载文件SHA256、8条原始探针结果及摘要。

## SDK与不可用原因

SDK为 `HPCKit/25.1.0.SPC001/kupl/gcc/release/lib/libkupl.so`，SHA256
`5955055a872388c2a9ae27280c0f602880538244b4acdd3985e713a5bb79964f`。
初次链接遇到`GLIBCXX_3.4.30`缺失，已改用SDK
`compiler/gcc/lib64/libstdc++.so.6.0.30`，其提供所需condition_variable符号。
这是C++运行库匹配问题，与HBM检测失败是两件事。

只读反汇编显示检测过程调用`numa_get_mems_allowed`，遍历NUMA节点，先排除CPU
mask非空的节点，再排除不在allowed mems中的节点；仅其余memory-only节点进入候选。
本次HBM全部被cpuset合法过滤，足以解释available=0。未发现需要按新芯片型号更新
检测表的证据；也没有从SDK目录发现比25.1.0.SPC001更新的已安装版本。
不能修改库检测逻辑、用numactl或其他分配器绕过作业内存权限。

SDK头文件定义HBW内存为page-locked，当前policy仅`KUPL_HBW_POLICY_BIND`。
`kupl_hbw_verify`返回1表示全部页面符合HBW、0表示有非HBW页面、-1表示验证失败。
后续若owned数据复制已经触页，应调用 `kupl_hbw_verify(ptr,bytes,0)`，不必再次启用
`KUPL_HBW_TOUCH_PAGES`。分配成功与实际页面驻留是不同证据；还需记录目标节点、
允许集合、分配字节和独立抽样驻留。

## Qlotus参考能证明什么

已阅读 `Qlotus-develop/AGENTS.md`、README、构建文档和实际源码。当前提供的树中
没有 `kupl_hbw_malloc/free` 调用，不能声称从Qlotus直接继承了已工作的HBW分配器。

- `src/fields/qlotus_memory.cpp::KMemory::InitMem/Free` 使用64字节aligned_alloc/free，
  或`USE_HPMEM`的MAP_HUGETLB/munmap。大页不等于HBM。
- 同文件`HaloMemory::InitHaloMem/Free` 使用KUPL共享通信窗口：comm_create、win_alloc，
  按win_free再comm_destroy释放；不是HBW malloc/free配对。
- `src/utils/qlotus_utils.cpp` 的OOB callbacks调用MPI_Allgather/Barrier；构造/释放通信
  对象需MPI已初始化、主线程与跨rank顺序一致，不能为单纯HBW分配无端引入该通信依赖。
- `checkHugePages()`固定检查node16，且只看nr_hugepages；不适合直接用于本项目允许
  节点动态变化的场景。源码部分分配路径未完整处理MAP_FAILED/null，也不能照搬。
- 可以参考持久资源对象、按需增长及并行first-touch；其HISQ三色批量SoA不是本项目
  Wilson四spin/12分量布局，算子和物理约定不能直接替换。

## 本项目可选分配策略

保留共享MG算法和默认DDR对齐数组。除现有owned页迁移路径，已经提供明确的
可选owned HBW独立缓冲区（sidecar）：仅为热点子数组调用`kupl_hbw_malloc`，验证
对齐/大小，复制owned数据并触页，`kupl_hbw_verify(...,0)`成功后才供对应内核使用。
保留原始DDR资产作为fallback与setup来源，索引转换必须按owned起点处理。

分配器身份必须伴随指针保存，KUPL指针只由`kupl_hbw_free`释放，不能调用普通free
或munmap；移动/异常路径也不得重复释放。总预算需要按CPU NUMA域汇总多个rank，
不能仅逐rank不超预算就认定不超过4GiB节点容量。`prefer`失败明确退回DDR并记录；
严格模式在任何rank验证失败时集体拒绝，不生成假的HBM性能成绩。

当前探针事实决定：先申请允许HBM的合法资源配置，再复核实际分配与驻留。该接口
是否提升296核完整传播子性能，只能由之后正确性门通过的完整重复测量决定。

## 本轮集成与296核实测

`src/support/hbw_buffer.{hpp,cpp}` 提供带所有权的 KUPL/DDR fallback 缓冲区。
`src/solver/native/hbw_assets.cpp` 只迁移本 rank 拥有的 links、Clover inverse、basis
和可选粗格子列矩阵；`hierarchy.hpp` 的 `links_block`、`basis_block` 及粗格子 helper
按 owned 起点索引 sidecar。`LQCD_HBW_ALLOC=off|prefer|require` 在上下文创建时做
MPI 一致性校验，`require` 在所有 rank 上验证失败时集体拒绝。默认仍为 `off`。

计算节点 `cn05137` 的第二次作业 `1971697` 使用前 8 个 CPU NUMA、8 MPI rank、每
rank 37 个线程（296 个应用核），开启 `LQCD_COARSE_FUSED=1`、
`LQCD_ARM_COARSE_SVE=1`、`LQCD_HBW_ALLOC=prefer`。同一 setup 后交替测试 batch 2、4、
12，各 3 轮，首轮预热；计时只包含纯求解，shared batch 时间已去重：

| RHS batch | 第二轮 (s) | 第三轮 (s) | 第二/三轮中位数 (s) |
|---:|---:|---:|---:|
| 2 | 36.4808 | 36.4907 | 36.4858 |
| 4 | 35.2638 | 35.2822 | 35.2730 |
| 12 | **34.7664** | **34.7997** | **34.7831** |

每列均收敛，独立标量参考逐列复核的最大相对残差为 `4.818811004e-9`。本作业的
KUPL 仍因 allowed memory nodes 只有 0--15 而回退到 POSIX DDR；因此上表是 SVE、粗
层融合和批量路径的 CPU 结果，不能称作 HBM 加速，也尚未达到 10 秒目标。原始
`comparison.json`、`result.json`、逐列复核日志保存在 `.cache/kupl-hbw-20261026/`。
