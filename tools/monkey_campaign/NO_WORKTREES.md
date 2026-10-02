## Permanent operator rule: explain unused agent capacity

Maintain maximum useful parallel capacity. Every coordinator progress report,
hourly audit, dispatch/replenishment cycle and session handoff must account for
utilization. When confirmed productive workers are below the configured target,
the user must be told why, without having to ask.

Report: observed-at time; confirmed productive workers / configured target;
ceiling; blocked, waiting, idle and unknown-status agents; standing services
separately; unfilled target slots; development-ready unassigned tasks; limiting
conditions with supporting evidence; action taken; and next recovery event or
check time. Do not invent an ETA when none is known.

Count distinct real agent/session identities including descendants once. Use the
current dispatcher/harness roster with assignment and progress evidence. Registry
claims alone do not prove a live productive agent. Historical directories, recent
file activity, background services and completed sessions cannot fill the target.
Unknown counts must be reported as unknown, never converted to 'capacity full'.

Use concrete reasons: API throttle/platform cap, insufficient independent ready
work, a specified dependency/decision, source ownership conflict, local resource
pressure, unavailable launcher/coordinator, or failed/interrupted worker. Explain
how the reason limits additional agents: occupied CPU or GPU slots alone do not
prove all development/review capacity is exhausted. Refill useful ready work before
reporting where possible; otherwise name the corrective action and owner.

Do not silently lower the configured target to hide a shortfall. A justified
temporary operating limit must show both the configured target and the temporary
limit, with the reason. Current target is 12 and ceiling 15 unless the versioned
profile changes. The ceiling is not a requirement to manufacture work. Once the
target is met, account for additional useful dispatch opportunities up to the
ceiling when claiming maximum useful capacity.

Report a newly detected shortfall or material change promptly and include it in
each regular report while unresolved. Do not flood the user with identical
poll-level messages. This reporting duty does not authorize duplicate work,
unsafe concurrency, bypassed gates or changes to physical acceptance criteria.

Required compact form:
Capacity: X/target productive; services S (separate); blocked B; unknown U.
Shortfall: N slots; ready-unassigned R; reason and evidence.
Action: what was done, owner of remaining action, next recovery event/check.

Publishing this rule does not prove that a running coordinator has read it or
that an autonomous notification service exists. Record actual revision pickup.

# File packages and runner-owned cleanup

Operator-authorized default, 2026-10-01. New task attempts use pinned file packages,
not Git clones or worktrees. Existing owners finish their current checkouts safely.

## Worker path

Run canonical worker_start.py with your existing arrival ID. An executable Kanban
allocation automatically invokes worker_checkout.prepare and returns working_directory
under the attempt's package/files directory. Missing source revisions or dependencies
are explicit blockers, never permission to clone. The source is the shared repository's
Git object database; source HEAD, index, working files and branches are not changed.

The allocation's base_sha (or review head_sha) pins the input. Otherwise the named
publication branch's cached origin ref is resolved and its SHA recorded. The publisher
must refresh that named ref in the shared repository when needed; a cached ref is not
a claim of remote freshness. Do not silently use whatever source HEAD happens to be.
The default write scope is the card contribution directory. The brief's package_reads
lists extra dependency files/directories; MAT2-M cards include the existing M01-M07
regression closure. A missing closure must be repaired before making a passing claim.
Large datasets stay in the existing evidence/data stores and are referenced by hash.

Edit the package files. Do not run experiments directly in the editing package.
Use the canonical CLI at E:/PythonChimera/tools/monkey_campaign/task_package.py:

    python -B task_package.py seal ABSOLUTE_PACKAGE_DIRECTORY
    python -B task_package.py run --sealed SEALED_DIRECTORY --keep outputs/result.json -- python -B relative/test.py

Use absolute paths to the CLI in actual dispatches. Each seal returns a manifest hash,
base SHA, changed-file list and binary Git patch. Only declared writes may change.
Each run verifies the sealed files and executes in one of four fixed slots, selected automatically by default. --slot 0 through
--slot 3 pin a slot when specifically needed. All slots busy returns state BUSY
and CLI exit 75. Wait/retry, never allocate another directory.
Generated output goes to CHIMERA_OUTPUT_DIR. Declare every evidence file with --keep;
undeclared files are disposable. Run receipts and bounded logs survive in
E:/ChimeraWork/task-runner/results/JOB_ID. Required missing outputs fail the job.

CPU commands only through this runner for now. GPU experiments still use the existing
GPU queue/worker and its evidence anchoring protocol; this tool does not certify GPU
queue cleanup. Git-dependent gates and final integration tests run in the existing
single-owner publication checkout. Do not claim that a reduced package passed a full
repository gate. Parallel agents can edit separate packages and review pinned data;
the one publication owner serializes Git mutations and integration testing.

## Publication and scientific precommitment

Send the sealed manifest hash, patch, base SHA and run receipts through the existing
card publication handoff. The publication owner may use:

    python -B task_package.py apply --sealed SEALED_DIRECTORY --target SHARED_PUBLICATION_CHECKOUT

Apply takes an OS lock and requires a clean target at exactly the recorded base.
It stages changes only; existing commit trailers, review, push, acceptance and merge
authority stay in force. Everyone writing that checkout must obey the single-owner
rule; the lock cannot prevent arbitrary external Git commands. A stale base requires
a fresh package/rebased proposal and relevant revalidation, not force application.

Preregs and amendments that require prior Git commits still require those commits,
published by the existing owner BEFORE gated experiments. A package seal is not a
substitute for a required commit. Submit prereg patches first and pin the subsequent
package to the published prereg commit. Preserve the existing unsquashed lineage law.

## Storage ownership

Runner cleanup is in code, not an AI checklist. Success, nonzero exit, timeout and
budget failure all stop the owned process tree, hash-verify declared output copies,
write receipts and remove scratch. Windows Job Objects own children before they run.
After a runner crash, the next use of that slot verifies its job identity, drains any
remaining named job, preserves declared outputs and removes the old scratch first.
Unknown directories, links, identity mismatches and failed preservation block reuse;
the runner never guesses another agent's data is disposable.

Limits: 256 MiB selected source per package, approximately 1 GiB retained package
history before further seals are refused, four slots, 2 GiB sampled scratch budget per
job, 256 MiB declared retained outputs per job, 1 MiB diagnostic log tail and 20 GiB
results admission threshold. Budget checks are admission/polling controls, not OS disk
quotas; a fast writer can overshoot. These are cooperative tools, not a hostile-code
sandbox: a command can write an absolute path outside scratch. No claim is made that
this controls every program on the machine. Directories preserved for proposals and
evidence have bounded admission, rather than unbounded automatic retries.

Evidence needed by the campaign must go through the existing anchor.py into the
sealed evidence store before it is referenced or its result retired. Runner results
and source proposals are not automatically erased before acceptance. Existing legacy
clone release/retention tools remain available to their owners; new clone creation
through workspace_lifecycle.py is disabled. This change deletes no active legacy work.


## Host resource profile and GLM handoff (2026-10-01)

Measured: i9-13900K, 24 physical cores / 32 logical processors, 137199087616
bytes usable installed RAM (128 GB class). Available RAM at configuration time:
96221601792 bytes. These are starting settings validated for correctness, not a
benchmark claiming optimal throughput. runner_profile.json is the active profile.

- Dispatcher target: 12 API worker/reviewer agents total, ceiling 15. Include
  nested descendants; do not interpret 15 as a per-parent allowance. The runner
  DOES NOT spawn/count API agents or alter GLM's application settings. Existing
  authenticated fleet capacity still applies; never bypass a lower registry limit.
- Four local CPU jobs. Each Windows Job has a 16 GiB aggregate committed-memory
  limit, including children. This is not a guarantee of 16 GiB physical residency.
- Admission requires at least 40 GiB available physical memory: 16 GiB job budget
  plus 24 GiB reserve. Other applications remain outside our limits.
- Four threads per job through OpenMP, MKL, OpenBLAS, NumExpr, Numba, BLIS,
  Accelerate, Rayon and CMake environment variables. Nested OpenMP is restricted.
  These are cooperative settings, not hard CPU quotas or CPU affinity. For tools
  that ignore them, pass explicit worker/build/thread limits of four, including
  pytest-xdist, Ninja, ffmpeg and custom multiprocessing as applicable.
- One publication writer. GPU work remains under the existing queue/lease rules;
  four CPU slots do not authorize four simultaneous GPU experiments.
- BUSY means retry with at least ten seconds of backoff; it is not a failed
  scientific test. HTTP 429/API throttling means honor Retry-After and reduce
  dispatch toward 10; do not create replacements/retry storms. Increase from 12
  toward 15 only within real platform capacity, stable memory and no sustained
  rate limiting. More source workers do not require more CPU slots.

### Instructions to give GLM

Use the installed file-package workflow. Read this document and runner_profile.json.
Reconcile existing owned work first. Target 12 active worker/reviewer agents total,
maximum 15 including descendants, subject to the existing registry/API capacity.
Do not launch duplicates just to reach a number. Keep ready agents on independent
scoped work; do not weaken acceptance or preregistration rules for throughput.

Run canonical startup with each worker's existing arrival ID:

    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id EXISTING_ID

Use its returned working_directory. New tasks get small pinned packages. Do not
make per-task clones/worktrees, run tests in editing packages, or bypass a BLOCKED
preparation. Submit required preregistration commits through the one publication
owner before gated experiments. A seal does not replace those commits.

    python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal PACKAGE_DIRECTORY
    python -B E:/PythonChimera/tools/monkey_campaign/task_package.py run --sealed SEALED_DIRECTORY --keep outputs/result.json -- PYTHON_EXECUTABLE -B RELATIVE_TEST.py

Replace placeholders with the actual returned paths, project interpreter and test;
omit --slot so the runner chooses a free one. Every needed output must be declared
using --keep. GPU runs use the existing GPU queue, not this CPU command.

Report the exact base SHA, sealed manifest hash, command, receipt path, exit status,
artifact hashes and cleanup_verified value. Only call a run passing when its actual
receipt says PASSED and cleanup_verified is true; that alone does not qualify physics
or imply campaign acceptance. Missing/skipped/unrun checks must be stated explicitly.
On BUSY/exit 75 wait and retry. On BLOCKED preserve data and report the exact reason;
do not invent success, increase budgets silently, or create another workspace.

Send proposals through the existing serialized publication path. Anchor required
evidence through anchor.py before registry reference. Existing checkout owners
finish and release their own legacy work; never delete another live lane. Automatic
runner scratch cleanup is already implemented: do not substitute promises to clean
it later. This setup does not clean old GPU outputs or the entire disk.
