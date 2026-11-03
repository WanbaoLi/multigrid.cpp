"""Acceptance-ledger tests; synthetic reports test gates, never claim HPC speed."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import tempfile
import time
import unittest

FILE = Path(__file__).resolve().parents[1] / "tools" / "optimization" / "campaign.py"
SPEC = importlib.util.spec_from_file_location("optimization_campaign", FILE)
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


class CampaignTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.skill = self.root / "skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text("---\nname: test-reference\n---\nFrozen evidence.\n")
        self.library = self.root / "measured.so"
        self.library.write_bytes(b"test executable bytes, not a numerical solver")
        (self.repo / "solver.cpp").write_text("int baseline = 1;\n")
        self.git("init", "-q")
        self.git("add", "solver.cpp")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "baseline")
        self.campaign = self.root / "campaign"
        self.input_sha = "a" * 64
        self.reference_sha = "b" * 64
        ledger.initialize(self.campaign, self.repo, self.skill, self.input_sha, self.reference_sha)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def proposal(self, **extra):
        history = ledger.show_history(self.campaign)
        return dict(bottleneck="Measured local-operator CPU cycles", hypothesis="Reuse source projection",
                    change="Move identical projection outside output-color loop",
                    mechanism="Avoid repeated loads/arithmetic", history_links=["history:initial"],
                    retry_conditions="Retest after a different compiler or changed blocked path",
                    history_read_token=history["history_read_token"], **extra)

    def create(self, name):
        ledger.propose(self.campaign, name, self.proposal())
        return ledger.snapshot(self.campaign, name)

    def report(self, name, values=(10., 10.1, 9.9), **overrides):
        snapshot = ledger.read(self.campaign / "attempts" / name / "attempt.json")["snapshot"]
        stats = [dict(converged=1, true_residual=4.8e-9, iterations=24) for _ in range(12)]
        result = dict(complete=True, timing_scope="full12_api", zero_initial_guess=True,
            input_sha256=self.input_sha, library_sha256=ledger.digest(self.library),
            library_path=str(self.library), source_manifest_sha256=snapshot["source_manifest_sha256"],
            comparison_key={"host": "test-node", "allocation": "one", "physical_problem": "fixture"},
            configuration={"threads": 37, "ranks": 16, "batch": 2},
            samples=[dict(repeat=0, warmup=True, wall_seconds=11., stats=copy.deepcopy(stats))] +
                    [dict(repeat=i+1, warmup=False, wall_seconds=value, stats=copy.deepcopy(stats))
                     for i, value in enumerate(values)],
            verification=dict(complete=True, passed=True, columns=12,
                reference_sha256=self.reference_sha, max_true_residual=4.9e-9,
                solution_relative_error=1e-7))
        result.update(overrides)
        return result

    def ingest(self, name, report):
        path = self.root / (name + "-report.json")
        ledger.atomic(path, report)
        return ledger.ingest(self.campaign, name, path)

    def baseline(self):
        self.create("baseline")
        self.ingest("baseline", self.report("baseline"))
        return ledger.promote(self.campaign, "baseline", baseline=True)

    def test_full12_gates_and_rollback_retain_best_binary(self):
        baseline = self.baseline()
        self.library.write_bytes(b"correct faster implementation")
        self.create("candidate")
        self.ingest("candidate", self.report("candidate", (8., 8.1, 7.9)))
        selected = ledger.promote(self.campaign, "candidate", against="baseline")
        self.assertAlmostEqual(selected["gain"], .2)
        ledger.rollback(self.campaign, "baseline", "Later fixture exposed a regression")
        self.assertEqual(ledger.read(self.campaign / "best.json")["attempt"], "baseline")
        binary = self.campaign / "attempts" / "baseline" / "artifacts" / "liblqcd_cpu.so"
        self.assertEqual(ledger.digest(binary), baseline["library_sha256"])
        self.assertTrue((self.campaign / "attempts" / "candidate" / "report.json").is_file())

    def test_incomplete_bad_precision_wrong_input_never_ingest(self):
        self.create("bad")
        original = self.report("bad")
        cases = []
        for key, value in [("complete", False), ("timing_scope", "local_kernel"),
                           ("propagator_sha256", "1"*64),
                           ("shared_process_thread_teams", [dict(fine_threads=32,coarse_threads=32),
                                                            dict(fine_threads=37,coarse_threads=37)]),
                           ("zero_initial_guess", False), ("input_sha256", "c"*64),
                           ("source_manifest_sha256", "d"*64), ("library_sha256", "e"*64)]:
            cases.append({**copy.deepcopy(original), key: value})
        for field, value in [("complete", False), ("passed", False), ("columns", 1),
                             ("max_true_residual", 2e-8), ("solution_relative_error", 2e-6),
                             ("reference_sha256", "f"*64)]:
            row = copy.deepcopy(original)
            row["verification"][field] = value
            cases.append(row)
        row = copy.deepcopy(original)
        row["samples"][1]["stats"] = row["samples"][1]["stats"][:1]
        cases.append(row)
        row = copy.deepcopy(original)
        row["samples"][1]["stats"][3]["true_residual"] = float("inf")
        # NaN/inf serialized JSON is intentionally rejected by the canonical writer,
        # and also by validation if supplied through a permissive external parser.
        with self.assertRaises(ledger.EvidenceError):
            ledger.validate_report(row, ledger.read(self.campaign / "campaign.json"),
                                   original["source_manifest_sha256"])
        for row in cases:
            with self.subTest(row=row):
                with self.assertRaises(ledger.EvidenceError):
                    self.ingest("bad", row)
        self.assertFalse((self.campaign / "best.json").exists())

    def test_need_three_steady_and_a_complete12_warmup(self):
        self.create("few")
        with self.assertRaises(ledger.EvidenceError):
            self.ingest("few", self.report("few", (8., 8.1)))
        row = self.report("few")
        row["samples"][0]["warmup"] = False
        with self.assertRaises(ledger.EvidenceError):
            self.ingest("few", row)

    def test_noisy_or_small_or_overlapping_gain_cannot_promote(self):
        self.baseline()
        for name, samples in [("noisy", (7., 8., 9.)), ("small", (9.7, 9.8, 9.9)),
                              ("overlap", (9.0, 9.5, 9.92))]:
            self.create(name)
            self.ingest(name, self.report(name, samples))
            with self.assertRaises(ledger.EvidenceError):
                ledger.promote(self.campaign, name, against="baseline")
            self.assertEqual(ledger.read(self.campaign / "best.json")["attempt"], "baseline")

    def test_unmatched_node_cannot_promote(self):
        self.baseline()
        self.create("othernode")
        self.ingest("othernode", self.report("othernode", (8., 8.1, 7.9), comparison_key="different allocation"))
        with self.assertRaisesRegex(ledger.EvidenceError, "Unmatched"):
            ledger.promote(self.campaign, "othernode", against="baseline")

    def test_modified_skill_or_source_or_binary_cannot_promote(self):
        self.create("protected")
        self.ingest("protected", self.report("protected"))
        skill = self.skill / "SKILL.md"
        original = skill.read_bytes()
        skill.write_bytes(b"changed")
        with self.assertRaisesRegex(ledger.EvidenceError, "reference skill changed"):
            ledger.promote(self.campaign, "protected", baseline=True)
        skill.write_bytes(original)
        source = self.campaign / "attempts" / "protected" / "source" / "solver.cpp"
        original_source = source.read_bytes()
        source.write_text("wrong source")
        with self.assertRaisesRegex(ledger.EvidenceError, "source changed"):
            ledger.promote(self.campaign, "protected", baseline=True)
        source.write_bytes(original_source)
        binary = self.campaign / "attempts" / "protected" / "artifacts" / "liblqcd_cpu.so"
        binary.write_bytes(b"wrong binary")
        with self.assertRaisesRegex(ledger.EvidenceError, "library is missing/changed"):
            ledger.promote(self.campaign, "protected", baseline=True)

    def test_history_read_receipt_and_retry_attribution(self):
        proposal = self.proposal()
        ledger.propose(self.campaign, "first", proposal)
        with self.assertRaisesRegex(ledger.EvidenceError, "stale/missing"):
            ledger.propose(self.campaign, "stale", proposal)
        ledger.conclude(self.campaign, "first", "inconclusive", "Noise exceeded measured gain", ["first/log"])
        with self.assertRaisesRegex(ledger.EvidenceError, "retry_of"):
            ledger.propose(self.campaign, "repeat", self.proposal())
        retry = self.proposal(retry_of="first")
        retry["retry_conditions"] = "New exclusive allocation removes observed contention"
        ledger.propose(self.campaign, "repeat", retry)

    def test_snapshot_records_dirty_untracked_and_deleted_source(self):
        (self.repo / "solver.cpp").unlink()
        (self.repo / "new.cpp").write_text("new code")
        (self.repo / ".gitignore").write_text("ignored/\n")
        ignored = self.repo / "ignored"
        ignored.mkdir()
        (ignored / "build.so").write_bytes(b"not source")
        self.create("dirty")
        path = self.campaign / "attempts" / "dirty"
        manifest = ledger.read(path / "source-manifest.json")
        entries = {entry["path"]: entry for entry in manifest["files"]}
        self.assertTrue(entries["solver.cpp"]["deleted"])
        self.assertIn("new.cpp", entries)
        self.assertNotIn("ignored/build.so", entries)
        self.assertEqual((path / "source" / "new.cpp").read_text(), "new code")
        self.assertTrue((path / "build").is_dir())
        (path / "source" / "unrecorded.hpp").write_text("new numeric implementation")
        with self.assertRaisesRegex(ledger.EvidenceError, "Unrecorded source"):
            ledger.snapshot(self.campaign, "dirty")

    def test_fresh_control_preserves_old_source_after_repo_head_advances(self):
        baseline = self.baseline()
        old_head = ledger.git(self.repo, "rev-parse", "HEAD")
        (self.repo / "solver.cpp").write_text("int faster_candidate = 2;\n")
        self.git("add", "solver.cpp")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "candidate")
        new_head = ledger.git(self.repo, "rev-parse", "HEAD")
        self.assertNotEqual(old_head, new_head)
        ledger.propose(self.campaign, "fresh-control", self.proposal())
        copied = ledger.snapshot_from(self.campaign, "fresh-control", "baseline")
        self.assertEqual(copied["source_manifest_sha256"], baseline["source_manifest_sha256"])
        self.assertEqual(copied["git_head"], old_head)
        control_path = self.campaign / "attempts" / "fresh-control"
        self.assertEqual((control_path / "source" / "solver.cpp").read_text(), "int baseline = 1;\n")
        self.assertEqual(list((control_path / "build").iterdir()), [])
        control_state = ledger.read(control_path / "attempt.json")
        self.assertNotIn("report", control_state)
        self.assertEqual(control_state["stages"], {})
        self.assertEqual(copied, ledger.snapshot_from(self.campaign, "fresh-control", "baseline"))
        new_allocation = {"host":"new-node", "allocation":"fresh", "physical_problem":"fixture"}
        self.ingest("fresh-control", self.report("fresh-control", comparison_key=new_allocation))

        self.library.write_bytes(b"correct faster implementation after new HEAD")
        candidate = self.create("new-candidate")
        self.assertEqual(candidate["git_head"], new_head)
        self.assertNotEqual(candidate["source_manifest_sha256"], copied["source_manifest_sha256"])
        self.ingest("new-candidate", self.report("new-candidate", (8.,8.1,7.9), comparison_key=new_allocation))
        selected = ledger.promote(self.campaign, "new-candidate", against="fresh-control")
        self.assertAlmostEqual(selected["gain"], .2)
        self.assertEqual(ledger.git(self.repo, "rev-parse", "HEAD"), new_head)
        self.assertEqual((self.repo / "solver.cpp").read_text(), "int faster_candidate = 2;\n")

    def test_copied_source_parent_needs_verified_artifacts(self):
        self.create("unverified-parent")
        ledger.propose(self.campaign, "control", self.proposal())
        with self.assertRaisesRegex(ledger.EvidenceError, "complete report"):
            ledger.snapshot_from(self.campaign, "control", "unverified-parent")
        self.baseline()
        archive = self.campaign / "attempts" / "baseline" / "source.tar.gz"
        original = archive.read_bytes()
        archive.write_bytes(b"corrupt archive")
        with self.assertRaisesRegex(ledger.EvidenceError, "archive changed"):
            ledger.snapshot_from(self.campaign, "control", "baseline")
        archive.write_bytes(original)
        artifact = self.campaign / "attempts" / "baseline" / "artifacts" / "liblqcd_cpu.so"
        artifact.write_bytes(b"unverified replacement")
        with self.assertRaisesRegex(ledger.EvidenceError, "library is missing/changed"):
            ledger.snapshot_from(self.campaign, "control", "baseline")

    def test_successful_stage_resume_is_idempotent(self):
        self.create("run")
        command = {"argv": [sys.executable, "-c", "from pathlib import Path; p=Path('counter'); p.write_text(p.read_text()+'x' if p.exists() else 'x')"],
                   "cwd": "{build}", "timeout_seconds": 5}
        first = ledger.run_stage(self.campaign, "run", "test", command)
        second = ledger.run_stage(self.campaign, "run", "test", command)
        self.assertEqual(first, second)
        self.assertEqual((self.campaign / "attempts" / "run" / "build" / "counter").read_text(), "x")
        ledger.seal(self.campaign, "run")
        ledger.seal(self.campaign, "run")
        with self.assertRaisesRegex(ledger.EvidenceError, "sealed"):
            ledger.run_stage(self.campaign, "run", "new", command)

    def test_interrupted_checkpoint_needs_explicit_retry_and_reason(self):
        self.create("interrupted")
        path = self.campaign / "attempts" / "interrupted" / "attempt.json"
        data = ledger.read(path)
        data["stages"]["test"] = {"status": "running", "command_sha256": "unknown", "log": "old.log"}
        ledger.atomic(path, data)
        command = {"argv": [sys.executable, "-c", "print('resumed')"], "timeout_seconds": 5}
        with self.assertRaises(ledger.EvidenceError):
            ledger.run_stage(self.campaign, "interrupted", "test", command)
        with self.assertRaises(ledger.EvidenceError):
            ledger.run_stage(self.campaign, "interrupted", "test", command, retry_interrupted=True)
        result = ledger.run_stage(self.campaign, "interrupted", "test", command,
                                  retry_interrupted=True, reason="Confirmed old allocation ended")
        self.assertEqual(result["status"], "passed")
        self.assertEqual(len(result["prior_runs"]), 1)

    def test_timeout_is_retained_and_not_a_success(self):
        self.create("timeout")
        command = {"argv": [sys.executable, "-c", "import time; time.sleep(3)"], "timeout_seconds": .1}
        result = ledger.run_stage(self.campaign, "timeout", "test", command)
        self.assertEqual(result["status"], "timeout")
        self.assertIn("log_sha256", result)
        with self.assertRaises(ledger.EvidenceError):
            ledger.run_stage(self.campaign, "timeout", "test", command)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux direct stage SIGTERM lifecycle')
    def test_direct_stage_sigterm_checkpoints_and_cleans_detached_grandchild(self):
        self.create("signal")
        build = self.campaign / "attempts" / "signal" / "build"
        grandchild = ("import os,signal,time; from pathlib import Path; "
                      "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                      "Path('grandchild.pid').write_text(str(os.getpid())); time.sleep(60)")
        task = ("import os,subprocess,sys,time; from pathlib import Path; "
                f"subprocess.Popen([sys.executable,'-c',{grandchild!r}],start_new_session=True); "
                "Path('task.pid').write_text(str(os.getpid())); time.sleep(60)")
        command = self.root / "nested-command.json"
        ledger.atomic(command,dict(argv=[sys.executable,'-c',task],cwd='{build}',timeout_seconds=50))
        controller = subprocess.Popen([sys.executable,str(FILE),'--campaign',str(self.campaign),
            'run','signal','--stage','nested','--command',str(command)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        owned = []
        try:
            deadline = time.monotonic()+8
            pidfiles = [build/f'{name}.pid' for name in ['task','grandchild']]
            while time.monotonic()<deadline and not all(p.exists() and p.stat().st_size for p in pidfiles):
                time.sleep(.03)
            self.assertTrue(all(p.exists() and p.stat().st_size for p in pidfiles))
            owned = [int((build/f'{name}.pid').read_text()) for name in ['task','grandchild']]
            self.assertNotEqual(os.getsid(owned[0]),os.getsid(owned[1]))
            controller.send_signal(signal.SIGTERM)
            controller.communicate(timeout=12)
            self.assertEqual(controller.returncode,1)
            stage = ledger.read(self.campaign/'attempts'/'signal'/'attempt.json')['stages']['nested']
            self.assertEqual(stage['status'],'interrupted')
            self.assertEqual(stage['interrupt_signal'],int(signal.SIGTERM))
            self.assertTrue(stage['cleanup']['complete'])
            for pid in owned:
                with self.assertRaises(ProcessLookupError):os.kill(pid,0)
            self.assertFalse((self.campaign/'.lock').exists())
        finally:
            if controller.poll() is None:
                controller.kill();controller.communicate()
            for pid in owned:
                try:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass


if __name__ == "__main__":
    unittest.main()
