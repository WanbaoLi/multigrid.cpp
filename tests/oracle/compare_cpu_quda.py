import json
import os
from pathlib import Path
import numpy as np

R = Path(
    os.environ.get(
        "LQCD_ARTIFACT_DIR", str(Path(__file__).resolve().parent / ".cache" / "fine")
    )
)
q = np.load(R / "quda_M_source_global.npy")
c = np.fromfile(R / "cpu_M_source_global.bin", dtype=np.complex128).reshape(q.shape)
cd = np.fromfile(R / "cpu_M_source_global.bin.dslash", dtype=np.complex128).reshape(
    q.shape
)
cc = np.fromfile(R / "cpu_M_source_global.bin.clover", dtype=np.complex128).reshape(
    q.shape
)
d = np.load(R / "quda_dslash_source_global.npy")
cl = np.load(R / "quda_clover_source_global.npy")


def stat(a, b):
    x = a - b
    i = np.unravel_index(np.argmax(abs(x)), x.shape)
    return {
        "relative_l2": float(np.linalg.norm(x) / np.linalg.norm(a)),
        "max_abs": float(np.max(abs(x))),
        "max_index": [int(v) for v in i],
    }


out = {
    "cpu_dslash_vs_quda": stat(d, cd),
    "cpu_clover_vs_quda": stat(cl, cc),
    "cpu_full_M_vs_quda": stat(q, c),
    "cpu_split_vs_cpu_full": stat(c, cd + cc),
    "quda_M_reconstruction_from_split": stat(q, d + cl),
    "quda_dslash_norm": float(np.linalg.norm(d)),
    "quda_clover_norm": float(np.linalg.norm(cl)),
}
print(json.dumps(out, indent=2))
(R / "cpu_quda_compare.json").write_text(json.dumps(out, indent=2) + "\n")

for name, metrics in out.items():
    if isinstance(metrics, dict):
        error = metrics["relative_l2"]
        if not np.isfinite(error) or error > 1e-12:
            raise SystemExit(f"Fine operator FAIL: {name}: {error}")
print("Fine operator PASS")
