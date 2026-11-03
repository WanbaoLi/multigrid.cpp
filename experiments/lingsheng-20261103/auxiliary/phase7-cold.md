# 新层次完整12列的独立验收：准备版本，未部署

`phase7_cold.py` 将新层次首次完整12列放入单独的cold选择记录。现有warm campaign
继续以 `full12_api` 排名，其 `best.json`逐次校验、从不修改。两种指标分别保留，
不会把约15秒的层次复用求解称作包含约200秒建层的首次总时间。

输入是两份已经由现有框架构建、CTest和独立完整12验证的ledger attempt。候选可以
是measured而未promote的版本，因此建层加速不需要先在warm API产生3%收益。
`--candidate-tests`明确指出匹配source manifest和实际动态库字节的CTest build。
仅这一条已知构建产物入口会把CMake的`liblqcd_cpu.so`版本链接解析到实际文件，
并要求实际文件仍在同一个canonical build目录内。contract同时记录逻辑路径、
实际路径、build目录和SHA；input/gold/source及父轮artifacts路径仍保持原strict规则。
源码构建和 `--source-from` 复用继续由已有 `trial.py` 完成；本控制器不选择算法、
不修改或编译数值代码。当前冻结protocol4要求两份源码的Python bench/helper保持
已核对字节；从711基础只修改C++的候选满足此条件。

控制器先复用trial.py分别启动warm控制A、候选、控制B，各一次完整12预热及3次稳态，
每组都做原v4独立12列校验。随后用7个全新进程/上下文/层次按顺序执行：

```text
baseline0 → candidate0 → candidate1 → baseline1 → baseline2 → candidate2 → baseline3
```

候选3次、基线4次，最后一份是closing control。每份从相同canonical fixture读取、
规范场全字节校验、context/load/clover、setup直到首次完整12列，由一只连续时钟测量。
不清除OS页缓存，也不声称物理存储缓存冷启动。输出、独立验证、源码检查及Python/MPI
启动沿用原cold边界。每份独立scalar残差上限1e-8、全部12列gold相对差上限1e-6；
所有源/库、输入、配置、rank/NUMA masks、同主机同allocation和protocol4终态都复核。
不复用092未发布或失败的冷样本。

新自产prop只在计时外用 `phase7_cold_entry.py` 的新发布边界；详见
`phase7-publication.md`。输入、gold及发布后的v4验证保持原strict。每次新样本保留
首读失败/进度/终态收据，原expected和旧失败记录不改。

采用门：cold中位耗时至少下降3%，全部样本范围分离，极差/中位数不超过10%，基线
首尾以及前两份/后两份中位漂移不超过5%。warm候选最慢样本必须不超过两份控制
最快样本的102%，各组噪声及前后漂移也须合格；仅median持平但不确定度覆盖退化
时不采用。placement/setup/solve线程、rank数、batch、block和seed固定。

还需要显式同allocation runtime证明：在匹配warm进程setup阶段实际观察rank0/8的
GOMP、MPI、C++、libc maps及SHA，source/lib/configuration与两份parent对应，并核对
loader环境和库文件未变。可以复用phase5 SetupObserver在warm计时开始前采集；
本准备版本尚未自动整合observer。没有证明时仍保存全部样本和精度，但状态为
`pending_runtime`，不晋升。不谎称每个cold PID都采过图。runtime证明示例结构：

```json
{
  "complete": true,
  "host": "cn19483",
  "allocation": "实际新作业标识",
  "scope": "separate warm-process rank0/8 maps; cold loader environment pinned",
  "parents": {
    "baseline": {
      "library_sha256": "实际baseline动态库SHA",
      "configuration": {},
      "loader_environment": {"LD_LIBRARY_PATH": "实际路径", "LD_PRELOAD": null,
        "OMP_WAIT_POLICY": null, "GOMP_SPINCOUNT": null},
      "ranks": [{"rank": 0, "captured_during_setup": true, "task_owned": true,
        "libraries": [{"path": "/实际映射库路径", "sha256": "实际文件SHA"}]}]
    },
    "candidate": {}
  }
}
```

示例省略字段不能作为有效证明：实际两份parent都需要完整configuration、rank0和8、
四个runtime家族及真实SHA；设置过的已验证libgomp preload等必须反映实际环境。
不得手填布尔值冒充观测。

实际运行示例，所有ID和路径须替换为新allocation的已验证选择：

```bash
python phase7_cold.py --root ROOT --campaign ROOT/campaign --tools-project ROOT/source \
  --auxiliary ROOT --fixture CANONICAL_FIXTURE --reference FROZEN_SCALAR \
  --extractor FROZEN_EXTRACTOR --baseline BASELINE_ID --candidate CANDIDATE_ID \
  --candidate-tests CANDIDATE_BUILD_ID --prefix NEW_PREFIX --backend arm \
  --expected-host cn19483 --runtime-proof ACTUAL_RUNTIME.json --experience EXPERIENCE.md \
  --store ROOT/cold-selection --execute --adopt
```

省略`--execute`仅输出协议，不运行。必须在已有owned worker task中执行，并继承真实
allocation和safe deadline。未开始组要求至少7150秒，按Arm已观测的每个完整warm
进程约650秒、baseline cold进程650～700秒，计算3份warm、7份cold及300秒reserve。
这些进程成本已包括源码/输出读取和严格独立精度验证，不仅是native建层或API时间。
每cold开始还要求1400秒，
普通阶段850秒、验证450秒。不能把理论相加当可靠ETA。预计整个最小组超过一小时，
应安排新allocation，而不是混用跨作业控制。stage时间预算不足时保留pending状态。

每次propose先读取ledger和可写经验，保存阅读回执；源码使用snapshot_from保持精确
父版本。通过阶段按原命令恢复，不重复计算；failed/running/interrupted阶段不自动
重试。先用原campaign显式归因恢复；若warm child已通过但主控制器中断，可在确认
精确tag无存活进程后用`--resume-reason`认领完成检查点。同一组换主机、allocation、
源码或helper一律新epoch。原有failed阶段/日志不删除、不改为passed。

所有门通过且`--adopt`时，只更新独立store的`best-cold.json`，保留实际.so、不可变
accepted state快照和best历史。rollback命令只接受曾被采用的历史记录及明确原因：

```bash
python phase7_cold.py rollback --store ROOT/cold-selection \
  --record ROOT/cold-selection/best-cold-history/ACTUAL_RECORD.json \
  --tools-project ROOT/source --auxiliary ROOT --reason '实际回归证据'
```

10项cold验收/rollback合约在WSL全部通过，Windows9项通过、1项实际Linux链接测试跳过；
涵盖已观测预算、真实CMake两级版本链接及目录逃逸拒绝、精度/源身份/跨allocation/
时钟/样本数、cold漂移/噪声/范围/门槛、warm非退化不确定性和历史二进制损坏拒绝。
数值/HPC条件尚未运行验证；该版本需经root评审、冻结SHA后才能部署。
