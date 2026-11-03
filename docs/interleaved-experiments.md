# 在同一层次上比较求解策略

`tools/optimization/interleaved.py` 复用已有最佳版本的源码快照和保留库，
只比较求解阶段可以动态改变的选项。它不会重新建层、改代码、放宽精度门或
修改参考 skill。上下文创建时缓存的 SIMD、分配器或布局选项应使用独立
`trial.py` 进程，并复测匹配的当前最佳控制。

开始前先运行 `campaign.py history` 和 `summarize.py`，阅读失败归因和未结束轮次。
为每个 case 准备 `proposals/CASE.json`，解释瓶颈、假设、改动、机制、历史证据、
重试条件。case ID 同时是 ledger attempt ID；不要覆盖旧 ID。

计划示例（实际 context 必须完整复制当前最佳 report 的 configuration）：

```json
{
  "context_environment": {},
  "placement_threads": 37,
  "setup_threads": 37,
  "cases": [
    {"id": "030-control", "threads": 32, "batch": 2, "environment": {}},
    {"id": "031-sap5", "threads": 32, "batch": 2,
     "environment": {"LQCD_MG_SAP_STEPS": 5}}
  ]
}
```

第一项必须准确复现当前最佳版本，包括保留库、求解线程、绑核范围、建层线程、
batch 和全部环境选项。示例仅演示格式，不是推荐参数。若最佳版本的 setup 为37、
solve 为32，后续控制仍要保留这一区别。

在已分配计算节点内执行，路径按实际环境替换：

```bash
python tools/optimization/interleaved.py \
  --campaign /path/campaign --reuse-attempt CURRENT_BEST \
  --plan /path/plan.json --proposals /path/proposals \
  --fixture /path/frozen-fixture --reference /path/frozen-scalar \
  --extractor /path/frozen-extractor \
  --reference-propagator /path/frozen-fixture/propagator.npy \
  --backend arm --allocation SAME_ALLOCATION --repeats 3
```

所有 case 共用一次建层，逐轮交替正反顺序，完整12列预热后测至少3轮；
所有计时结束后才写大数组并逐个做独立12列校验。样本、精度、源代码和库摘要
满足 ledger 门槛后，按速度顺序尝试采用候选；噪声过大的最快项不会阻止另一个
满足全部门槛的候选被检查。只采用第一个合格候选，其余保留证据和结论。

再次执行同一命令会复用已通过阶段。修改计划、重复次数或命令不能覆盖既有阶段；
失败/中断需要 `campaign.py run --retry --retry-reason ...`，或归因后新建 attempt。
当前最佳已经改变时禁止启动新的旧版本对照组；已有组仍可审核和恢复。

报告中的 `samples` 才是本轮性能证据。旧报告顶层的 `first_seconds`、
`steady_median_seconds` 等字段可能来自 fixture 生成历史，不能参与排名。
