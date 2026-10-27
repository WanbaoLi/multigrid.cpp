"""No MPI or solver required: cpuset/SMT placement and aggregate safety."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

spec = importlib.util.spec_from_file_location(
    "run_numa", Path(__file__).resolve().parents[2] / "tools/run_numa.py"
)
numa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(numa)


class PlacementTests(unittest.TestCase):
    def test_mpi_launcher_detection_and_arguments(self):
        for banner, family in (("mpirun (Open MPI) 4.1.6", "openmpi"),
                               ("prterun (PRRTE) 3.0.8", "openmpi"),
                               ("HYDRA build details: Version: 4.3.1", "mpich")):
            with patch.object(numa.subprocess, "run", return_value=
                              subprocess.CompletedProcess([], 0, banner, "")):
                self.assertEqual(numa.detect_launcher("/mpi/mpiexec"), family)
        with patch.object(numa.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 1, "", "unknown --version"),
                subprocess.CompletedProcess([], 0, "MPICH HYDRA 4.3.1", "")]) as run:
            self.assertEqual(numa.detect_launcher("mpiexec"), "mpich")
            self.assertEqual(run.call_args_list[1].args[0], ["mpiexec", "-version"])
        with patch.object(numa.subprocess, "run", return_value=
                          subprocess.CompletedProcess([], 0, "unrelated launcher", "")):
            with self.assertRaisesRegex(ValueError, "unrecognized"):
                numa.detect_launcher("mpiexec")
        self.assertEqual(numa.launcher_prefix("mpi", "openmpi", 8),
                         ["mpi", "--host", "localhost:8", "-n", "8", "--bind-to", "none"])
        hydra = numa.launcher_prefix("mpi", "mpich", 8)
        self.assertEqual(hydra, ["mpi", "-n", "8", "-bind-to", "none",
                                "-launcher", "fork", "-rmk", "user"])
        self.assertNotIn("--host", hydra)

    def test_mpich_rank_environment_and_conflicts(self):
        plan = numa.make_plan({0: [0, 2], 1: [4, 6]}, [24,24,24,64], [6,6,6,4])
        env = {"PMI_RANK": "1", "PMI_SIZE": "2"}
        self.assertEqual(numa.rank_placement(plan, env, plan["host"])["cpus"], [4,6])
        for invalid in ({"PMI_RANK": "1"}, dict(env, PMI_SIZE="3"),
                        dict(env, PMI_RANK="2"),
                        dict(env, OMPI_COMM_WORLD_RANK="0", OMPI_COMM_WORLD_SIZE="2")):
            with self.assertRaises(ValueError):
                numa.rank_placement(plan, invalid, plan["host"])

    def test_multi_rank_numa_disjoint_complete_and_heterogeneous(self):
        nodes = {3: [0, 2, 4, 6, 8], 9: [11, 13, 15, 17, 19, 21, 23]}
        plan = numa.make_plan(nodes, [24,24,24,64], [6,6,6,4], ranks_per_numa=2)
        self.assertEqual(plan['threads_per_rank'], [3,2,4,3])
        self.assertEqual(plan['ranks'], 4)
        self.assertEqual([p['node'] for p in plan['placement']], [3,3,9,9])
        self.assertEqual([p['numa_partition'] for p in plan['placement']], [0,1,0,1])
        flattened = [cpu for p in plan['placement'] for cpu in p['cpus']]
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(set(flattened), set(nodes[3] + nodes[9]))
        fixed = numa.make_plan(nodes, [24,24,24,64], [6,6,6,4], threads=2, ranks_per_numa=2)
        self.assertEqual(fixed['threads_per_rank'], [2]*4)
        self.assertEqual([p['cpus'] for p in fixed['placement']], [[0,2],[4,6],[11,13],[15,17]])

    def test_multi_rank_invalid_resources_and_geometry(self):
        for value in (0, -1, True, 1.5):
            with self.assertRaisesRegex(ValueError, 'ranks-per-numa'):
                numa.make_plan({0:[0,1,2,3]}, [24,24,24,64], [6,6,6,4], ranks_per_numa=value)
        for value in (0, -1, True, 1.5):
            with self.assertRaisesRegex(ValueError, 'threads'):
                numa.make_plan({0:[0,1,2,3]}, [24,24,24,64], [6,6,6,4], threads=value)
        with self.assertRaisesRegex(ValueError, 'physical cores'):
            numa.make_plan({0:[0,1,2]}, [24,24,24,64], [6,6,6,4], threads=2, ranks_per_numa=2)
        with self.assertRaisesRegex(ValueError, 'physical cores'):
            numa.make_plan({0:[0]}, [24,24,24,64], [6,6,6,4], ranks_per_numa=2)
        with self.assertRaisesRegex(ValueError, 'complete time aggregates'):
            numa.make_plan({node:list(range(node*4,node*4+4)) for node in range(8)},
                           [24,24,24,64], [6,6,6,4], ranks_per_numa=4)

    def test_sparse_cpuset_smt_and_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for node, cpulist in [(0, "0-3,8-11"), (2, "4-7,12-15")]:
                path = root / "node" / f"node{node}"
                path.mkdir(parents=True)
                (path / "cpulist").write_text(cpulist)
            for cpu in range(16):
                topology = root / "cpu" / f"cpu{cpu}" / "topology"
                topology.mkdir(parents=True)
                (topology / "core_id").write_text(str(cpu % 4))
                (topology / "physical_package_id").write_text(str((cpu % 8) // 4))
            self.assertEqual(
                numa.discover_nodes(root, {0, 8, 9, 4, 12, 15}), {0: [0, 9], 2: [4, 15]}
            )

    def test_sibling_groups_and_die_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node = root / "node" / "node0"
            node.mkdir(parents=True)
            (node / "cpulist").write_text("0-7")
            # The same package/core IDs occur on two dies. CPUs 4-7 are SMT
            # siblings of 0-3; the first member of a group need not be allowed.
            for cpu in range(8):
                topology = root / "cpu" / f"cpu{cpu}" / "topology"
                topology.mkdir(parents=True)
                (topology / "physical_package_id").write_text("0")
                (topology / "core_id").write_text(str(cpu % 2))
                (topology / "die_id").write_text(str((cpu % 4) // 2))
            allowed = {0, 4, 5, 2, 6, 7}
            self.assertEqual(numa.discover_nodes(root, allowed), {0: [0, 2, 5, 7]})
            for cpu in range(8):
                topology = root / "cpu" / f"cpu{cpu}" / "topology"
                (topology / "thread_siblings_list").write_text(
                    f"{cpu % 4},{cpu % 4 + 4}"
                )
                # Sibling identities take precedence over ambiguous legacy IDs.
                (topology / "die_id").unlink()
                (topology / "core_id").write_text("0")
            self.assertEqual(numa.discover_nodes(root, allowed), {0: [0, 2, 5, 7]})

    def test_rank_local_threads_and_noncontiguous_ids(self):
        plan = numa.make_plan(
            {2: [3, 5, 7], 7: [12, 14]}, [24, 24, 24, 64], [6, 6, 6, 4]
        )
        self.assertEqual(plan["threads_per_rank"], [3, 2])
        self.assertEqual(plan["grid"], [1, 1, 1, 2])
        self.assertEqual(plan["placement"][0]["cpus"], [3, 5, 7])
        self.assertEqual(
            numa.rank_environment(plan["placement"][1])["OMP_PLACES"], "{12},{14}"
        )

    def test_invalid_divisibility_and_oversubscription(self):
        for ranks in [3, 32]:
            with self.assertRaisesRegex(ValueError, "complete time aggregates"):
                numa.make_plan(
                    {n: [n] for n in range(ranks)}, [24, 24, 24, 64], [6, 6, 6, 4]
                )
        with self.assertRaisesRegex(ValueError, "physical cores"):
            numa.make_plan({0: [2, 3]}, [24, 24, 24, 64], [6, 6, 6, 4], threads=3)
        with self.assertRaisesRegex(ValueError, "no allowed"):
            numa.make_plan({0: [2, 3]}, [24, 24, 24, 64], [6, 6, 6, 4], selected=[1])

    def test_environment_is_replaced_and_rank_metadata_is_explicit(self):
        plan = numa.make_plan(
            {0: [4, 6], 1: [10, 12, 14]}, [24, 24, 24, 64], [6, 6, 6, 4]
        )
        env = numa.rank_environment(plan["placement"][1])
        self.assertEqual(env["OMP_NUM_THREADS"], "3")
        self.assertEqual(env["OMP_PROC_BIND"], "close")
        self.assertEqual(env["OMP_PLACES"], "{10},{12},{14}")
        self.assertNotIn("OMP_NUM_THREADS=88", env.values())
        self.assertEqual([p["rank"] for p in plan["placement"]], [0, 1])

    def test_rank_validation(self):
        plan = numa.make_plan({0: [4], 1: [10, 12]}, [24, 24, 24, 64], [6, 6, 6, 4])
        valid = {"OMPI_COMM_WORLD_RANK": "1", "OMPI_COMM_WORLD_SIZE": "2"}
        self.assertEqual(
            numa.rank_placement(plan, valid, plan["host"])["cpus"], [10, 12]
        )
        for environment in (
            {},
            dict(valid, OMPI_COMM_WORLD_RANK="-1"),
            dict(valid, OMPI_COMM_WORLD_RANK="2"),
            dict(valid, OMPI_COMM_WORLD_SIZE="3"),
        ):
            with self.assertRaises(ValueError):
                numa.rank_placement(plan, environment, plan["host"])
        with self.assertRaisesRegex(ValueError, "single-host"):
            numa.rank_placement(plan, valid, "remote-host")

    def test_local_even_extent_required(self):
        # Four complete bt=3 aggregates still leave odd local t=3.
        with self.assertRaisesRegex(ValueError, "local lattice extents must be even"):
            numa.make_plan({n: [n] for n in range(4)}, [8, 8, 8, 12], [2, 2, 2, 3])

    def test_core_counts_not_machine_specific(self):
        for cores in [1, 36, 38, 128, 304]:
            plan = numa.make_plan(
                {
                    node: list(range(node * cores, (node + 1) * cores))
                    for node in range(8)
                },
                [24, 24, 24, 64],
                [6, 6, 6, 4],
            )
            self.assertEqual(plan["threads_per_rank"], [cores] * 8)
            self.assertEqual(plan["ranks"], 8)


if __name__ == "__main__":
    unittest.main()
