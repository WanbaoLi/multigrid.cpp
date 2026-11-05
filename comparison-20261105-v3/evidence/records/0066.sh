#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v2
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
label=$1; configuration=$2; mode=${3:-full}
if [[ $label == login ]]; then
 export PYQCU_KUPL_LIB=/home/share/nsls_lwb/.cache/pyqcu-login-v20261104/build-login/libqcu.so
else
 export PYQCU_KUPL_LIB=/home/share/nsls_lwb/.cache/pyqcu-kunpeng-recheck/build-kunpeng/libqcu.so
fi
if [[ $configuration == 128 ]]; then ranks=4;threads=32;grid=(1 4 1 1)
else ranks=16;threads=37;grid=(1 4 4 1);fi
export KUPL_OMP_THREADS=$threads OMP_NUM_THREADS=$threads OMP_DYNAMIC=FALSE
export KUNPENG_BIND_WORKERS=1 KUNPENG_RESTORE_MASTER=1 KUNPENG_WAIT_POLICY=ACTIVE KUNPENG_BLOCKTIME=200
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 KUPL_FUSED_BICG_DOTS=1 KUPL_DISABLE_CLOVER_CACHE=0
export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader OMPI_MCA_coll='^hcoll,ucg,ucc'
export OMPI_MCA_rmaps_base_oversubscribe=1 OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated
unset OMP_PROC_BIND OMP_PLACES KMP_AFFINITY GOMP_CPU_AFFINITY
extra=();if [[ $mode == pilot ]]; then export FAIR_PILOT=1;extra=(--columns 0);fi
OUT=$TASK/results/$label-$configuration-pyqcu-$mode;mkdir "$OUT"
mpirun --bind-to none -np "$ranks" python /home/share/nsls_lwb/.cache/pyqcu-kunpeng-recheck/bind_kunpeng_rank.py \
 python /home/share/nsls_lwb/.cache/pyqcu-propagator24-v20261103/native_cpu_bootstrap.py \
 --repo /home/share/nsls_lwb/PyQCU-lingsheng-v20261103 --script "$TASK/pyqcu_entry.py" -- \
 --gauge "$TASK/input/gauge-pyqcu-ap-c128.h5" --lat 24 24 24 64 --grid "${grid[@]}" \
 --mass -.277 --csw 1.160920226 --dtype c128 --atol 1e-8 --max-iter 6000 \
 --boundary 1 1 1 -1 --levels 1 --restart 0 --max-residual-restarts 2 --report "$OUT/result.json" "${extra[@]}"

