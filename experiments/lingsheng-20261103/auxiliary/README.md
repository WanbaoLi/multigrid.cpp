# 灵晟实验辅助程序快照（持续进行）

此目录保存本轮实验已冻结的辅助源码，按原始字节复制。它不替代通用实验框架，也不表示优化已经结束。`manifest.json` 记录每个文件的 SHA256、实际远端路径、部署相对路径和截至打包时的运行状态；`selection-manifest.json` 保留复制前后的选择过程。已完成实验的小体积汇总放在 `results/`；完整原始数值/性能证据仍由单独的导出快照提供。目录名使用 `auxiliary`，避免 Windows 的 AUX 保留设备名。

## 通用框架与本站点程序

仓库的 `tools/optimization/` 是可复用框架：`campaign.py` 管理提案、精确源码快照、命令检查点、验收和回滚；`trial.py` 执行构建/测试/完整十二列测量；`summarize.py` 汇总可写经验；`export_evidence.py` 只读导出证据。使用方法见 `docs/optimization-framework.md`，编译和两种架构运行方法见 `docs/lingsheng-x86-runbook.md`。

此目录中的 phase2/3/4/5/6/8、worker6、冷启动和 profile 程序是本次站点控制器。它们包含已审阅的节点、SDK、作业和数据路径，须配合原 campaign、实际资源及精确源码版本。旧作业号和检查点不适合作为新作业直接重跑；缺少输入、参考可执行文件或分配条件应保持阻塞。phase5/8 的本地准备和契约测试不等于硬件实验通过。

`phase3.py` 保留远端实际执行版本的原始字节；它与本地不同版本 `phase3_campaign.py` 分别记录，不能互相冒充。`diagnostics/` 保存旧失败与恢复代码，并通过清单中的 `deployment_relative_path` 记录它们原来在远端根目录的位置。复现旧恢复控制器需要保持这些原部署映射；新实验使用通用框架。

## 已冻结的读取与精度协议

`file_integrity.py` 使用只读文件描述符和显式偏移 `os.pread`；每次读取不超过剩余长度，短读按实际长度推进，中断重试原偏移。超长返回、提前结束、文件末尾后的一字节探测非空、元数据/身份变化、字节数错误或摘要不一致都会失败。OpenSSL 与独立 CPython 软件 SHA256 接收同一份不可变字节。异常字节只允许保存在新建的私有快照中。

`raw_benchmark_v4.py` 仅替换冻结 benchmark 的文件哈希回调，不改 Solver、计时器、样本、数值库或原有预期 SHA。`raw_scalar_helper.py` 先核验冻结标量辅助脚本的完整 SHA，再仅替换 `sha` 函数体；所有其他语法树节点的规范表示完全相同。原标量 C++、提取器、物理参数、边界条件、列集合和精度门槛保持不变，辅助脚本生成的证据不事后改写。

总协议完成前，发布的 `verification.complete` 和 `passed` 保持 false。只有父程序、辅助程序、全部十二列残差、参考解差异及所有最终审计都通过，才发布终态成功。087 已通过这个协议；原 057 profile 仍归属 worker5，在 worker6 上的精度恢复不会把旧计时重新标为新分配的结果。

`raw_protocol_v4.py` 提供唯一的已冻结 SHA 链，避免为每个控制器复制长命令。例如在已核验的站点辅助根目录中构造一个任务的 argv：

```python
from raw_protocol_v4 import command

argv = command(
    root=ROOT,
    entry=ROOT / "phase6_halo.py",
    entry_sha=REVIEWED_CONTROLLER_SHA,
    audit_tag="100-halo",
    python=PYTHON,
    arguments=["--prefix", "100-halo", "--profile-state", FRESH_PROFILE_STATE],
)
```

这里 `ROOT` 是辅助文件部署根目录，`PYTHON` 是已经过验证的 Python 解释器路径，`REVIEWED_CONTROLLER_SHA` 是所选控制器的完整摘要，`FRESH_PROFILE_STATE` 是本次分配中已通过验证的新 profile 状态文件。函数只构造并验证命令，不提交任务。后续任务必须在前置任务通过且清理完成后单独发布。

## 历史、恢复与回滚

不得用本地当前源码的 SHA 替换历史记录中的冻结源码清单，也不得为让旧报告通过而重新填写预期数据哈希。新代码、新读取协议、新分配或新假设使用新的记录，原失败日志、状态、报告和证据继续保留。接受指标来自完整十二列 `samples`；诊断 profile、未 ingest 的报告、局部算子耗时不能参与排名。

```bash
python tools/optimization/campaign.py --campaign CAMPAIGN history
python tools/optimization/summarize.py --campaign CAMPAIGN --output NEW_EXPERIENCE_DIR
python tools/optimization/campaign.py --campaign CAMPAIGN rollback ACCEPTED_ID --reason "已记录的回归证据"
```

中断/失败恢复继续使用 `campaign.py run` 的显式 `--retry-interrupted` / `--retry-failed` 和原因；先核实旧作业终止及所属进程清理。回滚只切换已验收版本指针，不删除实验。

## 校验此快照

```bash
python experiments/lingsheng-20261103/auxiliary/check_manifest.py
# Linux/WSL 下运行严格文件身份契约：
python experiments/lingsheng-20261103/auxiliary/run_contracts.py
```

契约测试只操作临时小文件和模拟接口，不调用 SSH、求解器或调度器。为保持原始测试源码不变，AST 测试所需的冻结辅助脚本单独放在 `multigrid.cpp/benchmarks/runtime/` 这一窄目录中。严格文件身份测试要求 Linux `os.pread`；Windows 文件时间戳观察差异会被如实拒绝，使用 WSL 运行该组。一个依赖历史 perf 文本的解析测试在未安装独立结果快照时会明确跳过；不会编造输入或把跳过当作硬件通过。

不打包科学数组、SDK、库安装、构建树、凭据或大 perf 文件。外部依赖与冻结输入/参考的身份由原 campaign 和单独的结果导出记录；本目录的代码复制和摘要校验不产生新的数值或性能验收。


## 本次扩展与真实进展

扩展清单在 `extension-selection.json`，所有新增运行源码按原始字节复制；复制前后及归档文件的 SHA256 一致。此前1ac57bc快照的62个原运行/支持文件保持原样。`phase7-preparation-manifest.json` 等准备清单保留它们当时的原始状态，不把后来的结果倒写进历史文件。

- x86 node5005：同一 f94/c30 二进制关闭/开启 source-owned setup，连续 canonical prepared 场到首次完整12列的冷启动中位数为119.8056→35.5412秒，减少70.3343%。四个关闭样本、三个开启样本全部保留，暖求解通过2%保守非回归门。全部12列独立残差与gold解误差通过；未达到暖求解3%晋升门，暖最佳指针保持原样。参见 [实际报告](results/x86-source-owned-cold/report.md)、[汇总](results/x86-source-owned-cold/summary.json)和[samples](results/x86-source-owned-cold/samples.csv)。节点没有调度器独占；这是 prepared fixture 的新进程/新层次结果，OS/存储缓存未清空，也不是从原LIME重新stout的结果。
- ARM：103已完整结束、rc0且清理通过，保留最佳052，本轮未采用候选；原100仍是失败，原38个CTest、SVE与7个steady样本通过原检查点复用。新独立验证与实际halo诊断、末端控制归入新103状态，不能把100改成成功。
- ARM source-owned：114只发布了构建/测试任务，尚无性能结论。worker7已核验部署但未提交，新分配必须重新验证资源和相应资格。flat setup诊断仅完成本地准备与合同测试。

ARM专用派生控制器、115准备项和暂停的portable phase5草稿列在 `manifest.json.pending`，没有因文件存在就打包为冻结版本或宣称完成。103闭环的小体积汇总与原100失败/新103终态在 `results/arm-main-phase6/`；完整已下载导出位于工作区 `outputs/optimization-20261103/phase6-final/evidence`，3811条included export摘要逐项核对通过，ongoing仍为true。

## 两种新文件发布协议

下列协议都使用相同的只读精确偏移读取、双SHA、完整字节数、末尾探测与稳定身份门。不可变输入、参考、gold及已有预期摘要的数据始终走原严格协议。

| 对象 | 开始前的预期摘要 | 适用边界与完成条件 |
|---|---|---|
| `phase7_cold_entry.py` / `phase7_publication.py` 的新传播子 | 尚未发布，必须为None | 仅启动时不存在的新输出，在冷/API计时结束后生成首个摘要。第一次严格读若只因mtime/ctime拒绝，持久保存收据后，以尚未发布的候选摘要进行两次完整严格稳定复读；最多三次。发布后恢复不可变数据规则。 |
| `raw_scalar_helper_derived.py` / `derived_publication.py` 的新 `gauge.bin` | 从启动时固定为canonical126d6589…，长度509607936字节 | 仅辅助验证器新建输出目录中的scratch场。第一次拒绝前内容摘要就必须等于固定预期，只允许mtime/ctime变化；保留首次拒绝和字节快照，经只读FD同步后，两次完整严格读都要匹配首次结束元数据和同一固定摘要。任何再次变化立即失败，最多三次。 |

第二种协议不会把固定摘要改成首次观察值。返回给冻结v4父程序的行是真实的最终严格成功行，行摘要覆盖完整发布过程；首次拒绝仍保留为失败。标量辅助脚本仍先核对bc441c56…全文件摘要，仅替换 `sha` 函数体，其余语法树、C++、提取器、边界条件、12列集合和精度阈值完全相同。总校验终态成功前，输出报告不能成为可验收结果。

新实验可用 `raw_protocol_derived.command()` 构造显式新阶段参数；`legacy_helper=True` 保留旧通过命令的原始身份。已经适配的 `benchmark_command()` 直接用于新阶段，不能再套一次raw controller。说明与合同见 [派生场协议](derived-publication.md)和 [冷场发布协议](phase7-publication.md)。

## 暖求解与冷启动的独立验收

暖指标是已有层次上完整12列API墙时，使用warm campaign的 `best.json`。冷指标是新进程/新层次从canonical场读取到首次完整12列的连续墙时，使用独立cold store的 `best-cold.json`。`phase7_cold.py` 要求同一冻结源码、二进制、配置、输入、参考和本次分配，四个夹持控制冷样本与三个候选冷样本、独立暖A/C/B非回归，以及实际运行库映射证明；局部setup降时不能自动替代完整冷计时或暖晋升。

新节点、新分配或源码/运行库改变时，使用新实验身份和匹配控制。缺少时间、实际映射、独立12列或前置条件时保持pending/blocked；未ingest和诊断报告不参与暖排名。冷、暖回滚分别只切换各自已验收指针，并保留旧决定。参见 [phase7用法](phase7-cold.md)。

`historical_adapters/` 保存103恢复及114发布器的原始源码/精确任务JSON。按清单的 `deployment_relative_path` 还原原部署映射后才能审核历史命令；这些代码包含旧作业和阶段身份，不能拿来覆盖或重跑已有记录。原失败、日志、快照、输入预期SHA和源码清单永久保留；显式恢复使用新阶段、新输出目录和原因，不自动重试未知/失败阶段。

## worker7与setup诊断准备

worker7要求显式 `--source` 和 `--expected-source-head`，并把相同参数绑定到调度器命令、登录认证、计算节点入口和启动状态，核对五个core tool摘要。运行库探测只在子进程加载GOMP/KUPL，父进程必须一直保留原592 CPU掩码。新源可放在独立目录；不会修改主 `ROOT/source`。原任务终止与清理确认后才可提交，细节见 [worker7说明](worker7-preparation.md)。归档中的六个 `multigrid.cpp/tools/` 文件是实际ROOT/source711的窄测试依赖，其身份由既有 `frozen-framework.json` 核验；它们不构成一个可混用的候选源码树。

`profile_setup_flat.py` 从309cd4ea…原版只增加 `perf report --call-graph none`，原始差异在 `profile_setup_flat.diff`。采样仍是19Hz的DWARF记录、仅Solver.setup、rank0/8，计时和数值调用不变。重试理由是旧092默认DWARF报告超时而flat解码约0.4秒；092保留失败。准备工具复用已冻结完整recipe的环境、NUMA、源码、库和物理参数，另生成新输出及未profile的全12列独立验证。需要真实ARM f94资格/冷实验后才可运行；目前没有新的setup热点结果。参见 [flat setup准备](setup-profile-flat.md)。


冻结的 `phase5_validation_shim.py` 与其10项合同也已收录，但运行库/线程比较尚未执行。它通过仅含旧libgomp符号链接的目录和完整 `LD_LIBRARY_PATH` 选择运行库，两个SDK控制配置保持原样；实际rank的库映射、环境和线程掩码仍是采用前的必需证据。登录节点的loader检查不算求解通过。`historical_adapters/queue_phase5_shim110.py` 从未入队，其旧100-pass依赖现在保持阻塞，不能借103完成而绕过；暂停的新版publisher仍列pending。
