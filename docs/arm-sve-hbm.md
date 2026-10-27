# ARM SVE 与 HBM 尝试（2026-10-26）

已实现并在真实计算节点执行显式 SVE Wilson/Clover；HBM placement 已实现，但本次
调度分配不允许访问 HBM，尚无 HBM 性能数据。SSH恢复后已取回完整传播子的SVE/
关闭SVE同机对照成绩，第二轮纯求解为38.957/22.726秒，仍未达到5秒目标。
独立scalar输出复核状态与跨硬件对比见[完整记录](hardware-comparison-20261026.md)。

## 实现

`src/backends/arm/wilson_sve.hpp` 使用 SVE ACLE 谓词加载/存储、signed-index gather，
按 `svcntw()` 遍历，支持不对齐起点与尾部。局部负邻居被掩码，保留奇偶半块的安全
alias；全局指针宽度索引仅在完整字段能放入 INT_MAX 时转32位，其他情况走原 portable
路径。Clover 和 inverse 的 site SIMD 也有 SVE 实现。`__ARM_FEATURE_SVE` 之外的
构建保留NEON/portable路径；`LQCD_ARM_SVE=0` 关闭新路径，`1` 开启。
没有改变算子、源归一化、stout、MG参数、零初值策略和原 double 全残差门。

`src/support/hbm_placement.hpp` 和 `src/solver/native/memory_placement.cpp` 在最终
hierarchy通过数值门之后，对每rank拥有的links、diag、clover inverse、basis、coarse
及邻居索引的完整页范围设置可选 NUMA policy。总预算限制1GiB/rank，setup全局副本
和大Krylov工作区留在DDR。最近的memory-only NUMA候选必须位于作业允许的mems内；
该启发式需结合平台探测确认HBM类型，不能把任意memory-only节点自动认定为HBM。

HBM模式：默认 `LQCD_HBM=off`；`prefer` 记录无法放置的原因后继续，`require` 在
任一rank迁移/抽样验证失败时collective报错。实现记录mbind错误和move_pages抽样
驻留结果，不能把申请成功等同于所有数据已使用HBM。调用方应使用NUMA启动器，
提供对应的 `LQCD_NUMA_NODE`。setup计时包含这次可选页迁移，solve计时不包含它。

## 已取得的实机证据

Donau作业1963656在 `cn05132`，同型双路304核节点，592个允许物理核，16个CPU NUMA。
GCC10.3.1/HMPI4.1.6、native构建；SVE为64字节，即16个float lane。库SHA256：
`0d9825815790636288e4ac2b3ae3e8eea89590eb2e6d60b40fa93e4ed827d118`。
反汇编确认实际出现 `mov z4.s`、`ld1w {z1.s}, p1/z` 等SVE指令。

计算节点15项测试全部通过，包括独立SVE Clover double oracle、Wilson portable
对照、EO alias/partial/tail/超大索引回退，以及MPI2 CPU、LIME、stout和MG调参。
本机x86完整31项回归通过；x86上的SVE专用分支未执行，实机15项才是ARM验证依据。

单核绑定CPU570、B=864（6³×4）内核微基准，每轮100次，5轮交替portable/SVE顺序，
随机填充和校验不计时，每次清零输出计时。输出checksum防止优化消除，最大相对差
约7.51e-8。下表为观测范围，不能替代传播子计时：

| 内核 | SVE相对portable加速 |
|---|---:|
| 完整局部Wilson+Clover | 1.49–1.50× |
| EO半块Wilson+Clover | 2.14–2.16× |
| EO半块hopping | 2.50–2.51× |
| Clover-only | 1.94–2.11× |
| 全局ptrdiff gather Wilson | 1.328–1.335× |

微基准在8 NUMA求解使用0–7域时绑定CPU570（15域），不占用性能样本的核。
源码和日志位于本地 `.cache/hbm-sve-20261026/kernel_bench.cpp`、`kernel-bench.log`。
后续连续加载候选留在同一cache目录，尚未接入生产，需ARM实机验证后再决定。

## HBM访问限制

本次作业仍报告 `Mems_allowed_list: 0-15`，对应DDR；HBM节点16–31被排除。
`numactl --membind=16 /bin/true` 返回1并报告节点无效。Donau显示保留61440MiB内存，
但这个总量本身不能证明其具体保留策略。`dsub -a help` 和 `-a none` 都被拒绝；
没有经过验证的站点HBM申请参数。未修改cgroup或系统配置，未突破调度器分配范围。
在取得允许HBM的分配前，`prefer`日志中的 `target=-1`、`bound_bytes=0` 表示确实
没有迁移，不能标注为HBM运行。

## 完整格子性能

远端目录 `/home/share/nsls_lwb/.cache/multigrid-hbm-sve-20261026/` 中，
`tasks/002-sve-scaling.sh` 和 `003-portable-scaling.sh` 在同一独占作业内串行执行且均返回0：
SVE开/关各做8 MPI×37与16 MPI×37，每组2轮12列、原始24³×64 LIME、一步stout、
mass=-.277、csw=1.160920226、true residual≤1e-8。SVE实验设置HBM prefer，但
当前分配只能实际使用DDR；portable对照为HBM off。

| 第二轮，秒 | 8 MPI×37，296核 | 16 MPI×37，592核 |
|---|---:|---:|
| SVE关闭，12列纯求解 | 46.456866 | 29.452243 |
| **SVE开启，12列纯求解** | **38.957395** | **22.725742** |
| 同机纯求解加速 | 1.193× | 1.296× |
| SVE开启，完整12列API | 39.492406 | 23.226137 |
| SVE开启，setup（排除在solve之外） | 195.115664 | 187.897988 |

两个结果目录为 `results-sve/`、`results-portable/`，各自有 `scaling.json` 和
`numa{8,16}/result.json`、`propagator.npy`。所有报告complete=true；SVE的两组最大
真残差分别4.818817693e-9和4.818843169e-9，24–25次迭代，无refinement。
原始LIME SHA256仍为`47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30`。
完整12列采用两列batch，内部共享batch计时只计一次；与单核EO hopping 2.5×加速
不能等同，因为其余SAP/粗层/归约/通信工作仍占用完整求解时间。

本地计时与日志已取回到`.cache/hbm-sve-20261026/evidence/`。新SVE输出采用独立
scalar C++逐列复核，结果保存于同一cache下`verification-sve/numa{8,16}/verification.json`；
机器比较表与JSON保存单列补测、原始计时、实际核数和来源SHA256。

本次控制器修正了上次等待期限退出问题：先处理finish，再在空闲时检查期限。
调度作业限制7200秒，控制器空闲期限6900秒；即使连接中断也有有界资源占用。
