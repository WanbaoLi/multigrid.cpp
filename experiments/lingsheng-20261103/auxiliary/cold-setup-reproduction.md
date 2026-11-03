# 首次完整传播子、稳态传播子和 setup 诊断

这些文件位于项目外，尚未部署、排队或取得真实冷启动成绩。不能把已有约 16–17 秒的
完整 API 数字称为从原始组态开始的耗时；当前观察到的默认 setup 约 207 秒仍需独立
profile 解释。最终采用首次求解还是共享层级后的多源摊销指标，等待用户澄清。

| 指标 | 实际范围 |
|---|---|
| 既有稳态 full12_api | 同一层级上一次预热后重复求解完整 12 列；不含读取、stout、建层 |
| cold_canonical_fixture_to_first12 | 一只连续时钟：fixture 元数据/读取、实际规范场字节校验、创建上下文、load/clover、setup、设置 solve 线程及第一次完整 12 列 |
| cold_lime_to_first12 | 连续时钟另含原始 LIME 元数据、完整输入 SHA、校验读取和一次 stout；生成规范场必须匹配 canonical SHA |
| profile_cold_* | 仅供 setup 归因；带 perf 或其他诊断开销，不参与生产性能排名 |

Python/MPI 进程启动、冻结源码/库检查在冷计时之前。输出规范场与传播子、上下文销毁、
独立标量十二列复核及相对解差异检查在计时之后。各阶段分别取 rank 最大值，不能把
这些最大值相加当成连续端到端墙时。这里的 cold 只表示新进程、新上下文、新层级，
不表示清除了 OS 页缓存或存储缓存；工具从不执行 drop_caches。

原始 `solve_lime_propagator` 的 `total_wall_seconds` 不能替代上述冷指标：元数据和
完整输入 SHA 位于其计时前（已可能预热输入文件缓存），其计时尾部又包含文件写出、
关闭上下文等工作。旧 `first_seconds` 仅是 setup 完成后的首次完整 12 列 API。

## 从最终 ledger 选定版本生成编译与运行命令

使用 `prepare_best_replay.py`、`cold_full12.py`；它们保持在辅助目录，不覆盖任何运行
中的主源码。配方生成器只读 ledger，`--attempt best` 在生成时冻结当前选择，也可传
明确的已验收 ID。它复核 source/archive/library、参考程序、提取器和已有 baseline
输出摘要，保存 selection.json、单 case plan，以及安全引用的 shell 参数数组。

灵晟计算节点中，SDK/Python 路径与主 runbook 保持一致。例如准备一次新复现：

```bash
ROOT=/home/share/nsls_lwb/.cache/mg-opt-20261103
AUX=$ROOT/aux-cold
PYTHON=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
OUT=$ROOT/replay-cold-new
"$PYTHON" "$AUX/prepare_best_replay.py" --tools-project "$ROOT/source" \
  --campaign "$ROOT/campaign" --attempt best --backend arm \
  --fixture /home/share/nsls_lwb/.cache/mg-20261102/propagator \
  --gauge /home/share/nsls_lwb/.cache/multigrid-arm-20261025/configuration24.lime \
  --allocation "$LQCD_OPT_ALLOCATION" --python "$PYTHON" --output "$OUT"
# 以下为独立、顺序执行的命令；只运行当次已安排的实验，不同时启动。
bash "$OUT/build-source.sh"
bash "$OUT/run-rebuilt-cold-fixture.sh"
bash "$OUT/run-cold-fixture.sh"
bash "$OUT/run-steady.sh"
bash "$OUT/run-cold-lime.sh"
```

构建脚本在目标计算节点先确认 SVE 64 字节，再用已核对的 GCC/sysroot/HMPI、KUPL
和显式 SDK C++ runtime `-L`/rpath 配置、编译并跑 CTest；不会在无 SVE 登录节点
使用 native 编译。run-rebuilt-cold-fixture.sh 明确运行新构建库并计算其实际 SHA，
后续执行完整十二列独立校验。其余运行脚本默认使用实测最佳归档库，保持精确二进制
复现。新构建产物不自动晋升，需要新的 matched framework 实验。

node5005 上只需改变根目录、Python、campaign 和输入路径：

```bash
ROOT=/public2/home/lwb_720/.cache/mg-opt-20261103
AUX=$ROOT/aux-cold
PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python
OUT=$ROOT/replay-cold-new
"$PYTHON" "$AUX/prepare_best_replay.py" --tools-project "$ROOT/source" \
  --campaign "$ROOT/campaign-canonical" --attempt best --backend x86 \
  --fixture "$ROOT/fixture-ls-canonical" \
  --gauge /public2/home/lwb_720/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime \
  --allocation node5005-cold-new --python "$PYTHON" --output "$OUT"
bash "$OUT/build-source.sh"
bash "$OUT/run-rebuilt-cold-fixture.sh"
bash "$OUT/run-cold-fixture.sh"
```

x86 必须使用 `fixture-ls-canonical`，不能使用原先 prepared gauge 不同的 x86 fixture。
旧 epoch 的 x86 原始 LIME→stout 结果与 canonical 字节不同；raw cold 脚本如果仍然
失败，会保留期望/实际摘要及失败 JSON，并在创建求解器前停止，绝不悄悄替换场。
两架构可以先比较同一 canonical fixture 上新层级到第一次完整求解的时间。

所有运行脚本显式区分 placement、setup 和 solve 线程，读取最终 report 的动态调优
参数，不硬编码尚未最终确定的 best。普通运行不载入 perf/PMPI；若最终已验收配置
选择旧 libgomp，则只恢复该已记录 preload。每个运行后都用当前严格 bookkeeping
验证驱动和冻结 C++ scalar reference/extractor 检查十二列、最终原始文件 SHA、
`1e-8` 真残差及已有 baseline 的 `1e-6` 相对解差。失败原件保留，不自动重试。

每次冷样本都必须使用新配方目录/新进程；若要三份冷样本，重复生成三个新目录，
而不是在同一上下文中跑三遍并叫冷启动。生成器不写 ledger、不晋升版本。
生成器按冻结源中的 getenv/setting 字面量，联合已审核的 setup/细粗层/allocator
变量清单，在启动前清除未记录数值设置，再恢复显式 context。`LQCD_NUMA_NODE`、
`LQCD_OPT_*` 归属及 launcher 放置变量保留。冷 worker 对未记录 setup/缓存/数值
开关直接拒绝；selection/report 记录清理策略和源摘要，未设置值使用该源的默认值。
baseline 路径可以覆盖，但字节 SHA 必须与该报告已验证参考输出一致；新参考协议
必须另立实验，不能用任意文件替代。

## 单独 profile setup

`profile_setup.py` 复用现有 `profile_full12.py` 的 runtime evidence、perf SIGINT
flush/退出判定和报告工具，只 monkeypatch `Solver.setup`。rank 0/8 各对自身进程
采样一次 `cycles:u -F 19 --call-graph dwarf,4096`，生成 flat report；默认较低采样率
用于限制约 200 秒 setup 的 DWARF 数据量，可用 `--frequency` 明确修改。原始 setup
返回值和最终传播子保持原样。实际库 maps/SHA、线程状态、构造/load 的 cold 阶段
墙时以及 setup 前后 CPU 时间、缺页和峰值 RSS 分别保留。不把单核频率快照称为
全核时钟，不把诊断耗时当作生产冷启动或稳态收益。

在已有 launcher 内，将 cold worker 那一项替换为：

```text
PYTHON profile_setup.py --cold-wrapper AUX/cold_full12.py
  --profile-helper SOURCE/tools/optimization/profile_full12.py
  --profile-output NEW_PROFILE_DIR --diagnostic [原 cold_full12.py 的完整参数数组]
```

这里 `PYTHON`、`AUX`、`SOURCE` 代表上述已选路径；该示意不是可直接复制的 shell
命令。实际完整参数可从新生成 run-cold-fixture.sh 获取，父控制器负责审查及排队。
采样结束后仍在计时之外使用同一独立验证命令。任何 perf 启动/停止/解码失败保留
错误并返回非零，不生成假的 profile 通过。

## 分布式 setup 候选的数学风险

目前只准备诊断，不实现分布式建层。`assemble_local_block` 按源 coarse block
写入目标 block/direction；时间边界上的目标行可能由邻 rank 的源贡献。因此把
source-owned 部分构造结果当作同形 row slab 直接 Allgather 是错误的。一个需要
后续验证的方案是：各 rank 在全局形状零 stencil 中只组装自己的源贡献，然后对
该约 340 MB stencil 做 MPI_Allreduce(sum)；基矢正交化按 owned blocks 后再按
block 连续顺序 Allgather，全球 basis 约 8 GB。规模数字来自当前配置，仍需实际
profile 与内存证据确认收益。任何方案都必须比较层级内容、边界矩阵和独立 oracle，
不能仅凭 setup 计时或局部正确就接受。

本地计时/摘要契约：`python work/test_cold_full12.py -v`。这些 tiny fake fields
只检验时钟边界、完整十二列记录、canonical 不一致失败以及 profile 不排名，
不构成真实 MPI/LQCD 或硬件性能验证。
