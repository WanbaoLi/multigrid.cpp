#!/bin/bash
set -eo pipefail
TASK=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
source "$TASK/ours_env.sh"
export LQCD_OPT_ALLOCATION=single-source-outer-precision-v4
"$FAIR_PYTHON" -c 'import os,json,socket,time; from pathlib import Path; p=Path("/home/share/nsls_lwb/.cache/fair-solve-20261105-v4"); (p/"compute-startup.json").write_text(json.dumps(dict(host=socket.gethostname(),cpus=sorted(os.sched_getaffinity(0)),epoch=time.time(),status=[s for s in Path("/proc/self/status").read_text().splitlines() if s.startswith(("Mems_allowed_list:","Cpus_allowed_list:"))]),indent=2))'
exec "$FAIR_PYTHON" -u /home/share/nsls_lwb/.cache/mg-opt-20261103/source-delivery-297/tools/optimization/worker.py \
 --queue "$TASK/compute-queue" --lifetime 14000 --idle-timeout 1800
