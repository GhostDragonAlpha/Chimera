# ONT-P05 — milestone recovery and artifact identity audit report

**Verdict (correction 2, 2026-09-26): the done_when record classes EXIST and
verify — recoverable commits, training checkpoints, raw/blob/canonical hash
labels and retry rules pass their independent oracles outright (4/5 clauses
green, all batteries OK); run manifests exist as schemas and modern
verifiable records, and the standing audit names TWO real historical-record
defects (the agent_fleet MANIFEST.json does not reproduce against its own
pinned `source_base`; the FEATURE_WALK raw-hash manifest's capture frames
are preserved nowhere reachable). Zero silent gaps; nothing repaired or
fabricated.**

CORRECTION: this revision answers the lead's CHANGES_REQUIRED on PR #146
head `f1b18a55…` — the training-checkpoints clause is now supported by an
IDENTIFIED recoverable training-state artifact (path, recomputed SHA-256,
run identity, format-appropriate load evidence), not only by checkpoint
schema/law, curriculum records and test receipts. No new training run was
performed or needed; the historical F1/F2 findings and the prior attempt's
official probe are preserved unmodified. The preregistration description is
also corrected: amendment 2 FOLLOWED probe run 1 (it voided and repaired
that probe's instrument) and is never "pre-measurement"; only amendment 1
was.

- Card `ONT-P05`, planning `P05`, kind integration, profile `records`
  (offline). Correction attempt `d7e4d5e96bb741c7b434f94d4bc3c560`, agent
  `arrival-0aa44ef399f64a029e1a268ffcaac2af`, branch `branch-1`
  (prior attempt `1ea58bee28c04768b15253c2f1ba7888`, agent
  `arrival-9de32a8d32144d1fb62ffc7308cd11d7`, branch `branch-6`),
  criteria `53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4`,
  scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
- Dependency ONT-P03: qualified winner PR #140 (merged 2026-09-26,
  merge `736d12cca04964c333410a41ac31ced4bd004344`) — its ledger
  reconciliation tool was reused as prior art, not re-derived.
- Preregistration frozen BEFORE implementation/probes, with two recorded
  amendments: amendment 1 pre-measurement (before any probe); amendment 2
  FOLLOWED probe run 1 and voided it before any result was accepted (see
  below), plus a correction addendum frozen before this correction probe.

## The audit tool (deliverable)

`implementation.py::audit(DEFAULT_PATHS)` — READ-ONLY, stdlib, CPU-only.
Binds each done_when clause to actual current records and re-verifies each
through an independent oracle: recomputed raw SHA-256, canonical
`sha256-chimera-json-v1` digest via `integrity.content_digest` /
`integrity.verify_catalog` (external anchor enforced), Git blob identity
via read-only `git hash-object` / `git cat-file`, and re-execution of the
campaign's own rule batteries (`unittest`, `python -B`). Every cited record
carries its raw-file SHA-256 label. Output: `identity_audit.json`
(schema `ont-p05.identity_audit.v1`), rerunnable with two named live-store
drifts: the shared startup-receipt store GROWS as other workers arrive
(25 receipts at the prior probe, 40 at the review rerun, 50 at the
correction probe), and battery summaries embed wall-clock times; the
verdicts, findings, labels and recomputed hashes are stable, and each
published probe artifact is pinned by its own raw SHA-256.
Correction: the training-checkpoints clause additionally identifies the
trainer's saved policy-parameter checkpoints and binds them to their
preserved run records (below); the `.npy` header is parsed without numpy.

## The identified training-state checkpoints (correction deliverable)

The gait trainers save the session's best policy parameters with
`np.save(OUTDIR / out_name, best_ever[1])` (git-tracked
`E:/PythonChimera/tools/train_walk.py`, line 512) into the campaign
checkout's `ports` store, and the judge restores them with
`np.load` (`f4_walk.py --theta <path>`). A saved theta IS the complete
trained state of these policy classes (`tools/policy_classes.py`: the
incumbent classes are memoryless/fixed-window and can be warm-started from
the saved vector), and the campaign's own shape law calls these files
checkpoints (`parser.check_theta_shape`: "a trainer that saves a short
theta is minting a checkpoint"; "lets an old checkpoint be re-judged").
Identified at correction probe time (hashes recomputed; header load is a
read-only structural parse; NO rollout was executed — the judge is cited
as the restore consumer, not run, per the frozen addendum):

| Checkpoint (E:/PythonChimera/ChimeraEngine/output/ports/) | raw SHA-256 | format (stdlib header load) | width law |
|---|---|---|---|
| `walk_theta_entrained.npy` | `8f5dd3a68ec4d430a9883f267112b6f7b043ec1432dba6a59d131e87d2a9af92` | npy v1, `<f8`, shape (8,) | entrained width N_FREE+2 = 8 ✓ |
| `walk_theta_mult.npy` | `ad8ed9a9451f1c943bf535a98f2a7cf2fb38b5e36388b636177c3087854d8e90` | npy v1, `<f8`, shape (6,) | plain width N_FREE = 6 ✓ |
| `stand_theta.npy` | `684f1eaab29f683ef7c803180c32e9d4f1e5ddd64656d103ac5391fc79e851b7` | npy v1, `<f8`, shape (1160,) | 4-block stand checkpoint (p_only a0\|kh\|kp\|kr) |
| `step_theta.npy` | `db943f46b29422dc45053c0d9541a0be537cfc93149660a0d8a7cc9cac6e2a3c` | npy v1, `<f8`, shape (7,) | step checkpoint |

N_FREE is read from the law text, not hardcoded: `walk_port.py`
`OSC_JOINTS = ("hip_flexion", "knee_angle", "ankle_angle")`,
`N_FREE = 2 * len(OSC_JOINTS)` → 6.

Run/source identity: the preserved run record
`agent_logs/f4_walk_walk_theta_entrained.json`
(raw SHA-256 `9cd272ea65bd30305d122b9c8b1e5b64b7265d3e60278d74db9b01b5746873aa`)
names `walk_theta_entrained.npy` and is byte-identical at THREE preserved
sites — `E:/ChimeraWork/l0-baseline-repro`,
`E:/ChimeraWork/lane-archive/w47-agent`, `E:/ChimeraWork/pass3-integ/repo`.
It records the entrained walk training run: seed_ids [0], target speed
0.9924 m/s, measured median speed 0.46006 m/s, periodicity 0.1666, and
`verdict: false` (travel/cycle/upright gates not met; ablation passed).
The verdict is reported VERBATIM: no checkpoint in this store belongs to a
certified walking policy, and the audit does not fabricate one — the
clause requires checkpoints to EXIST, and these recoverable
training-state checkpoints do. Honest caveats, named in the audit output:
the store is live working data (git-ignored, preserved at this single
site; 108 `.npy` trainer states total), and `certified_policy_checkpoints:
0`. The correlated judge capture
`f4_walk_walk_theta_entrained.png` (raw `4b1bf56ede348a8e47733de2e3223e8b0c6b11296c807ea95b7d1da269cda6d0`)
sits beside the checkpoint in the same store.

## Measured against the live records (official correction probe = probe 3, 2026-09-26)

| Clause | Records inspected | Oracle result |
|---|---|---|
| Recoverable commits | 40 `chimera.startup_recovery.v1` receipts (25 at the prior probe); own receipt `733183cf…` (task ONT-P05, correction attempt, criteria — all bound); `checkout_identity.json` (head `c525b82c…`, branch-1); winner merges of ONT-P01/P03/X01 | PASS — every receipt filename == SHA-256(arrival_id); all 3 winner merge SHAs resolve as commits; attempt head resolves |
| Run manifests | `chimera.checkpoint_context.v1` + `chimera.visual_capture_manifest.v1` schema records + CHECKPOINT_WORKFLOW candidate-manifest law; fleet `MANIFEST.json` (21 entries, `source_base bf0a6216…`); `FEATURE_WALK/MANIFEST_sha256.txt`; per-attempt `checkout_identity.json` | PARTIAL — schema/law records present; fleet manifest DOES NOT reproduce against its declared generation (finding F1); FEATURE_WALK frames absent everywhere reachable (finding F2) |
| Training checkpoints | the IDENTIFIED checkpoint store + run identity records (table above); trainer/judge law tokens (`train_walk.py` save line, `walk_port.py` width law, `f4_walk.py --theta` restore consumer); `chimera.checkpoint_receipt.v1` law (checkpoints.py); CHECKPOINT_WORKFLOW 7-checkpoint table; CHECKPOINT_VERIFICATION; engine curriculum `pending_checkpoints.json` (18 entries, all `status: pending` — none fabricates a pass); 3 W5/W6/W7 training-suite receipts; `test_checkpoints` battery | PASS — checkpoints exist as recoverable artifacts with recomputed hashes, bound run identity, format-appropriate load evidence and the width law verified; battery 19 tests OK; certified-walk checkpoint count 0, reported honestly |
| Raw/blob/canonical hash labels | `integrity.py` (`sha256-chimera-json-v1`); dual-labeled `APPROVED_SCOPE.json`; map file | PASS — for `monkey_completion_map.json`: raw `010311bb…`, Git blob `466ba011f9df369e706497a7b21b516f36643385`, canonical `01ea5cdd…` — three DISTINCT labeled identities; `verify_catalog` passes with the human-pinned external anchor; lock's own bytes `92d0c33f…` recorded |
| Retry rules | `kanban.py` `ALREADY_COMPLETED`; `continuous_cycle.py` `PUBLICATION_ALREADY_REQUESTED`; `suggestion_box.py` `exact_retry`; MERGE_SERVICE.md retry-accept-merge; STARTUP_RECOVERY.md retry-same-arrival; 4 `accept-*-result.json` receipts | PASS — all markers present; batteries green: test_kanban 11 OK, test_suggestion_box 5 OK, test_merge_service 2 OK, test_checkpoints 19 OK (0 failures, 0 skips) |

Preserved prior evidence (unmodified, by hash): the prior attempt's
official probe `identity_audit.json` @ review/ONT-P05
`f1b18a55c58bef45bb25dacadde162f0ff09f9c1`, raw SHA-256
`516e9edb0683e687a7490bb42d6fe28982d187ba9114677ed9254ace43f8bf88`, whose
5-clause audit and F1/F2 inventory this correction re-derives live with
the same named outcomes; the prior probe's tool, report, receipt and
preregistration remain reviewable at that head.

## Findings (work product for the lead — named, never silent)

- **F1 — agent_fleet MANIFEST.json is not reproducible against its own
  pinned generation.** All 8 sampled entries fail the generation oracle:
  7 paths (AGENT_BOOTSTRAP_READINESS.md, AGENT_START.md, THE_AGENT_FLEET.md,
  THE_HOLODECK_BLUEPRINT.md, DOCUMENTATION_INDEX.json,
  DOCUMENTATION_REVIEW.md, its PREREGISTRATION.md) do not exist at all in
  commit `bf0a6216…`; `docs/THE_MASTER_LIST.md` exists there but its blob
  differs from the manifest's recorded SHA-256. Cross-checks (recorded in
  prior probe history): `bf0a6216…` resolves identically in BOTH the main
  checkout (E:/PythonChimera) and the play worktree; the recorded
  THE_MASTER_LIST hash `4410bdfb…` matches neither the pinned generation,
  nor E:/PythonChimera current, nor the play worktree copy — three distinct
  states, none matching. The manifest's `source_base` label does not bind
  the content it labels. Re-confirmed at correction probe time (8/8 named).
- **F2 — FEATURE_WALK/MANIFEST_sha256.txt labels unpreserved subjects.**
  Its g000.png–gNNN.png raw-hash entries resolve to no file in the play
  worktree, the datastore-agent copy, or any reachable location (the
  feature_walk.mp4 videos and keyframe_*.png ARE preserved). Either the
  frames survive at an unreferenced location (restore + relabel) or the
  manifest must be marked partial; disposition is lead's, not this audit's.
  Re-confirmed at correction probe time (8/8 sampled absences named).
- **F3 (correction inventory, named honestly) — the identified checkpoint
  store is single-site live data.** The `.npy` trainer states survive only
  at `E:/PythonChimera/ChimeraEngine/output/ports/` (git-ignored); the
  multi-site-preserved part of the identity is the run-record JSON set.
  No checkpoint in the store belongs to a certified walk run (run verdicts
  verbatim). Whether to archive/hash-pin the store is lead disposition;
  this audit neither repairs nor relocates it.

All findings are exactly the profile falsifier's target ("missing
identities … fails"): the audit REFUSES to pass the affected historical
manifest records while establishing that the run-manifest mechanism itself
(schema law + generation pinning + modern records such as
`checkout_identity.json` and the dual-labeled scope lock) exists and works.

## Preregistration discipline

Amendment 1 (pre-measurement): corrected clause 4's raw-label subject
reading — the lock's `raw_file_sha256` binds the MAP file's bytes, not the
lock's own (discovered by hashing candidate subjects before any probe ran;
recorded in PREREGISTRATION.md). AMENDMENT 2 FOLLOWED PROBE RUN 1 — it is
NOT pre-measurement, and this sentence is the correction the lead
required: probe run 1 was executed, exposed two DEFECTS IN THE PROBE
INSTRUMENT (not in the records), and was VOIDED before any result was
accepted; amendment 2 then corrected (A) the law-token file pairing and
(B) the fleet oracle's verification target (the manifest's DECLARED
generation, `source_base` `bf0a6216…`). The official run of the original
attempt was probe 2. Its prediction scorecard: P1 PASS, P2 PASS,
**P3 FAIL** (predicted all 8 fleet entries generation_match; measured 0/8 —
the failure IS finding F1 and is reported as the work product, not tuned
away), P4 PASS, P5 PASS, P6 PASS.

CORRECTION ADDENDUM (this attempt, frozen BEFORE the correction probe =
probe 3): C1 — identify an actual recoverable training-state artifact
(path + recomputed hash + run/source identity + format-appropriate
load/restore evidence) or honestly mark the clause UNAVAILABLE; the
search space and falsifiers were declared in advance (see
PREREGISTRATION.md). C1(a) was satisfied: the checkpoint store and run
identity records above. C2 — amendment 2 must never be described as
pre-measurement; enforced in this report and the receipt. No new training
run, no GPU, no rollout; the judge restore path was cited, never executed.

## Tests and commands

```
cd <attempt>/checkout/tools/monkey_campaign/contributions/ONT-P05
python -B -m unittest test_implementation          # 23 tests, OK (fixtures, temp dirs)
python -B implementation.py --out identity_audit.json   # official correction probe (exit 0)
# batteries re-executed by the probe via: python -B -m unittest <module>
#   in E:/PythonChimera/tools/monkey_campaign: test_kanban, test_suggestion_box,
#   test_merge_service, test_checkpoints — all OK
```

Fixture regressions cover each falsifier arm: forged receipt filename,
wrong own-receipt identity, missing own receipt, tampered manifest entry
(stale, never silently matched), unlabeled manifest entries, unlabeled walk
lines, dual-label verification, tampered subject failing both oracles,
missing algorithm label, missing retry markers, sparse merge receipts,
failing battery, driver gap-naming. HashLabelTests run against a real
temporary git repository so the blob-identity path is exercised.
Correction fixtures (CheckpointStoreTests): a fully identified checkpoint
set verifies with hash + header load + width law + hash-stable run records
and NO rollout; missing store file, forged (non-npy) checkpoint, width
mismatch, disagreeing run-record sites, a record naming another
checkpoint, and an absent trainer-law token are each NAMED as findings.

## Limits

Records and hash oracles only: no visual, runtime, engine, GPU or human
claim is made or needed (profile `records`, `nonvisual_reason`: a
records/numerical-oracle task). Battery runs exercise fixture registries,
not live state. The audit is read-only over the live registry and record
trees; the only write is its `--out` report inside this attempt workspace.
Checkpoint load evidence is a read-only structural parse of the `.npy`
header against the trainer's width law; no MuJoCo rollout or engine/model
start is performed, and the documented judge (`python tools/f4_walk.py
--theta <path>`) remains the restore consumer. Historical-record repair
(F1/F2/F3) is OUT of scope: this card reconciles and qualifies the
existing machinery; it does not rewrite preserved evidence.
