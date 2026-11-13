"""Pure contract tests for the real-LIME health driver."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_lime_solver", ROOT / "benchmarks/runtime/check_lime_solver.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_lime_solver", ROOT / "benchmarks/runtime/verify_lime_solver.py"
)
VERIFY = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY)


class LimeSolverContractTest(unittest.TestCase):
    def test_streamed_column_and_single_layouts(self):
        try:
            import numpy as np
        except ModuleNotFoundError:
            self.skipTest("NumPy is supplied by the runtime Python environment")
        with tempfile.TemporaryDirectory() as directory:
            root, work = Path(directory), Path(directory) / "work"
            work.mkdir()
            lattice = (2, 2, 2, 4)
            propagator = np.arange(np.prod((4, 2, 2, 2, 4, 4, 3, 3)),
                                   dtype=np.float64).reshape((4, 2, 2, 2, 4, 4, 3, 3))
            propagator = propagator + 1j * (propagator + 0.5)
            np.save(root / "propagator.npy", propagator)
            columns = VERIFY.write_columns(root, work, lattice)
            for column, path in enumerate(columns):
                spin, color = divmod(column, 3)
                expected = propagator[..., :, spin, :, color].reshape(-1, 4, 3)
                actual = np.fromfile(path, dtype="<c16").reshape(-1, 4, 3)
                np.testing.assert_array_equal(actual, expected)
            for rank in range(2):
                local = np.arange(np.prod((2, 2, 2, 2, 4, 3)), dtype=np.float64)
                local = (local + rank * local.size + 1j * (local + 1)).reshape((2, 2, 2, 2, 4, 3))
                np.save(root / f"single_rank{rank:05d}.npy", local)
            single = VERIFY.write_single(root, work, 2, lattice)
            expected = np.concatenate([
                np.load(root / f"single_rank{rank:05d}.npy").reshape(-1, 4, 3)
                for rank in range(2)
            ])
            actual = np.fromfile(single, dtype="<c16").reshape(-1, 4, 3)
            np.testing.assert_array_equal(actual, expected)

    def test_mass_normalized_rhs_uses_source_spin_color_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rhs.bin"
            VERIFY.write_rhs(path, sites=16, lattice=(2, 2, 2, 2),
                             point=(1, 0, 0, 1), column=5,
                             mass=-0.279, source_scale=1.5)
            site = ((1 * 2 + 0) * 2 + 0) * 2 + 1
            with path.open("rb") as stream:
                stream.seek((site * 12 + 5) * 16)
                real, imag = struct.unpack("<dd", stream.read(16))
            self.assertAlmostEqual(real, 1.5 / (4.0 - 0.279), places=14)
            self.assertEqual(imag, 0.0)
            self.assertEqual(path.stat().st_size, 16 * 12 * 16)

    def test_native_batch_timer_is_counted_once(self):
        summary = MODULE.native_timing([
            {"solver_seconds": 2.0, "api_seconds": 2.5,
             "timing_scope": "shared_batch", "batch_size": 2,
             "refinement_steps": 1},
            {"solver_seconds": 2.0, "api_seconds": 2.5,
             "timing_scope": "shared_batch", "batch_size": 2,
             "refinement_steps": 0},
            {"solver_seconds": 0.7, "api_seconds": 0.8,
             "refinement_steps": 0},
        ])
        self.assertAlmostEqual(summary["native_solver_seconds"], 2.7)
        self.assertAlmostEqual(summary["native_api_seconds"], 3.3)
        self.assertTrue(summary["correction_solves_occurred"])


if __name__ == "__main__":
    unittest.main()
