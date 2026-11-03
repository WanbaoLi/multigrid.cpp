# 灵晟实验辅助程序快照（持续进行）

此目录保存本轮实验已冻结的辅助源码，按原始字节复制。它不替代通用实验框架，也不表示优化已经结束。`manifest.json` 记录每个文件的 SHA256、实际远端路径、部署相对路径和截至打包时的运行状态；`selection-manifest.json` 保留复制前后的选择过程。最终数值/性能证据由单独的 `results` 快照提供。目录名使用 `auxiliary`，避免 Windows 的 AUX 保留设备名。

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
