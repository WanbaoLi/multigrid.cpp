# 灵晟 C24 MPI 布局与 RoCE 对照

使用与 [初次测试](results.json) 同一份 `24³×64` `cfg_5000` 输入。每种布局分别重用
一次建好的多重网格，单列和 12 列各从零初值求解三轮，以第二轮纯求解时间比较。完整
Wilson–Clover 相对残差门槛为 `1e-8`，`multigrid.cpp` 的第二轮输出另由独立标量算子复核。

Grid 复用同一可执行文件，在 `cn12053` 比较 16 MPI × 32 线程与 32 MPI × 16 线程。
`multigrid.cpp` 的单节点布局对照在 `cn12060` 的同一独占分配内完成。两种布局各用
512 个物理核。双节点 TCP 与 RoCE 对照在 `cn12044` 和 `cn12114` 的同一分配内完成，
每节点配置 16 MPI × 32 线程。直接比较同一对节点的 TCP 和 RoCE 数据可避免把节点差异
归入传输切换的收益。

| 配置 | 单列第二轮（秒） | 12 列第二轮（秒） |
| --- | ---: | ---: |
| Grid 单节点 16 MPI × 32 线程 | 69.182 | 828.653 |
| Grid 单节点 32 MPI × 16 线程 | 36.892 | 447.242 |
| multigrid.cpp 单节点 16 MPI × 32 线程 | 6.502 | 83.084 |
| multigrid.cpp 单节点 32 MPI × 16 线程 | 7.164 | 93.055 |
| multigrid.cpp 双节点 TCP | 8.385 | 79.668 |
| multigrid.cpp 双节点 RoCE | 2.987 | 32.458 |
| multigrid.cpp 双节点 RoCE 发布配置复跑 | 3.260 | 36.731 |

Grid 已启用两层 V-cycle。16 MPI 单列第二轮的 69.182 秒中，66.309 秒位于
多重网格预条件器；32 MPI 时预条件器为 34.609 秒，外层仍是 65 次。两组 Grid
的 12 列均逐列求解，`multigrid.cpp` 以两个 RHS 为一批。

同一双节点作业中，RoCE 将 64 字节归约从 469 微秒降到 33 微秒，一张细层
时间面大小的环交换从 3.08 毫秒降到 1.26 毫秒。求解加速分别为 2.81 倍和
2.45 倍，两种传输的外层迭代均为每列 24 次。[完整测量记录](mpi-followup.json)

提交 `13e6c80282e0952a98802d7f0315b2cbcdec9cfc` 中，灵晟实验脚本在显式选择
`LS_MPI_TRANSPORT=ucx` 后采用 `roceroh0:1`、IPv4 GID 索引 1 和一条 rendezvous rail。
此前设备自动选择的探测在共享通信域建立时达到超时。通信门禁核对两主机的绑核、
8 MiB 环交换的数据及归约结果。传输选择只作用于本次运行，可用 UCX 环境变量覆盖。

## 在灵晟复跑双节点 RoCE

以下命令使用本次已部署的源码包、已校验的 ARM SVE 库和独立复核程序。

```bash
root="$HOME/lqcd-run/ls-grid-wall-20261123"
work="$root/mpi-roce-default"
gauge="$HOME/inputs/grid-wall/beta6.20_mu-0.2790_ms-0.2400_L24x64_cfg_5000.lime"
revision=13e6c80282e0952a98802d7f0315b2cbcdec9cfc
tag=$(date +%Y%m%d-%H%M%S)

dsub -q q_hpcapp -A common --mpi hmpi -nn 2 -N 32 -rpn 16 -x job \
  -nl 'cn12044 cn12114' -R 'cpu=37,mem=30000MB' -T 5400 \
  --cwd "$work" -o "$work/native-two-$tag.job.log" \
  /usr/bin/env LQCD_LS_SDK=/work_ssd/software/HPCKit/25.2.1 \
  LS_MPI_TRANSPORT=ucx LS_RESULT_SUFFIX="$tag" \
  /bin/bash "$root/mpi-followup/launch.sh" native-two "$work" "$revision" "$gauge"
```

第二轮纯求解时间在新运行目录的 `measurements/result.json` 中，
字段为 `single_pure_summary.second_seconds` 和 `twelve_pure_summary.second_seconds`。
`second-round-residuals.log` 记录独立复核的 13 个残差。
