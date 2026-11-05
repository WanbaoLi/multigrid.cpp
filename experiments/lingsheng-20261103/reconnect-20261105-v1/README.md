# Reconnect and fresh allocation

Worker11 task155 completed successfully. Its scheduler job2026153 exited
naturally at2026-11-04T14:34:30Z; all owned descendants were cleaned. Old startup
records and deadlines remain unchanged.

Worker12 job2035397 was submitted for cn19486, which was occupied by another
exclusive job. Only this owned PENDING job was cancelled through a state-filtered
command. Actual terminal scheduler evidence shows no start time, no execution
node and zero execution duration. No active numerical work was interrupted.
The initially considered cn10583 became occupied before submission; its prepared
worker13-v1 files were never deployed or submitted. Worker13-v2 binds cn19480.

Fresh job2035635 started on cn19480 with592 allowed CPUs and480000MB exclusive
memory request. Actual allocation authentication, clean parent affinity,64-byte
SVE and16rank KUPL availability/allocation/residency gates passed. Startup,
wrapper manifests, submission receipts and scheduler query are retained here.
Task158 is the new actual ARM Clover qualification; this allocation archive does
not claim it has completed or that a candidate is faster.

The new wrappers reuse tested worker11 infrastructure.35 pure namespace and
authentication contracts passed before deployment. The earlier worker11-v1
queue-clone preparation mistake and corrected v2 are retained; no job was
submitted using that wrong queue. Experiments stay outside frozen reference skills.
