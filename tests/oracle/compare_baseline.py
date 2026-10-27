"""Compare a refactored run to the frozen CPU outputs, in addition to QUDA."""

import json
from pathlib import Path
import sys
import numpy as np

ref, out = map(Path, sys.argv[1:])
report = {}
for mode in ("gcr", "mg"):
    old = ref / mode / "x.bin"
    new = out / mode / "x.bin"
    a, b = np.fromfile(old, np.complex128), np.fromfile(new, np.complex128)
    error = float(np.linalg.norm(a - b) / np.linalg.norm(a))
    ah, bh = np.loadtxt(str(old) + ".history"), np.loadtxt(str(new) + ".history")
    assert ah.shape == bh.shape and np.array_equal(
        ah[:, 0], bh[:, 0]
    ), "history indices differ"
    hist = float(np.max(np.abs(ah[:, 1] - bh[:, 1]) / np.maximum(ah[:, 1], 1e-10)))
    ai, bi = int(Path(str(old) + ".iterations").read_text()), int(
        Path(str(new) + ".iterations").read_text()
    )
    residual = float(Path(str(new) + ".residual").read_text())
    passed = (
        ai == bi
        and np.isfinite(error)
        and error <= 1e-11
        and np.isfinite(hist)
        and hist <= 2e-5
        and np.isfinite(residual)
        and residual <= 1e-10
    )
    report[mode] = dict(
        iterations=[ai, bi],
        solution_relative_error=error,
        history_max_relative_error=hist,
        true_residual=residual,
        passed=bool(passed),
    )
    print(mode, report[mode], flush=True)
(out / "baseline-report.json").write_text(json.dumps(report, indent=2) + "\n")
if not all(r["passed"] for r in report.values()):
    raise SystemExit("CPU baseline comparison FAIL")
print("CPU baseline comparison PASS")
