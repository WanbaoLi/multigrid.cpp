"""Convert library solutions to canonical layout and compare with QUDA."""

from pathlib import Path
import json, sys
import numpy as np
import h5py

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
run = Path(sys.argv[1])
S = np.load(WORKSPACE / ".cache/cpu_libraries/input/spin_openqcd.npy")
with h5py.File(WORKSPACE / "PyQCU/data/lime_mg_20261013/quda_solution.h5", "r") as f:
    reference = np.asarray(f["x"]).transpose(5, 4, 3, 2, 0, 1).reshape(-1, 4, 3)
refnorm = np.linalg.norm(reference)
checks = {}
for name in ("dd", "openqcd", "grid"):
    d = json.loads((run / (name + ".json")).read_text())
    chunks = []
    with (run / (name + "_canonical.bin")).open("wb") as f:
        for rank in range(d["ranks"]):
            x = np.fromfile(run / f"{name}.rank{rank}.bin", np.complex128).reshape(
                -1, 4, 3
            )
            if name != "grid":
                x = np.einsum("ab,vbc->vac", S.conj().T, x)
            x.tofile(f)
            chunks.append(x)
    x = np.concatenate(chunks)
    error = float(np.linalg.norm(x - reference) / refnorm)
    checks[name] = {
        "solution_error_vs_quda": error,
        "operator_error": d["operator_error"],
    }
    assert error < 1e-6, (name, error)
(run / "solution_checks.json").write_text(json.dumps(checks, indent=2) + "\n")
print(json.dumps(checks, indent=2))
