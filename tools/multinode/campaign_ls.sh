#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$1
gauge=$2
mkdir -p "$out"
exec > >(tee "$out/campaign.log") 2>&1
bash "$root/tools/multinode/gate_ls.sh" "$out/gates"
bash "$root/tools/multinode/probe_ls.sh" "$out/gates/build"
bash "$root/tools/multinode/run_ls.sh" "$out/solve" "$gauge" "$out/gates/build"
