"""Prepare independently exported oracle inputs for CPU replay."""

from pathlib import Path
import sys
import numpy as np
from oracle_io import read_trace

root = Path(sys.argv[1])
q = root / "quda"
read_trace(q, "ec").tofile(root / "mg/quda_ec.bin")
for mode, src, dst in [
    ("plain", "plain_solution.npy", "gcr"),
    ("mg", "pyquda_mg_solution.npy", "mg"),
]:
    np.asarray(np.load(q / src), dtype=np.complex128).tofile(root / dst / "quda_x.bin")
