#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/multinode/ls_env.sh"
unset OMPI_MCA_ras OMPI_MCA_plm OMPI_MCA_btl OMPI_MCA_pml
export OMPI_MCA_coll=${LQCD_MPI_COLLECTIVES:-basic,tuned,self,libnbc}
export OMPI_MCA_pml=${LQCD_MPI_PML:-ob1} OMPI_MCA_btl=${LQCD_MPI_BTL:-self,vader,tcp}
echo PROBE_HOST $(hostname)
python - <<'PY'
import os
for k in sorted(os.environ):
    if k in ('CCS_ALLOC_FILE','CCS_HOST_FILE','CCS_JOB_ID','DONAU_JOB_ID','MPI_HOSTFILE','PMI_SIZE'):
        print(k,os.environ[k])
        if 'FILE' in k:
            print(open(os.environ[k]).read())
PY
mpirun -n 2 --map-by ppr:1:node --bind-to none hostname
export PYTHONPATH=$root/bindings
export LQCD_CPU_LIBRARY=$1/liblqcd_cpu.so
export LQCD_DISTRIBUTED_STORAGE=1
mpirun -n 2 --map-by ppr:1:node:PE=2 --bind-to core python "$root/tests/runtime/test_cpu_backend.py"
echo MULTIHOST_GATE_PASSED
