# 灵晟与 node5005：编译、完整传播子运行和冻结实验复现

这是正在进行的优化任务的操作手册，**不表示优化结束**。下面给出已经核对的工具链、
CLI 和可运行起点。最终采用哪个 plan、源码/库摘要、线程配置及性能样本，以最终
验收报告补齐；不要把这里的示例参数自动称为最佳参数。

目标固定为原始组态 `24×24×24×64`，质量参数 `-0.277`，Clover 系数
`1.160920226`，四方向一次 stout、参数 `0.125`，时间反周期，原点单位点源。
完整传播子包含 4 个源自旋与 3 个源颜色，共 12 列；每列每轮零初值。
完整双精度相对残差不超过 `1e-8`，即十的负八次方。读入、平滑、建立层级、
写文件单独计时；最终比较完整 12 列公共 API 墙时，不能由单列乘 12 或局部核推算。

## 已核对的路径与边界

| 项目 | 灵晟 | node5005 |
|---|---|---|
| 登录入口 | `ssh ls`，之后使用 Donau 计算节点分配 | `ssh itp`，再 `ssh node5005` |
| 当前任务根目录 | `/home/share/nsls_lwb/.cache/mg-opt-20261103` | `/public2/home/lwb_720/.cache/mg-opt-20261103` |
| Python | `/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python` | `/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python` |
| 编译器 | sysroot 的 GCC/G++ 10.3.1 | 002 构建记录为 `/public2/home/lwb_720/miniconda3/bin/gcc`、`g++` 14.4.0 |
| MPI | HPCKit 25.1.0.SPC001 HMPI，匹配该 Python 的 mpi4py | `pyquda` 环境中的 Open MPI，匹配该 Python 的 mpi4py |
| 物理布局 | 16 个带 CPU 的 NUMA 域；当前作业每域允许 37 核 | 8 个 NUMA 域，每域 32 核；每域 2 个进程时每进程 16 核 |

NUMA 表示核到不同内存区域的访问距离不同。灵晟登录机是较旧的无 SVE CPU，
**不能在登录机用 `-march=native` 编译后声称是目标 SVE 构建**。构建、硬件探针和
性能运行都应在实际计算节点执行；可用核、内存节点及向量长度由本次分配重新探测。
node5005 此前通过用户指定的直接 SSH 路径测试，未取得排他 Slurm 分配；该限制
应随性能数字披露。正式比较尽量在排他或已确认空闲的单节点分配内进行。

冻结的官方适用性依据见 `skills/kunpeng-lqcd-reference/`；保持该目录只读。
当前 SDK 的 ABI 及内存约束不能由较新网页示例替代。

## 灵晟：在分配的计算节点内编译

以下代码保存为项目外的新作业脚本，例如 `$HOME/lqcd-run/build-and-run-ls.sh`。
`PROJECT` 改为本次明确选择的干净源码目录；不要覆盖正在使用的旧实验源码或构建。
脚本中的 `BUILD`、`OUTPUT` 都应使用新目录。

```bash
#!/bin/bash
set -eo pipefail
PROJECT=/home/share/nsls_lwb/.cache/mg-opt-20261103/source
RUN_ROOT=$HOME/lqcd-run/ls-new
BUILD=$RUN_ROOT/build
OUTPUT=$RUN_ROOT/raw-lime
TASK_SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
TASK_SYSROOT=/work_ssd/system/os_jasmine_v01/vroot
TASK_KUPL=$TASK_SDK/kupl/gcc/release
TASK_CXX_RUNTIME=$TASK_SDK/compiler/gcc/lib64
PYTHON=$HOME/.cache/multigrid-arm-20261025-env/bin/python
GAUGE=$HOME/.cache/multigrid-arm-20261025/configuration24.lime
mkdir -p "$RUN_ROOT"
test ! -e "$BUILD"
test ! -e "$OUTPUT"

source "$TASK_SDK/setvars.sh" --use-bisheng --force
# 保留 setvars 产生的 SDK/MPI 依赖，明确选择本轮验证过的 GCC C++ 运行库。
export PATH="$(dirname "$PYTHON"):$PATH"
export CC=$TASK_SYSROOT/usr/bin/gcc CXX=$TASK_SYSROOT/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$TASK_SYSROOT/usr/include:$TASK_SYSROOT/usr/local/include
export LIBRARY_PATH=$TASK_CXX_RUNTIME:${LIBRARY_PATH:-}:$TASK_SYSROOT/usr/lib64:$TASK_SYSROOT/usr/lib
export LD_LIBRARY_PATH=$TASK_CXX_RUNTIME:$TASK_KUPL/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close
export LQCD_TEST_PYTHON=$PYTHON
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated
export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
unset LD_PRELOAD PERF_COUNTER_ROOT

cd "$PROJECT"
"$PYTHON" tools/probe_host.py > "$RUN_ROOT/host.json"
"$PYTHON" -c 'from mpi4py import MPI; import numpy; print(MPI.Get_library_version()); print(numpy.__version__)'
cmake -S "$PROJECT" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
  -DLQCD_BUILD_RUNTIME=ON -DLQCD_DD_REFERENCE=OFF \
  -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
  -DMPI_C_COMPILER="$(command -v mpicc)" \
  -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
  -DLQCD_TEST_PYTHON="$PYTHON" -DLQCD_MPI_FLAGS="$LQCD_MPI_FLAGS" \
  -DCMAKE_C_COMPILER_LAUNCHER="$PYTHON;$PROJECT/tools/pin_build.py" \
  -DCMAKE_CXX_COMPILER_LAUNCHER="$PYTHON;$PROJECT/tools/pin_build.py" \
  -DLQCD_KUPL_HBW=ON -DLQCD_KUPL_ROOT="$TASK_KUPL" \
  -DCMAKE_EXE_LINKER_FLAGS="-L$TASK_CXX_RUNTIME -Wl,-rpath,$TASK_CXX_RUNTIME" \
  -DCMAKE_SHARED_LINKER_FLAGS="-L$TASK_CXX_RUNTIME -Wl,-rpath,$TASK_CXX_RUNTIME"
cmake --build "$BUILD" -j16
OMP_NUM_THREADS=2 OMP_PLACES=cores ctest --test-dir "$BUILD" --output-on-failure \
  -R '^(core|arm_.*|coarse_kernel|coarse_overlap_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|cpu_backend_mpi2|runtime_batch|batch12_mpi2|mg_tuning)$'
ldd "$BUILD/liblqcd_cpu.so" > "$RUN_ROOT/library-dependencies.txt"
sha256sum "$BUILD/liblqcd_cpu.so" > "$RUN_ROOT/library.sha256"
```

这套设置对应 LS 010/020 的 GCC 10.3.1、HMPI 构建及 010 任务的 SDK 运行库选择。
`LIBRARY_PATH` 只影响链接搜索，`LD_LIBRARY_PATH` 影响加载；GCC 的隐式 C++ 搜索
目录可能早于 `LIBRARY_PATH`，所以这里同时传入明确的 `-L` 和 rpath，避免再次把
需要 `GLIBCXX_3.4.30` 的 KUPL 与旧 `libstdc++` 混用。不要手动覆盖系统 libc 或把
旧 sysroot 的 libc 路径随意加到加载路径最前。`ldd`/运行时映射用于确认实际依赖。

`site_job.sh` 已复用相同 HPCKit、sysroot 编译器、MPI 和 NUMA 基础设置，但它的入口
是队列 worker，而且还需要任务显式给出上述已验证的 SDK GCC/KUPL 加载目录。
`trial.py` 接受 `LQCD_EXPERIMENT_KUPL_ROOT` 和 `LQCD_EXPERIMENT_CXX_RUNTIME`，会加入
对应 CMake 选项；普通 `build_runtime.sh` 不自动打开 KUPL，不能只设置环境就假设已链接。

## 灵晟：从原始 LIME 求完整 12 列

接在同一计算节点脚本的构建段之后执行。以下是已验证的 SVE、双 RHS、HBW 起点，
不是 phase2/3 的最终参数。除明确给出的开关，求解使用该源码默认值。

```bash
export LQCD_CPU_LIBRARY=$BUILD/liblqcd_cpu.so
unset NATIVE_SAP_STEPS NATIVE_SAP_CYCLES NATIVE_COARSE_IT NATIVE_OUTER_FLOAT
unset LQCD_MG_SAP_STEPS LQCD_MG_SAP_CYCLES LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL
unset LQCD_CORRECTION_BASE_TOL LQCD_COARSE_THREADS
export LQCD_MG_SETUP_PASSES=2 LQCD_MG_SETUP_ITERATIONS=3 LQCD_MG_SETUP_SMOOTH=12
export LQCD_FLOAT_CORRECTION_VERIFY=0 LQCD_FINE_TEAM_FUSED=1
export LQCD_LOCAL_CONTIGUOUS=1 LQCD_COARSE_CGS2=0 LQCD_RESTRICT_FLOAT=0 LQCD_GCR_FUSED=1
export LQCD_SAP_EO=1 LQCD_COARSE_EO=1 LQCD_SETUP_UPDATE=inverse
export LQCD_ADAPTIVE_CORRECTION=1 LQCD_HALO_OVERLAP=1
export LQCD_ARM_SVE=1 LQCD_ARM_SVE_REUSE=0
export LQCD_ARM_SVE_PLANNED=0 LQCD_ARM_SVE_TRANSFER=0
export LQCD_COARSE_FUSED=0 LQCD_ARM_COARSE_SVE=0 LQCD_COARSE_SPATIAL_OVERLAP=0
export LQCD_HBM=off
export LQCD_HBW_ALLOC=require
export LQCD_RHS_BATCH=2
export LQCD_VERBOSE=0 LQCD_HALO_PROFILE=0
unset LD_PRELOAD PERF_COUNTER_ROOT
"$PYTHON" tools/run_numa.py --threads 37 -- \
  "$PYTHON" -u tools/solve_propagator.py --backend arm \
  --library "$LQCD_CPU_LIBRARY" --gauge "$GAUGE" \
  --mass -0.277 --csw 1.160920226 --normalization mass \
  --block 6 6 6 4 --source 0 0 0 0 --source-scale 1 \
  --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --tol 1e-8 --seed 1024 --threads 37 --repeats 4 \
  --save-gauge --output "$OUTPUT"
```

`require` 只适用于**本次作业允许访问 HBW 节点，且真实 KUPL 分配/验证成功**的情形。
检查 `host.json` 的 `Mems_allowed_list`、本次 `hbw_probe.cpp` 日志以及求解日志每个
进程的 `provider=KUPL`、`sdk_verify=1` 和实际驻留节点；不能只凭“有 memory-only
NUMA”认定成功。当前 016 取得了这类证据，历史只允许 0–15 的分配则没有。
新分配若不满足条件，`require` 必须报错；若要测普通内存基线，明确改成 `off` 并
作为不同实验记录，不能把 `prefer` 回退计成 HBW 成绩。不要把整个约数百 GB 的
setup 进程强绑到 4 GiB 的某个内存域。`LQCD_HBM` 是另一条已有页迁移路径，此处
保持 off，避免把两种机制混在一次对照中。

在 `ssh ls` 登录 shell 提交已保存的完整脚本，例如：

```bash
dsub -q q_hpcapp -A common -nn 1 -N 1 -x job \
  -R 'cpu=592,mem=480000MB' -T 3600 \
  --cwd "$HOME/lqcd-run" -o "$HOME/lqcd-run/ls-new.log" \
  /bin/bash "$HOME/lqcd-run/build-and-run-ls.sh"
```

资源参数是本任务已用配置，不保证未来分配的内存允许集合相同。脚本会在分配的
计算节点执行探针、原生构建和运行；不要直接在登录节点执行构建段。

## node5005：原生构建与原始 LIME 完整求解

先 `ssh itp`、再 `ssh node5005`，在实际 node5005 shell 中执行。下例用已验收历史
EPYC profile 展示生产入口；本轮稳定对照 002 还比较了默认值与该 profile 的不同
线程数，最终胜出者由后续完整精度及样本决定。

```bash
set -eo pipefail
PROJECT=/public2/home/lwb_720/.cache/mg-opt-20261103/source
RUN_ROOT=$HOME/lqcd-run/x86-new
BUILD=$RUN_ROOT/build
OUTPUT=$RUN_ROOT/raw-lime
PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python
export PATH="$(dirname "$PYTHON"):$PATH"
export CC=/public2/home/lwb_720/miniconda3/bin/gcc
export CXX=/public2/home/lwb_720/miniconda3/bin/g++
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close
unset LD_PRELOAD PERF_COUNTER_ROOT
mkdir -p "$RUN_ROOT"
test ! -e "$BUILD"
test ! -e "$OUTPUT"
cd "$PROJECT"
"$PYTHON" tools/probe_host.py > "$RUN_ROOT/host.json"
cmake -S "$PROJECT" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
  -DLQCD_BUILD_RUNTIME=ON -DLQCD_DD_REFERENCE=OFF -DLQCD_KUPL_HBW=OFF \
  -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
  -DMPI_C_COMPILER="$(command -v mpicc)" \
  -DMPI_CXX_COMPILER="$(command -v mpicxx)" -DLQCD_TEST_PYTHON="$PYTHON" \
  -DCMAKE_C_COMPILER_LAUNCHER="$PYTHON;$PROJECT/tools/pin_build.py" \
  -DCMAKE_CXX_COMPILER_LAUNCHER="$PYTHON;$PROJECT/tools/pin_build.py"
cmake --build "$BUILD" -j16
OMP_NUM_THREADS=2 OMP_PLACES=cores ctest --test-dir "$BUILD" --output-on-failure

# 受版本控制的现有环境文件，不把任意 JSON 拼成 shell/eval。
source profiles/epyc9755_physical.env
unset NATIVE_SAP_STEPS NATIVE_SAP_CYCLES NATIVE_COARSE_IT NATIVE_OUTER_FLOAT
unset LQCD_COARSE_THREADS
export LQCD_HBW_ALLOC=off LQCD_HBM=off
export LQCD_VERBOSE=0 LQCD_HALO_PROFILE=0
export LQCD_CPU_LIBRARY=$BUILD/liblqcd_cpu.so
GAUGE=/public2/home/lwb_720/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime
"$PYTHON" tools/run_numa.py --ranks-per-numa 2 --threads 16 -- \
  "$PYTHON" -u tools/solve_propagator.py --backend x86 \
  --library "$LQCD_CPU_LIBRARY" --gauge "$GAUGE" \
  --mass -0.277 --csw 1.160920226 --normalization mass \
  --block 6 6 6 4 --source 0 0 0 0 --source-scale 1 \
  --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 \
  --solver-options profiles/epyc9755_physical_solver.json \
  --tol 1e-8 --seed 1024 --threads 16 --repeats 4 \
  --save-gauge --output "$OUTPUT"
```

两平台普通计时都不得预载 perf/PMPI；必要的 SDK/MPI 加载路径仍须保留。
`--repeats 4` 表示四次实际完整传播子：第一轮预热，其余三轮全部保留。原始 LIME
工作流的结果没有 ledger 的 `warmup` 字段，应明确按首轮/后三轮解释；不要改变或
删除异常慢样本。严格实验门控优先使用下一节的冻结 fixture 驱动。

## 独立参考程序：先校验冻结摘要

原始 LIME 的已知 SHA256 为：

```text
47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30
```

下列冻结程序用于独立算子复核，不要用候选构建覆盖它们。两平台的程序不同，所以
摘要不同；不能只凭文件名认定一致。

| 平台 | 冻结根目录 | `multigrid` SHA256 | `extract_columns` SHA256 |
|---|---|---|---|
| LS | `/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation` | `1534d9c0653a019dcac4df98965f47f14d052cb324c35e568faa760d50878e9c` | `efd900b99630c3cf2ea4ba285b38a5a123faa8e9d5d7cbbaf0f3169a8a58cc5b` |
| x86 | `/public2/home/lwb_720/.cache/mg-20261102/source/build/validation` | `c5803d59b8c35d5b0bb07e45b98353194e927a3fd8ea1c57ee40070ae9433929` | `d3a1348cd4a54fb477bcd2c13ee094675a45a4c582a69f3349769c229172a251` |

将该平台根目录设为 `REFERENCE_BUILD`、表中两个摘要设为 `REFERENCE_SHA` 和
`EXTRACTOR_SHA` 后，用数据参数校验；这里不执行 JSON 中的 shell 字符串：

```bash
REFERENCE=$REFERENCE_BUILD/multigrid
EXTRACTOR=$REFERENCE_BUILD/extract_columns
"$PYTHON" - "$REFERENCE" "$REFERENCE_SHA" "$EXTRACTOR" "$EXTRACTOR_SHA" <<'PY'
import hashlib, sys
from pathlib import Path
for filename, expected in zip(sys.argv[1::2], sys.argv[2::2]):
    value=hashlib.sha256()
    with Path(filename).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024**2),b''): value.update(chunk)
    if value.hexdigest()!=expected: raise SystemExit('Frozen reference changed: '+filename)
    print(filename,value.hexdigest())
PY
```

对上面 `--save-gauge` 的新原始 LIME 输出复核全部 12 列：

```bash
"$PYTHON" benchmarks/runtime/verify_fixture_propagator.py \
  "$OUTPUT" "$REFERENCE" "$EXTRACTOR" "$RUN_ROOT/independent"
```

这个检查器按列提取字节，调用冻结标量程序重算完整相对残差，保留质量归一化的
换算及时间边界约定。检查所有 12 列而非仅第一列，输出 `verification.json`。

## 冻结 fixture：复现已验收的源码、库和 plan

这条路径省去重复 LIME 解析/stout，但不导入预存解，也不跳过新的残差复核。
同一输入的预处理规范场缓存位置：

- LS：`/home/share/nsls_lwb/.cache/mg-20261102/propagator`。
- x86：`/public2/home/lwb_720/.cache/mg-20261102/propagator`。

必须保留 `result.json` 和全部 `gauge_rankNNNNN.npy`；已有 `propagator.npy` 仅用于
额外的解差异比较，不能作为新求解的初值或输出。fixture 的旧计时字段不属于新样本。

先在该平台对应的编译/运行环境中设置：

```bash
# RUN_BASE 是上表任务根目录；SOURCE 是执行当前账本 CLI 的源码。
SOURCE=$PROJECT
CAMPAIGN=$RUN_BASE/campaign
FIXTURE=/该平台上述冻结fixture绝对路径
ACCEPTED_ID=替换为最终报告选定的已验证轮次
PLAN=$RUN_ROOT/selected-plan.json
PROPOSAL=$RUN_ROOT/reproduce-proposal.json
REPRODUCE_ID=替换为未使用过的短ID
ALLOCATION=替换为本次真实计算节点分配ID
BACKEND=arm
# x86 改 BACKEND=x86。不要同时在两台主机写同一个 campaign。
```

从保留的报告读取参数并写受控 JSON，避免人工漏掉 context/批量/线程条件。
这是导出已有配置，不搜索参数，也不执行其中的字符串：

```bash
"$PYTHON" - "$CAMPAIGN" "$ACCEPTED_ID" "$PLAN" "$PROPOSAL" <<'PY'
import json, sys
from pathlib import Path
campaign, identity, plan_path, proposal_path=sys.argv[1:]
report_path=Path(campaign)/'attempts'/identity/'report.json'
configuration=json.loads(report_path.read_text())['configuration']
plan=dict(context_environment=configuration['context_environment'],cases=[dict(
    id='full12',threads=configuration['threads'],batch=configuration['batch'],
    environment=configuration['solve_environment'])])
for key in ['placement_threads','setup_threads']:
    if key in configuration: plan[key]=configuration[key]
proposal=dict(bottleneck='Reproduce a retained full12 measurement on the current allocation',
    hypothesis='Same frozen source/library/configuration remains correct and repeatable',
    change='Fresh control; no numerical edit',mechanism='Measure allocation drift without source rollback',
    history_links=[str(report_path),'docs/lingsheng-x86-runbook.md'],
    retry_conditions='Repeat only with new allocation evidence or attributed prior interruption')
for filename,value in [(plan_path,plan),(proposal_path,proposal)]:
    with Path(filename).open('x') as stream: json.dump(value,stream,indent=2)
PY
"$PYTHON" "$SOURCE/tools/optimization/campaign.py" --campaign "$CAMPAIGN" history
"$PYTHON" "$SOURCE/tools/optimization/trial.py" \
  --campaign "$CAMPAIGN" --id "$REPRODUCE_ID" \
  --proposal "$PROPOSAL" --plan "$PLAN" \
  --source-from "$ACCEPTED_ID" --reuse-attempt "$ACCEPTED_ID" \
  --fixture "$FIXTURE" --reference "$REFERENCE" --extractor "$EXTRACTOR" \
  --reference-propagator "$FIXTURE/propagator.npy" \
  --backend "$BACKEND" --allocation "$ALLOCATION"
```

`trial.py` 逐项复核父轮源码/归档/保留库，从其快照复制源码，保持原始摘要，并建立
新结果目录；它不会 checkout/reset 当前工作树。复用库时应继承该轮经过验证的 SDK、
MPI、C++ 运行库及 HBW 允许条件。这个例子只生成新的控制报告，不加 `--against` 或
`--baseline`，因此不会自动改变现有最佳版本。若没有可复用的已验证轮次，按
`docs/optimization-framework.md` 初始化新 campaign，再用现有 `trial.py` 构建和验收。

底层 `bench_full12.py` 的 `--repeats 3` 实际执行一次完整预热加三次完整稳态；
`trial.py` 自动传入真实快照摘要，随后调用同一驱动的 `--verify`，完成独立全列残差
及相对冻结解的 `1e-6` 误差门。完整后才 ingest，部分结果和 diagnostic 不参与排名。
需要同 hierarchy 的多配置交错比较时，复用 `interleaved.py`；缓存/context 开关
必须另开进程，不得在同一进程中修改后假定生效。

## CPU 放置、setup 与 solve 线程必须分别记录

| 条件 | 控制方式 | 含义 |
|---|---|---|
| placement | `run_numa.py --threads` 与 plan 的 `placement_threads` | 每进程获准使用的物理核集合及 `OMP_PLACES` |
| setup | plan 的 `setup_threads` | 构建该 hierarchy 时的 OpenMP 线程数 |
| fine solve | case 的 `threads` | setup 后 `Solver.set_threads()` 的线程数 |
| coarse solve | case 动态参数 `LQCD_COARSE_THREADS` | 粗层局部线程上限，返回细层前恢复；0 继承 fine 团队 |

例如固定 placement=37、setup=37，只将 solve 依次设为 37/32/16，才能隔离小团队
调度收益，而不是同时改变 CPU 分配与层级构建。node5005 类似地固定 placement=16、
setup=16，再比较 solve=16/12/8。同节点一进程/NUMA 与每 NUMA 两进程是不同拓扑，
也不能仅按线程数混在一起比较。

现有原始 LIME CLI 的 `--threads` 同时设置初始 setup 和后续 solve；它没有单独
的 `--setup-threads` 参数。需要这三种条件分离时使用冻结 fixture 的 benchmark/ledger
路径，不要伪造原始 CLI 选项。最终报告须同时保存这三个值、NUMA/MPI、完整样本和
精度证据。所有读取/写出均在普通计时之外；层级复用不等于跨轮复用解。

经验汇总及恢复入口见 `docs/optimization-framework.md`。日志中若出现加载失败、
HBW require 失败、未完成独立验证或不一致的放置条件，应保留证据并报告阻塞，
不能以局部核加速替代完整 12 列验收。最终最佳 plan 路径与精确数字由后续报告填写。
