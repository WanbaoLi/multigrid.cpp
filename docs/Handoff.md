# multigrid.cpp 交接（2026-11-16）

本对话到此结束；交接文档不要求自动提交新作业或继续调优。
本轮排队对照已完成，不能再沿用“2137061 尚在排队”的旧状态。

## 1. 目标与用户约定

- GitHub 为项目源码、脚本、配置及实验实现的唯一规范记录：<https://github.com/WanbaoLi/multigrid.cpp>。
- 项目自有 CPU Wilson–Clover MG；DDalphaAMG 仅作外部参考，不能计为自研成绩。
- 优先做好**单组态、单 source 的完整 12 列传播子**。不展开多个源点分组并行。
- 实际应用复用层次求多个源点；优先看预热后完整 12 列纯求解，单列仅作补充。
- 当前交付目标是实输入 24³×64、完整真实相对残差不超过 `1e-8`、12 列 15 秒内；早期 5 秒目标不是当前验收要求。
- 零初值；层次复用不能变成解向量热启动。读取、stout、Clover 构造、setup、布局转换、纯求解、完整 API 与独立验证分别计时。
- 正式比较固定 **16 MPI**；灵晟每 CPU NUMA 一个 MPI，setup/placement 37 个允许物理核，求解每 MPI **32 线程**。使用 `tools/run_numa.py` 绑定，排除保留核。
- 所有实验必须先 commit/push，再同步或运行到远程；记录编译源码、控制脚本的精确提交及二进制哈希。不要改运行中的源码/脚本。
- 默认保留最佳正确版本。实验前读历史，每轮写假设、机制、profile、精度、性能和结论；不可将一次局部提速当完整求解收益。
- 给用户解释算法时结合代码；公式里的每个字母都要解释。数据规模、参数、切割和精度要说清楚。

## 2. 分支、源码与本地工作区

| 用途 | 版本/位置 |
|---|---|
| 稳定开发主分支 | `develop`；本交接提交前为 `141db3982afdbf3f64dd025831bc9edd6adbaa1e` |
| 本轮 ARM 实验 | `codex/arm-coalesced-layout`；交接前结果头为 `3c5502c9a2feee40dbceac8f707718dfd2e52b7f` |
| 本轮最快 12 列的编译源码 | **`820918fa6e029246515e77b885c99d10696f74c6`**，原布局，`LQCD_ARM_WILSON_PACKED=0` |
| 打包 B 编译源码 | `c5528663bfb4d94345baef43e1d88ce0ba84ad18` |
| 本轮干净独立工作树 | `C:/Users/lwb/.cache/mg-coalescing-20261115` |
| 最快版本冻结源码备份 | `C:/Users/lwb/.cache/mg-coalescing-best-820918f.tar`（只读，SHA256 见 best-known.json） |

本交接文档同步到主分支**不表示实验实现已合入主分支**。本轮没有推广打包为生产默认。
需要恢复测得的最佳版本时检出 `820918f`，不能用最新实验分支 HEAD 冒充该测量版本。

主工作区 `C:/Users/lwb/Documents/ChatGPT/multigrid.cpp` 另处于
`codex/fine-site-balance-20261115`，交接时有未提交的 `docs/灵晟测试报告.md`。
这是其他工作，未纳入本轮提交。后续先检查 `git status`，不得覆盖、reset 或顺手发布。

项目入口：公共 ABI `include/lqcd.h`；生命周期/布局 `src/runtime/`；共享算法
`src/solver/native/`；硬件核 `src/backends/arm/`、`src/backends/x86/`；
绑定 `bindings/lqcd_cpu/`，`PYTHONPATH` 指向 `bindings`。文档在 `docs/`，不要在根目录堆文件。

## 3. SSH 已修好

- 当前 `ssh ls` 指向 `10.44.9.4:22`、账号 `nsls_lwb`；2026-11-16 实测登录 **login02**，多次连接成功。
- 同一入口曾登录 login09/login06；节点公钥不同。本地只保存一个公钥导致反复 `HOST IDENTIFICATION HAS CHANGED`。
- 本次通过已认证的 h20 SSH 取回其现有 `~/.ssh/known_hosts_ls`（10 个已保存登录节点公钥），当前服务端公钥与其中记录吻合。
- 本机 `C:/Users/lwb/.ssh/config` 的 `Host ls` 新增 `UserKnownHostsFile ~/.ssh/known_hosts_ls`；仍为 `StrictHostKeyChecking yes`、`UpdateHostKeys no`。
- 本机专用公钥文件为 `C:/Users/lwb/.ssh/known_hosts_ls`；配置备份为 `config.bak-ls-pool-20261116112351`。其余 Host 配置未改动，已比较验证。
- 后续若出现不在可信列表的新公钥，重新核验，不能关闭严格检查或无条件接受扫描结果。
- h20 的 `ls` 旧反向通道 `127.0.0.1:24495` 本次拒绝连接；当前使用本机 VPN 直连。
- 不在文档/GitHub 保存密码、私钥或整份私人 SSH 配置。

## 4. 最近真实结果：24³×64

机器 cn19672；16 MPI，setup 37 / solve 32 线程，块 `6,6,6,4`，每批 2 列；
质量参数 `-0.277`，Clover 系数 `1.160920226`，seed `1024`。一次 stout：
`steps=1, rho=0.125, dir_ignore=4`；此实现方向编号为 0–3，`dir_ignore=4` 表示四方向均参与。
表中为首次预热之后两次样本的中位数，单位秒：

| 实现/编译源码 | 1 列纯求解 | 12 列纯求解 | 12 列 API |
|---|---:|---:|---:|
| 原布局前测，820918f | 1.303801 | **14.122205** | **14.591878** |
| 打包 A，同一 820918f 二进制 | 1.288674 | 14.402341 | 14.874289 |
| 原布局回测，同一 820918f 二进制 | 见 JSON | 14.486748 | 14.992009 |
| 打包 B，c552866 | 1.330043 | 14.777751 | 15.264690 |
| B 同一二进制，稍后原布局 | 见 JSON | 15.868849 | 16.358183 |

最佳版本首次/第二次完整 12 列纯求解为 14.707697 / 14.122920 秒，最快稳态样本
14.121491 秒；setup 205.552 秒，stout 3.513 秒。它们是本轮测得值，不是跨节点速度保证或全局最优。

精度是**混合精度**：内部主要迭代/MG 热数据 FP32，可靠更新及完整真实残差 FP64；
外部数组 complex128。各组保存的单列及完整 12 列由独立标量 `multigrid` 逐列检查，
最大残差约 `4.82e-9`。没有额外 API correction solve；这不表示内部没有可靠更新。
输出 lex 文件 shape 为 `(64,24,24,24,4,4,3,3)`；默认 PyQUDA 奇偶布局兼容接口也保留。

**结论：保持原布局为本轮最佳。** A 的前后原版漂移 2.548%，A 相对其均值慢约 0.684%。
B 的稍后原布局跑在 B 完成约一小时之后，中间排队；仅这组迟到对照显示 B 快约 6.876%，
但缺少相邻、平衡的时间对照，不能宣称稳定布局收益或断言差异全部由节点状态造成。

记录目录：[experiments/arm-coalesced-layout-20261115](https://github.com/WanbaoLi/multigrid.cpp/tree/codex/arm-coalesced-layout/experiments/arm-coalesced-layout-20261115)。
重点读取 `best-known.json`、`summary-A.json`、`result-B.json`、`result-B-original.json`、
`followup-complete.json`、`codegen-A.json`、`codegen-B.json`、`vector-lengths.json` 及 README。
`followup-pending.json` 是历史排队快照，已被完成记录更新，不代表当前阻塞。

作业：2135942（SVE 向量长度）、2136318（A/原版续跑）、2136624（B）、2137061（B 后原版）
均 SUCCEEDED。2137061 实际运行 **2026-11-16 01:03:10–01:10:27**。
2135811 在原版通过后为复用二进制而主动终止，调度器 FAILED 不能当成数值失败。
上述本轮作业均已结束，无需继续监控或重提。

## 5. 本轮做了什么及不应误判的地方

- **原来已有重排**：自旋场为 `[聚合块][24 个实分量][块内格点]`，奇偶各占半块；
  24 来自 4 自旋 ×3 颜色 ×实/虚两部分。不是直接按 LIME 文件顺序算。
- 原矩阵为 `[聚合块][144 实平面][格点]`。A 将进程拥有的规范场、Clover、Clover 逆额外打包为
  `[聚合块][16 点小块][144 平面][16 点]`；一次 setup 打包，KUPL 分配/验证实际使用的打包热数组。
- 仍保留 raw 回退；C24 额外普通存储约 1.42 GiB/节点，热数组继续受原有 1 GiB/rank 预算约束。
- B 将局部/全局及 Clover/hopping 分派改成编译期模板，数学和布局不变；本次 A/B 输出哈希相同。
- 核心文件：`src/backends/arm/wilson_sve.hpp`；`src/solver/native/{hierarchy.*,fine_operator.cpp,batched_fine_operator.cpp,hbw_assets.cpp,kernels.hpp}`。
- 两次编译均过 34 项选定 CTest，含实际启用 packed 的 MPI2/batch12；核测试另过 16/32/64 字节 SVE 长度 ×投影复用开/关共 6 组。
- 当前硬件实测 SVE 为 64 字节，每向量 16 个 float。部分时间面范围不对齐：216 点区间 `[108,324)`
  原版 14 个向量段，打包版 15 段；完整分割块为 56 对 58 段。此为代码段数，不是耗时百分比。
- 反汇编显示 B 全局分派入口栈帧从 400 降至 256 字节，但局部 Clover 仍 400 字节。
  符号大小含不同分派分支，不等于动态指令数；不能据此认定寄存器溢出是主因。
- 所选 SVE 符号未见融合乘加指令；未测内存控制器带宽，**尚不能量化算力/HBW 峰值利用率或确认计算/访存受限**。
- 历史 profile150 两个 rank 有较高 GOMP 用户周期样本；当前诊断 SAP/粗层仍重要。
  阶段计时是 rank0 局部累计，不能当全节点周期占比；batch2 共享计时只能计一次。
- ARM 跨 RHS 的小块融合尚未实现。全场 SoA→AoSoA、融合乘加、减少地址开销和同步均是未完成候选，不能称所有优化已穷尽。
- `LQCD_ARM_SVE_PLANNED` / transfer 向量化历史上无稳定端到端收益；不应无机制地重复扫开关。

## 6. 灵晟路径与可复现入口

远程根目录：`/home/share/nsls_lwb/lqcd-run/arm-pack-20261115/`。

| 位置 | 含义 |
|---|---|
| `source/` | 冻结 820918f，不要修改 |
| `run01/baseline-a/build/` | 最佳已测库及独立参考；哈希见 best-known.json |
| `source-c552866/` | 冻结 B 源码，不要修改 |
| `run02/packed/`、`run02/baseline-b/` | 复用 820918f 构建的 A 与原版结果 |
| `run03/` | B 的构建、CTest、L24 结果 |
| `run04/baseline-b/` | B 同一二进制关闭打包后的已完成结果 |

24 组态：
`/home/share/nsls_lwb/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime`。
输入 SHA256：`47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30`。
大数组验证后已删除，不在 Git 中；原始日志与构建保留在远程运行目录。

以下为**手动复现示例，不要因读到文档就提交**。在灵晟登录节点，使用干净的目标版本，
将 `c24-replay-NEW` 换成一个不存在的输出目录：

```bash
cd /home/share/nsls_lwb/lqcd-run/arm-pack-20261115/source
git status --short
git rev-parse HEAD   # 必须为 820918fa6e029246515e77b885c99d10696f74c6
LQCD_HEALTH_GEOMETRIES=24 bash tools/health/submit_ls.sh \
  "$HOME/lqcd-run/c24-replay-NEW" \
  "$HOME/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime" \
  "$HOME/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime"
```

第三个位置为 C32 参数占位；只选 24 时不会运行它。脚本申请独占 592 核/480000 调度器 MB，
在计算节点构建、CTest、求解和独立验证；**不要在老登录 CPU 上 `-march=native` 编译**。
SDK 为 `/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001`，Python 为
`$HOME/.cache/multigrid-arm-20261025-env/bin/python`；加载和编译命令已在 health 脚本中。
本轮 profile 为 `profiles/optimization/lingsheng-shared-uniform.json`。

实验 profile：`lingsheng-packed-coefficients.json`。实验重放/续跑工具位于 `tools/optimization/`：
`run_arm_packed_comparison.sh`、`run_arm_packed_reuse.sh`、`summarize_arm_packed.py`、
`check_sve_lengths.py`、`inspect_arm_wilson_codegen.py`。复用构建须检查同节点、同源码和哈希；
`LQCD_LAYOUT_CASES=baseline-b` 支持只补原版对照。静态环境开关在进程内缓存，不能在同一 live context 里随意切换 packed。

## 7. 更早结果、x86 与 C64 边界

- AMD node5005 是 **AMD EPYC 9755 128-Core ×2**。正式历史比较源为 `efe57de`，见
  [单节点报告](single-node-health-20261113.md) 和 `experiments/single-node-health-20261113/`；不要混淆纯求解/API。
- x86 的 `tools/x86/build.sh`、`test.sh`、`test.md` 可用，但旧 test 默认 8 MPI，
  **不是用户后来要求的固定 16 MPI 配方**。正式 16 MPI 比较使用 health 脚本；历史为 placement/setup 16、solve 12 线程，勿写成灵晟的 32。
- 在已分配的 node5005 上，自动构建/CTest/真实验证入口为：

```bash
bash tools/health/run_single_node.sh x86 \
  "$HOME/.cache/mg-health-replay-NEW" \
  /public2/home/lwb_720/lqcd/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime \
  /public2/home/lwb_720/.cache/mg-health-20261113/inputs/beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime
```

- C32 的规范场文件名是 `beta6.20_mu-0.2790_ms-0.2400_L32x64_cfg_10000.lime`，灵晟旧位置
  `$HOME/multigrid.cpp/data/C32P23/`；复现前确认可读。C32 使用块 `8,8,8,4`、16 MPI、残差 `1e-8`。
  本轮 packed 没做 C32 实输入性能验收，不能把 C24 结论直接外推。
- 灵晟旧 C24/C32 API 中位数为 14.853 / 63.850 秒；x86 为 6.216 / 29.989 秒，均为 2026-11-13 历史记录。
- C64 原始 F64P14 已传灵晟：
  `/home/share/nsls_lwb/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime`；
  19327493608 字节，历史校验 SHA256 `30790de7907dc66a6555bd62fb276d365aceedb07cb9eb3bc7e567847a250183`。
- **没有 C64 成功 setup 或预热后 1/12 列时间**。两节点任务 2125108 在建层时失败，峰值内存压力高、MPI daemon 丢失，未见明确 OOM 证据，不能写成已证实 OOM。
- halo 页复用候选在 `codex/c64-halo-pages`（10864b2），尚未在目标机编译/数值验收，不能当可用最佳版本。
  详情 `experiments/distributed-C64-20261114/README.md`。
- 用户要求超过现有节点资源就停，让其申请。不要自行重提更多节点 C64 作业；四节点是历史预测候选，不是成功测量。
  16/128 节点愿景还需要空间 MPI 分解，不能只增加当前时间切片的 rank 数。
- 调度器单位须核对：本次观测其 MB 按 MiB 解释，480000 对应约 468.75 GiB；旧记录的约 458 GiB 换算不应继续使用。
- 申请用报告为 `docs/灵晟测试报告.md`；本地主工作区另有未提交版本，需用户/所属任务自行整合。

## 8. 后续建议与终止状态

本对话没有遗留需监控的本轮作业。SSH 可用，测试结果已归档，最快正确版本及原始数据来源已保留。
若用户要求继续：先读本文件、AGENTS.md、本轮 README 和只读 skill manifest，再确认 checkout/资源。
冻结参考在 `skills/kunpeng-lqcd-reference/`，保持只读；SDK 的 KUPL 分配 API 是已核验的旧版本接口，不能抄新手册签名。

下一步首先解决测量漂移：同一分配、同一二进制、平衡顺序的原版/候选，记录实际亲和性、HBW 驻留、迭代与校正。
再以当前完整求解 profile 决定是否做跨 RHS tile 复用、范围对齐、算术指令或 OpenMP/粗层同步改进。
本轮数据不证明“带宽已打满”，也不证明“全程序一定计算受限”。读到本文件不构成新资源申请或新任务的授权。
