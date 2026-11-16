#!/usr/bin/env python3
"""Same-node baseline/candidate/baseline full12 comparison, using NUMA-derived teams."""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
import socket
import shutil
import statistics
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "tools"))
from run_numa import discover_nodes, make_plan


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024**2), b""):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def run(argv, log, env=None):
    print("STAGE", log.name, flush=True)
    with log.open("w") as f:
        subprocess.run(list(map(str, argv)), stdout=f, stderr=subprocess.STDOUT,
                       env=env, check=True)


def snapshot(source):
    # Exports contain only committed Git files plus this explicit provenance.
    revision = json.loads((source / "source-revision.json").read_text())
    h = hashlib.sha256()
    for p in sorted(source.rglob("*")):
        if (p.is_file() and p.name != "source-revision.json" and ".git" not in p.parts
                and "__pycache__" not in p.parts and p.suffix != ".pyc"):
            h.update(p.relative_to(source).as_posix().encode() + b"\0")
            h.update(bytes.fromhex(sha(p)))
    return dict(**revision, manifest_sha256=h.hexdigest())


def solve_seconds(sample, batch):
    stats = sample["stats"]
    assert len(stats) == 12
    total = 0.
    for i in range(0, len(stats), batch):
        group = stats[i:i + batch]
        assert all(s["solver_seconds"] == group[0]["solver_seconds"] for s in group)
        total += group[0]["solver_seconds"]
    return total


def summarize(root, runs):
    groups = []
    for name, version in runs:
        report = json.loads((root / name / "full12" / "result.json").read_text())
        assert report["verification"]["passed"] and report["zero_initial_guess"]
        samples = report["samples"]
        steady = [s for s in samples if not s["warmup"]]
        groups.append(dict(name=name, version=version,
            library_sha256=report["library_sha256"], setup_seconds=report["setup_seconds"],
            api_samples_seconds=[s["wall_seconds"] for s in samples],
            solver_samples_seconds=[solve_seconds(s, 2) for s in samples],
            api_steady_median=statistics.median(s["wall_seconds"] for s in steady),
            solver_steady_median=statistics.median(solve_seconds(s, 2) for s in steady),
            correction_solves_occurred=any(r["refinement_steps"] for s in samples for r in s["stats"]),
            correction_steps=[[r["refinement_steps"] for r in s["stats"]] for s in samples],
            max_internal_residual=max(r["true_residual"] for s in samples for r in s["stats"]),
            verification=report["verification"]))
    a, b, closing = groups
    mean_control = (a["api_steady_median"] + closing["api_steady_median"]) / 2
    gain = 1 - b["api_steady_median"] / mean_control
    drift = abs(a["api_steady_median"] - closing["api_steady_median"]) / mean_control
    result = dict(complete=True, host=socket.gethostname(), groups=groups,
        candidate_api_reduction_vs_mean_control=gain, control_relative_drift=drift,
        candidate_faster_than_both_controls=b["api_steady_median"] < min(
            a["api_steady_median"], closing["api_steady_median"]),
        scope="bounded A/B/A, one compute node, full12 API; no global-optimum claim")
    save(root / "summary.json", result)
    print(json.dumps(result), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend", choices=["arm", "x86"], required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--gold", type=Path, required=True)
    args = p.parse_args()
    archive = args.output.resolve()
    archive.mkdir(exist_ok=False, parents=True)
    # Build, arrays and byte-extracted scalar inputs stay on the allocated
    # node, avoiding shared-home quotas and shared-filesystem timing noise.
    assert shutil.disk_usage("/tmp").free >= 24 * 1024**3, "Need 24 GiB node-local scratch"
    root = Path(tempfile.mkdtemp(prefix="lqcd-fine-sites-"))
    state = dict(complete=False, node_local_outputs=str(root), host=socket.gethostname())

    def archive_metadata():
        for source in root.rglob("*.json"):
            relative = source.relative_to(root)
            if any(part.startswith("build-") for part in relative.parts):
                continue
            target = archive / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for source in root.glob("*.log"):
            shutil.copyfile(source, archive / source.name)
        save(archive / "status.json", state)
        print("ARCHIVED_METADATA", str(archive), flush=True)

    atexit.register(archive_metadata)
    sources = {v: getattr(args, v).resolve() for v in ("baseline", "candidate")}
    identities = {v: snapshot(s) for v, s in sources.items()}
    nodes = discover_nodes()
    per_numa = 1 if args.backend == "arm" else 2
    topology = make_plan(nodes, [24, 24, 24, 64], [6, 6, 6, 4], ranks_per_numa=per_numa)
    assert topology["ranks"] == 16, "This comparison requires 16 MPI ranks"
    widths = topology["threads_per_rank"]
    assert len(set(widths)) == 1, "Existing frozen-fixture driver requires uniform teams"
    threads = widths[0]  # Measured allocation, never a machine-specific constant.
    profile = "lingsheng-shared-uniform.json" if args.backend == "arm" else "node5005-833-full12.json"
    plan = json.loads((PROJECT / "profiles/optimization" / profile).read_text())
    plan.update(placement_threads=threads, setup_threads=threads)
    plan["cases"] = [dict(id="full12", threads=threads, batch=2,
                          environment={"LQCD_COARSE_BATCH_REDUCE": 1})]
    save(root / "plan.json", plan)
    save(root / "provenance.json", dict(host=socket.gethostname(), sources=identities,
        control_source=snapshot(PROJECT), topology=topology,
        fixture=str(args.fixture), gold=str(args.gold), gold_sha256=sha(args.gold),
        zero_initial_guess=True, sequence=["baseline", "candidate", "baseline"],
        samples_per_process="first warmup + three steady full12 solves",
        allocation=os.environ.get("DONAU_JOB_ID", "same exclusive compute-node job")))
    for version, source in sources.items():
        build = root / ("build-" + version)
        command = ["cmake", "-S", source, "-B", build, "-DCMAKE_BUILD_TYPE=Release",
            "-DMULTIGRID_NATIVE=ON", "-DLQCD_BUILD_RUNTIME=ON", "-DLQCD_DD_REFERENCE=OFF",
            "-DCMAKE_C_COMPILER=" + os.environ["CC"],
            "-DCMAKE_CXX_COMPILER=" + os.environ["CXX"],
            "-DLQCD_TEST_PYTHON=" + sys.executable,
            "-DLQCD_MPI_FLAGS=--host;localhost:4;--bind-to;none"]
        if args.backend == "arm":
            sdk = Path(os.environ["LQCD_COMPARISON_SDK"])
            runtime = sdk / "compiler/gcc/lib64"
            flags = "-L" + str(runtime) + " -Wl,-rpath," + str(runtime)
            command += ["-DLQCD_KUPL_HBW=ON", "-DLQCD_KUPL_ROOT=" + str(sdk / "kupl/gcc/release"),
                "-DCMAKE_EXE_LINKER_FLAGS=" + flags, "-DCMAKE_SHARED_LINKER_FLAGS=" + flags]
        run(command, root / ("configure-" + version + ".log"))
        run(["cmake", "--build", build, "-j", "16"], root / ("build-" + version + ".log"))
        test_env = dict(os.environ, OMP_NUM_THREADS="2", OMP_PLACES="cores", OMP_PROC_BIND="close")
        run(["ctest", "--test-dir", build, "--output-on-failure", "-R",
             "^(core|arm_.*|wilson_.*|fine_site_work|fine_site_balance_mpi[124]|cpu_backend_mpi2|shared_cpu_backend_mpi2|batch12_mpi2|shared_batch12_mpi2|numa_launcher)$"],
            root / ("ctest-" + version + ".log"), test_env)
    reference = root / "build-baseline/multigrid"
    extractor = root / "extract_columns"
    run([os.environ["CXX"], "-O2", "-std=c++17", PROJECT / "benchmarks/runtime/extract_propagator_columns.cpp",
         "-o", extractor], root / "extractor-build.log")
    runs = [("01-baseline", "baseline"), ("02-candidate", "candidate"), ("03-baseline", "baseline")]
    # No verification compute or other benchmarks between the A/B/A processes.
    for name, version in runs:
        run([sys.executable, PROJECT / "tools/run_numa.py", "--ranks-per-numa", str(per_numa), "--",
             sys.executable, "-u", PROJECT / "tools/optimization/bench_full12.py",
             "--fixture", args.fixture, "--plan", root / "plan.json",
             "--library", root / ("build-" + version) / "liblqcd_cpu.so", "--backend", args.backend,
             "--output", root / name, "--allocation", socket.gethostname() + "-fine-sites-aba",
             "--snapshot-sha", identities[version]["manifest_sha256"],
             "--reference-propagator", args.gold], root / (name + ".log"))
    for name, _ in runs:
        run([sys.executable, PROJECT / "tools/optimization/bench_full12.py", "--verify",
             root / name / "full12", "--reference", reference, "--extractor", extractor],
            root / (name + "-verify.log"))
    assert all(snapshot(s) == identities[v] for v, s in sources.items()), "Source export changed during run"
    summarize(root, runs)
    state["complete"] = True


if __name__ == "__main__":
    main()
