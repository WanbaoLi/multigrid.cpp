#!/usr/bin/env bash
# One allocated compute node: fresh build, selected CTest, then real 24/32^3x64
# single-column and full12 checks with one setup per configuration.
set -eo pipefail
if [[ $# -ne 4 || ("$1" != arm && "$1" != x86) ]]; then
    echo "usage: $0 arm|x86 NEW_RUN_ROOT GAUGE24 GAUGE32" >&2
    exit 2
fi
backend=$1
project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
run_root=$(realpath -m "$2")
gauge24=$(realpath -m "$3")
gauge32=$(realpath -m "$4")
geometries=${LQCD_HEALTH_GEOMETRIES:-24,32}
case "$geometries" in 24|32|24,32|32,24) ;; *) echo "LQCD_HEALTH_GEOMETRIES must be 24, 32 or 24,32" >&2; exit 2;; esac
case "$run_root/" in "$project_dir/"*) echo "Run outputs must be outside the source checkout" >&2; exit 2;; esac
case ",$geometries," in *,24,*) [[ -f "$gauge24" ]] || { echo "L24 gauge is missing: $gauge24" >&2; exit 2; };; esac
case ",$geometries," in *,32,*) [[ -f "$gauge32" ]] || { echo "L32 gauge is missing: $gauge32" >&2; exit 2; };; esac
[[ ! -e "$run_root" ]] || { echo "Run root already exists: $run_root" >&2; exit 2; }
mkdir -p "$run_root"
exec > >(tee "$run_root/run.log") 2>&1
build_dir=$run_root/build
active_scratch=
python_bin=${LQCD_HEALTH_PYTHON:-}
build_jobs=${LQCD_HEALTH_BUILD_JOBS:-16}
reference_threads=${LQCD_HEALTH_REFERENCE_THREADS:-8}
source_commit=$(git -C "$project_dir" rev-parse HEAD)
source_branch=$(git -C "$project_dir" rev-parse --abbrev-ref HEAD)
[[ -z $(git -C "$project_dir" status --porcelain --untracked-files=no) ]] || {
    echo "Source checkout contains tracked modifications" >&2; exit 2;
}
[[ -z ${LQCD_HEALTH_EXPECT_COMMIT:-} || "$source_commit" == "$LQCD_HEALTH_EXPECT_COMMIT" ]] || {
    echo "Source changed since submission" >&2; exit 2;
}
case "$backend:$(uname -m)" in
    arm:aarch64|arm:arm64|x86:x86_64|x86:amd64) ;;
    *) echo "Backend $backend does not match this node: $(uname -m)" >&2; exit 2;;
esac

case "$backend" in
arm)
    task_sdk=${LQCD_HEALTH_SDK:-/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001}
    task_sysroot=${LQCD_HEALTH_SYSROOT:-/work_ssd/system/os_jasmine_v01/vroot}
    task_kupl=$task_sdk/kupl/gcc/release
    task_cxx_runtime=$task_sdk/compiler/gcc/lib64
    python_bin=${python_bin:-$HOME/.cache/multigrid-arm-20261025-env/bin/python}
    source "$task_sdk/setvars.sh" --use-bisheng --force
    export CC=$task_sysroot/usr/bin/gcc CXX=$task_sysroot/usr/bin/g++
    export OMPI_CC=$CC OMPI_CXX=$CXX
    export CPATH=$task_sysroot/usr/include:$task_sysroot/usr/local/include
    export LIBRARY_PATH=$task_cxx_runtime:$task_sysroot/usr/lib64:$task_sysroot/usr/lib:${LIBRARY_PATH:-}
    export LD_LIBRARY_PATH=$task_cxx_runtime:$task_kupl/lib:$task_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
    export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
    mpi_flags='--host;localhost:4;--map-by;ppr:1:numa:PE=2;--bind-to;core'
    plan=$project_dir/profiles/optimization/lingsheng-052-full12.json
    plan24=${LQCD_HEALTH_PLAN24:-${LQCD_HEALTH_PLAN:-$plan}}
    plan32=${LQCD_HEALTH_PLAN32:-${LQCD_HEALTH_PLAN:-$plan}}
    launcher_threads=37
    ranks_per_numa=1
    numa_count24=16
    numa_count32=${LQCD_HEALTH_32_NUMA_COUNT:-16}
    ranks32=${LQCD_HEALTH_32_RANKS:-16}
    cmake_extra=(-DLQCD_KUPL_HBW=ON "-DLQCD_KUPL_ROOT=$task_kupl"
        "-DCMAKE_EXE_LINKER_FLAGS=-L$task_cxx_runtime -Wl,-rpath,$task_cxx_runtime"
        "-DCMAKE_SHARED_LINKER_FLAGS=-L$task_cxx_runtime -Wl,-rpath,$task_cxx_runtime")
    ;;
x86)
    task_mpi=${LQCD_HEALTH_MPI_PREFIX:-/public2/home/lwb_720/miniconda3/envs/pyquda}
    task_compiler=${LQCD_HEALTH_COMPILER_PREFIX:-/public2/home/lwb_720/miniconda3}
    python_bin=${python_bin:-$task_mpi/bin/python}
    export CC=$task_compiler/bin/gcc CXX=$task_compiler/bin/g++
    export PATH=$task_mpi/bin:$task_compiler/bin:$PATH
    export LD_LIBRARY_PATH=$task_mpi/lib:${LD_LIBRARY_PATH:-}
    mpi_flags='--map-by;slot:PE=2;--bind-to;core'
    plan=$project_dir/profiles/optimization/node5005-833-full12.json
    plan24=${LQCD_HEALTH_PLAN24:-${LQCD_HEALTH_PLAN:-$plan}}
    plan32=${LQCD_HEALTH_PLAN32:-${LQCD_HEALTH_PLAN:-$plan}}
    launcher_threads=16
    ranks_per_numa=2
    numa_count24=8
    numa_count32=${LQCD_HEALTH_32_NUMA_COUNT:-8}
    ranks32=${LQCD_HEALTH_32_RANKS:-16}
    cmake_extra=(-DLQCD_KUPL_HBW=OFF)
    ;;
esac
numa_nodes24=${LQCD_HEALTH_24_NUMA_NODES:-0-$((numa_count24-1))}
numa_nodes32=${LQCD_HEALTH_32_NUMA_NODES:-0-$((numa_count32-1))}
set -u
[[ -x "$python_bin" && -x "$CC" && -x "$CXX" ]] || { echo "Selected toolchain is incomplete" >&2; exit 2; }
export PATH=$(dirname "$python_bin"):$PATH
mpi_c=$(command -v mpicc)
mpi_cxx=$(command -v mpicxx)
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
# The saved plan sets runtime knobs deliberately. Do not inherit another run.
while IFS='=' read -r task_key task_value; do
    case "$task_key" in LQCD_*|NATIVE_*) unset "$task_key";; esac
done < <(env)
export PYTHONPATH=$project_dir/bindings:${PYTHONPATH:-}

on_exit() {
    task_exit=$?
    trap - EXIT
    if [[ -n "$active_scratch" && -d "$active_scratch/run" ]]; then
        mkdir -p "$run_root/failure-metadata"
        for task_file in "$active_scratch"/run/*.json; do
            [[ ! -f "$task_file" ]] || cp "$task_file" "$run_root/failure-metadata/"
        done
    fi
    "$python_bin" - "$run_root" "$task_exit" "$active_scratch" <<'PY'
import json, sys
from pathlib import Path
root, status, scratch = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
blocked = []
for preflight in root.glob('L*/resource-preflight.json'):
    d = json.loads(preflight.read_text())
    if not d.get('memory_sufficient', False):
        blocked.append(str(preflight))
(root/'status.json').write_text(json.dumps({
    'complete': status == 0, 'exit_code': status, 'blocked': blocked,
    'preserved_failed_scratch': scratch if status else None,
}, indent=2)+'\n')
PY
    exit "$task_exit"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$project_dir"
"$python_bin" - "$run_root" "$source_commit" "$source_branch" "$backend" "$gauge24" "$gauge32" "$plan24" "$plan32" "$geometries" <<'PY'
import json, platform, sys
from pathlib import Path
out, commit, branch, backend, gauge24, gauge32, plan24, plan32, geometries = sys.argv[1:]
d = dict(source_commit=commit, source_branch=branch, source= str(Path.cwd()),
         backend=backend, host=platform.node(), gauges={'L24':gauge24,'L32':gauge32},
         selected_geometries=geometries,
         plans={'L24':json.loads(Path(plan24).read_text()),'L32':json.loads(Path(plan32).read_text())})
Path(out,'source-and-plan.json').write_text(json.dumps(d,indent=2)+'\n')
PY
"$python_bin" tools/probe_host.py > "$run_root/host.json"
"$python_bin" - "$backend" <<'PY'
import os, sys
sys.path.insert(0, 'tools')
from run_numa import discover_nodes
nodes = discover_nodes()
backend = sys.argv[1]
expected_nodes, per_node = (16,37) if backend == 'arm' else (8,32)
assert len(nodes) == expected_nodes and all(len(c) == per_node for c in nodes.values()), nodes
assert len(os.sched_getaffinity(0)) == expected_nodes*per_node
print('ALLOWLIST_OK', len(nodes), 'NUMA', per_node, 'physical cores/domain')
PY
"$CC" --version | head -1
"$python_bin" -c 'from mpi4py import MPI; import numpy; print(MPI.Get_library_version()); print(numpy.__version__)'
: > "$run_root/inputs.sha256"
case ",$geometries," in *,24,*) sha256sum "$gauge24" >> "$run_root/inputs.sha256";; esac
case ",$geometries," in *,32,*) sha256sum "$gauge32" >> "$run_root/inputs.sha256";; esac
cmake -S "$project_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DMULTIGRID_NATIVE=ON \
    -DLQCD_BUILD_RUNTIME=ON -DLQCD_DD_REFERENCE=OFF \
    "-DCMAKE_C_COMPILER=$CC" "-DCMAKE_CXX_COMPILER=$CXX" \
    "-DMPI_C_COMPILER=$mpi_c" "-DMPI_CXX_COMPILER=$mpi_cxx" \
    "-DLQCD_TEST_PYTHON=$python_bin" "-DLQCD_MPI_FLAGS=$mpi_flags" "${cmake_extra[@]}"
cmake --build "$build_dir" -j "$build_jobs"
"$CXX" -O2 -std=c++17 benchmarks/runtime/extract_propagator_columns.cpp -o "$build_dir/extract_columns"
ctest --test-dir "$build_dir" --output-on-failure --parallel 1 \
    -R '^(core|arm_.*|wilson_.*|hbw_buffer|hbm_placement|native_allocator|numa_launcher|thread_defaults|cpu_backend_mpi2|runtime_batch|batch12_mpi2|lime_io|stout_smearing|propagator_io)$'
sha256sum "$build_dir/liblqcd_cpu.so" "$build_dir/multigrid" "$build_dir/extract_columns" > "$run_root/build.sha256"

run_geometry() {
    local label=$1 lattice=$2 block=$3 gauge=$4 mass=$5 csw=$6
    local plan_path=$7 selected_nodes=$8 case_ranks=$9
    mkdir "$run_root/$label"
    "$python_bin" - "$run_root/$label" "$lattice" "$block" "$plan_path" "$selected_nodes" "$case_ranks" <<'PY' > "$run_root/$label/launcher-args.txt"
import json, math, os, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from run_numa import discover_nodes, make_plan, parse_cpu_list
out, lattice, block, plan_path, selected_nodes, ranks = sys.argv[1:]
out, lattice, block, ranks = Path(out), int(lattice), int(block), int(ranks)
nodes = discover_nodes()
selected = parse_cpu_list(selected_nodes)
if not selected or ranks < len(selected) or ranks % len(selected):
    raise SystemExit('Ranks must divide the selected NUMA domains into a positive integral ranks-per-NUMA count')
settings = json.loads(Path(plan_path).read_text())
threads = int(settings['placement_threads'])
cases = settings['cases']
if len(cases) != 1 or max(int(settings['setup_threads']), int(cases[0]['threads'])) > threads:
    raise SystemExit('Plan must have one case and setup/solve threads must fit placement_threads')
topology = make_plan(nodes, [lattice,lattice,lattice,64], [block,block,block,4],
                     selected, threads, ranks//len(selected))
mem_available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
limits = []
# Capture both cgroup-v2 and cgroup-v1 finite memory budgets, including parents.
for line in Path('/proc/self/cgroup').read_text().splitlines():
    _, controllers, relative = line.split(':', 2)
    if controllers == '':
        mount, limit_name, used_name = Path('/sys/fs/cgroup'), 'memory.max', 'memory.current'
    elif 'memory' in controllers.split(','):
        mount, limit_name, used_name = Path('/sys/fs/cgroup/memory'), 'memory.limit_in_bytes', 'memory.usage_in_bytes'
    else:
        continue
    current = mount/relative.lstrip('/')
    while current == mount or mount in current.parents:
        try:
            value = (current/limit_name).read_text().strip()
            if value != 'max' and 0 < int(value) < 2**60:
                used = int((current/used_name).read_text().strip())
                limits.append(dict(path=str(current/limit_name), limit_bytes=int(value),
                                   used_bytes=used, available_bytes=max(0,int(value)-used)))
        except (OSError, ValueError):
            pass
        if current == mount:
            break
        current = current.parent
# Static native assets at 32^3x64 and 16 private MPI ranks: about 383 GiB
# double assets + 126 GiB private float assets. This is an estimated lower
# bound, not measured RSS; omitted workspaces require an additional margin.
lower_bound = math.ceil(509*1024**3*(lattice/32)**3*(ranks/16))
required = lower_bound + 16*1024**3
budget = min([mem_available, *[r['available_bytes'] for r in limits]])
preflight = dict(
    lattice_xyzt=[lattice,lattice,lattice,64], ranks=ranks,
    placement_threads=threads, setup_threads=int(settings['setup_threads']),
    solve_threads=int(cases[0]['threads']), numa_nodes=selected, topology=topology,
    plan_path=str(Path(plan_path).resolve()), plan=settings,
    estimated_live_bytes_lower_bound=lower_bound,
    estimate_kind='conservative_static_asset_lower_bound_not_measured_RSS',
    estimate_reference='32^3x64/16 MPI: approximately 383 GiB double assets plus 126 GiB private float assets; scaled by sites and ranks',
    safety_margin_bytes=16*1024**3, required_budget_bytes=required,
    mem_available_bytes=mem_available, cgroup_memory_budgets=limits,
    effective_memory_budget_bytes=budget, memory_sufficient=budget>=required,
)
(out/'resource-preflight.json').write_text(json.dumps(preflight,indent=2)+'\n')
if not preflight['memory_sufficient']:
    raise SystemExit(f'BLOCKED: {lattice}^3x64/{ranks} MPI static lower bound {lower_bound/1024**3:.1f} GiB '
                     f'+16 GiB margin exceeds available budget {budget/1024**3:.1f} GiB')
print(','.join(map(str, selected)))
print(ranks//len(selected))
print(threads)
PY
    local case_ranks_per_numa case_threads
    local -a launcher_values
    mapfile -t launcher_values < "$run_root/$label/launcher-args.txt"
    selected_nodes=${launcher_values[0]}
    case_ranks_per_numa=${launcher_values[1]}
    case_threads=${launcher_values[2]}
    "$python_bin" - <<'PY'
import shutil
assert shutil.disk_usage('/tmp').free >= 24*1024**3, 'Need 24 GiB of node-local /tmp for arrays and scalar verification'
PY
    active_scratch=$(mktemp -d "/tmp/lqcd-health-$backend-$label-XXXXXXXX")
    printf '%s\n' "$active_scratch" > "$run_root/scratch-$label.txt"
    "$python_bin" tools/run_numa.py --lattice "$lattice" "$lattice" "$lattice" 64 \
        --block "$block" "$block" "$block" 4 --numa-nodes "$selected_nodes" \
        --ranks-per-numa "$case_ranks_per_numa" --threads "$case_threads" -- \
        "$python_bin" -u benchmarks/runtime/check_lime_solver.py \
        --gauge "$gauge" --output "$active_scratch/run" --backend "$backend" \
        --mass "$mass" --csw "$csw" --block "$block" "$block" "$block" 4 \
        --plan "$plan_path" --library "$build_dir/liblqcd_cpu.so" --repeats 3 --tol 1e-8 \
        --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4
    "$python_bin" benchmarks/runtime/verify_lime_solver.py "$active_scratch/run" \
        --reference "$build_dir/multigrid" --extractor "$build_dir/extract_columns" \
        --reference-threads "$reference_threads" --tol 1e-8
    "$python_bin" - "$active_scratch" "$run_root/$label" <<'PY'
import json, shutil, sys
from pathlib import Path
scratch, out = map(lambda p: Path(p).resolve(), sys.argv[1:])
assert scratch.parent == Path('/tmp') and scratch.name.startswith('lqcd-health-')
run = scratch/'run'
report = json.loads((run/'result.json').read_text())
verification = json.loads((run/'verification.json').read_text())
assert report['complete'] and verification['passed'] and len(verification['columns']) == 13
for p in run.glob('*.json'):
    shutil.copyfile(p,out/p.name)
report['health_resource_preflight'] = json.loads((out/'resource-preflight.json').read_text())
report['large_arrays_retained'] = False
report['large_array_policy'] = 'independently checked in node-local scratch, removed after all thirteen residual checks'
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.rmtree(scratch)
print('VERIFIED_AND_ARCHIVED', report['lattice_xyzt'], report['single_summary'], report['twelve_summary'], flush=True)
PY
    active_scratch=
}
case ",$geometries," in
    *,24,*) run_geometry L24 24 6 "$gauge24" -0.277 1.160920226 "$plan24" "$numa_nodes24" 16;;
esac
case ",$geometries," in
    *,32,*) run_geometry L32 32 8 "$gauge32" -0.279 1.1606789224 "$plan32" "$numa_nodes32" "$ranks32";;
esac
echo "HEALTH_COMPLETE $run_root"

