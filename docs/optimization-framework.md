# 灵晟完整传播子优化框架

框架复用现有 CMake/CTest、`tools/run_numa.py`、生产 Python 接口和独立标量参考。
`tools/optimization/campaign.py` 是只依赖 Python 标准库的实验账本和执行器；它负责
冻结证据、运行有界命令、保留失败、恢复断点和选择最佳正确版本，不自动猜测数值代码。
每一轮仍由真实 profile 提出修改，再以完整 12 列传播子的实际公共 API 墙时验收。

用户于 2026-11-04 明确实际工作负载：一个组态建立一次多重网格层次，随后复用它
求多个源点。因此首要指标是已建层情况下，一个源点完整 12 列的公共 API 墙时。
一次完整 12 列预热之后，比较至少三次完整 12 列样本的中位数，并继续执行原有
精度、前后控制、漂移和噪声门。读入、建层、首次 12 列及写文件分别报告；建层
加速不能单独触发求解最佳版本的替换。机器可读的本次决策及后续实验顺序见
`experiments/lingsheng-20261103/reuse-objective-20261104.json`。

当前冻结真实组态基准在同一层次上重复求原点源，每列仍从零初值开始。这可以比较
固定问题的重复求解成本，但尚不证明多个不同源点的性能或精度。不同源点应另开
明确记录坐标的验收组，对照两端使用相同坐标和顺序；每个源点的全部 12 列均须
独立计算双精度残差，参考解也须匹配该坐标。不得把原点参考解套到其他源点，
也不得用平移传播子代替实际求解。保留现有冻结基准及历史报告的原始身份。

## 三类独立资产

1. **只读参考 skill**：官方 KUPL/KML、Arm 指令与架构约束、经过核对的安装库信息。
   建立后冻结；初始化记录每个文件的 SHA256，后续每次操作重新核对。经验不得追加到
   参考目录。文件权限只防误写，逐文件校验防止误用已经变化的参考。
2. **可写经验与计划**：实验假设、历史链接、归因和重试条件。每次提案必须先运行
   `history`，使用这次读取的摘要令牌。历史改变后令牌失效。重复失败/无结论的同一
   假设必须注明 `retry_of`，说明条件发生什么变化。
3. **实验目录**：每次提案独立保存源码快照、构建目录、命令与日志、普通计时、
   profile、精度报告和被冻结的实际动态库。最佳版本只由原子更新的指针选择，回滚
   不修改工作树、不删除失败实验、不覆盖旧二进制。

推荐把 campaign 放在仓库外的独立磁盘目录，或仓库 `.cache/` 内。大组态和传播子
保持独立路径，不提交 Git。每个 campaign 对应一套输入及独立参考程序；ARM/x86 可
各有 campaign，最终比较表须匹配物理输入、精度和计时口径。

```text
CAMPAIGN/
  campaign.json                 目标、输入/参考哈希、固定误差及决策标准
  history-read.json             最新历史阅读回执
  events/*.json                 逐个原子写入的事件；保留失败及回滚
  best.json                     当前最佳正确版本及前一个版本
  best-history/*.json           历次最佳指针
  attempts/ID/
    attempt.json                假设、状态、命令断点和全部重试记录
    source-manifest.json        Git HEAD + 每个源码文件的内容哈希
    source.diff                 相对 HEAD 的二进制安全 diff
    git-status.txt              staged/unstaged/untracked 状态
    source.tar.gz               实际工作树源码；含未提交新文件和删除项清单
    source/                     冻结源码的构建输入
    build/                      该轮独立构建目录
    STAGE-NNN.log               每次运行的独立日志
    report.json                 通过入口校验的完整 12 列报告
    artifacts/liblqcd_cpu.so     实际测量的库，按 SHA256 冻结
    seal.json                   封存时所有文件的哈希
```

`source.diff` 包含相对 HEAD 的 staged/unstaged 跟踪文件变化；未跟踪文件内容由
源码快照保存。Git 忽略的构建输出不进入源码快照。源码必须是普通文件，遇到符号
链接明确拒绝，防止快照引用外部可变数据。编译必须使用 `source/` 并把生成文件放在
`build/`；不要在冻结源码内运行格式化或生成器。Python 自身生成的缓存文件不计入
原始源码清单，受跟踪文件仍逐次复核。

## 初始化与记录假设

以下命令中的 `CAMPAIGN`、`REPO`、`SKILL`、`INPUT_SHA`、`REFERENCE_SHA` 都是示例
占位值：分别替换为实验根目录、仓库目录、冻结参考 skill 目录、组态 SHA256 和
独立标量参考可执行文件 SHA256。SHA256 是文件内容的 256 位摘要。

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN init \
  --repo REPO --reference-skill SKILL --input-sha256 INPUT_SHA \
  --reference-sha256 REFERENCE_SHA --baseline-commit HEAD

python tools/optimization/campaign.py --campaign CAMPAIGN history > history.json
```

读取历史后创建提案 JSON，并填入 `history.json` 返回的 `history_read_token`：

```json
{
  "bottleneck": "记录 profile 文件及具体热点，区分采样占比和墙时",
  "hypothesis": "说明哪个可验证机制正在限制完整求解",
  "change": "本轮准备改变的唯一主要因素",
  "mechanism": "为何能减少搬运、计算、同步或暴露的通信时间",
  "history_links": ["docs/kunpeng-hpc-optimization.md", "上一轮实验目录/profile.json"],
  "retry_conditions": "失败后何种证据或条件变化值得重试",
  "history_read_token": "填入实际历史摘要"
}
```

首次基线也须提案，描述测量和复核目的。重试可增加 `"retry_of": "前轮ID"`，
并把 `retry_conditions` 写为本次实际变化；不能把“再试一次”当作归因。

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN propose baseline --proposal proposal.json
python tools/optimization/campaign.py --campaign CAMPAIGN snapshot baseline
```

快照返回 `source_manifest_sha256`，必须原样写进测量报告。基线提交只是起点，不把
未提交修改伪装成基线代码；归档保存实际文件。每轮独立快照后再构建，禁止边编译
边修改同一快照。源树、库和输入内容同时记录，路径名称不能代替版本证据。

仓库 HEAD 前进、或换到新节点后，需要重新测量冻结的最佳版作为控制。不要为此
回退工作树或把旧二进制标记为当前新源码。先正常阅读历史并提案，再执行：

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN snapshot fresh-control \
  --from-attempt accepted-best
```

这会逐项复核父轮的完整报告、独立精度证据、源码和实际库，将已冻结的源码清单及
归档按原字节复制到新轮，保留原 `source_manifest_sha256` 和 Git HEAD。新轮得到独立
源码位置和空构建目录，记录 `origin_attempt`、父报告及父库摘要，但不继承测试或
性能通过状态。父轮可以是正确且完整的已验收版本，也可以是已独立验证的测量控制。
新轮仍须重新测量与验证；候选随后用 `--against fresh-control` 比较。该操作不会
改变当前仓库 HEAD 或文件。中断产生的半份复制保留以供检查，需使用新的实验 ID。

## 有界运行、中断恢复

运行命令使用 JSON 参数数组，不拼接 shell。`{source}`、`{build}`、`{attempt}`、
`{campaign}`、`{repo}` 会替换成绝对路径。环境变量只在该子进程内覆盖。

```json
{
  "argv": ["cmake", "-S", "{source}", "-B", "{build}", "-DCMAKE_BUILD_TYPE=Release", "-DLQCD_BUILD_RUNTIME=ON", "-DMULTIGRID_NATIVE=ON"],
  "cwd": "{source}",
  "env": {"OPENBLAS_NUM_THREADS": "1"},
  "timeout_seconds": 300
}
```

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN run baseline --stage configure --command configure.json
python tools/optimization/campaign.py --campaign CAMPAIGN run baseline --stage build --command build.json
python tools/optimization/campaign.py --campaign CAMPAIGN run baseline --stage ctest --command ctest.json
python tools/optimization/campaign.py --campaign CAMPAIGN run baseline --stage benchmark --command benchmark.json
```

编译器/MPI 必须由实际计算节点的一致工具链提供；沿用站点脚本设置 CPATH、运行库
和 `CMAKE_*_COMPILER_LAUNCHER`，不要在登录节点做 `-march=native` 构建。线程和
NUMA 放置继续使用 `run_numa.py`，而不是在账本中复制一套启动逻辑。

执行器在启动子进程前写入 running 检查点。成功阶段相同命令再次执行只返回旧结果，
不重跑；不同命令须换阶段或新实验。超时和 Ctrl-C 会终止自己的进程组并保留日志。
被强制杀死/调度终止后若仍是 running，不自动认定失败或重新运行。先确认旧进程或
作业已经结束，再显式 `--retry-interrupted --reason '具体证据'`；失败或超时后用
`--retry-failed --reason '归因与改进'`。同主机检测到旧进程仍存在时拒绝重复启动。
跨主机共享目录时，操作者须核对调度器和旧主机 PID，账本不猜测远端进程状态。

Linux 清理不能只给最外层进程组发信号：CMake、MPI、阶段执行器和 perf 可能启动
新的 session。worker 在用户环境覆盖之后生成唯一 `LQCD_OPT_TASK_ID`，每个阶段
再生成唯一 `LQCD_OPT_STAGE_ID`。清理器只选择相同 UID 下具有精确标签的进程，或
已经验证的父子进程；发信号前核对 PID 的启动时间，不根据程序名匹配，也不输出
环境内容。它重复扫描 `/proc`，先 TERM、等待，再 KILL，并通过 Linux subreaper
回收已接管的孙进程。记录包含目标 PID、信号数量及存活 PID，不包含环境变量内容。
阶段直接收到 SIGTERM 时写入 interrupted 检查点，清理其独立 session 中的后代。
若仍有可观察的所属进程存活，状态为 cleanup_failed，队列不启动下一项，running
声明保留。重启 worker 时遇到遗留 running 声明也拒绝自动继续；必须先核对状态、
所属进程和调度器，再明确处理旧声明。SIGKILL 不能被进程捕获，遗留检查点正是其
恢复依据。Windows 继续使用 taskkill 的进程树回退，Linux 的跨 session 保证须在
Linux 上运行生命周期测试验证。

`.lock` 由写操作持有，防止同一 campaign 并发更新。进程异常终止遗留锁时先检查
锁内 host/PID 和阶段，确认没有活跃控制器后用 `unlock --reason '证据'`；本机
仍存活的锁持有者不能解锁。不要删除日志来“恢复”。

## 完整 12 列报告的验收契约

测量器应先在独立运行取得 profile，再在不带外部 profiler 的条件下测普通性能。
每个配置至少一次完整 12 列预热、三次完整 12 列稳态样本；保留首轮、全部后续
样本和每列统计。前后对照采用同一节点/作业中的交错顺序，避免只取一次最快值。
每列均从零初值开始，物理规范场、质量、Clover 系数、边界、平滑和容差不变。

只接受下面的结构。`samples` 中必须实际有 12 个逐列 `stats`，此处省略重复项
仅为说明格式；缺少任何列、`complete=false`、没有独立验证或只有局部内核时间均拒绝。

```json
{
  "complete": true,
  "timing_scope": "full12_api",
  "zero_initial_guess": true,
  "input_sha256": "实际组态摘要",
  "source_manifest_sha256": "本轮快照摘要",
  "library_sha256": "实测库摘要",
  "library_path": "/实际存在的/liblqcd_cpu.so",
  "comparison_key": {
    "host": "实际计算节点",
    "allocation": "同一作业ID",
    "problem": "物理参数、源、预处理和输入摘要",
    "scope": "相同完整12列API计时边界"
  },
  "configuration": {"ranks": 16, "threads": 37, "batch": 2},
  "samples": [{
    "repeat": 0,
    "warmup": true,
    "wall_seconds": 24.0,
    "stats": [{"converged": 1, "true_residual": 4.8e-9, "iterations": 24}]
  }],
  "verification": {
    "complete": true,
    "passed": true,
    "columns": 12,
    "reference_sha256": "冻结独立参考可执行文件摘要",
    "max_true_residual": 4.9e-9,
    "solution_relative_error": 1e-7
  }
}
```

真实输入和参考必须是 64 位十六进制字符组成的 SHA256。报告中每个 repeat ID 唯一，
`warmup` 明确为布尔值，所有时间/误差必须有限。真实相对残差上限为 `1e-8`，即
十的负八次方；如有参考解，相对解误差上限为 `1e-6`，即十的负六次方。不能用
候选自身的单精度算子作为独立参考。修改数值内核还应先运行相应 CTest/oracle，
覆盖随机源、非平凡规范场、奇偶、尾部、alias、归一化和 MPI 边界。独立逐列验证
负责真实组态的完整算子残差；CTest 记录保留在该轮阶段日志中。

数值残差通过后仍须核对文件身份：独立脚本报告的传播子摘要必须与测量完成时
保存的摘要一致，十二个自旋/颜色源必须唯一。身份不一致时保留独立输出，禁止
发布精度通过状态；ledger 也拒绝摘要相互矛盾的报告。诊断适配器若在末尾审计
失败，阶段退出码仍是失败，不能仅凭中间JSON的complete字段判断整轮通过。

独立验证若中断或在末尾哈希复核失败，原 `independent/` 目录完整保留，默认命令
拒绝覆盖。检查失败原因后可显式重试到新目录，例如：

```sh
python tools/optimization/bench_full12.py --verify RUN --reference REFERENCE \
  --extractor EXTRACTOR --verification-output independent-retry1
```

`RUN` 是原完整测量目录，`REFERENCE` 和 `EXTRACTOR` 仍是同一冻结标量参考程序和
列提取器。新目录名只允许单级小写字母、数字、下划线和短横线。整个固定 12 列
流程及原文件/参考程序的前后哈希检查重新执行；不会修改预期传播子 SHA256。
报告记录 `verification.evidence_relative_path` 和本次 Python 驱动的
`verification_driver_sha256`。缓存复核按记录路径找证据，缺路径字段的旧报告
继续使用 `independent/verification.json`；绝对路径、上级跳转和符号链接均拒绝。
驱动摘要记录历史 provenance，不要求旧已接受报告由当前版本的 Python 文件生成。

`comparison_key` 是前后对照约束：同一主机和分配、相同物理问题及计时口径。
允许候选的线程数、分块、批大小、内部算法和库不同，它们记录在 `configuration`；
不得把这些值混入必须相等的比较键，否则无法比较调度优化。更换节点后必须在
新节点重新测量当前最佳版作为控制，不把旧节点的低值拿来验收新候选。

`library_path` 必须可读且实测 SHA256 一致。导入时自动复制到本轮 `artifacts/`，
随后重建/删除原路径也不会丢失最佳实现。额外字段可以记录 setup、MPI 最大墙时、
内核 profile、线程亲和性、HBW 驻留、编译器和验证日志路径。两列共享内部计时
不能相加，最终指标使用真实完整传播子 API 的最大进程墙时。

## 选择最佳版、失败归因与回滚

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN ingest baseline --report full12.json
python tools/optimization/campaign.py --campaign CAMPAIGN promote baseline --baseline

# 新候选与本轮测量的当前最佳控制版比较
python tools/optimization/campaign.py --campaign CAMPAIGN ingest candidate --report candidate-full12.json
python tools/optimization/campaign.py --campaign CAMPAIGN promote candidate --against control
```

首次 `--baseline` 仅能在没有最佳版时使用。后续 `--against` 的控制报告必须实际
使用当前最佳库和配置，可以是新作业中对最佳版重新测量的一轮。候选/控制的稳态
repeat ID 必须相同。默认同时满足以下条件才晋升：

- 各自至少三次完整稳态样本，全部精度检查通过；
- 各组最大最小时间差除以中位数不超过 10%；
- 中位数改善至少 3%；
- 候选最慢稳态时间仍小于控制最快稳态时间。

最后一项是保守的噪声门，不是统计置信区间。它可能拒绝实际的小收益，拒绝后可
增加匹配样本并归因波动，不应修改误差门或挑选最快样本。`--minimum-gain` 和
`--maximum-spread` 仅初始化时指定，改变决策标准应新开 campaign 并说明原因。

晋升未通过时，报告和日志保留。必须记录结论再选择下一次实验：

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN conclude candidate \
  --status inconclusive --conclusion '局部核快但完整求解落在波动内；粗层占比未降' \
  --evidence profile.json candidate-full12.json
python tools/optimization/campaign.py --campaign CAMPAIGN rollback baseline \
  --reason '扩展验证发现候选回归，恢复最近正确版本'
python tools/optimization/campaign.py --campaign CAMPAIGN seal candidate
```

可用状态包括 failed、rejected、inconclusive、blocked。每轮记录假设、改动、profile、
精度、性能、结论和下一次值得尝试的条件。封存后不能重新运行或追加结论；需要时
新开后续实验并引用旧轮次。回滚只允许回到曾经通过验收的版本，指针更换前仍会
复核源码、报告、二进制及参考 skill。恢复时复制被选版本的归档库/源码，不执行
`git reset --hard` 或删除其他人的工作。

## 生成下一轮可阅读的经验

`summarize.py` 复用账本的完整 12 列数值契约，读取全部轮次、阶段、原始报告和
best/rollback 事件，在账本外生成 `experience.md` 与 `experience.json`：

```bash
python tools/optimization/summarize.py --campaign CAMPAIGN --output EXPERIENCE_DIR
# 在原节点或完整恢复了源码/库归档时，可额外重算冻结资产的摘要：
python tools/optimization/summarize.py --campaign CAMPAIGN --output EXPERIENCE_DIR --verify-artifacts
```

工具只读账本，不创建历史阅读回执、不改报告、不晋升版本。输出目录必须位于账本
外；经验文件可写，再次生成会覆盖，所以正式结论仍应写入 `campaign.py conclude`。
JSON 保存每列统计、全部样本、假设/机制/重试条件、配置、输入/源码/库摘要、日志和
profile 路径、阶段失败以及最佳版本历史。Markdown 列出当前失败、blocked、中断及
缺少结论的轮次，供下一轮先读；已有提案不能因为测量结束就自动变成“已处理”。

只有已经 ingest、摘要匹配且通过完整精度契约的报告才计作完整。未导入的原始
result、diagnostic、局部算子和缺失/损坏证据不会完成计数或参与排序。噪声超过
campaign 阈值的结果保留但不排名；其余仅在相同 `comparison_key` 内按实测中位数
排列，不能用排序替代原有晋升门，也不跨主机/分配宣称硬件快慢。工具默认不重哈希
全部构建资产；需要时使用 `--verify-artifacts`。若读取过程中账本发生变化，则
保留“读取不一致”标记、取消排名并返回非零，待阶段结束后重新生成。

恢复及回滚仍使用现有 `run --retry-interrupted/--retry-failed`、`conclude` 和
`rollback`；汇总文件提供入口，不自动执行未知状态的命令。读取汇总后，提案前仍需
运行 `campaign.py history` 取得当时的历史回执。测试汇总契约：

```bash
python tests/test_optimization_summary.py -v
```

## 导出小体积只读证据包

在登录节点运行导出工具即可，无需启动求解、profile 或申请计算核：

```bash
python tools/optimization/export_evidence.py --campaign CAMPAIGN \
  --output EXPORT_PARENT/asof-UTC_TIMESTAMP --max-log-bytes 131072
```

输出目录必须是尚不存在的新目录，且位于账本、冻结源码及参考 skill 之外。默认
`--completed-only` 保留所有轮次的状态、提案与计划，但不复制运行中或尚未结束轮次
的日志和测量载荷。`--no-completed-only` 可纳入尚未结束但没有 running 阶段的载荷；
运行中的载荷始终排除。failed、blocked、中断及未 ingest 的轮次仍保留原有状态，
不能因导出变成已完成。工具不调用 `history`、`seal`、`ingest`、晋升或回滚。
交错实验的候选报告若引用父轮次目录中的独立校验，会按已 ingest 报告中的原始
`evidence_sha256` 精确定位，只补拷对应校验 JSON 和十二列日志/残差文件，不把
父轮次认定为已完成，也不复制其大数组。

`export-manifest.json` 记录每个原始绝对路径、大小、原始 SHA、导出路径/SHA、
脱敏或摘录操作、排除原因、全部轮次和最佳版本状态。源归档按内容 SHA 去重，
逐项核对归档与 source-manifest；当前最佳另保留 `best/source/` 和实测库
`best/liblqcd_cpu.so`。原始冻结参考 skill 的六个文件按 campaign 保存的摘要逐字节
复制，不修改原件。普通运行命令、环境白名单、计划、报告、逐列校验 JSON、十二列
日志和残差小文件均保留。私密环境变量值与凭据赋值会脱敏，因此原始与导出文件
摘要可能不同；不要使用脱敏副本替换原始 ledger 的证据。

默认每个日志最多 128 KiB，超限导出首尾摘录并标记；总导出预算默认 256 MiB，
可通过 `--max-total-bytes` 调整。build、其他库/构建树、缓存、原始 perf.data、
传播子和 gauge 数组不打包、不重新哈希。被排除数组的 `declared_sha256` 来自原始
报告，仅是声明；`sha256: null` 表示导出工具没有读取原始大文件计算摘要。原始
source archive 若包含环境凭据文件、数组、链接或路径越界，会明确报错而非改写
归档继续沿用旧摘要。

导出只复核已有报告契约、独立 verification 摘要、十二列覆盖及日志残差的一致性，
不重跑数值验证。`complete_review_material` 表示这些审阅材料齐备，仍应结合
`read_consistent`、错误列表及冻结源码/库条目检查；它不表示未打包数组被重新验证。
读取期间文件集合或内容变化会标记 `read_consistent: false` 并返回非零。所有中间
产物保留供诊断，待稳定时换一个新输出目录重试，绝不封存正在运行的轮次。
已 ingest 报告缺少审阅材料时，`registered_review_complete` 为 false 并返回非零；
`best_review_complete` 单独标明当前最佳的十二列精度材料是否齐备。

收到包后，可在包目录核对全部已导出文件的摘要：

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('.')
manifest = json.loads((root / 'export-manifest.json').read_text())
assert manifest['export_complete'] and manifest['read_consistent']
for row in manifest['entries']:
    if row['included']:
        path = root / row['export_path']
        assert path.stat().st_size == row['export_bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['export_sha256']
print('Exported file bytes match the export manifest; no numerical solve was run.')
PY
```

原始大数组仍在源机器上；完整数值复现使用原有 fixture/独立标量校验命令。
中断恢复和回滚继续使用原 ledger 的命令；此包不是可直接继续运行的完整账本。
只读及并发/脱敏契约测试：`python tests/test_optimization_export.py -v`。

## 停止条件与边界

每个方向先解释失败，再根据新证据进行下一版；不能一次失败即永久排除。方向表
应覆盖实测主要热点：SAP/细层、粗层与全局归约、线程调度、搬运与计算重叠、
缓存/分块/融合、多源系数复用及适用的 KUPL/KML。既有实验中的默认开关、无收益
候选和环境异常必须先阅读；新条件下重试时写明差异。

停止需要可审查证据：主要 profile 热点均已处理，剩余可消除墙时很小，或多个有
依据的后续候选持续无超过噪声的完整求解收益。缺少计算节点、参考程序、组态、
官方适用接口或独立精度条件时记录 blocked；未运行、只编译、只局部测试不能
宣称完成。这一账本不会从本地伪造远端硬件结果，也不会定时无限占用节点。

框架本身的门控与中断行为测试：

```bash
python tests/test_optimization_framework.py -v
```

这些测试使用临时 Git 仓库与人工报告验证工作流，不是 multigrid 数值正确性或
灵晟性能成绩。硬件实测与独立算子验证必须由生产程序在真实计算节点完成。

## 从实际分配派生队列

`allocation_contract.py`只读解析已完成认证的worker启动记录、其SHA绑定的
入口和调度认证文件，由入口的常量派生队列路径。它不重新提交作业、装载
OpenMP或把历史样本改成当前分配。后续依赖检查同时核对源版本、节点、
分配标识、任务通过状态和子进程清理结果。这样可以避免复制实验脚本时
漏改旧队列路径；真实159启动失败已单独保留，不能通过覆盖状态修复。

`tests/test_optimization_allocation.py`覆盖旧队列、改动入口、跨分配状态、
未完成依赖及遗留子进程等实际失效条件。新工具已在cn19480的实际启动记录
和已关闭158资格记录上验证；当前已运行的worker和封存实验保持原命令。
