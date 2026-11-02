# 双平台开发与验证入口（2026-11-02）

基于 develop 的 `0b8f9f1`，本轮使用独立的 `~/.cache/mg-20261102/source`，
不覆盖 h20 的 `~/lqcd/multigrid.cpp`：该目录存在尚未提交的批处理优化。
本轮解决构建/启动问题并测试已有双 RHS 调优开关，尚未新增求解器算术内核。

完整 CTest 还需要 PyQUDA 的 host 模块 `pyquda`、`pyquda_comm`、`pyquda_utils`，
其中 `pyquda_comm.pointer` 是 CPU Cython 扩展；不需要 QUDA GPU 扩展或 GPU 初始化。
`validate_host.sh` 在编译前检查这些导入。灵晟原 venv 缺少这些模块，本轮从 h20 的
PyQUDA checkout 复制 host 包和生成的 pointer.c 到 `~/.cache/mg-20261102/pyquda-host`，
由 venv 的 `lqcd_validation_host.pth` 引入，并在 ARM 原生编译 pointer；未复制 x86 的
`.so`。复制时须包含 `pyquda_core/pyquda`、`pyquda_core/pyquda_comm`，根目录的
`pyquda`/`pyquda_comm` 是相对符号链接，不能只复制链接。
复现时需保持此目录或安装兼容的 host 包。

## 修复内容

- `.gitattributes` 固定脚本 LF，避免 Windows 快照在 Linux 上出现 `pipefail\r`。
- `build_runtime.sh` 将 MPI wrapper 解析为绝对路径，避免 CTest 生成 `/mpiexec`。
- 支持显式 `LQCD_MPI_FLAGS`；Donau 单 replica 测试用 localhost:4，实际求解由
  NUMA launcher 指定本机 slots、逐 rank CPU 绑定。
- `probe_host.py` 记录计算节点 affinity、内存域、HWCAP 和 SVE VL，不依赖个人 skill。
- `pin_build.py` 只约束串行编译子进程；不改变求解器 MPI/OpenMP 绑定。
- `validate_host.sh` 顺序执行原生编译、完整 CTest，再按需解真实传播子；失败立即退出。

## x86：h20 / Slurm

在源码根目录执行。先用 `sinfo -p amd256c_2025` 检查资源；本轮 node5002–5004
为 MIXED，不能将部分节点运行当作独占性能纪录。以下申请 128 核、16 MPI slots；
实际求解 rank 数由允许 cpuset 的 NUMA 分布确定。

```bash
export MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda
export PATH="$MPI_PREFIX/bin:$PATH"
export LQCD_TEST_PYTHON="$MPI_PREFIX/bin/python"
export LQCD_GAUGE=/public2/home/lwb_720/lqcd/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
export LQCD_OUTPUT="$PWD/results/x86-$(date +%Y%m%dT%H%M%S)"
sbatch -p amd256c_2025 -N 1 -n 16 -c 8 --mem=192G -t 00:30:00 \
  --chdir="$PWD" -o "$PWD/x86-validation-%j.log" \
  --wrap='bash tools/validate_host.sh'
```

如果需要指定 node5004，加 `-w node5004`。构建为 `build/validation`，使用计算节点
`-march=native`；不要在登录节点构建后假定相同 ISA。

## 灵晟：Donau

在源码根目录执行，工具链/venv 路径为本轮检查到的站点路径。

```bash
export LQCD_GAUGE="$HOME/.cache/multigrid-arm-20261025/configuration24.lime"
export LQCD_RHS_BATCH=1
export LQCD_OUTPUT="$PWD/results/arm-$(date +%Y%m%dT%H%M%S)"
dsub -q q_hpcapp -A common -nn 1 -N 1 -x job \
  -R 'cpu=592,mem=480000MB' -T 1800 --cwd "$PWD" \
  -o "$PWD/arm-validation.log" /bin/bash "$PWD/tools/donau_validate.sh"
```

两端输入 SHA256 相同：
`47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30`。

计算节点实测双路 304 核，共 608 核，允许 592 核；CPU NUMA0–15，每域允许37核。
memory-only NUMA16–31 各4096MB，本轮 cpuset 的 `Mems_allowed_list=0-31`。
HWCAP 显示 SVE/SVE2/SME，SVE VL 为64字节；native 库反汇编含 `ld1w {z2.s}, p0/z`
等 SVE 指令。SME 算术内核没有实测，内存域允许访问也不能代表已经使用 HBM。
当前求解默认 HBM off；后续可对 owned 热点资产做 require 模式迁移/驻留验证后再测量。

完整回归中，缺失 host 依赖导致的失败经补齐后重跑；36项在原预算下通过。
`native_halo` 和 `sap_eo` 的 240 秒预算在第三次 hierarchy 构建阶段不足，ARM
预算改为480秒后分别在348.34/305.65秒通过；保留全部模式、非等线程和残差门。
两项补测后，38项均有通过结果；没有将 timeout 记为数值通过。

## x86 本轮有限扫描

node5004 为双路 EPYC 9755、256 物理核、**2 个 NUMA**；与旧 node5005 的 8 NUMA
配置不同。本次分配 128 核，launcher 得 2 MPI，分别 72/56 OpenMP 线程。
38 项 CTest 全通过。下表两次使用相同库 SHA256、相同 affinity、相同科学参数。

| LQCD_RHS_BATCH | setup 秒 | 首轮12列秒 | 第二轮12列秒 | 最大真残差 |
|---|---:|---:|---:|---:|
| 1（默认） | 45.001 | 15.570 | 15.410 | 4.746e-9 |
| 2 | 44.794 | 14.060 | 13.867 | 4.746e-9 |

batch=2 第三轮 13.956 秒，后两轮中位数 13.911 秒。第二轮耗时减少 10.02%，
加速比 1.111；是当前 MIXED 节点上的有限比较，不代表全节点最优或独占性能。
复测命令在上述运行命令前执行 `source profiles/epyc9755_two_numa.env`，使用新的输出目录；
不要直接套用 8 NUMA 的 `--threads 16` profile。

双 RHS 最终输出 12 列均经独立 C++ 参考算子复核，最大残差
`4.745945120813694e-9`。验证器将 `.npy` 按字节提取列，不做浮点换基或重缩放；
规范场为实际 stout 后保存的 gauge。参考算子使用 M/(4+mass)，因此其显式 rhs
为 delta/(4+mass)，不能误用另一个归一化。工具仅接受本文固定 fixture 参数：

```bash
c++ -O2 -std=c++17 benchmarks/runtime/extract_propagator_columns.cpp -o build/validation/extract_columns
python benchmarks/runtime/verify_fixture_propagator.py \
  "$LQCD_OUTPUT" "$PWD/build/validation/multigrid" \
  "$PWD/build/validation/extract_columns" "$PWD/results/new-verification"
```

需 `--save-gauge` 输出和新的验证目录，约 10GB 临时磁盘空间；成功后删除临时二进制，
保留逐列日志与 `verification.json`。性能计时不包含此验证。

## 灵晟本轮有限扫描

灵晟 cn10580 同一独占分配、同一库及16 MPI×37线程的实测如下。

| LQCD_RHS_BATCH | setup 秒 | 首轮12列秒 | 第二轮12列秒 | 最大真残差 |
|---|---:|---:|---:|---:|
| 1（保留） | 313.946 | 103.286 | 103.171 | 4.819e-9 |
| 2（不采用） | 312.753 | 114.922 | 114.974 | 4.819e-9 |

batch=2 第三轮114.979秒，后两轮中位数114.976秒；第二轮比batch=1慢11.44%。
该节点本轮保留batch=1，不推广x86的双RHS profile。两端数据不能直接作为硬件峰值
对比：x86仅分配128核且节点MIXED，ARM为592核独占；本轮ARM结果慢于历史记录，
差异原因尚未定位，不能把旧记录的28秒列为本轮成绩。仓库的<5秒目标尚未达到。

保留的batch=1输出12列独立参考算子复核全部通过，最大残差
`4.81885811253433e-9`。完整清单（两端的单/双RHS原始报告、库/输入哈希、CPU绑定、
逐列统计、架构探测和独立验证）见 `validation-20261102.json`。
远端大体积传播子保存在两端 `~/.cache/mg-20261102/propagator{,-batch2}`，未上传Git。

下一阶段先在同一分配中复现历史参数环境、分析细/粗层与归约分项，再评估选择性HBM；
h20原工作目录未提交的field-batch改动保持原样，合入前需单独建立数值与性能对照。

## 科学参数和验收

此入口显式使用 mass=-0.277、csw=1.160920226、一步四方向 stout/rho=0.125、
时间反周期、单位原点源，12 列逐次零初值，双精度完整真残差门 1e-8，两轮传播子。
这些是复现现有物理 profile 的基线参数；物理研究应根据目标 action 明确修改，
不能将 csw=1 的旧结果与此口径直接混比。

`result.json` 保留 setup、首轮、第二轮、逐列残差；输出 `propagator.npy`。
`--save-gauge` 保存预处理后的规范场。内部真残差检查不等价于独立 scalar oracle；
独立验解和性能调优结果必须另外标明。

仅构建/回归时不设置 `LQCD_GAUGE`；已构建后的独立运行命令为：

```bash
export LQCD_CPU_LIBRARY="$PWD/build/validation/liblqcd_cpu.so"
python tools/run_numa.py --dry-run -- python tools/solve_propagator.py --help
python tools/run_numa.py -- python -u tools/solve_propagator.py \
  --gauge "$LQCD_GAUGE" --mass -0.277 --csw 1.160920226 \
  --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --repeats 2 --save-gauge --output "$LQCD_OUTPUT"
```

该运行命令也必须在分配的计算节点内执行，并使用与构建相同的 MPI/Python 环境。
