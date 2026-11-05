#!/bin/bash
# Build and independently verify the retained full12 configuration on one node.
# Invoke on an allocated LingSheng compute node or on node5005, not a login CPU.
set -eo pipefail
if [ "$#" -ne 2 ]; then
    echo "usage: bash tools/optimization/replay_verified.sh arm|x86 NEW_RUN_ROOT" >&2
    exit 2
fi
task_platform=$1
task_run_root=$2
task_project=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
if [ -e "$task_run_root" ]; then
    echo "Use a new run directory; existing evidence will not be overwritten" >&2
    exit 2
fi
case "$task_platform" in
arm)
    task_sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
    task_sysroot=/work_ssd/system/os_jasmine_v01/vroot
    task_python=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
    "$task_python" -c 'import platform; from pathlib import Path; assert platform.machine() == "aarch64" and "sve" in Path("/proc/cpuinfo").read_text().split(), "Run on an allocated SVE compute node, not the login CPU"'
    source "$task_sdk/setvars.sh" --use-bisheng --force
    export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
    export OMPI_CC=$CC OMPI_CXX=$CXX
    export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
    export LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
    export LD_LIBRARY_PATH=$task_sdk/compiler/gcc/lib64:$task_sdk/kupl/gcc/release/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
    export LQCD_EXPERIMENT_CXX_RUNTIME=$task_sdk/compiler/gcc/lib64
    export LQCD_EXPERIMENT_KUPL_ROOT=$task_sdk/kupl/gcc/release
    export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
    task_fixture=${LQCD_REPLAY_FIXTURE:-/home/share/nsls_lwb/.cache/mg-20261102/propagator}
    task_reference=${LQCD_REPLAY_REFERENCE:-/home/share/nsls_lwb/.cache/mg-20261102/source/build/validation/multigrid}
    task_gold=${LQCD_REPLAY_GOLD:-$task_fixture/propagator.npy}
    task_plan=$task_project/profiles/optimization/lingsheng-052-full12.json
    ;;
x86)
    task_python=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python
    "$task_python" -c 'import platform; assert platform.machine() == "x86_64", "Use the x86 compute node"'
    export CC=/public2/home/lwb_720/miniconda3/bin/gcc
    export CXX=/public2/home/lwb_720/miniconda3/bin/g++
    unset LQCD_EXPERIMENT_CXX_RUNTIME LQCD_EXPERIMENT_KUPL_ROOT
    task_fixture=${LQCD_REPLAY_FIXTURE:-/public2/home/lwb_720/.cache/mg-opt-20261103/fixture-ls-canonical}
    task_reference=${LQCD_REPLAY_REFERENCE:-/public2/home/lwb_720/.cache/mg-20261102/source/build/validation/multigrid}
    task_gold=${LQCD_REPLAY_GOLD:-/public2/home/lwb_720/.cache/mg-opt-20261103/campaign-canonical/attempts/000-canonical-paired/measurements/default-t16/propagator.npy}
    task_plan=$task_project/profiles/optimization/node5005-833-full12.json
    ;;
*) echo "Platform must be arm or x86" >&2; exit 2 ;;
esac
export PATH="$(dirname "$task_python"):$PATH"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_PROC_BIND=close
export CMAKE_C_COMPILER_LAUNCHER="$task_python;$task_project/tools/pin_build.py"
export CMAKE_CXX_COMPILER_LAUNCHER=$CMAKE_C_COMPILER_LAUNCHER
export LQCD_MPI_FLAGS='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
unset NATIVE_SAP_STEPS NATIVE_SAP_CYCLES NATIVE_COARSE_IT NATIVE_OUTER_FLOAT
unset LQCD_MG_SETUP_PASSES LQCD_MG_SETUP_ITERATIONS LQCD_MG_SETUP_SMOOTH LQCD_SETUP_UPDATE
unset LQCD_MG_SAP_STEPS LQCD_MG_SAP_CYCLES LQCD_MG_COARSE_IT LQCD_MG_COARSE_TOL
unset LQCD_COARSE_THREADS LQCD_CORRECTION_BASE_TOL LQCD_ARM_SVE_CLOVER_REUSE
cd "$task_project"
test -x "$task_python"
test -x "$task_reference"
test -f "$task_gold"
task_reference_sha=$(sha256sum "$task_reference" | cut -d' ' -f1)
mkdir -p "$task_run_root"
task_run_root=$(cd "$task_run_root" && pwd)
"$task_python" tools/optimization/campaign.py --campaign "$task_run_root/campaign" init \
    --repo "$task_project" --reference-skill "$task_project/skills/kunpeng-lqcd-reference" \
    --input-sha256 47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30 \
    --reference-sha256 "$task_reference_sha" --baseline-commit HEAD
"$task_python" tools/optimization/trial.py \
    --campaign "$task_run_root/campaign" --id replay-current \
    --proposal profiles/optimization/replay-proposal.json --plan "$task_plan" \
    --fixture "$task_fixture" --reference "$task_reference" \
    --extractor "$(dirname "$task_reference")/extract_columns" \
    --reference-propagator "$task_gold" --backend "$task_platform" \
    --allocation "$(hostname)-replay-current"
echo "Verified full12 report: $task_run_root/campaign/attempts/replay-current/report.json"
