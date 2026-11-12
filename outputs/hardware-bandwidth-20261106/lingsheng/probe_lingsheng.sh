#!/usr/bin/env bash
#DSUB -q q_hpcapp
#DSUB -n bandwidth-memory-probe
#DSUB -N 1
#DSUB -R "cpu=592;mem=96G"
#DSUB -oo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/probe-r2.stdout
#DSUB -eo /home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105/probe-r2.stderr
#DSUB -T 600
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105
source /home/share/nsls_lwb/.cache/pyqcu-lingsheng-v20261103/env.sh
export LD_LIBRARY_PATH=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release/lib:${LD_LIBRARY_PATH}
export LD_PRELOAD=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64/libstdc++.so.6
mkdir -p "$TASK/probe"
python "$TASK/probe_memory.py" "$TASK/probe" \
 /home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/kupl/gcc/release/lib/libkupl.so.25.1.0.SPC001
