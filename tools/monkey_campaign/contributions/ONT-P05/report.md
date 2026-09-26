# ONT-P05 — milestone recovery and artifact identity audit report

**Verdict: the done_when record classes EXIST and verify — recoverable
commits, training checkpoints, raw/blob/canonical hash labels and retry
rules pass their independent oracles outright (4/5 clauses green, all
batteries OK); run manifests exist as schemas and modern verifiable
records, and the standing audit names TWO real historical-record defects
(the agent_fleet MANIFEST.json does not reproduce against its own pinned
`source_base`; the FEATURE_WALK raw-hash manifest's capture frames are
preserved nowhere reachable). Zero silent gaps; nothing repaired or
fabricated.**

- Card `ONT-P05`, planning `P05`, kind integration, profile `records`
  (offline). Attempt `1ea58bee28c04768b15253c2f1ba7888`, agent
  `arrival-9de32a8d32144d1fb62ffc7308cd11d7`, branch `branch-6`,
  criteria `53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4`,
  scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
- Dependency ONT-P03: qualified winner PR #140 (merged 2026-09-26,
  merge `736d12cca04964c333410a41ac31ced4bd004344`) — its ledger
  reconciliation tool was reused as prior art, not re-derived.
- Preregistration frozen BEFORE implementation/probes, with two recorded
  amendments (both pre-measurement; see below).

## The audit tool (deliverable)

`implementation.py::audit(DEFAULT_PATHS)` — READ-ONLY, stdlib, CPU-only.
Binds each done_when clause to actual current records and re-verifies each
through an independent oracle: recomputed raw SHA-256, canonical
`sha256-chimera-json-v1` digest via `integrity.content_digest` /
`integrity.verify_catalog` (external anchor enforced), Git blob identity
via read-only `git hash-object` / `git cat-file`, and re-execution of the
campaign's own rule batteries (`unittest`, `python -B`). Every cited record
carries its raw-file SHA-256 label. Output: `identity_audit.json`
(schema `ont-p05.identity_audit.v1`), rerunnable deterministically.

## Measured against the live records (official probe, 2026-09-26)

| Clause | Records inspected | Oracle result |
|---|---|---|
| Recoverable commits | 25 `chimera.startup_recovery.v1` receipts; own receipt `edbb3770…` (task ONT-P05, attempt, criteria — all bound); `checkout_identity.json` (head `c525b82c…`, branch-6); winner merges of ONT-P01/P03/X01 | PASS — every receipt filename == SHA-256(arrival_id); all 3 winner merge SHAs resolve as commits; attempt head resolves |
| Run manifests | `chimera.checkpoint_context.v1` + `chimera.visual_capture_manifest.v1` schema records + CHECKPOINT_WORKFLOW candidate-manifest law; fleet `MANIFEST.json` (21 entries, `source_base bf0a6216…`); `FEATURE_WALK/MANIFEST_sha256.txt`; per-attempt `checkout_identity.json` | PARTIAL — schema/law records present; fleet manifest DOES NOT reproduce against its declared generation (finding F1); FEATURE_WALK frames absent everywhere reachable (finding F2) |
| Training checkpoints | `chimera.checkpoint_receipt.v1` law (checkpoints.py); CHECKPOINT_WORKFLOW 7-checkpoint table; CHECKPOINT_VERIFICATION; engine curriculum `pending_checkpoints.json` (18 entries, all `status: pending` — none fabricates a pass); 3 W5/W6/W7 training-suite receipts; `test_checkpoints` battery | PASS — law records present; curriculum parses with verbatim statuses; battery 19 tests OK |
| Raw/blob/canonical hash labels | `integrity.py` (`sha256-chimera-json-v1`); dual-labeled `APPROVED_SCOPE.json`; map file | PASS — for `monkey_completion_map.json`: raw `010311bb…`, Git blob `466ba011f9df369e706497a7b21b516f36643385`, canonical `01ea5cdd…` — three DISTINCT labeled identities; `verify_catalog` passes with the human-pinned external anchor; lock's own bytes `92d0c33f…` recorded |
| Retry rules | `kanban.py` `ALREADY_COMPLETED`; `continuous_cycle.py` `PUBLICATION_ALREADY_REQUESTED`; `suggestion_box.py` `exact_retry`; MERGE_SERVICE.md retry-accept-merge; STARTUP_RECOVERY.md retry-same-arrival; 4 `accept-*-result.json` receipts | PASS — all markers present; batteries green: test_kanban 11 OK, test_suggestion_box 5 OK, test_merge_service 2 OK, test_checkpoints 19 OK (0 failures, 0 skips) |

## Findings (work product for the lead — named, never silent)

- **F1 — agent_fleet MANIFEST.json is not reproducible against its own
  pinned generation.** All 8 sampled entries fail the generation oracle:
  7 paths (AGENT_BOOTSTRAP_READINESS.md, AGENT_START.md, THE_AGENT_FLEET.md,
  THE_HOLODECK_BLUEPRINT.md, DOCUMENTATION_INDEX.json,
  DOCUMENTATION_REVIEW.md, its PREREGISTRATION.md) do not exist at all in
  commit `bf0a6216…`; `docs/THE_MASTER_LIST.md` exists there but its blob
  differs from the manifest's recorded SHA-256. Cross-checks (recorded in
  probe history): `bf0a6216…` resolves identically in BOTH the main
  checkout (E:/PythonChimera) and the play worktree; the recorded
  THE_MASTER_LIST hash `4410bdfb…` matches neither the pinned generation,
  nor E:/PythonChimera current, nor the play worktree copy — three distinct
  states, none matching. The manifest's `source_base` label does not bind
  the content it labels.
- **F2 — FEATURE_WALK/MANIFEST_sha256.txt labels unpreserved subjects.**
  Its g000.png–gNNN.png raw-hash entries resolve to no file in the play
  worktree, the datastore-agent copy, or any reachable location (the
  feature_walk.mp4 videos and keyframe_*.png ARE preserved). Either the
  frames survive at an unreferenced location (restore + relabel) or the
  manifest must be marked partial; disposition is lead's, not this audit's.

Both findings are exactly the profile falsifier's target ("missing
identities … fails"): the audit REFUSES to pass the affected historical
manifest records while establishing that the run-manifest mechanism itself
(schema law + generation pinning + modern records such as
`checkout_identity.json` and the dual-labeled scope lock) exists and works.

## Preregistration discipline

Amendment 1 (pre-probe): corrected clause 4's raw-label subject reading —
the lock's `raw_file_sha256` binds the MAP file's bytes, not the lock's own
(discovered by hashing candidate subjects before any probe ran; recorded in
PREREGISTRATION.md). Amendment 2 (probe run 1 VOIDED, no result accepted):
instrument fixes — law-token wired to the wrong file, and the fleet oracle
corrected to the manifest's DECLARED generation (source_base) instead of
drifted worktree files, after calibrating that `bf0a6216…` resolves. The
official run is probe 2. Its prediction scorecard: P1 PASS, P2 PASS,
**P3 FAIL** (predicted all 8 fleet entries generation_match; measured 0/8 —
the failure IS finding F1 and is reported as the work product, not tuned
away), P4 PASS, P5 PASS, P6 PASS.

## Tests and commands

```
cd <attempt>/checkout/tools/monkey_campaign/contributions/ONT-P05
python -B -m unittest test_implementation          # 16 tests, OK (fixtures, temp dirs)
python -B implementation.py --out identity_audit.json   # official probe (exit 0)
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

## Limits

Records and hash oracles only: no visual, runtime, engine, GPU or human
claim is made or needed (profile `records`, `nonvisual_reason`: a
records/numerical-oracle task). Battery runs exercise fixture registries,
not live state. The audit is read-only over the live registry and record
trees; the only write is its `--out` report inside this attempt workspace.
Historical-record repair (F1/F2) is OUT of scope: this card reconciles and
qualifies the existing machinery; it does not rewrite preserved evidence.
