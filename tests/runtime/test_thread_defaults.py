"""Python thread selection tests; never load the native solver library."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
import lqcd_cpu


class ThreadDefaults(unittest.TestCase):
    def test_affinity_and_environment(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            os, "sched_getaffinity", return_value={2, 4, 7}
        ):
            self.assertEqual(lqcd_cpu._resolve_threads(None), 3)
            with patch.dict(os.environ, {"OMP_NUM_THREADS": " 8, 2 "}):
                self.assertEqual(lqcd_cpu._resolve_threads(None), 8)
                self.assertEqual(lqcd_cpu._resolve_threads(5), 5)
        self.assertEqual(lqcd_cpu._resolve_threads(np.int32(7)), 7)

    def test_invalid_counts(self):
        for value in (0, -1, 2**32 + 1, 2**31, 1.5, "4", True, np.bool_(True)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                lqcd_cpu._resolve_threads(value)
        for value in ("abc", "3,", "3,0", "-1", str(2**31)):
            with self.subTest(value=value), patch.dict(
                os.environ, {"OMP_NUM_THREADS": value}
            ), self.assertRaises(ValueError):
                lqcd_cpu._resolve_threads(None)

    def test_capture_before_library_affinity_change(self):
        # Model libgomp dlopen narrowing the main thread to the first OMP place.
        comm = Mock(rank=0)
        comm.allgather.side_effect = lambda value: [value]
        comm.py2f.return_value = 0
        library = Mock()
        library.lqcd_create.return_value = 0
        with patch.dict(os.environ, {}, clear=True), patch.object(
            os, "sched_getaffinity", return_value={3, 5, 7}
        ) as affinity:

            def load(_):
                affinity.return_value = {3}
                return library

            with patch.object(lqcd_cpu, "_library", side_effect=load):
                solver = lqcd_cpu.Solver([8] * 4, [1] * 4, mass=0.05, comm=comm)
            self.assertEqual(solver.config.threads, 3)
            self.assertEqual(os.sched_getaffinity(0), {3})

    def test_invalid_request_is_collective_before_library_load(self):
        comm = Mock(rank=0)
        comm.allgather.side_effect = lambda value: [value]
        with patch.object(lqcd_cpu, "_library") as load:
            with self.assertRaises(ValueError):
                lqcd_cpu.Solver(
                    [8] * 4, [1] * 4, mass=0.05, threads=2**32 + 1, comm=comm
                )
            load.assert_not_called()
            self.assertEqual(comm.allgather.call_count, 1)


if __name__ == "__main__":
    unittest.main()
