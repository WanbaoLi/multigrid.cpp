#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
gauge=$2
mkdir -p "$out"
exec > >(tee "$out/campaign.log") 2>&1
if [[ $# -ge 3 ]]; then
  # Resume with an existing build after a completed full regression gate.
  # Rebuild and rerun the storage/solve gates for the exact current commit.
  build=$3
  source "$root/tools/multinode/ls_env.sh"
  cmake --build "$build" -j 24
  ctest --test-dir "$build" --output-on-failure \
    -R '^(compact_basis|distributed_cpu_backend_mpi2|distributed_batch12_mpi2)$'
else
  bash "$root/tools/multinode/gate_ls.sh" "$out/gates"
  build=$out/gates/build
fi
bash "$root/tools/multinode/probe_ls.sh" "$build"
LQCD_MULTINODE_SKIP_GATES=1 bash "$root/tools/multinode/run_ls.sh" "$out/c24" \
 "$HOME/.cache/pyqcu-propagator24-v20261103/inputs/beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime" "$build" 24
LQCD_MULTINODE_SKIP_GATES=1 bash "$root/tools/multinode/run_ls.sh" "$out/solve" "$gauge" "$build" 64
