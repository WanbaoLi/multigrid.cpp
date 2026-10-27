"""Numerical gates for a fresh, complete GPU/CPU run (run on node5006)."""

import json
import re
import sys
from pathlib import Path
import numpy as np

root = Path(sys.argv[1])
q = root / "quda"
report = {}


def gate(name, value, limit):
    value = float(value)
    report[name] = {
        "value": value,
        "limit": limit,
        "pass": bool(np.isfinite(value) and value <= limit),
    }
    print(
        f"{name}: {value:.9e} <= {limit:.3e} "
        + ("PASS" if report[name]["pass"] else "FAIL"),
        flush=True,
    )


def relative(a, b):
    return float(np.linalg.norm(a - b) / max(float(np.linalg.norm(a)), 1e-300))


from oracle_io import read_trace


def trace(name):
    return read_trace(q, name)


log = (root / "logs/quda.log").read_text()
meta = json.loads((q / "quda_mg_ref_meta.json").read_text())
for key, expected in {
    "tol": 1e-10,
    "restart": 8,
    "solve_type": "DIRECT",
    "coarse_solver": "GCR",
    "smoother": "CA_GCR",
    "initial_guess": "zero",
    "coarse_dof": 48,
    "nu_pre": 0,
    "nu_post": 1,
    "coarse_tol": 0.5,
    "coarse_maxiter": 8,
}.items():
    if meta[key] != expected:
        raise RuntimeError(f"input mismatch: {key}: {meta[key]} != {expected}")
source = np.fromfile(q / "source.bin", np.complex128)
gate("source norm", abs(np.linalg.norm(source) - 1), 1e-14)
for mode, tag in [("plain", "PLAIN"), ("mg", "MG")]:
    stage = root / ("gcr" if mode == "plain" else "mg")
    cpu = stage / "x.bin"
    qx = np.load(
        q / ("plain_solution.npy" if mode == "plain" else "pyquda_mg_solution.npy")
    ).reshape(-1)
    cx = np.fromfile(cpu, np.complex128)
    cparams = json.loads(Path(str(cpu) + ".params.json").read_text())
    for key in (
        "tol",
        "restart",
        "maxiter",
        "initial_guess",
        "solve_type",
        "mass",
        "coarse_dof",
        "nu_pre",
        "nu_post",
        "coarse_tol",
        "coarse_maxiter",
        "coarse_solver",
        "smoother",
        "lattice",
        "mg_block",
        "nvec",
        "kappa",
        "clover_coeff_t",
        "clover_coeff_r",
        "anisotropy",
        "t_boundary",
    ):
        if cparams[key] != meta[key]:
            raise RuntimeError(f"{mode} input mismatch: {key}")
    gate(mode + " mathematical input parameters", 0, 0)
    report[mode + " parameters"] = {"cpu": cparams, "quda": meta}
    if cparams["mg_enabled"] != (mode == "mg"):
        raise RuntimeError("MG enable/disable mismatch")
    gate(mode + " final X", relative(qx, cx), 1e-11)
    qstat = (
        json.loads((q / "plain.json").read_text())
        if mode == "plain"
        else dict(
            iterations=int((q / "mg_iterations.txt").read_text()),
            residual=float((q / "pyquda_true_residual.txt").read_text()),
        )
    )
    cr = float(Path(str(cpu) + ".residual").read_text())
    ci = int(Path(str(cpu) + ".iterations").read_text())
    gate(mode + " QUDA true residual", qstat["residual"], meta["tol"])
    gate(mode + " CPU true residual", cr, meta["tol"])
    gate(
        mode + " QUDA X checked by CPU A",
        float((stage / "quda_verified.bin.residual").read_text()),
        meta["tol"],
    )
    gate(mode + " iterations", abs(qstat["iterations"] - ci), 0)
    section = log.split(f"[stage] {tag}_GCR_BEGIN", 1)[1].split(
        f"[stage] {tag}_GCR_END", 1
    )[0]
    hist = re.findall(
        r"^GCR:\s+(\d+) iterations,.*?\|r\|/\|b\| = ([\deE+.-]+)", section, re.M
    )
    gh = np.array([(int(i), float(r)) for i, r in hist])
    ch = np.loadtxt(str(cpu) + ".history")
    if gh.shape != ch.shape or not np.array_equal(gh[:, 0], ch[:, 0]):
        raise RuntimeError(
            f"{mode}: missing or mismatched residual history: {gh.shape}, {ch.shape}"
        )
    gate(
        mode + " residual history max relative",
        np.max(np.abs(ch[:, 1] - gh[:, 1]) / np.maximum(gh[:, 1], meta["tol"])),
        2e-5,
    )
    np.savetxt(stage / "quda.history", gh)
    report[mode + " summary"] = {
        "quda_iterations": qstat["iterations"],
        "cpu_iterations": ci,
        "quda_residual": qstat["residual"],
        "cpu_residual": cr,
        "cpu_seconds": float(Path(str(cpu) + ".seconds").read_text()),
    }
for name in ["b", "rc", "ec", "ace", "pe", "x"]:
    gpu = trace(name)
    cpu = np.fromfile(root / "mg/trace" / f"{name}.bin", np.complex128)
    # QUDA MG::verify explicitly uses 2e-3 for single-precision Ac/RAP.
    # The CPU assembled-vs-matrix-free RAP gate remains 1e-12.
    limit = 2e-3 if name == "ace" else (1e-7 if name == "b" else 5e-5)
    gate("V-cycle " + name, relative(gpu, cpu), limit)
# Compare the first coarse solve, whose vectors were independently exported.
mg_log = log.split("[stage] MG_GCR_BEGIN", 1)[1].split("[stage] MG_GCR_END", 1)[0]
coarse_rows = re.findall(
    r"^MG level .*?GCR:\s+(\d+) iterations,.*?\|r\|/\|b\| = ([\deE+.-]+)", mg_log, re.M
)
first = []
for i, r in coarse_rows:
    if int(i) == 0 and first:
        break
    first.append((int(i), float(r)))
coarse_gpu = np.asarray(first)
coarse_cpu = np.loadtxt(root / "mg/trace/coarse.history")
if coarse_gpu.shape != coarse_cpu.shape or not np.array_equal(
    coarse_gpu[:, 0], coarse_cpu[:, 0]
):
    raise RuntimeError(
        f"coarse residual history missing or mismatched: {coarse_gpu.shape}, {coarse_cpu.shape}"
    )
gate(
    "coarse residual history",
    np.max(
        np.abs(coarse_gpu[:, 1] - coarse_cpu[:, 1])
        / np.maximum(coarse_gpu[:, 1], 1e-30)
    ),
    5e-5,
)
gpu_ec = trace("ec")
gpu_rc = trace("rc")
gpu_ac = trace("ace")
same_ac = np.fromfile(root / "mg/trace/ace_same_input.bin", np.complex128)
same_rap = np.fromfile(root / "mg/trace/rap_same_input.bin", np.complex128)
gate("Ac oracle with identical coarse input", relative(gpu_ac, same_ac), 2e-3)
gate("Ac = RAP with identical coarse input", relative(same_rap, same_ac), 1e-12)
cpu_rc = np.fromfile(root / "mg/trace/rc.bin", np.complex128)
cpu_ac = np.fromfile(root / "mg/trace/ace.bin", np.complex128)
gate(
    "coarse true residual agreement",
    abs(relative(gpu_rc, gpu_ac) - relative(cpu_rc, cpu_ac)),
    5e-5,
)
gate(
    "coarse iterations",
    abs(
        int((q / "trace_coarse_iterations_rank0000.txt").read_text())
        - int((root / "mg/trace/coarse.iterations").read_text())
    ),
    0,
)
(root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
if not all(v.get("pass", True) for v in report.values()):
    raise SystemExit("Numerical gate FAIL; see report.json")
for name in [
    "Fine operator",
    "Plain GCR",
    "P/R",
    "Ac = RAP",
    "MG V-cycle",
    "Final solution",
]:
    # Prior stages write success markers only after their own numerical gates.
    if (
        name in ["Fine operator", "P/R", "Ac = RAP"]
        and not (root / "gates" / name.replace(" ", "_").replace("/", "_")).is_file()
    ):
        raise SystemExit(f"Missing numerical gate: {name}")
    print(f"{name:18} PASS")
m = report["mg summary"]
print(
    f"QUDA residual: {m['quda_residual']:.17e}\nCPU residual: {m['cpu_residual']:.17e}\nQUDA iterations: {m['quda_iterations']}\nCPU iterations: {m['cpu_iterations']}\nCPU runtime: {m['cpu_seconds']:.3f} s (setup + solve)"
)
