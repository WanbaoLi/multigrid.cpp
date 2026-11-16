"""Accounting checks for the real-input A/B/A comparison controller."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("compare_fine_sites",
    Path(__file__).resolve().parents[1] / "tools/optimization/compare_fine_sites.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


class ComparisonTests(unittest.TestCase):
    def test_shared_batch_seconds_are_counted_once(self):
        self.assertEqual(compare.solve_seconds({"stats": [{"solver_seconds": 2.}] * 12}, 2), 12.)
        with self.assertRaises(AssertionError):
            compare.solve_seconds({"stats": [{"solver_seconds": float(i)} for i in range(12)]}, 2)

    def test_closing_control_and_corrections_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = [("a", "baseline"), ("b", "candidate"), ("c", "baseline")]
            for (name, _), seconds in zip(runs, [10., 9., 12.]):
                output = root / name / "full12"
                output.mkdir(parents=True)
                stats = [dict(solver_seconds=seconds / 6, refinement_steps=int(name == "b"),
                              true_residual=4e-9)] * 12
                report = dict(verification=dict(passed=True), zero_initial_guess=True,
                    library_sha256="a" * 64, setup_seconds=1., samples=[
                        dict(warmup=i == 0, wall_seconds=seconds, stats=stats) for i in range(4)])
                (output / "result.json").write_text(json.dumps(report))
            compare.summarize(root, runs)
            result = json.loads((root / "summary.json").read_text())
            self.assertAlmostEqual(result["candidate_api_reduction_vs_mean_control"], 2 / 11)
            self.assertAlmostEqual(result["control_relative_drift"], 2 / 11)
            self.assertTrue(result["groups"][1]["correction_solves_occurred"])


if __name__ == "__main__":
    unittest.main()
