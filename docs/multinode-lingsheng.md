# 灵晟多节点运行

当前任务固定每节点 16 个 MPI 进程，每进程 32 个 OpenMP 线程。每个进程绑定一个
NUMA 域内实际允许使用的 32 个物理核。MPI 进程数、线程数和 NUMA 域数分别配置。

## 输入与划分

- 输入：`$HOME/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime`。
- 输入来源、文件长度和 SHA-256：见 [F64P14-input.md](F64P14-input.md)。
- 格点：`64,64,64,128`；全局 MPI 拓扑：`1,1,1,32`。
- 两节点、共 32 个 MPI；每进程本地格点：`64,64,64,4`。
- 连续聚合块：`8,8,8,4`；粗网格：`8,8,8,32`；24 个测试向量，手征分裂后粗自由度 48。
- 质量参数 `mass=-0.2334`；Clover 系数 `csw=1.140825606017`。
- 每个组态执行一次 stout：1 步，`rho=0.125`，四个方向均参与。
- 目标完整算子相对残差不超过 `1e-8`；所有计时求解均从零初值开始。
- 主要迭代和 MG 系数为 FP32，可靠更新、完整算子残差和外部场为 FP64。
  分布式路径的外层 GCR 重启长度为 16，12 列以 batch2 顺序完成。

## 编译与提交

在灵晟登录节点、已与 GitHub 对齐的干净源码目录运行。不能在旧登录 CPU 上用
`-march=native` 编译后直接充当新计算 CPU 的性能构建；下面的任务在分配到的计算
节点上编译。`ls_env.sh` 复用本账号已验证的 HPCKit、HMPI 和 Python 环境。

```bash
cd "$HOME/lqcd-run/C64-20261114/source"
git status --short
git rev-parse HEAD
task_out="$HOME/lqcd-run/C64-$(date +%Y%m%d-%H%M%S)"
task_gauge="$HOME/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime"
mkdir -p "$task_out"
dsub -q q_hpcapp -A common --mpi hmpi \
  -nn 2 -N 2 -rpn 1 -x job -R 'cpu=592,mem=480000MB' -T 14400 \
  --cwd "$task_out" -o "$task_out/job.log" \
  /bin/bash "$PWD/tools/multinode/campaign_ls.sh" "$task_out" "$task_gauge"
```

`campaign_ls.sh` 顺序执行编译、CTest、跨主机小格子测试、真实 C24 门禁、真实
F64P14 测量和独立标量残差检查。失败会停止任务，保留日志和已写检查点。新的
输出目录可重新运行；目前检查点用于诊断，尚不支持从内存中的建层状态继续。

Donau 的上述申请每节点只有一个逻辑任务槽，但保留整个节点。`run_ls.sh` 中
`--oversubscribe` 用于启动每主机 16 个 MPI；`rank_exec.py` 再显式选择各自 NUMA
域的 32 个物理核，实际计算不会共享这些核。不能把这个选项用于超额使用未申请
的 CPU。账号当前 CPU 配额只允许这样的两个整节点；四节点申请曾被配额阻塞。

## 内存与计时边界

`LQCD_DISTRIBUTED_STORAGE=1` 保留全局虚拟索引，只驻留本进程负责的数据与所需
halo。它与旧的单主机 `LQCD_SHARED_COEFFICIENTS=1` 互斥。FP64 basis 的严格手征
零块不存储；建层结束后释放 FP64 basis、粗算子和测试向量，保留求解所需 FP32
数据和 FP64 规范场、Clover。标量预热的 Krylov 缓存会在 batch2 分配前释放。

两节点峰值初步预算约 350–440 GiB/节点，申请上限约 458 GiB/节点。预算按不同
阶段的活跃缓冲区计算，不能把所有阶段的数据尺寸相加。最终以内存检查点的 PSS、
调度器每节点 `memMax` 与 swap/OOM 状态为准。完整实验记录见
[distributed-C64-20261114](../experiments/distributed-C64-20261114/README.md)。

`solve/result.json` 只会在独立标量算子检查全部通过后标为 `complete=true`。主要
字段为 `single_pure_summary` 和 `twelve_pure_summary`：首次、第二次、后两次的
中位数以及本次实测最小值。12 列的同一 batch 耗时只计算一次。纯求解时间包含
实际迭代和必要的纠正求解，排除读入、smear、装载/Clover、setup、输出及标量校验。
API 总耗时另外保留，避免混淆。

每次测量保存源码分支、提交号、动态库 SHA-256、绑核列表、内存检查点和每列真实
残差。二进制规范场及传播子校验文件写入计算节点 `/tmp`，全部校验通过后删除。
完整日志保留在源码目录外，Git 中只保存结构化结果与分析。
