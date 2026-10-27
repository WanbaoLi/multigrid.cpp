# 鲲鹏HPC手册驱动的ARM后端优化（2026-10-26）

依据用户提供的《鲲鹏920专业版系统开发手册.docx》，SHA256
`018a5811dd7529dc37c43a99897dfed50b67bf4de4bcd4455ff4b6412cf1670c`。
手册封面V1.1、文档版本01、发布日期2026-06-01；本地提取567个非空段落、3个表格。
其CPU/NUMA/片上内存与矩阵编程内容已整理为可复用skill：
`LQCD_Skills/kunpeng-hpc/`，同时安装在`~/.codex/skills/kunpeng-hpc/`。

## CPU与CANN的范围

本次继续优化`src/backends/arm/`，通过共同NativeMG求解Wilson–Clover。
当前multigrid.cpp没有CANN生产求解后端。手册的HPCKit、KUPL、KuDNN、SME及SDMA
属于鲲鹏CPU开发路径，不能直接当成AscendC/CANN算子API。
本次没有新增NPU/CANN依赖；PyQUDA布局、源归一化与独立scalar参考保留。

## 手册内容如何落到代码

| 手册章节 | 与MG的联系 | 本轮处理 |
|---|---|---|
| 3.3，512bit向量计算 | float Wilson/Clover热点 | VLA SVE谓词、连续加载候选与原gather共用数学 |
| 4.1/4.2，Flat/Cache与片上内存 | 大层级不能整体强绑4GB内存域 | 保留选择性owned页迁移，补充策略/驻留诊断 |
| 6.1，housekeeping核 | 每38核域保留末核 | 通过allowed cpuset得37线程，避免硬编码608个可用核 |
| 7，矩阵化/ZA与KUPL/KML | 未来coarse dense/GEMM候选 | 本轮不以SME理论算力替代实际测量；未新增强制库依赖 |
| 9，带宽与指令混合测量 | 判断计算/带宽/归约瓶颈 | 同机同库A/B、完整12列与内核计时分别记录 |

## SVE地址计划

`wilson_sve.hpp`新增共享寻址helper，未复制一整份Wilson算子。
局部计划复用`hierarchy.cpp`已有的`local_load_offsets`：仅当方向内有效邻居满足统一
`index-site`偏移、当前tile不跨parity半块且地址范围安全时改用谓词连续加载。
实际邻居掩码仍保留，Dirichlet洞、跨半块和尾部继续回退gather。

全场路径可直接读取已有、经过范围检查的`neighbor32`，避免每个tile将ptrdiff逐元素
转成32位临时数组。完整float字段超过INT_MAX时仍使用pointer-width portable路径。
单列与两列halo的完整/部分时间范围调用均已传递计划；MPI协议、EO/Schur、P/R、
归约和停止条件保持同一实现。

新路径通过启动前`LQCD_ARM_SVE_PLANNED=1`显式启用，默认0，便于同一二进制比较。
`LQCD_ARM_SVE=0`仍选择portable；SVE编译目标可能使portable循环被自动向量化，
不能把开关称为“完全禁用SVE ISA”。

相关文件：`src/backends/arm/wilson_sve.hpp`、`wilson_kernel.hpp`，
`src/solver/native/kernels.hpp`、`fine_operator.cpp`、`batched_fine_operator.cpp`。
测试`tests/unit/arm_sve_plan_test.cpp`覆盖缺失邻居、partial/tail、半块跨越、奇偶alias、
compact/无compact索引和超大场guard；包括实验开启、关闭及portable三种独立进程配置。

## P插值寄存器tile候选

[transfer_sve.hpp](../src/backends/arm/transfer_sve.hpp) 的 `prolongate_component_sve()`
按 `svcntw()` 组织site tile，将非零初始fine值加载到寄存器，依序累加24个basis后写回。
[cycle.cpp](../src/solver/native/cycle.cpp) 和
[batched_cycle.cpp](../src/solver/native/batched_cycle.cpp) 共用该内核。
`LQCD_ARM_SVE_TRANSFER=1` 是独立的实验开关，默认0；测试使用double oracle检查
非零累加、不对齐输出、尾部和输入保护。实机完整求解未得到稳定加速，保留为关闭的候选。

## 内存诊断

`memory_placement.cpp`明确当前分配器为posix_memalign，HBM路径是已有页的mbind迁移，
不是KUPL/memkind分配。日志包含allowed_mems、目标候选、迁移/查询返回码、
目标/非目标/未知样本页；原始驻留、硬件Cache/Flat模式并未自动探明，明确标记unknown。
CPU affinity不等于内存binding；1GiB/rank是请求预算，不是发现的容量或预留保证。
未迁移存储继续沿用原numactl/分配器策略，不能一概说留在DDR。

## 验证与计时状态

本机x86完整35项CTest通过；新增SVE分支在x86被跳过，不能代替ARM实机验证。
Donau作业1965917在cn05133构建，18项检查中17项通过，已有cpu_backend_serial
在继承spread亲和性时240秒超时，保留原失败记录。该串行门随后以两个明确本地CPU
places重试并在56.62秒通过，数值测试及原timeout未修改。CMake已为串行CPU门固定close策略。
第二版ARM选择的19项CTest全部通过；另有三个依赖PyQUDA的历史测试因远端没有
pyquda_comm而未能执行，其失败记录保留，不列为通过。独立CPU serial/MPI2门已覆盖
两种归一化、EO/lex、随机源、单/双RHS与完整算子残差。
本次allowed CPU仍是592个，Mems_allowed_list仍为0–15，不能声称获得HBM驻留。
最终实机结果已完成。job 1965917 在 cn05133、592允许物理核、Mems_allowed=0–15上完成：

| 实际核数 | 寻址候选关闭 | 寻址候选开启 | P插值候选关闭 | P插值候选开启 |
|---:|---:|---:|---:|---:|
| 296 | 37.887534 s | 37.644782 s | 37.814163 s | 37.800604 s |
| 592 | 22.869655 s | 22.607259 s | 22.670395 s | 22.733672 s |

每一对开关使用同一库文件；寻址实验库SHA为`7df9422275d33c2602f884e9e58f8778be0e67d94483d9a72eb437aa68452740`，
插值实验库SHA为`6cbdbd146d22aa4586c50bfd5c5af7947c6b4b4957305f1da9c3a8cab282afc8`，两组实验的基线不能交叉混用。
均为第二轮12列内部solver计时；所有轮次最大真残差约`4.82e-9`，独立scalar 12列复核返回0。
寻址候选的局部微基准加速约1.17×（EO Clover）、1.25×（EO hopping）、1.08×（global int32），
但完整求解只快0.64%/1.15%；P插值候选分别快0.04%/慢0.28%，没有稳定收益。因此两个实验开关均保持默认关闭。

单RHS 592核剖析显示第二次调用约1.889秒，其中 profile 粗层约0.594秒、SAP约0.846秒、
restriction约0.099秒、prolongation约0.084秒；后续优先级应放在粗层密集矩阵/EO-GCR、SAP
与MPI归约，而不是继续堆叠一个未验证的P插值内核。

SVE进程长度16/32/64字节均独立启动通过 arm_sve、寻址计划和P插值测试；这只证明VLA
正确性，不宣称三种长度的完整传播子性能相同。HBM仍未分配，所有上述成绩均不能标为HBM收益。

完整数值、阶段、源文件SHA256及原始计时索引见[机器记录](kunpeng-hpc-optimization.json)。
新skill入口：[kunpeng-hpc](../../LQCD_Skills/kunpeng-hpc/SKILL.md)。
