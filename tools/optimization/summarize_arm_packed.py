#!/usr/bin/env python3
"""Reduce independently verified baseline/packed/baseline health outputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ctest_evidence(path):
    text = path.read_text(encoding="utf-8",errors="replace")
    total = re.search(r"100% tests passed, 0 tests failed out of (\d+)",text)
    rows = [dict(name=m[1],seconds=float(m[2])) for m in re.finditer(
        r"\d+/\d+ Test\s+#\s*\d+: (\S+)\s+\.{2,}\s+Passed\s+([\d.]+) sec",text)]
    required = {"arm_sve_packed","arm_sve_packed_no_reuse",
                "arm_packed_backend_mpi2","arm_packed_batch12_mpi2"}
    if not total or len(rows) != int(total[1]) or not required <= {r["name"] for r in rows}:
        raise ValueError(f"missing successful required CTests: {path}")
    return dict(passed=True,count=len(rows),tests=rows,raw_run_log_sha256=digest(path))


def diagnostic_stages(path):
    text = path.read_text(encoding="utf-8",errors="replace")
    pattern = (r"native profile R ([\d.eE+-]+) coarse ([\d.eE+-]+) P ([\d.eE+-]+) "
               r"SAP ([\d.eE+-]+) nrhs (\d+) timing_scope shared_batch aggregation rank0_local_sums")
    batches = [tuple(map(float,m.groups())) for m in re.finditer(pattern,text)]
    if sum(r[4] for r in batches) != 12:
        raise ValueError(f"missing final diagnostic twelve-column stages: {path}")
    return dict(scope="unranked final diagnostic; rank0 local sums, not whole-node cycle fractions",
        batches=len(batches),restrict_seconds=sum(r[0] for r in batches),
        coarse_seconds=sum(r[1] for r in batches),prolong_seconds=sum(r[2] for r in batches),
        sap_seconds=sum(r[3] for r in batches))


def summarize(root):
    rows = []
    common = None
    keys = ("host", "lattice_xyzt", "grid_xyzt", "block_xyzt", "ranks",
            "mass", "csw", "tol", "source_xyzt", "source_scale", "gauge_sha256",
            "setup_threads", "solve_threads", "batch", "stout", "seed",
            "source_commit", "zero_initial_guess", "solve_environment")
    for name in ("baseline-a", "packed", "baseline-b"):
        path = root / name / "L24" / "result.json"
        data = load(path)
        verified = data["verification"]
        if not data["complete"] or not verified["complete"] or not verified["passed"]:
            raise ValueError(f"incomplete numerical gate: {name}")
        if len(verified["columns"]) != 13 or not data["zero_initial_guess"]:
            raise ValueError(f"missing columns or nonzero start: {name}")
        if data["tol"] > 1e-8 or any(not math.isfinite(c["residual"]) or
                c["residual"] > data["tol"] for c in verified["columns"]):
            raise ValueError(f"independent full residual gate failed: {name}")
        match = {k: data[k] for k in keys}
        match["smeared_gauge_sha256"] = verified["gauge_sha256"]
        match["independent_reference_sha256"] = verified["reference_sha256"]
        match["placement_cpus"] = [r["cpus"] for r in data["placement"]]
        if common is not None and match != common:
            raise ValueError(f"unmatched input/resources/source: {name}")
        common = match
        context = data["context_environment"].copy()
        packed = int(context.pop("LQCD_ARM_WILSON_PACKED", 0))
        if packed != int(name == "packed"):
            raise ValueError(f"wrong packed switch: {name}")
        if rows and context != rows[0]["context_environment_without_packing"]:
            raise ValueError(f"confounded context settings: {name}")
        phases = {}
        for phase in ("single", "twelve"):
            samples = data[phase + "_samples"]
            if len(samples) < 3:
                raise ValueError("need first, second and third zero-start samples")
            phases[phase] = dict(
                first_solver_seconds=samples[0]["native_solver_seconds"],
                second_solver_seconds=samples[1]["native_solver_seconds"],
                steady_solver_seconds=[s["native_solver_seconds"] for s in samples[1:]],
                steady_solver_median_seconds=statistics.median(s["native_solver_seconds"] for s in samples[1:]),
                steady_api_seconds=[s["wall_seconds"] for s in samples[1:]],
                steady_api_median_seconds=statistics.median(s["wall_seconds"] for s in samples[1:]),
                corrections=[s["refinement_steps"] for s in samples],
                iterations=[[c["iterations"] for c in s["stats"]] for s in samples])
        reuse_path = root/name/"build-reuse.json"
        reuse = load(reuse_path) if reuse_path.exists() else None
        tests = ctest_evidence(Path(reuse["ctest_log"]) if reuse else root/name/"run.log")
        tests["reused_from_checked_build"] = reuse
        rows.append(dict(attempt=name, result_sha256=digest(path),
            source_commit=data["source_commit"], library_sha256=data["library_sha256"],
            propagator_sha256=data["propagator_sha256"],
            context_environment_without_packing=context,
            setup_seconds=data["setup_seconds"], stout_seconds=data["stout_seconds"],
            independent_max_residual=verified["max_true_residual"],
            ctest=tests,
            diagnostic_stages=diagnostic_stages(root/name/"run.log"),
            phases=phases))
    a, packed, b = rows
    base = statistics.mean(r["phases"]["twelve"]["steady_solver_median_seconds"] for r in (a,b))
    trial = packed["phases"]["twelve"]["steady_solver_median_seconds"]
    drift = abs(a["phases"]["twelve"]["steady_solver_median_seconds"]-
                b["phases"]["twelve"]["steady_solver_median_seconds"])/base
    return dict(complete=True, numerically_passed=True, common=common, attempts=rows,
        metric="complete twelve-column native solver time; first sample excluded",
        baseline_bracket_mean_seconds=base, packed_steady_seconds=trial,
        relative_solver_reduction=1-trial/base, baseline_relative_drift=drift,
        bitwise_identical_propagators=len({r["propagator_sha256"] for r in rows}) == 1,
        promotion_automatic=False,
        interpretation="bounded same-node comparison; inspect scatter, API, iterations and corrections before promotion")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_root", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    value = summarize(args.run_root.resolve())
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in value.items() if k not in ("attempts","common")},indent=2))


if __name__ == "__main__":
    main()
