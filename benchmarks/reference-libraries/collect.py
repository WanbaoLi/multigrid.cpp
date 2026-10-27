"""Collect measured second solves only after independent residual gates pass."""

from pathlib import Path
import hashlib, json, sys, subprocess

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
run = Path(sys.argv[1]).resolve()
checks = json.loads((run / "solution_checks.json").read_text())
rows = []
for key in ("openqcd", "dd", "grid"):
    d = json.loads((run / f"{key}.json").read_text())
    verified = float((run / f"{key}_verified.bin.residual").read_text())
    assert d["operator_error"] < 1e-11 and verified <= 1e-8
    assert max(d["true_residual"]) <= 1e-8
    row = dict(
        name=d["library"],
        cores=d["ranks"] * d["threads_per_rank"],
        mpi_ranks=d["ranks"],
        threads_per_rank=d["threads_per_rank"],
        solve_seconds=d["solve_seconds"],
        second_seconds=d["solve_seconds"][1],
        setup_seconds=d["setup_seconds"],
        native_true_residual=d["true_residual"][1],
        independent_cpp_residual=verified,
        operator_error=d["operator_error"],
        solution_error_vs_quda=checks[key]["solution_error_vs_quda"],
        iterations=d["iterations"][1],
    )
    if key == "grid":
        row.update(
            refinement_steps=d["refinement_steps"][1],
            inner_iterations=d["inner_iterations"][1],
            final_double_iterations=d["final_double_iterations"][1],
        )
    rows.append(row)
p = json.loads((run / "pyqcu.json").read_text())
assert all(s["passed"] for s in p["solves"])
rows.append(
    dict(
        name="PyQCU real/imag + compile BiCGStab",
        cores=88,
        solve_seconds=[s["seconds"] for s in p["solves"]],
        second_seconds=p["solves"][1]["seconds"],
        native_true_residual=p["solves"][1]["true_residual"],
        iterations=len(p["solves"][1]["history"]) - 1,
        solution_error_vs_quda=p["solution_error_vs_quda"],
    )
)
c = json.loads((run / "cpp.bin.solve_timings.json").read_text())
assert max(s["true_residual"] for s in c) <= 1e-8
rows.append(
    dict(
        name="multigrid.cpp MG/GCR",
        cores=88,
        solve_seconds=[s["seconds"] for s in c],
        second_seconds=c[1]["seconds"],
        native_true_residual=c[1]["true_residual"],
        iterations=int((run / "cpp.bin.run2.iterations").read_text()),
    )
)
pytime = rows[-2]["second_seconds"]
cpptime = rows[-1]["second_seconds"]
for r in rows:
    r.update(
        speedup_vs_pyqcu=pytime / r["second_seconds"],
        speedup_vs_cpp=cpptime / r["second_seconds"],
    )


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(8 << 20), b""):
            h.update(buf)
    return h.hexdigest()


provenance = {}
for name in ["DDalphaAMG", "Grid"]:
    provenance[name] = subprocess.check_output(
        [
            "git",
            "-C",
            str(WORKSPACE / ".cache/cpu_libraries" / name),
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()
provenance["openQCD"] = "2.4.3"
provenance["gauge_sha256"] = sha(WORKSPACE / ".cache/cpu_libraries/input/gauge.bin")
provenance["source_sha256"] = sha(WORKSPACE / ".cache/cpu_libraries/input/b.bin")
result = dict(
    run=str(run),
    lattice=[24, 24, 24, 64],
    mass=-0.277,
    csw=1,
    temporal_boundary=-1,
    rhs_count=1,
    initial_guess="zero for every solve",
    timing="second solve, setup/I/O excluded",
    full_residual_gate=1e-8,
    all_independent_checks_passed=True,
    rows=rows,
    provenance=provenance,
)
(run / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
lines = [
    "# CPU library comparison: 24³×64",
    "",
    "Same LIME-derived gauge and one spin-color point-source column. Second zero-start solve; setup, compilation, I/O and independent checks excluded.",
    "",
    "| Solver | CPU cores | First / s | Second / s | Full true residual | vs optimized PyQCU | vs multigrid.cpp |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for r in rows:
    lines.append(
        f"| {r['name']} | {r['cores']} | {r['solve_seconds'][0]:.6f} | {r['second_seconds']:.6f} | {r['native_true_residual']:.3e} | {r['speedup_vs_pyqcu']:.2f}x | {r['speedup_vs_cpp']:.2f}x |"
    )
lines += [
    "",
    "External library solutions pass a second, independent full residual calculation using multigrid.cpp.",
    "openQCD uses 72 cores because its geometric thread blocking cannot use 88 on this lattice.",
    "Different algorithms/precision strategies: DDalphaAMG three-level MG; openQCD deflated SAP-GCR; Grid even-odd mixed BiCGStab; PyQCU full BiCGStab; C++ full MG/GCR.",
    "Grid counts are refinement steps plus inner/final BiCGStab iterations, not MG outer iterations.",
    "All results are a single propagator column, not all 12 columns. Native CPU timings do not establish performance or hardware support on Sunway or LineShine.",
    "",
    "Reproduction: multigrid.cpp/benchmarks/reference-libraries/run.sh; versions, configuration and portability discussion are in that directory.",
    "",
]
(run / "summary.md").write_text("\n".join(lines))
print("\n".join(lines))
