"""Select a validated single-node candidate or compute two-node strong scaling."""

import argparse
import json
import math
from pathlib import Path


SWEEP = [(16, 0), (16, 8), (32, 0), (32, 8)]


def verified(case):
    report = json.loads((case / "result.json").read_text())
    rows = report["independent_verification"]["columns"]
    residual = rows[0]["residual"] if len(rows) == 1 and rows[0]["column"] == 0 else math.inf
    sample = report["single_samples"][1]
    elapsed = report["single_pure_summary"]["second_seconds"]
    if (not report["complete"] or not report["independent_verification"]["passed"]
            or not report["zero_initial_guesses"] or report["source"] != "wall"
            or not 0 <= residual <= report["tol"] <= 1e-8
            or not math.isfinite(elapsed) or elapsed <= 0 or sample["run"] != 2):
        raise ValueError(f"Invalid warmed single-column result in {case}")
    return {
        "case": case.name, "fixture_sha256": report["input_sha256"],
        "library_sha256": report["library_sha256"], "lattice_xyzt": report["lattice_xyzt"],
        "block_xyzt": report["block_xyzt"], "mass": report["mass"], "csw": report["csw"],
        "tol": report["tol"], "ranks": report["ranks"], "ranks_per_node": report["ranks_per_node"],
        "threads_per_rank": report["threads"], "hosts": sorted({r["host"] for r in report["placement"]}),
        "coarse_threads": int(report["context_environment"].get("LQCD_COARSE_THREADS", 0)),
        "solver_seconds": elapsed, "independent_full_residual": residual,
        "correction_solves_occurred": sample["correction_solves_occurred"],
    }


def check_comparable(reference, candidate):
    keys = ("fixture_sha256", "library_sha256", "lattice_xyzt", "block_xyzt", "mass", "csw", "tol")
    if any(reference[key] != candidate[key] for key in keys):
        raise ValueError("Fixture, solver, or operator differs between cases")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--two", type=Path)
    args = parser.parse_args()
    baseline = args.work / "native-one-mpi16-coarse0"
    if args.two is None:
        cases = []
        missing = []
        for ranks, coarse in SWEEP:
            path = args.work / f"native-one-mpi{ranks}-coarse{coarse}"
            if not (path / "result.json").is_file():
                missing.append(path.name)
                continue
            result = verified(path)
            if cases:
                check_comparable(cases[0], result)
            if ((cases and result["hosts"] != cases[0]["hosts"]) or len(result["hosts"]) != 1
                    or result["ranks"] != ranks or result["ranks_per_node"] != ranks
                    or result["threads_per_rank"] * ranks != 512 or result["coarse_threads"] != coarse):
                raise ValueError(f"Inconsistent placement or tuning in {result['case']}")
            cases.append(result)
        if not cases:
            raise ValueError("No candidate passed independent validation")
        best = min(cases, key=lambda result: result["solver_seconds"])
        summary = {"best_measured": best["case"], "cases": cases, "missing_verified_result": missing}
        output = args.work / "single-node-sweep.json"
    else:
        reference = verified(baseline)
        candidate = verified(args.two)
        check_comparable(reference, candidate)
        if (len(reference["hosts"]) != 1 or len(candidate["hosts"]) != 2
                or candidate["ranks"] != 2 * reference["ranks"]
                or any(reference[key] != candidate[key]
                       for key in ("ranks_per_node", "threads_per_rank", "coarse_threads"))):
            raise ValueError("Two-node run did not match the per-node baseline")
        speedup = reference["solver_seconds"] / candidate["solver_seconds"]
        summary = {"one_node": reference, "two_nodes": candidate, "speedup": speedup,
                   "parallel_efficiency": speedup / 2}
        output = args.work / "strong-scaling.json"
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(summary, indent=2) + "\n")
    temporary.replace(output)
    print(output)


if __name__ == "__main__":
    main()
