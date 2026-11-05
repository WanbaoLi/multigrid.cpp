# 重放当前保留配置

这份命令重放当前052配置，候选仍在独立实验中。完整12列稳态为主要指标；
建层、首轮和独立精度检查分别记录。输入是已经保存的一次stout后规范场，
基准不会重复做stout。原始LIME准备及工具链构建细节见
[现有操作手册](lingsheng-x86-runbook.md)。

先在实际计算节点按操作手册设置对应工具链。灵晟必须从`ssh ls`提交Donau
计算节点作业；node5005从`ssh itp`后`ssh node5005`进入。所有输出使用新目录。

灵晟的核心环境与CMake选项如下，项目目录改为本次干净Git checkout：

```bash
PROJECT=/home/share/nsls_lwb/multigrid.cpp
RUN_ROOT=$HOME/lqcd-run/replay-arm-01
TASK_SDK=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
TASK_SYSROOT=/work_ssd/system/os_jasmine_v01/vroot
PYTHON=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
source "$TASK_SDK/setvars.sh" --use-bisheng --force
export PATH="$(dirname "$PYTHON"):$PATH"
export CC=$TASK_SYSROOT/usr/bin/gcc CXX=$TASK_SYSROOT/usr/bin/g++
export OMPI_CC=$CC OMPI_CXX=$CXX
export CPATH=$TASK_SYSROOT/usr/include:$TASK_SYSROOT/usr/local/include
export LIBRARY_PATH=$TASK_SDK/compiler/gcc/lib64:$TASK_SDK/kupl/gcc/release/lib:$TASK_SYSROOT/usr/lib64:$TASK_SYSROOT/usr/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$TASK_SDK/compiler/gcc/lib64:$TASK_SDK/kupl/gcc/release/lib:$TASK_SDK/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export LQCD_EXPERIMENT_CXX_RUNTIME=$TASK_SDK/compiler/gcc/lib64
export LQCD_EXPERIMENT_KUPL_ROOT=$TASK_SDK/kupl/gcc/release
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
FIXTURE=/home/share/nsls_lwb/.cache/mg-20261102/propagator
REFERENCE=/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid
GOLD=$FIXTURE/propagator.npy
PLAN=$PROJECT/profiles/optimization/lingsheng-052-full12.json
BACKEND=arm
```

node5005使用另一套环境和同一物理规范场的独立准备文件：

```bash
PROJECT=/public2/home/lwb_720/multigrid.cpp
RUN_ROOT=$HOME/lqcd-run/replay-x86-01
PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python
export PATH="$(dirname "$PYTHON"):$PATH"
export CC=/public2/home/lwb_720/miniconda3/bin/gcc
export CXX=/public2/home/lwb_720/miniconda3/bin/g++
unset LQCD_EXPERIMENT_CXX_RUNTIME LQCD_EXPERIMENT_KUPL_ROOT
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
FIXTURE=/public2/home/lwb_720/.cache/mg-opt-20261103/fixture-ls-canonical
REFERENCE=/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid
GOLD=/public2/home/lwb_720/.cache/mg-opt-20261103/campaign-canonical/attempts/000-canonical-paired/measurements/default-t16/propagator.npy
PLAN=$PROJECT/profiles/optimization/node5005-833-full12.json
BACKEND=x86
```

在选定平台环境后执行公共部分。`trial.py`在账本的独立快照目录里调用CMake、
编译和CTest，再运行完整12列；因此无需另外覆盖实验用的旧build。实际编译
参数、库摘要、测试日志、求解样本和独立精度都在`RUN_ROOT/campaign`保存。

```bash
set -eo pipefail
mkdir -p "$RUN_ROOT"
cd "$PROJECT"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close
export CMAKE_C_COMPILER_LAUNCHER="$PYTHON;$PROJECT/tools/pin_build.py"
export CMAKE_CXX_COMPILER_LAUNCHER="$CMAKE_C_COMPILER_LAUNCHER"
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
unset NATIVE_SAP_STEPS NATIVE_SAP_CYCLES NATIVE_COARSE_IT NATIVE_OUTER_FLOAT
unset LQCD_MG_SETUP_PASSES LQCD_MG_SETUP_ITERATIONS LQCD_MG_SETUP_SMOOTH LQCD_SETUP_UPDATE
unset LQCD_MG_SAP_STEPS LQCD_MG_SAP_CYCLES LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL
unset LQCD_COARSE_THREADS LQCD_CORRECTION_BASE_TOL LQCD_ARM_SVE_CLOVER_REUSE
TASK_REF_SHA=$(sha256sum "$REFERENCE" | cut -d' ' -f1)
"$PYTHON" tools/optimization/campaign.py --campaign "$RUN_ROOT/campaign" init \
  --repo "$PROJECT" --reference-skill "$PROJECT/skills/kunpeng-lqcd-reference" \
  --input-sha256 47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30 \
  --reference-sha256 "$TASK_REF_SHA" --baseline-commit HEAD
"$PYTHON" tools/optimization/trial.py \
  --campaign "$RUN_ROOT/campaign" --id replay-current \
  --proposal profiles/optimization/replay-proposal.json --plan "$PLAN" \
  --fixture "$FIXTURE" --reference "$REFERENCE" \
  --extractor "$(dirname "$REFERENCE")/extract_columns" \
  --reference-propagator "$GOLD" --backend "$BACKEND" \
  --allocation "$(hostname)-replay-01"
```

`trial.py`默认执行一次完整12列预热和三次完整12列稳态，全部从零初值开始。
独立标量复核覆盖12列，残差上限`1e-8`，参考解相对误差上限`1e-6`。
结果在`attempts/replay-current/report.json`；未通过精度或未完成的结果不能排名。
这条命令重放数值与计时流程，不会自动替换原任务的最佳指针。

若本机文件系统再次触发已记录的校验读取不一致，原样保留失败。当前任务的
严格读取／输出发布适配器和精确命令已归档在实验目录，不能通过更换期望摘要
或删除坏样本把失败改成成功。

灵晟JSON使用37线程建层、32线程求解，HBW分配要求必须由本次分配实际验证；
node5005使用16线程建层、12线程求解，每个NUMA域两个MPI进程。两平台都为
16MPI进程、每批2列。不同源点需生成匹配该坐标的独立参考解，当前冻结基准
仍是原点源，不能把当前结果描述成已经验收所有源点。
