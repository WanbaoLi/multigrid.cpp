# 如何阅读最终稳态验证

`phase8_final_validation.py` 尚未排队或运行。它在所有指定结构优化阶段、phase5
均完成，且 phase5 对应当前 best 后，冻结 best 指针及原始 `010-baseline`。
三份新进程按 DDR010 → 当前 best → DDR010 顺序运行；各自创建新层级，先完整
预热 12 列，再保留 5 个完整稳态样本（`--repeats 7` 可改为七份）。不重新编译，
不采样 perf，不把同一实现的新验证 ID 晋升为新优化。

示例命令需在有足够剩余时间的已分配计算节点执行，辅助脚本路径由 root 部署：

```bash
python phase8_final_validation.py --root /home/share/nsls_lwb/.cache/mg-opt-20261103 \
  --prefix 090-final --repeats 5 \
  --structural-state /实际已完成的结构优化状态.json \
  --structural-state /其他已完成的结构优化状态.json \
  --phase5-state /实际已完成的phase5-state.json \
  --experience /实际可写经验.md
```

每个结构阶段都应显式列出。控制器要求真实 worker 的 allocation/deadline/归属 tag，
开始整组至少剩余 2200 秒，各进程预留 800–900 秒；不足时记录 pending。失败或
未知运行状态保留，不能自动重跑或覆盖校验目录。明确恢复使用 `--resume` 和
`--resume-reason`；已失败的内部阶段仍需先通过已有 framework 的显式恢复流程。
本控制器的 `_trial` 仅在独立子进程中复用原有 trial.py，把 benchmark 的实际参数
补上指定 `--repeats`，不修改其文件或数值代码，不在 trial 外再套持锁的 run_stage。

最终 JSON 同时保留两种数值，不能混用：

- `historical_best_median_seconds`：best 当时晋升或验收的历史中位数，可能来自旧节点、
  分配及时间段。它用于追溯选择，不作为这次最终性能数字。
- `fresh_validation_attempt` / `fresh_final_validation`：这次新进程、新层级但完成预热
  后的完整 12 列 API 中位数、五/七份样本及范围。它是本次最终稳态数字；源码、库、
  配置和全部逐列精度记录在 `measurements` 中。
- `fresh_ddr_brackets`：同一节点/分配新测的原始 DDR010。只有两端控制与 best 的
  噪声、范围、重复 ID、最低增益和不超过 5% 的控制漂移均通过，
  `assessment.qualified_overall_gain` 才提供总体改善和加速比；否则为 null，保留
  具体原因及所有实测数据。旧 010 的历史中位数不参与这项计算。

所有新报告必须属于相同 canonical 规范场字节、当前 host/allocation 和普通
`full12_api` 范围；历史 010 的 prepared SHA 也在开始前核对。原始 DDR 两项内存
开关保持 off。每轮先读当前经验和提案，启动前清除未记录的数值/setup 设置，并
保留 worker 归属与 NUMA 资源；缓存/运行库 context 在 benchmark 进程启动前恢复。
完整十二列均执行冻结独立 scalar reference、输出 SHA 和原有精度门。

这些是共享已建层级后的稳态求解数字，**不包含 LIME/stout、setup、输出或独立
校验时间**，不能改称一次组态首次求解总耗时。首次求解和冷启动报告继续使用
`cold_*_to_first12` 的独立范围，指标偏好仍等待用户澄清。

本地协议测试：`python work/test_phase8_final_validation.py -v`；这些模拟测试不构成
真实硬件或 LQCD 精度/性能结果。

## 后续公共框架集成事项

当前 `interleaved.py` 可以交错不同 fine 线程数并自动晋升。017 的团队切换探针已
证明切换会重建 worker；022–025 中夹在 16/32 线程案例之间的 37 线程控制，也可能
包含这种历史影响。它们是当时交错协议的真实记录，024 的暂定 best 及原证据不得
追溯改写，不能据此直接认定固定生产进程的 32 线程优于 37。

phase5 必须先完成独立进程的 32→37→32（若当前为 37，则反向夹逼）及两端门控，
确认/修正实际生产 best；phase8 再验证该稳定 best。公共框架后续应拒绝把跨线程
团队的交错结果直接用于排名/晋升，或显式标记并强制提供独立进程确认。动态算法
参数仍可按定义清楚、零初值且数值对齐的同层级交错协议测试。本次仅记录集成待办，
没有修改正在使用的 ROOT/tools 或数值代码。
