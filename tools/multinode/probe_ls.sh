#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/multinode/ls_env.sh"
unset OMPI_MCA_ras OMPI_MCA_plm OMPI_MCA_btl OMPI_MCA_pml
export OMPI_MCA_coll=${LQCD_MPI_COLLECTIVES:-basic,tuned,self,libnbc}
export OMPI_MCA_pml=${LQCD_MPI_PML:-ob1} OMPI_MCA_btl=${LQCD_MPI_BTL:-self,vader,tcp}
if [[ -n ${LQCD_MPI_TCP_IF:-} ]]; then
  export OMPI_MCA_btl_tcp_if_include=$LQCD_MPI_TCP_IF
  export OMPI_MCA_oob_tcp_if_include=$LQCD_MPI_TCP_IF
fi
echo PROBE_HOST $(hostname)
python - <<'PY'
import os
for k in sorted(os.environ):
    if k in ('CCS_ALLOC_FILE','CCS_HOST_FILE','CCS_JOB_ID','DONAU_JOB_ID','MPI_HOSTFILE','PMI_SIZE'):
        print(k,os.environ[k])
        if 'FILE' in k:
            print(open(os.environ[k]).read())
PY
timeout 90s mpirun -n 32 --bind-to none python "$root/tools/multinode/rank_exec.py" \
  python -u "$root/tests/runtime/test_multinode_communication.py"
echo MULTIHOST_GATE_PASSED
