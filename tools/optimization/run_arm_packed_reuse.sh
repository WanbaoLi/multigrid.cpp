#!/usr/bin/env bash
# Continue a completed baseline using the SAME tested binary on the SAME node.
# No repeated build/CTest: candidate-on MPI/kernel gates ran in the baseline.
set -eo pipefail
if [[ $# != 4 ]]; then
    echo "usage: $0 FROZEN_SOURCE CHECKED_BASELINE NEW_RUN_ROOT GAUGE24" >&2
    exit 2
fi
reuse_source=$(realpath "$1")
reuse_checked=$(realpath "$2")
reuse_root=$(realpath -m "$3")
reuse_gauge=$(realpath "$4")
reuse_python=$HOME/.cache/multigrid-arm-20261025-env/bin/python
reuse_build=$reuse_checked/build
[[ ! -e "$reuse_root" ]] || { echo 'Run root exists' >&2; exit 2; }
[[ -z $(git -C "$reuse_source" status --porcelain --untracked-files=no) ]] || exit 2
reuse_commit=$(git -C "$reuse_source" rev-parse HEAD)
reuse_controller=$(realpath "${BASH_SOURCE[0]}")
reuse_controller_commit=${LQCD_CONTROLLER_COMMIT:-unrecorded}
reuse_cases=${LQCD_LAYOUT_CASES:-packed baseline-b}
case "$reuse_cases" in 'packed baseline-b'|'baseline-b') ;; *) echo 'Unsupported continuation cases' >&2; exit 2;; esac
"$reuse_python" - "$reuse_checked" "$reuse_source" "$reuse_commit" <<'PY'
import json, socket, sys
from pathlib import Path
root, source, commit = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
report = json.loads((root/'L24/result.json').read_text())
assert json.loads((root/'status.json').read_text())['complete']
assert report['complete'] and report['verification']['passed']
assert report['source_commit'] == commit and report['host'] == socket.gethostname()
assert report['lattice_xyzt'] == [24,24,24,64] and report['grid_xyzt'] == [1,1,1,16]
assert report['zero_initial_guess'] and report['tol'] == 1e-8
assert str(source) == json.loads((root/'source-and-plan.json').read_text())['source']
log = (root/'run.log').read_text(errors='replace')
assert '100% tests passed, 0 tests failed out of 34' in log
for test in ['arm_sve_packed', 'arm_packed_backend_mpi2', 'arm_packed_batch12_mpi2']:
    assert test in log
PY
sha256sum -c "$reuse_checked/build.sha256"
mkdir -p "$reuse_root"
reuse_seed_label=$("$reuse_python" - "$reuse_checked/L24/result.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print('checked-packed' if int(d['context_environment'].get('LQCD_ARM_WILSON_PACKED',0)) else 'baseline-a')
PY
)
ln -s "$reuse_checked" "$reuse_root/$reuse_seed_label"
reuse_sdk=/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001
reuse_sysroot=/work_ssd/system/os_jasmine_v01/vroot
source "$reuse_sdk/setvars.sh" --use-bisheng --force
export LD_LIBRARY_PATH=$reuse_sdk/compiler/gcc/lib64:$reuse_sdk/kupl/gcc/release/lib:$reuse_sdk/hmpi/bisheng/release/hmpi/lib:${LD_LIBRARY_PATH:-}
export OMPI_MCA_ras=^donau OMPI_MCA_plm=isolated OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader,tcp
export PATH=$(dirname "$reuse_python"):$PATH
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close
unset LD_PRELOAD LD_DEBUG LD_DEBUG_OUTPUT PERF_COUNTER_ROOT OMP_WAIT_POLICY GOMP_SPINCOUNT
while IFS='=' read -r reuse_key reuse_value; do
    case "$reuse_key" in LQCD_*|NATIVE_*) unset "$reuse_key";; esac
done < <(env)
export PYTHONPATH=$reuse_source/bindings:${PYTHONPATH:-}
set -u
cd "$reuse_source"
"$reuse_python" - <<'PY'
import os, shutil
from tools.run_numa import discover_nodes
nodes = discover_nodes()
assert len(nodes) == 16 and all(len(c) == 37 for c in nodes.values()), nodes
assert len(os.sched_getaffinity(0)) == 592
assert shutil.disk_usage('/tmp').free >= 24*1024**3
PY
reuse_scratch=
trap 'echo "Interrupted/exit: preserve scratch $reuse_scratch"' EXIT
for reuse_case in $reuse_cases; do
    reuse_out=$reuse_root/$reuse_case
    mkdir -p "$reuse_out/L24"
    if [[ "$reuse_case" == packed ]]; then
        reuse_plan=$reuse_source/profiles/optimization/lingsheng-packed-coefficients.json
    else
        reuse_plan=$reuse_source/profiles/optimization/lingsheng-shared-uniform.json
    fi
    "$reuse_python" - "$reuse_out" "$reuse_checked" "$reuse_commit" "$reuse_controller" "$reuse_controller_commit" <<'PY'
import hashlib, json, sys
from pathlib import Path
out, checked, commit, controller = map(Path,sys.argv[1:5])
(out/'build-reuse.json').write_text(json.dumps(dict(
    source_commit=str(commit), checked_baseline=str(checked),
    ctest_log=str(checked/'run.log'), tests_repeated=False,
    controller_path=str(controller),
    controller_commit=sys.argv[5],
    controller_sha256=hashlib.sha256(controller.read_bytes()).hexdigest()),indent=2)+'\n')
PY
    reuse_scratch=$(mktemp -d /tmp/lqcd-health-arm-L24-reuse-XXXXXXXX)
    "$reuse_python" tools/run_numa.py --lattice 24 24 24 64 --block 6 6 6 4 \
        --numa-nodes 0-15 --ranks-per-numa 1 --threads 37 -- \
        "$reuse_python" -u benchmarks/runtime/check_lime_solver.py \
        --gauge "$reuse_gauge" --output "$reuse_scratch/run" --backend arm \
        --mass -0.277 --csw 1.160920226 --block 6 6 6 4 --plan "$reuse_plan" \
        --library "$reuse_build/liblqcd_cpu.so" --repeats 3 --tol 1e-8 \
        --stout-steps 1 --stout-rho 0.125 --stout-dir-ignore 4 --profile-diagnostic \
        > "$reuse_out/run.log" 2>&1
    "$reuse_python" benchmarks/runtime/verify_lime_solver.py "$reuse_scratch/run" \
        --reference "$reuse_build/multigrid" --extractor "$reuse_build/extract_columns" \
        --reference-threads 8 --tol 1e-8 >> "$reuse_out/run.log" 2>&1
    "$reuse_python" - "$reuse_scratch" "$reuse_out" <<'PY'
import json, shutil, sys
from pathlib import Path
scratch, out = map(lambda p: Path(p).resolve(),sys.argv[1:])
assert scratch.parent == Path('/tmp').resolve() and scratch.name.startswith('lqcd-health-arm-L24-reuse-')
report=json.loads((scratch/'run/result.json').read_text())
assert report['complete'] and report['verification']['passed']
assert len(report['verification']['columns']) == 13
for p in (scratch/'run').glob('*.json'): shutil.copyfile(p,out/'L24'/p.name)
report['large_arrays_retained']=False
report['build_reuse']=json.loads((out/'build-reuse.json').read_text())
(out/'L24/result.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'status.json').write_text(json.dumps(dict(complete=True,exit_code=0))+'\n')
shutil.rmtree(scratch)
print('REUSE_VERIFIED',out,report['twelve_summary'],flush=True)
PY
    reuse_scratch=
done
sha256sum -c "$reuse_checked/build.sha256"
echo "ARM_PACKED_REUSE_COMPLETE $reuse_root"
