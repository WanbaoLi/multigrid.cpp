#!/usr/bin/env python3
"""Compare complete, zero-start propagator solves on subsets of one CPU node."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from run_numa import discover_nodes, make_plan


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def command_report(argv):
    if shutil.which(argv[0]) is None:
        return {"available": False}
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    return {"available": True, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def validate_result(result, count, threads, repeats):
    if not result.get("complete") or len(result.get("samples", [])) != repeats:
        raise ValueError("incomplete propagator run")
    if result["grid_xyzt"] != [1, 1, 1, count]:
        raise ValueError("unexpected MPI decomposition")
    if [entry["threads"] for entry in result["resources"]] != threads:
        raise ValueError("runtime thread counts disagree with NUMA plan")
    if result["initial_guess"] != "zero_for_every_column_every_round":
        raise ValueError("benchmark requires independent zero initial guesses")
    for sample in result["samples"]:
        if len(sample["stats"]) != 12 or any(
            not stat["converged"] or not math.isfinite(stat["true_residual"])
            or stat["true_residual"] > result["input"]["tol"]
            for stat in sample["stats"]
        ):
            raise ValueError("one or more columns failed the full residual gate")


def solver_seconds(sample):
    # The runtime duplicates shared-batch timing in each member's stats.
    stats = sample["stats"]
    total, column = 0.0, 0
    while column < len(stats):
        stat = stats[column]
        batch = int(stat.get("batch_size", 1))
        if batch < 1 or column + batch > len(stats):
            raise ValueError("invalid shared-batch timing")
        if batch > 1 and stat.get("timing_scope") != "shared_batch":
            raise ValueError("unknown batch timing scope")
        total += stat["solver_seconds"]
        column += batch
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gauge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--numa-counts", type=int, nargs="+", default=[8, 16])
    parser.add_argument("--threads", type=int, help="per-rank threads; default all allowed physical cores")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--mpirun", default="mpirun")
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--mass", type=float, default=-.277)
    parser.add_argument("--csw", type=float, default=1.160920226)
    parser.add_argument("--block", type=int, nargs=4, default=[6, 6, 6, 4])
    parser.add_argument("--lattice", type=int, nargs=4, default=[24, 24, 24, 64])
    parser.add_argument("--backend", choices=["arm", "x86"], default="arm")
    parser.add_argument("--rhs-batch", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.repeats < 2 or not 1 <= args.rhs_batch <= 12:
        parser.error("at least two rounds and RHS batch must be between 1 and 12")
    if not args.numa_counts or len(set(args.numa_counts)) != len(args.numa_counts):
        parser.error("NUMA counts must be nonempty and distinct")
    if any(count < 1 for count in args.numa_counts):
        parser.error("NUMA counts must be positive")
    nodes = discover_nodes()
    counts = sorted(args.numa_counts)
    if counts[-1] > len(nodes):
        parser.error(f"need {counts[-1]} available CPU NUMA domains, found {len(nodes)}")
    plans = [make_plan(nodes, args.lattice, args.block,
                       selected=sorted(nodes)[:count], threads=args.threads)
             for count in counts]
    # This experiment doubles ranks at fixed per-rank resources. Refuse an
    # accidental mixed-width/cpuset comparison instead of labelling it scaling.
    widths = {width for plan in plans for width in plan["threads_per_rank"]}
    if len(widths) != 1:
        parser.error("selected NUMA domains must have equal per-rank thread counts")
    gauge, library = args.gauge.expanduser().resolve(), args.library.expanduser().resolve()
    if not gauge.is_file() or not library.is_file():
        parser.error("gauge and runtime library must exist")
    output = args.output.expanduser().resolve()
    tools = Path(__file__).resolve().parent
    commands = []
    for count, plan in zip(counts, plans):
        commands.append([
            sys.executable, str(tools / "run_numa.py"),
            "--lattice", *map(str, args.lattice), "--block", *map(str, args.block),
            "--numa-nodes", ",".join(map(str, sorted(nodes)[:count])),
            "--threads", str(plan["threads_per_rank"][0]), "--mpirun", args.mpirun,
            "--", sys.executable, "-u", str(tools / "solve_propagator.py"),
            "--backend", args.backend, "--gauge", str(gauge),
            "--mass", str(args.mass), "--csw", str(args.csw),
            "--block", *map(str, args.block), "--stout-steps", "1", "--stout-rho", ".125",
            "--stout-dir-ignore", "4", "--tol", "1e-8", "--repeats", str(args.repeats),
            "--save-gauge", "--output", str(output / f"numa{count}")])
    if args.dry_run:
        print(json.dumps({"plans": plans, "commands": commands}, indent=2))
        return
    # A fresh directory prevents overwriting previous scientific evidence.
    output.mkdir(parents=True, exist_ok=False)
    report = dict(complete=False, host=socket.gethostname(), plans=plans, commands=commands,
                  gauge_sha256=sha256(gauge), library_sha256=sha256(library),
                  scheduler={key: os.environ[key] for key in (
                      "SLURM_JOB_ID", "SLURM_JOB_NODELIST", "SLURM_JOB_CPUS_PER_NODE",
                      "SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE", "SLURM_JOB_PARTITION")
                      if key in os.environ},
                  environment={key: value for key, value in sorted(os.environ.items())
                               if key.startswith(("LQCD_", "OMP_", "MPICH_", "OMPI_"))},
                  memory_policy=command_report(["numactl", "--show"]),
                  topology=command_report(["numactl", "--hardware"]), cases=[])
    report_path = output / "scaling.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    env = dict(os.environ, LQCD_CPU_LIBRARY=str(library),
               LQCD_RHS_BATCH=str(args.rhs_batch), OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    for count, plan, command in zip(counts, plans, commands):
        print(f"Starting {count} NUMA, {sum(plan['threads_per_rank'])} physical cores", flush=True)
        begin = time.monotonic()
        with (output / f"numa{count}.log").open("x") as log:
            subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        result_path = output / f"numa{count}" / "result.json"
        result = json.loads(result_path.read_text())
        validate_result(result, count, plan["threads_per_rank"], args.repeats)
        if result["gauge_sha256"] != report["gauge_sha256"] or result["library_sha256"] != report["library_sha256"]:
            raise ValueError("input/library changed during scaling comparison")
        case = dict(numa_domains=count, mpi_ranks=count,
                    threads_per_rank=plan["threads_per_rank"],
                    physical_cores=sum(plan["threads_per_rank"]),
                    setup_seconds=result["setup_seconds"],
                    first_seconds=result["first_seconds"], second_seconds=result["second_seconds"],
                    steady_median_seconds=result["steady_median_seconds"],
                    solver_second_seconds=solver_seconds(result["samples"][1]),
                    rounds=[sample["wall_seconds"] for sample in result["samples"]],
                    iterations_second=[s["iterations"] for s in result["samples"][1]["stats"]],
                    refinement_second=[s["refinement_steps"] for s in result["samples"][1]["stats"]],
                    max_true_residual=result["max_true_residual"],
                    result_sha256=sha256(result_path), total_case_seconds=time.monotonic() - begin)
        report["cases"].append(case)
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(case), flush=True)
    base = report["cases"][0]
    for case in report["cases"]:
        case["second_speedup"] = base["second_seconds"] / case["second_seconds"]
        case["parallel_efficiency"] = case["second_speedup"] * base["physical_cores"] / case["physical_cores"]
    report["complete"] = True
    report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
