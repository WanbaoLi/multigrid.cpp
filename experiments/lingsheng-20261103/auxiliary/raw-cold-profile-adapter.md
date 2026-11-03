# External cold/profile file-integrity adapter

This adapter addresses the observed file-read boundary, not its unknown root cause. Diagnostic085 showed that the previously captured buffered view contained the correct logical prefix plus 1,048,448 zero bytes beyond EOF. Explicit-offset reads, raw FileIO and GNU checks agreed on the exact 2,038,431,872-byte original. Retry086 still failed inside the unchanged scalar helper's buffered hash despite all external raw checks and all12 numerical checks passing. No rejected run is accepted by these adapters.

The only rebound file callbacks are:

| Process | Callback | Scope |
| --- | --- | --- |
| Cold/profile child | `cold_full12.sha` | Source/library/input/output file hashes |
| Profile child | `profile_full12.sha` | Runtime/library and closed perf-data/report hashes |
| Controller | `prepare_best_replay.sha` | Frozen reference, gold, source and recipe identities |
| Controller | `campaign.digest` | File identities for the ledger and artifacts |

All use the same frozen `file_integrity.py`: exact-offset bounded `os.pread`, exact count, one-byte EOF probe, stable path/FD metadata and two independent SHA implementations on the same immutable bytes. On failure the adapter records evidence and rejects; a bounded bad view is retained as a new0600 artifact. It never changes the expected digest or the original payload. The physical propagator name has an explicit 2,038,431,872-byte size gate.

`campaign.object_digest`, cold's in-memory canonical prepared-field hash, all solver methods, numerical thresholds, original clocks and original perf sampling remain unchanged. Original source bytes are SHA-guarded, bounded-read and compiled unchanged; only the named namespace callback bindings are replaced. Protocol files record source SHA, excluded-callback AST fingerprints, complete callback list and audit-row hashes. The profile main body has an empty exclusion list. The original cold report still identifies its frozen source; the separate external protocol/manifest identifies this adapter.

The call chain is: `raw_cold_controller` → unchanged `raw_controller_v4` → unchanged setup controller → derived four-line bash → unchanged NUMA/Python prefix → `raw_cold_adapter` → unchanged profile main and exact cold `runpy` target. The outer hook installs before v4 so the latter transforms benchmark/independent stages first. Independent scalar validation continues through the reviewed v4 helper adapter. Neither original shell nor frozen Python files are overwritten. Actual ledger argv identifies the derived shell, whose manifest records both the original and replacement inner argv and their SHA. Only a Python script entry is matched; the `--cold-wrapper` argument value is not another entry.

For canonical cold runs, the memory prepared-field hash inside the clock is unchanged; the new file-integrity callbacks run in the original file-hash locations. For a raw-LIME cold run, the original `input_sha_seconds` stage lies inside the continuous clock: its dual file hash has additional real cost. Such a number must be labelled with this protocol and compared with x86 using the same protocol. Profile setup remains diagnostic and unranked; runtime evidence and perf decoding/hashing do not become ordinary solver scores.

Compose with the existing parameterized v4 command as follows; `target_args` are the unchanged setup-controller arguments, not new solver flags:

```python
base = raw_protocol_v4.command(root, root/'queue_setup_profile.py', queue_sha,
                               '092-setup-profile', python, target_args)
assert base[:3] == [str(python), '-u', str(root/'raw_controller_v4.py')]
outer = [str(python), '-u', str(root/'raw_cold_controller.py'),
    '--base-controller', str(root/'raw_controller_v4.py'), '--base-sha', base_sha,
    '--cold-adapter', str(root/'raw_cold_adapter.py'), '--cold-adapter-sha', cold_adapter_sha,
    '--cold-source', str(root/'cold_full12.py'), '--expected-cold-sha', cold_sha,
    '--profile-source', str(root/'profile_setup.py'), '--expected-profile-sha', profile_sha,
    '--profile-helper', str(root/'source/tools/optimization/profile_full12.py'),
    '--expected-profile-helper-sha', profile_helper_sha,
    '--prepare-source', str(root/'prepare_best_replay.py'), '--prepare-sha', prepare_sha,
    '--campaign-source', str(root/'source/tools/optimization/campaign.py'), '--campaign-sha', campaign_sha,
    '--reader-sha', reader_sha, '--controller-sha', outer_sha,
    '--audit-root', str(root/'raw-driver-evidence/092-cold-outer'), '--', *base[3:]]
```

Use actual deployed/frozen source hashes from the accompanying manifest. In particular the current remote protected `campaign.py` differs from the working checkout. The wrapper requires the exact reviewed generated four-line shell shape and refuses shell operators, ambiguous Python entries, source changes and reused per-rank audit directories. An interrupted cold/profile stage requires a fresh attempt/output and audit path; no partial output is accepted or overwritten.

Validation: nine isolated Linux/Python3.9.9 toy contracts passed, including the real-shaped full NUMA/profile argv, both profile/runpy hooks, unchanged memory hash/argv, source tampering, stale output rejection, derived-script replay, unrelated stages and composition with the base controller's stage hook. AST tests detect a changed main/clock while permitting only the named callback change. These are infrastructure contracts, not MPI, perf or numerical validation. Tests ran in a disposable login `/tmp` without solver/queue/ROOT deployment. Windows execution exposed NTFS Path.stat versus fstat ctime differences; the Linux production metadata gate was retained.
