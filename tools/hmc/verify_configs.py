"""Independent SciDAC CRC/readback, NumPy plaquette and native Dirac gates."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from mpi4py import MPI
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bindings'))
sys.path.insert(0, str(ROOT / 'src'))
from lqcd_cpu.io import read_lime_gauge
from hmc.reference import CloverHMC, lime_sha256


def numpy_plaquette(u):
    total = 0.
    for mu in range(4):
        for nu in range(mu):
            a, b = u[..., mu, :, :], u[..., nu, :, :]
            p = a @ np.roll(b, -1, axis=3 - mu) @ np.roll(a, -1, axis=3 - nu).conj().swapaxes(-1, -2) @ b.conj().swapaxes(-1, -2)
            total += np.trace(p, axis1=-2, axis2=-1).real.mean() / 3
    return total / 6


def main():
    p = argparse.ArgumentParser()
    p.add_argument('run', type=Path)
    p.add_argument('--reference', type=Path, required=True)
    args = p.parse_args()
    d = json.loads((args.run / 'result.json').read_text())
    if not d['complete']:
        raise RuntimeError('Incomplete chain')
    torch.set_num_threads(1)
    m = CloverHMC(d['lattice_xyzt'], d['beta'], d['mass_light'], d['mass_strange'], d['csw'],
                  dense_reference=False)
    records = []
    rng = np.random.default_rng(881)
    for item in d['saved_configurations']:
        path = args.run / item['file']
        if lime_sha256(path) != item['sha256']:
            raise RuntimeError('Configuration hash mismatch')
        u = read_lime_gauge(path, comm=MPI.COMM_SELF)
        error = float(np.max(np.abs(u.conj().swapaxes(-1, -2) @ u - np.eye(3))))
        det_error = float(np.max(np.abs(np.linalg.det(u) - 1)))
        plaq = numpy_plaquette(u)
        if error > 1e-10 or det_error > 1e-10 or abs(plaq - item['plaquette']) > 1e-13:
            raise RuntimeError('SU(3) or independent plaquette mismatch')
        native_errors = []
        with tempfile.TemporaryDirectory(prefix='hmc-native-probe-') as temporary:
            out = Path(temporary)
            u.tofile(out / 'gauge.bin')
            probe = rng.normal(size=m.volume * 12) + 1j * rng.normal(size=m.volume * 12)
            probe.astype(np.complex128).tofile(out / 'probe.bin')
            for mass in (m.ml, m.ms):
                subprocess.run([str(args.reference), '--dims', *map(str, m.lattice),
                    '--gauge', str(out / 'gauge.bin'), '--source', str(out / 'probe.bin'),
                    '--mass', str(mass), '--csw', str(m.csw), '--operator', '--out', str(out / 'image.bin')],
                    check=True, capture_output=True)
                native = np.fromfile(out / 'image.bin', dtype=np.complex128)
                applied = m.apply_dirac(torch.from_numpy(u.reshape(-1, 4, 3, 3)), mass,
                                        torch.from_numpy(probe)).numpy()
                relative = float(np.linalg.norm(native - applied) / np.linalg.norm(native))
                if relative > 5e-14:
                    raise RuntimeError('Independent native operator mismatch')
                native_errors.append(relative)
        records.append(dict(file=item['file'], scidac_crc_passed=True, sha256=item['sha256'],
            unitarity_error=error, determinant_error=det_error, numpy_plaquette=plaq,
            native_operator_errors_light_strange=native_errors))
    (args.run / 'verification.json').write_text(json.dumps(dict(
        passed=bool(records), configurations=records, method='existing SciDAC reader/CRC + NumPy plaquette + independent scalar native Dirac'), indent=2) + '\n')
    print(json.dumps(dict(passed=bool(records), configurations=len(records))))


if __name__ == '__main__':
    main()
