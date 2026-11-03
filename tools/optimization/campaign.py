#!/usr/bin/env python3
"""Evidence-driven, restartable full-propagator optimization ledger (stdlib only).

The ledger runs explicit commands; it never invents numerical edits or treats a
local-kernel speedup as acceptance. See docs/optimization-framework.md.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone

SCHEMA = 1
SHA = re.compile(r"^[0-9a-f]{64}$")
NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")


class EvidenceError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(data):
    return (json.dumps(data, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def object_digest(data):
    return hashlib.sha256(canonical(data)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with temporary.open("wb") as stream:
        stream.write(canonical(data))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def git(repo, *args, binary=False):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            check=True)
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def tree_manifest(root):
    root = Path(root).resolve()
    require(root.is_dir(), f"Reference directory missing: {root}")
    files = []
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Reference must not contain symlinks: {path}")
        if path.is_file():
            files.append({"path": path.relative_to(root).as_posix(),
                          "sha256": digest(path), "bytes": path.stat().st_size})
    require(files, "Reference directory is empty")
    require((root / "SKILL.md").is_file(), "Reference directory needs SKILL.md")
    return files


def check_reference(config):
    actual = tree_manifest(config["reference_skill"])
    require(actual == config["reference_manifest"],
            "Frozen reference skill changed; restore it or start a new campaign")


@contextlib.contextmanager
def locked(root):
    path = Path(root) / ".lock"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise EvidenceError(f"Campaign is locked: {path}; inspect status, then use unlock with a reason if the owner is gone") from exc
    try:
        os.write(descriptor, canonical({"pid": os.getpid(), "host": socket.gethostname(), "time": now()}))
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def campaign(root):
    root = Path(root).resolve()
    config = read(root / "campaign.json")
    require(config["schema"] == SCHEMA, "Unsupported campaign schema")
    check_reference(config)
    return root, config


def attempt_path(root, name):
    require(bool(NAME.fullmatch(name)), "Attempt id must be a short lowercase name")
    path = Path(root) / "attempts" / name
    require(path.is_dir(), f"No such attempt: {name}")
    return path


def event(root, kind, payload):
    directory = Path(root) / "events"
    directory.mkdir(exist_ok=True)
    # One file per event prevents a killed append from damaging earlier events.
    stamp = f"{time.time_ns():020d}-{os.getpid()}"
    atomic(directory / (stamp + ".json"), {"time": now(), "kind": kind, **payload})


def history_data(root):
    root = Path(root)
    return {"attempts": [read(p) for p in sorted((root / "attempts").glob("*/attempt.json"))],
            "events": [read(p) for p in sorted((root / "events").glob("*.json"))],
            "best": read(root / "best.json") if (root / "best.json").exists() else None}


def initialize(root, repo, reference_skill, input_sha256, reference_sha256,
               baseline_commit="HEAD", residual_limit=1e-8, solution_limit=1e-6,
               minimum_gain=0.03, maximum_spread=0.10):
    root, repo = Path(root).resolve(), Path(repo).resolve()
    require(not root.exists(), f"Refusing to overwrite campaign: {root}")
    require(SHA.fullmatch(input_sha256) and SHA.fullmatch(reference_sha256),
            "Input and independent reference hashes must be SHA256")
    require(0 < residual_limit <= 1e-8 and 0 < solution_limit <= 1e-6,
            "Campaign tolerances cannot weaken the residual/reference contract")
    require(0 < minimum_gain < 1 and 0 < maximum_spread < 1, "Invalid decision thresholds")
    config = dict(schema=SCHEMA, created=now(), repo=str(repo),
        baseline_commit=git(repo, "rev-parse", baseline_commit),
        reference_skill=str(Path(reference_skill).resolve()),
        reference_manifest=tree_manifest(reference_skill),
        input_sha256=input_sha256, reference_sha256=reference_sha256,
        objective="full12_api_wall_seconds", residual_limit=residual_limit,
        solution_relative_error_limit=solution_limit,
        minimum_gain=minimum_gain, maximum_relative_spread=maximum_spread,
        minimum_steady_samples=3)
    root.mkdir(parents=True)
    (root / "attempts").mkdir()
    atomic(root / "campaign.json", config)
    event(root, "initialize", {"baseline_commit": config["baseline_commit"]})
    return config


def show_history(root):
    root, _ = campaign(root)
    with locked(root):
        data = history_data(root)
        token = object_digest(data)
        receipt = {"history_sha256": token, "read_at": now(),
                   "host": socket.gethostname()}
        atomic(root / "history-read.json", receipt)
    return {**data, "history_read_token": token}


def propose(root, name, proposal):
    root, config = campaign(root)
    require(NAME.fullmatch(name), "Invalid attempt id")
    fields = ["bottleneck", "hypothesis", "change", "mechanism", "history_links",
              "retry_conditions", "history_read_token"]
    for field in fields:
        require(proposal.get(field), f"Proposal needs {field}")
    require(isinstance(proposal["history_links"], list), "history_links must be a list")
    require(all(isinstance(x, str) and x.strip() for x in proposal["history_links"]),
            "history_links must contain nonempty references")
    with locked(root):
        history = history_data(root)
        token = object_digest(history)
        receipt = read(root / "history-read.json") if (root / "history-read.json").exists() else {}
        require(proposal["history_read_token"] == token == receipt.get("history_sha256"),
                "Read current history first; proposal history token is stale/missing")
        repeated = [old for old in history["attempts"]
                    if old["status"] in ("failed", "rejected", "inconclusive", "blocked")
                    and old["proposal"]["change"] == proposal["change"]
                    and old["proposal"]["hypothesis"] == proposal["hypothesis"]]
        if repeated:
            require(proposal.get("retry_of") in [old["id"] for old in repeated],
                    "Repeated unsuccessful hypothesis needs retry_of and changed-condition rationale")
        path = root / "attempts" / name
        require(not path.exists(), f"Attempt already exists: {name}")
        path.mkdir()
        data = {"schema": SCHEMA, "id": name, "created": now(),
                "proposal": proposal, "status": "proposed", "stages": {}}
        atomic(path / "attempt.json", data)
        event(root, "propose", {"attempt": name, "history_sha256": token})
    return data


def snapshot(root, name):
    root, config = campaign(root)
    with locked(root):
        path = attempt_path(root, name)
        data = read(path / "attempt.json")
        if "snapshot" in data:
            check_snapshot(path, data)
            return data["snapshot"]
        repo = Path(config["repo"])
        names = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard", binary=True)
        source = path / "source"
        require(not source.exists(), "Incomplete source snapshot exists; retain it and use a new attempt")
        source.mkdir()
        entries = []
        for raw_name in sorted(set(names.split(b"\0")) - {b""}):
            relative = Path(os.fsdecode(raw_name))
            original = repo / relative
            # An in-repo campaign must not capture itself or its build products.
            if original.resolve().is_relative_to(root):
                continue
            require(not relative.is_absolute() and ".." not in relative.parts,
                    "Unsafe Git path")
            if not original.exists() and not original.is_symlink():
                entries.append({"path": relative.as_posix(), "deleted": True})
                continue
            require(original.is_file() and not original.is_symlink(),
                    f"Source snapshot requires regular files: {original}")
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
            entries.append({"path": relative.as_posix(), "sha256": digest(destination),
                            "bytes": destination.stat().st_size})
        manifest = {"git_head": git(repo, "rev-parse", "HEAD"), "files": entries}
        atomic(path / "source-manifest.json", manifest)
        (path / "source.diff").write_bytes(git(repo, "diff", "--binary", "HEAD", binary=True))
        (path / "git-status.txt").write_bytes(git(repo, "status", "--porcelain=v1", "-z", binary=True))
        with tarfile.open(path / "source.tar.gz", "w:gz") as archive:
            for entry in entries:
                if not entry.get("deleted"):
                    archive.add(source / entry["path"], arcname=entry["path"], recursive=False)
        (path / "build").mkdir()
        data["snapshot"] = {"source_manifest_sha256": digest(path / "source-manifest.json"),
                            "archive_sha256": digest(path / "source.tar.gz"),
                            "git_head": manifest["git_head"], "source": str(source),
                            "build": str(path / "build")}
        data["status"] = "snapshotted"
        atomic(path / "attempt.json", data)
        event(root, "snapshot", {"attempt": name, **data["snapshot"]})
    return data["snapshot"]


def check_snapshot(path, data):
    require("snapshot" in data, "Snapshot source before running or ingesting")
    snapshot = data["snapshot"]
    require(digest(path / "source-manifest.json") == snapshot["source_manifest_sha256"],
            "Source manifest changed")
    require(digest(path / "source.tar.gz") == snapshot["archive_sha256"], "Source archive changed")
    manifest = read(path / "source-manifest.json")
    expected = set()
    for entry in manifest["files"]:
        target = path / "source" / entry["path"]
        if entry.get("deleted"):
            require(not target.exists(), f"Deleted source reappeared: {target}")
        else:
            require(target.is_file() and not target.is_symlink() and digest(target) == entry["sha256"],
                    f"Frozen source changed: {target}")
            expected.add(entry["path"])
    actual = set()
    for candidate in (path / "source").rglob("*"):
        if candidate.is_file() or candidate.is_symlink():
            relative = candidate.relative_to(path / "source")
            if "__pycache__" in relative.parts and candidate.suffix == ".pyc":
                continue
            require(not candidate.is_symlink(), f"Symlink appeared in frozen source: {candidate}")
            actual.add(relative.as_posix())
    require(actual == expected, "Unrecorded source file appeared; use a new snapshot")
    # Python import caches are the sole allowed generated files in source.
    # CMake/build products belong in the isolated build folder.
    return expected


def check_artifact(path, data):
    require("report" in data, "No ingested evidence")
    library = Path(path) / "artifacts" / "liblqcd_cpu.so"
    require(library.is_file() and digest(library) == data["report"]["library_sha256"],
            "Frozen measured library is missing/changed")


def terminate(process):
    if process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def run_stage(root, name, stage, command, retry_interrupted=False, retry_failed=False, reason=None):
    root, config = campaign(root)
    require(NAME.fullmatch(stage), "Invalid stage name")
    require(isinstance(command.get("argv"), list) and command["argv"] and
            all(isinstance(x, str) for x in command["argv"]), "Command needs string argv array")
    timeout = command.get("timeout_seconds")
    require(isinstance(timeout, (int, float)) and 0 < timeout <= 86400,
            "Command needs a bounded timeout_seconds (<=86400)")
    with locked(root):
        path = attempt_path(root, name)
        data = read(path / "attempt.json")
        check_snapshot(path, data)
        previous = data["stages"].get(stage)
        request_sha = object_digest(command)
        if previous:
            if previous["status"] == "passed":
                require(previous["command_sha256"] == request_sha,
                        "Passed stage has a different command; use a new stage/attempt")
                require(digest(path / previous["log"]) == previous["log_sha256"], "Passed stage log changed")
                return previous
            interrupted = previous["status"] in ("running", "interrupted")
            require((interrupted and retry_interrupted) or (not interrupted and retry_failed),
                    "Prior stage is unfinished/failed; inspect it and explicitly opt into retry")
            require(reason, "An explicit retry reason is required")
            if interrupted and previous.get("host") == socket.gethostname() and previous.get("pid"):
                try:
                    os.kill(previous["pid"], 0)
                except OSError:
                    pass
                else:
                    raise EvidenceError("Prior stage process is still alive; do not duplicate it")
        require(not (path / "seal.json").exists(), "Attempt is sealed; create a new attempt")
        substitutions = {"campaign": str(root), "attempt": str(path),
                         "repo": config["repo"], "source": str(path / "source"),
                         "build": str(path / "build")}
        def expand(value):
            for key, replacement in substitutions.items():
                value = value.replace("{" + key + "}", replacement)
            return value
        argv = [expand(value) for value in command["argv"]]
        cwd = Path(expand(command.get("cwd", "{source}"))).resolve()
        require(cwd.is_dir(), f"Command cwd missing: {cwd}")
        env = dict(os.environ)
        overrides = command.get("env", {})
        require(isinstance(overrides, dict), "env must be an object")
        for key, value in overrides.items():
            require(isinstance(value, str), "Environment values must be strings")
            env[key] = expand(value)
        serial = len(previous.get("prior_runs", [])) + 1 if previous else 0
        log_name = f"{stage}-{serial:03d}.log"
        state = {"status": "running", "started": now(), "argv": argv, "cwd": str(cwd),
                 "env_overrides": {k: env[k] for k in overrides}, "timeout_seconds": timeout,
                 "command_sha256": request_sha, "log": log_name,
                 "prior_runs": ([*previous.get("prior_runs", []),
                                  {k: v for k, v in previous.items() if k != "prior_runs"}]
                                 if previous else [])}
        if reason:
            state["retry_reason"] = reason
        data["stages"][stage] = state
        atomic(path / "attempt.json", data)
        process = None
        try:
            with (path / log_name).open("wb") as log:
                process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=(os.name == "posix"))
                state["pid"] = process.pid
                state["host"] = socket.gethostname()
                atomic(path / "attempt.json", data)
                try:
                    state["returncode"] = process.wait(timeout=timeout)
                    state["status"] = "passed" if state["returncode"] == 0 else "failed"
                except subprocess.TimeoutExpired:
                    terminate(process)
                    state["status"] = "timeout"
                    state["returncode"] = process.returncode
        except KeyboardInterrupt:
            if process:
                terminate(process)
            state["status"] = "interrupted"
        except Exception as exc:
            if process:
                terminate(process)
            state["status"] = "failed"
            state["error"] = str(exc)
        state["ended"] = now()
        if (path / log_name).exists():
            state["log_sha256"] = digest(path / log_name)
        atomic(path / "attempt.json", data)
        event(root, "run_stage", {"attempt": name, "stage": stage, "status": state["status"]})
        check_reference(config)
        check_snapshot(path, data)
    return state


def number(value, label, positive=False):
    require(isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value),
            f"{label} must be finite")
    require(value > 0 if positive else value >= 0, f"Invalid {label}")
    return value


def validate_report(report, config, snapshot_sha):
    require(report.get("complete") is True, "Benchmark incomplete")
    require(report.get("timing_scope") == "full12_api", "Only full12_api wall time can be accepted")
    require(report.get("zero_initial_guess") is True, "Zero initial guess contract missing")
    require(report.get("input_sha256") == config["input_sha256"], "Input SHA mismatch")
    require(report.get("source_manifest_sha256") == snapshot_sha, "Source snapshot SHA mismatch")
    require(SHA.fullmatch(str(report.get("library_sha256", ""))), "Invalid library SHA")
    require(isinstance(report.get("comparison_key"), (str, dict)) and report["comparison_key"],
            "Report needs comparison_key for matched hardware/allocation/problem/timing scope")
    verification = report.get("verification", {})
    require(verification.get("complete") is True and verification.get("passed") is True,
            "Independent verification missing/failed/incomplete")
    require(verification.get("reference_sha256") == config["reference_sha256"], "Independent reference SHA mismatch")
    require(verification.get("columns") == 12, "Independent verification must cover all 12 columns")
    require(number(verification.get("max_true_residual"), "independent residual") <= config["residual_limit"],
            "Independent residual exceeds tolerance")
    if "solution_relative_error" in verification:
        require(number(verification["solution_relative_error"], "solution error") <= config["solution_relative_error_limit"],
                "Independent solution difference exceeds tolerance")
    samples = report.get("samples", [])
    require(isinstance(samples, list) and samples, "No benchmark samples")
    repeats, steady = set(), []
    warmup_count = 0
    for row in samples:
        repeat = row.get("repeat")
        require(isinstance(repeat, int) and not isinstance(repeat, bool) and repeat >= 0 and repeat not in repeats,
                "Samples require unique nonnegative repeat ids")
        repeats.add(repeat)
        require(isinstance(row.get("warmup"), bool), "Each sample needs explicit warmup flag")
        wall = number(row.get("wall_seconds"), "full12 wall seconds", positive=True)
        stats = row.get("stats", [])
        require(len(stats) == 12, "Each sample must contain all 12 columns")
        for stats_row in stats:
            require(stats_row.get("converged") in (1, True), "A column did not converge")
            require(number(stats_row.get("true_residual"), "column residual") <= config["residual_limit"],
                    "A column exceeds residual tolerance")
            require(isinstance(stats_row.get("iterations"), int) and stats_row["iterations"] >= 0,
                    "Column iteration count missing")
        if row["warmup"]:
            warmup_count += 1
        else:
            steady.append((repeat, wall))
    require(warmup_count >= 1, "At least one complete12 warmup is required")
    require(len(steady) >= config["minimum_steady_samples"], "Need >=3 complete12 steady samples")
    values = [item[1] for item in steady]
    median = statistics.median(values)
    spread = (max(values) - min(values)) / median
    return {"steady_samples": values, "steady_repeats": [x[0] for x in steady],
            "median_seconds": median, "relative_spread": spread,
            "minimum_seconds": min(values), "maximum_seconds": max(values)}


def ingest(root, name, report_path):
    root, config = campaign(root)
    with locked(root):
        path = attempt_path(root, name)
        data = read(path / "attempt.json")
        check_snapshot(path, data)
        report = read(report_path)
        summary = validate_report(report, config, data["snapshot"]["source_manifest_sha256"])
        report_sha = object_digest(report)
        if "report" in data:
            require(data["report"]["sha256"] == report_sha, "Cannot overwrite ingested evidence; use a new attempt")
            require(digest(path / "report.json") == report_sha, "Ingested report changed")
            check_artifact(path, data)
            return data["report"]
        require(not (path / "seal.json").exists(), "Attempt is sealed")
        library = Path(report.get("library_path", ""))
        require(library.is_file() and digest(library) == report["library_sha256"],
                "library_path must identify the actual measured binary with matching SHA256")
        (path / "artifacts").mkdir(exist_ok=True)
        shutil.copy2(library, path / "artifacts" / "liblqcd_cpu.so")
        atomic(path / "report.json", report)
        data["report"] = {"sha256": report_sha, "library_sha256": report["library_sha256"], **summary}
        data["status"] = "measured"
        atomic(path / "attempt.json", data)
        event(root, "ingest", {"attempt": name, "report_sha256": report_sha, **summary})
    return data["report"]


def checked_attempt(root, name, config):
    path = attempt_path(root, name)
    data = read(path / "attempt.json")
    check_snapshot(path, data)
    require("report" in data, "No accepted complete report")
    require(digest(path / "report.json") == data["report"]["sha256"], "Ingested report changed")
    check_artifact(path, data)
    report = read(path / "report.json")
    summary = validate_report(report, config, data["snapshot"]["source_manifest_sha256"])
    return data, report, summary


def promote(root, name, against=None, baseline=False):
    root, config = campaign(root)
    with locked(root):
        data, report, summary = checked_attempt(root, name, config)
        best_path = root / "best.json"
        old = read(best_path) if best_path.exists() else None
        require(summary["relative_spread"] <= config["maximum_relative_spread"],
                "Candidate samples too noisy; repeat matched full12 measurements")
        if old and old["attempt"] == name:
            require(old["report_sha256"] == data["report"]["sha256"], "Best evidence changed")
            return old
        gain = None
        if baseline:
            require(old is None and against is None, "Baseline can be adopted only before a best version exists")
        else:
            require(old is not None and against and against != name, "Candidate needs an existing best and a matched --against control")
            _, control, control_summary = checked_attempt(root, against, config)
            _, old_report, _ = checked_attempt(root, old["attempt"], config)
            require(control["library_sha256"] == old_report["library_sha256"] and
                    control.get("configuration", {}) == old_report.get("configuration", {}),
                    "Matched control must measure the current best library and configuration")
            require(report["comparison_key"] == control["comparison_key"], "Unmatched hardware/allocation/problem/timing contract")
            require(summary["steady_repeats"] == control_summary["steady_repeats"], "Candidate/control steady repeat ids differ")
            require(control_summary["relative_spread"] <= config["maximum_relative_spread"],
                    "Control samples too noisy; repeat matched measurements")
            gain = 1.0 - summary["median_seconds"] / control_summary["median_seconds"]
            require(gain >= config["minimum_gain"], "End-to-end gain below campaign threshold")
            # A separate uncertainty gate prevents a small median difference from
            # winning when the candidate/control timing ranges overlap.
            require(summary["maximum_seconds"] < control_summary["minimum_seconds"],
                    "Timing ranges overlap; result is inconclusive, collect more evidence")
        decision = {"attempt": name, "time": now(), "against": against,
                    "report_sha256": data["report"]["sha256"],
                    "library_sha256": report["library_sha256"],
                    "source_manifest_sha256": data["snapshot"]["source_manifest_sha256"],
                    "median_seconds": summary["median_seconds"], "gain": gain,
                    "previous_best": old["attempt"] if old else None}
        if old:
            directory = root / "best-history"
            directory.mkdir(exist_ok=True)
            atomic(directory / (str(time.time_ns()) + ".json"), old)
        atomic(best_path, decision)
        if not (attempt_path(root, name) / "seal.json").exists():
            data["status"] = "best"
            atomic(attempt_path(root, name) / "attempt.json", data)
        event(root, "promote", decision)
    return decision


def rollback(root, name, reason):
    root, config = campaign(root)
    require(reason, "Rollback needs a reason")
    with locked(root):
        data, report, summary = checked_attempt(root, name, config)
        promotions = [e for e in history_data(root)["events"] if e["kind"] in ("promote", "rollback")]
        require(any(e["attempt"] == name for e in promotions), "Rollback target was never accepted")
        old = read(root / "best.json")
        decision = dict(attempt=name, time=now(), reason=reason,
                        report_sha256=data["report"]["sha256"],
                        library_sha256=report["library_sha256"],
                        source_manifest_sha256=data["snapshot"]["source_manifest_sha256"],
                        median_seconds=summary["median_seconds"], previous_best=old["attempt"])
        (root / "best-history").mkdir(exist_ok=True)
        atomic(root / "best-history" / (str(time.time_ns()) + ".json"), old)
        atomic(root / "best.json", decision)
        event(root, "rollback", decision)
    return decision


def conclude(root, name, status, conclusion, evidence):
    require(status in ("failed", "inconclusive", "rejected", "blocked"), "Invalid conclusion status")
    require(conclusion and evidence, "Conclusion needs reasoning and evidence paths")
    root, _ = campaign(root)
    with locked(root):
        path = attempt_path(root, name)
        data = read(path / "attempt.json")
        require(not (path / "seal.json").exists(), "Attempt is sealed; record follow-up in a new attempt")
        data["status"] = status
        record = {"time": now(), "status": status, "conclusion": conclusion, "evidence": evidence}
        data.setdefault("conclusions", []).append(record)
        atomic(path / "attempt.json", data)
        event(root, "conclude", {"attempt": name, **record})
    return record


def seal(root, name):
    root, config = campaign(root)
    with locked(root):
        path = attempt_path(root, name)
        data = read(path / "attempt.json")
        require(not any(v["status"] == "running" for v in data["stages"].values()), "Cannot seal running commands")
        check_snapshot(path, data)
        files = []
        for candidate in sorted(path.rglob("*")):
            if candidate.is_file() and candidate.name != "seal.json":
                files.append({"path": candidate.relative_to(path).as_posix(), "sha256": digest(candidate)})
        manifest = {"sealed_at": now(), "files": files}
        if (path / "seal.json").exists():
            require(read(path / "seal.json")["files"] == files, "Sealed artifacts changed")
            return read(path / "seal.json")
        atomic(path / "seal.json", manifest)
        event(root, "seal", {"attempt": name, "seal_sha256": digest(path / "seal.json")})
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    subs = parser.add_subparsers(dest="action", required=True)
    init = subs.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--reference-skill", required=True)
    init.add_argument("--input-sha256", required=True)
    init.add_argument("--reference-sha256", required=True)
    init.add_argument("--baseline-commit", default="HEAD")
    init.add_argument("--minimum-gain", type=float, default=.03)
    init.add_argument("--maximum-spread", type=float, default=.10)
    for action in ("history", "status"):
        subs.add_parser(action)
    proposal = subs.add_parser("propose")
    proposal.add_argument("id")
    proposal.add_argument("--proposal", required=True, help="JSON file")
    for action in ("snapshot", "seal"):
        subs.add_parser(action).add_argument("id")
    run = subs.add_parser("run")
    run.add_argument("id")
    run.add_argument("--stage", required=True)
    run.add_argument("--command", required=True, help="JSON file containing argv, cwd, env, timeout_seconds")
    run.add_argument("--retry-interrupted", action="store_true")
    run.add_argument("--retry-failed", action="store_true")
    run.add_argument("--reason")
    ingest_parser = subs.add_parser("ingest")
    ingest_parser.add_argument("id")
    ingest_parser.add_argument("--report", required=True)
    promote_parser = subs.add_parser("promote")
    promote_parser.add_argument("id")
    promote_parser.add_argument("--against")
    promote_parser.add_argument("--baseline", action="store_true")
    rollback_parser = subs.add_parser("rollback")
    rollback_parser.add_argument("id")
    rollback_parser.add_argument("--reason", required=True)
    finish = subs.add_parser("conclude")
    finish.add_argument("id")
    finish.add_argument("--status", choices=["failed", "inconclusive", "rejected", "blocked"], required=True)
    finish.add_argument("--conclusion", required=True)
    finish.add_argument("--evidence", nargs="+", required=True)
    unlock = subs.add_parser("unlock")
    unlock.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        root = args.campaign
        if args.action == "init":
            result = initialize(root, args.repo, args.reference_skill, args.input_sha256,
                                args.reference_sha256, args.baseline_commit,
                                minimum_gain=args.minimum_gain, maximum_spread=args.maximum_spread)
        elif args.action == "history":
            result = show_history(root)
        elif args.action == "status":
            path, _ = campaign(root)
            result = history_data(path)
        elif args.action == "propose":
            result = propose(root, args.id, read(args.proposal))
        elif args.action == "snapshot":
            result = snapshot(root, args.id)
        elif args.action == "run":
            result = run_stage(root, args.id, args.stage, read(args.command),
                               args.retry_interrupted, args.retry_failed, args.reason)
        elif args.action == "ingest":
            result = ingest(root, args.id, args.report)
        elif args.action == "promote":
            result = promote(root, args.id, args.against, args.baseline)
        elif args.action == "rollback":
            result = rollback(root, args.id, args.reason)
        elif args.action == "conclude":
            result = conclude(root, args.id, args.status, args.conclusion, args.evidence)
        elif args.action == "seal":
            result = seal(root, args.id)
        elif args.action == "unlock":
            path, _ = campaign(root)
            lock = read(path / ".lock")
            if lock.get("host") == socket.gethostname():
                try:
                    os.kill(lock["pid"], 0)
                except OSError:
                    pass
                else:
                    raise EvidenceError("Lock owner is still alive")
            event(path, "unlock", {"reason": args.reason, "old_lock": lock})
            (path / ".lock").unlink()
            result = {"unlocked": True}
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        if args.action == "run" and result["status"] != "passed":
            return 1
        return 0
    except (EvidenceError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"campaign: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
