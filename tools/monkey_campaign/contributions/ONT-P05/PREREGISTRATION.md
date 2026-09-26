# PREREGISTRATION — ONT-P05 (milestone recovery and artifact identity)

Card `ONT-P05` (planning P05, group "Scope, identity, and fleet", kind
integration, verification profile `records`/offline). Attempt
`1ea58bee28c04768b15253c2f1ba7888`, agent
`arrival-9de32a8d32144d1fb62ffc7308cd11d7`, branch `branch-6`,
criteria `53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4`,
scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Dependency ONT-P03: qualified winner PR #140 (merged 2026-09-26). Written
BEFORE the audit tool was implemented or run against any record. Frozen
2026-09-26.

## STATEMENT (a theory that can lose)

The campaign already satisfies every clause of "Recoverable commits, run
manifests, training checkpoints, raw/blob/canonical hash labels, and retry
rules exist" with concrete current records — startup recovery receipts,
checkpoint/run/candidate manifest schemas, the checkpoint receipt law, the
triple raw/blob/canonical hash-label contract, and idempotent retry rules —
and a deterministic read-only audit can bind each clause to its actual
records, re-verify them through an independent oracle (recomputed hashes,
re-executed rule batteries), and name any absent or unresolved component
explicitly, reusing qualified prior evidence (ONT-P03 winner, merge-service
receipts) rather than re-deriving or manufacturing any record.

Clause-to-record reconciliation frozen in advance:

1. Recoverable commits — `chimera.startup_recovery.v1` receipts under
   E:/ChimeraWork/monkey-coordination/startup-receipts/; worker_start.py
   same-arrival retry paths; worker_checkout.py `checkout_identity.json`
   manifest + `unrecorded_checkout_preserved` rule; recoverable commits
   themselves (merged winner SHAs resolvable in the shared object store:
   ONT-P03 merge 736d12cca04964c333410a41ac31ced4bd004344, ONT-P01
   391f0ede0ebc2f4072c62c3386827b1b4eefc88e, ONT-X01
   7a3d11eab2d19c04d70b62e1559eca8d97886658).
2. Run manifests — `chimera.checkpoint_context.v1` pinned run/candidate
   manifest schema (checkpoints.py, campaign.py checkpoint runner,
   checkpoint_context.example.json); `chimera.visual_capture_manifest.v1`
   (visual_capture.py); fleet evidence manifests
   (docs/evidence/agent_fleet/MANIFEST.json with source_base + per-file
   sha256; FEATURE_WALK/MANIFEST_sha256.txt raw-hash manifests); per-attempt
   checkout_identity.json; publication-request artifact lists
   (path + raw sha256).
3. Training checkpoints — `chimera.checkpoint_receipt.v1` gate law
   (checkpoints.py) exercised by test_checkpoints.py; CHECKPOINT_WORKFLOW.md
   checkpoint table; engine curriculum training checkpoints
   (Chimera/docs/curriculum/pending_checkpoints.json, status-carrying);
   W5/W6/W7 training-suite receipts (agents/W7_landing/receipts/).
4. Raw/blob/canonical hash labels — integrity.py `sha256-chimera-json-v1`
   canonical digest + APPROVED_SCOPE.json, which dual-labels ONE subject
   (the sealed map) with BOTH identity rules: scope_sha256 (canonical) and
   raw_file_sha256 (raw bytes of monkey_completion_map.json); raw-file
   SHA-256 law in checkpoints.py evidence_hash and qualification receipts;
   Git blob identity as a distinct label per
   decisions/20260924_campaign_handoffs.md (MV-B4-1, M01-F1: "Label each
   identity").

## AMENDMENT 1 (2026-09-26, before any probe ran; no measurement executed)

While reconciling clause 4's record semantics — still pre-implementation,
pre-probe — the raw label's subject was misread in the first freeze: the
lock's `raw_file_sha256` was assumed to cover the lock's own bytes.
Hashing the candidate subjects (lock: 92d0c33f…, map: 010311bb…) shows the
recorded label 010311bb… binds the RAW BYTES OF monkey_completion_map.json
(165496 bytes). P4 below is re-frozen to the actual record semantics before
any probe or battery was executed; the amendment is recorded here instead of
being silently absorbed.
5. Retry rules — kanban.py accept-merge idempotent winner retry
   (`ALREADY_COMPLETED`, test_kanban.py
   `test_approved_merge_refills_once_and_retry_is_idempotent`);
   continuous_cycle.request_publication duplicate-request dedupe
   (`PUBLICATION_ALREADY_REQUESTED`); suggestion_box.py exact-retry
   idempotence; MERGE_SERVICE.md retry-accept-merge rule with on-disk
   receipts E:/Chimera/merge-service/accept-*-result.json;
   STARTUP_RECOVERY.md retry-the-same-arrival rule; PR head change
   invalidates prior approval (kanban.py/review head checks).

## AMENDMENT 2 (2026-09-26, instrument corrections; probe run 1 VOIDED, no result accepted)

The first audit execution exposed two DEFECTS IN THE PROBE INSTRUMENT, not in
the records; the run is voided before any result is accepted and the
instrument is corrected:

A. Law-token pairing: the token "first unmet checkpoint" was wired to
   CHECKPOINT_VERIFICATION.md, which does not contain it (its wording is
   "first-unmet-gate"); the phrase lives in CHECKPOINT_WORKFLOW.md. The
   record exists; the probe looked in the wrong file. Token pairs corrected.
B. Verification target for the fleet manifest: MANIFEST.json declares its
   own generation (`source_base` commit bf0a62162008c8415b88091c671ac180dbb50193,
   calibrated to resolve as a commit in the play worktree's object store).
   The correct independent oracle for a generation-pinned manifest is that
   declared generation (`git cat-file blob <source_base>:<path>`, read-only),
   not the live worktree files, which legitimately advanced past the
   historical snapshot (probe 1 showed first-8 docs entries "stale" —
   expected drift, mishandled by the instrument). On-disk comparison is
   retained and reported as auxiliary generation-drift information.
   The FEATURE_WALK manifest declares NO generation; its entries keep
   on-disk verdicts with absences named (probe 1 already showed its
   g*.png frames absent from this worktree copy — kept as a finding).

P3 is re-frozen for the official probe run: source_base resolves as a
commit; ALL 8 sampled fleet entries match their declared-generation blob
SHA-256 via read-only `git cat-file` (or the failure is named per entry);
all 8 sampled FEATURE_WALK entries yield definite verdicts with every
absence reported as a finding; all 16 sampled entries are hash-labeled;
no unlabeled manifest lines/entries beyond those reported.

## PREDICTION (not yet measured; each number checkable)

P1. ≥10 `chimera.startup_recovery.v1` receipts exist; for EVERY receipt, the
    filename equals SHA-256 of the `arrival_id` recorded inside it, and each
    names a resume_command invoking worker_start.py. This arrival's receipt
    (filename edbb3770b01289e53640c52e9d431b63fd9ff5ba9df946ac1b443bf0ad94e193.json)
    records task_id ONT-P05, assignment_id 1ea58bee28c04768b15253c2f1ba7888,
    criteria_sha256 53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4.
P2. All three merged winner SHAs named above resolve as objects in the
    attempt checkout's shared object store via read-only `git cat-file -t`
    (type commit). My attempt checkout carries checkout_identity.json whose
    head_sha is a 40-hex commit resolvable in the same store.
P3. agent_fleet/MANIFEST.json parses; `source_base` is 40-hex; every file
    entry carries nonempty path, integer bytes, 64-hex sha256. Of 16 sampled
    entries across MANIFEST.json (8) and FEATURE_WALK/MANIFEST_sha256.txt
    (8), ≥10 verify byte-identical on disk; every sampled entry yields a
    definite match/stale verdict (a mismatch is a REPORTED finding about
    that manifest's generation, never silently ignored).
P4. For tools/monkey_campaign/monkey_completion_map.json: the canonical
    `sha256-chimera-json-v1` digest recomputed via integrity.content_digest
    equals 01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6
    and equals APPROVED_SCOPE.json's recorded scope_sha256;
    integrity.verify_catalog with the external anchor succeeds. The lock's
    recorded raw_file_sha256 010311bb0a4fc5eec6c7f361db3a2631c2821e4b7d6cc56d751c02f6712fe161
    equals the raw SHA-256 of the map file's bytes (both labels bind the
    same subject under two identity rules). For that same map file the
    three labels — raw SHA-256, Git blob SHA-1, canonical
    sha256-chimera-json-v1 — are three DISTINCT values, each labeled as
    such; the lock record's own whole-file raw SHA-256 (92d0c33f…) is
    reported as the lock record's identity.
P5. The CPU-only unittest batteries test_checkpoints, test_kanban,
    test_suggestion_box and test_merge_service pass with 0 failures/errors
    (skips allowed only for the documented host-symlink fixture). kanban.py
    contains the `ALREADY_COMPLETED` idempotent winner return;
    continuous_cycle.py contains `PUBLICATION_ALREADY_REQUESTED`;
    suggestion_box.py returns `exact_retry`; ≥3 accept-*-result.json merge
    receipts exist under E:/Chimera/merge-service/.
P6. The engine curriculum record pending_checkpoints.json parses and every
    entry carries a `status` field; no entry fabricates a passed state
    (`status` values are reported verbatim).

## FALSIFIER

Any claimed existence unsupported by an actual record, or any record whose
independent oracle fails silently (mismatch swallowed, gap unnamed);
a fabricated identity (a field/record the audit manufactures instead of
reads); any write to the live registry, source checkout, or record trees;
a hash-label conflation (calling a raw label canonical, a blob label raw, or
presenting the synthetic example manifests as real captures); or a claimed
pass for a retry rule that its battery does not actually exercise. Missing
or stale components are REPORTED per clause as the audit's findings — the
audit never invents them nor repairs them in place.

## BOUNDS

Read-only over the live registry (`agent_slots.Registry` opened read-only),
startup-receipts, evidence trees and merge receipts; read-only git
(`cat-file`, `hash-object`, `rev-parse`) ONLY inside this attempt's checkout;
CPU-only, stdlib-only; fixture tests write only to temp directories; all
outputs land in this attempt workspace; ≤16 MiB total artifacts. No GPU, no
model/engine start, no source-tree edits, no pushes/merges. Example
checkpoint/visual manifests are cited as schema records, never as run
evidence; a screenshot substitutes for nothing (records profile).

## CORRECTION ADDENDUM (2026-09-26, FROZEN BEFORE THE CORRECTION PROBE RUN; lead CHANGES_REQUIRED on PR #146 head f1b18a55)

The lead's finding: the original probe's training-checkpoints PASS rested on
checkpoint schema/law records, 18 `status: pending` curriculum entries and
test-suite receipts — NOT on an identified recoverable training-state
artifact. Two corrections are frozen here BEFORE the correction probe runs;
no new training run is authorized or performed.

C1. Training-checkpoint clause (branching prereg, honesty decides): the
    correction audit must either
    (a) IDENTIFY an actual recoverable training-state artifact — exact path,
        raw SHA-256, the run/source identity it belongs to, and load/restore
        evidence appropriate to its format (a structural loader re-run
        read-only, or a verified restore receipt) — or
    (b) mark the clause UNAVAILABLE and leave qualification honestly
        incomplete on it.
    Search space declared in advance (read-only): the gait trainer's saved
    policy-parameter checkpoints under
    E:/PythonChimera/ChimeraEngine/output/ports/ (the `ports` store written
    by tools/train_walk.py `np.save(... best_ever[1])` and consumed by the
    f4_walk.py judge); the preserved gait run records under
    */agent_logs/*theta*.json in E:/ChimeraWork/l0-baseline-repro,
    E:/ChimeraWork/lane-archive/w47-agent and E:/ChimeraWork/pass3-integ/repo;
    certified-walk runbook checkpoints (E:/ChimeraWork/*integ*/ cert lanes);
    tie-v2 trainer states; wave-47 materials; engine_state stores; the
    curriculum's run manifests. Falsifier for (a): any relabeled
    non-checkpoint file, any checkpoint hash not recomputed, any run record
    tampered or hand-written now, any claimed certified policy not supported
    by a verdict in a preserved record, any rollout executed (a MuJoCo
    re-judgment is NOT run; the documented judge command is cited as the
    restore consumer, not executed).
C2. Preregistration-history honesty: amendment 2 above followed probe run 1
    (it CORRECTED that probe's instrument; the run was voided). Amendment 2
    must never be described as "pre-measurement"; only amendment 1 was.
    The correction deliverables (report.md, receipt.json) carry the fixed
    wording; this addendum is the frozen statement of that fix.

Also frozen for the correction probe: the audit's own-identity binding moves
to THIS attempt (`arrival-0aa44ef399f64a029e1a268ffcaac2af`, assignment
`d7e4d5e96bb741c7b434f94d4bc3c560`, branch `branch-1`, receipt stem
`733183cf8ddc94bfadccbef337858f41c517f0aafb63f8c9a85d977727ab252c`); the
prior attempt's official probe artifact `identity_audit.json`
(`516e9edb0683e687a7490bb42d6fe28982d187ba9114677ed9254ace43f8bf88`) and the
F1/F2 findings are preserved unmodified as historical evidence; the
correction probe (run 3, the official correction run) re-executes the
extended audit after this freeze. All bounds above still apply: read-only
records oracles, stdlib-only (the `.npy` header is parsed without numpy),
CPU-only, no GPU, no engine or model start, no MuJoCo rollout, writes only
inside this attempt workspace.
