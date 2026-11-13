#!/usr/bin/env bash
# Select a whole available Kunpeng compute node and submit a fresh health run.
# All submission metadata and logs are written beside, not inside, the source.
set -euo pipefail
if [[ $# -ne 3 ]]; then
    echo "usage: $0 NEW_RUN_ROOT GAUGE24 GAUGE32" >&2
    exit 2
fi
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
run_root=$(realpath -m "$1")
gauge24=$(realpath "$2")
gauge32=$(realpath "$3")
submission_root=$run_root.submission
queue=${LQCD_HEALTH_QUEUE:-q_hpcapp}
account=${LQCD_HEALTH_ACCOUNT:-common}
task_timeout=${LQCD_HEALTH_TIMEOUT:-7200}
python_bin=${LQCD_HEALTH_PYTHON:-$HOME/.cache/multigrid-arm-20261025-env/bin/python}
requested_node=${LQCD_HEALTH_LS_NODE:-}
case "$run_root/" in "$project_dir/"*) echo "Run outputs must be outside source checkout" >&2; exit 2;; esac
[[ -x "$python_bin" && -f "$gauge24" && -f "$gauge32" ]] || {
    echo "The selected Python and both LIME gauges must exist" >&2; exit 2;
}
[[ ! -e "$run_root" && ! -e "$submission_root" ]] || {
    echo "Run root or submission directory already exists" >&2; exit 2;
}
[[ -z $(git -C "$project_dir" status --porcelain --untracked-files=no) ]] || {
    echo "Source checkout contains tracked modifications" >&2; exit 2;
}
source_commit=$(git -C "$project_dir" rev-parse HEAD)
mkdir -p "$submission_root"
dnode -q "$queue" -J > "$submission_root/nodes.json"
node=$("$python_bin" - "$submission_root/nodes.json" "$submission_root/selected-node.json" "$requested_node" <<'PY'
import json, sys
from pathlib import Path
source, output, requested = sys.argv[1:]
payload = json.loads(Path(source).read_text())
if payload.get('code') != 'success' or not isinstance(payload.get('data'), list):
    raise SystemExit('Donau did not return a successful node list')
candidates = []
for row in payload['data']:
    native = row.get('nativeResources', {})
    load = native.get('loadResources', {})
    reserved = native.get('osReservedResources', {})
    available = native.get('availableResources', {})
    numa = row.get('numaInfo', {})
    if requested and row.get('nodeName') != requested:
        continue
    if row.get('status') != 'OK' or int(row.get('runningJobsCount', -1)) != 0:
        continue
    if int(reserved.get('cpu', 0)) != 16 or int(available.get('cpu', 0)) != 592:
        continue
    if int(load.get('cpuFree', 0)) < 592 or int(load.get('memFree', 0)) <= 480000:
        continue
    if int(available.get('mem', 0)) < 480000 or int(numa.get('nNumaNodes', 0)) != 16:
        continue
    if numa.get('architecture') != 'aarch64' or int(row.get('reservedCPU', 0)) != 0:
        continue
    if int(row.get('reservedMEM', 0)) != 0:
        continue
    candidates.append(row)
if not candidates:
    raise SystemExit('BLOCKED: no idle OK aarch64 node with 16 OS-reserved cores, '
                     '592 available/free cores and >480000 MB free memory')
candidates.sort(key=lambda r: (
    float(r['nativeResources']['loadResources'].get('util', 1.0)),
    -int(r['nativeResources']['loadResources']['memFree']), r['nodeName']))
chosen = candidates[0]
Path(output).write_text(json.dumps({
    'selected_node': chosen, 'eligible_nodes': len(candidates),
    'selection': 'lowest reported utilization, then largest free memory; not a reservation',
}, indent=2)+'\n')
print(chosen['nodeName'])
PY
)
job_script=$submission_root/job.sh
printf '#!/usr/bin/env bash\nset -euo pipefail\nexport LQCD_HEALTH_EXPECT_COMMIT=%q\nexec bash %q arm %q %q %q\n' \
    "$source_commit" "$project_dir/tools/health/run_single_node.sh" "$run_root" "$gauge24" "$gauge32" \
    > "$job_script"
"$python_bin" - "$submission_root/submission.json" "$source_commit" "$project_dir" "$run_root" "$queue" "$account" "$node" "$task_timeout" <<'PY'
import json, sys
from pathlib import Path
target, commit, source, run, queue, account, node, timeout = sys.argv[1:]
Path(target).write_text(json.dumps({
    'source_commit': commit, 'source': source, 'run_root': run,
    'queue': queue, 'account': account, 'node': node,
    'replicas': 1, 'nodes': 1, 'cpu': 592, 'memory_MB': 480000,
    'timeout_seconds': int(timeout),
}, indent=2)+'\n')
PY
dsub -q "$queue" -A "$account" -nn 1 -N 1 -x job -nl "$node" \
    -R 'cpu=592,mem=480000MB' -T "$task_timeout" --cwd "$submission_root" \
    -o "$submission_root/job.log" /bin/bash "$job_script" \
    | tee "$submission_root/submission.txt"
echo "SUBMITTED node=$node metadata=$submission_root results=$run_root"

