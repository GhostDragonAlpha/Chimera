# D-W04-MASS-20260924-FOLLOWUP — body/manifest consistency validator report

- card: **D-W04-MASS-20260924-FOLLOWUP** (planning ids W04/P02; depends on D-W04-MASS-20260924, merged PR #118 at 24db3062187e617cf576019adb131926df63a237)
- attempt: **1842fc38d3734ad096308bce09a7dfd6**
- arrival: **arrival-74c8fd34cbd5413d90aa516badcac808**
- branch: **branch-1** (isolated attempt checkout), base **c525b82c7c3ce0128565424764293a3c85811ab3**
- criteria: **d319ca0311e03505235364cec2dc895ef25fa527ad7a678f033c3df510026ee1**
- source repo (READ-ONLY): `E:/ChimeraWork/monkey-play-20260924`
- preregistration: `PREREGISTRATION.md` (written before any implementation edit; Rule-0 statement/prediction/falsifier)

## What was implemented

`implementation.py` — a source-bound walking body/manifest consistency validator
(stdlib-only, CPU-only, read-only against the source repo):

1. Resolves the acceptance CoT denominator from pinned git objects: `M_BODY_KG`
   literal in `tools/science_funnel/first_skill/acceptance.py` plus the structural
   guard that line `cot = work / (M_BODY_KG * dist)` exists.
2. Resolves the trainer's rigid-assembly mass from pinned
   `validation/gait_controller_20260918/derived_numbers.json` (`body_model.mass_kg`),
   or — when supplied — from a compiled scene bundle (`--scene-json`, nonzero
   `bodies[].mass_kg` sum), with the `walker_model.py`
   `self.body_mass[i] = float(b["mass_kg"])` structural binding recorded.
3. Enforces blob anchors: `--expect-*-blob` 40-hex anchors make it impossible to
   silently measure a different revision than the winning diagnostic cited
   (`BLOB_ANCHOR_MISMATCH` refusal).
4. Refuses (exit 3, named, NO output file) on: missing repo, unresolvable pin,
   path absent at pin, blob anchor mismatch, unparseable/non-finite masses,
   unparseable scene bundle, any nonzero git exit.
5. Reports explicit units (`kg`, `N`, `dimensionless`, `g0=9.80665 m/s^2`),
   full provenance (commit + blob + byte size + raw sha256 per file), the ratio
   `denominator/training`, the weight cross-check `mass x g0` vs the recorded
   `weight_N`, and consistency of ALL frozen definition sites (acceptance literal,
   `run_manifest.json` definition, `RUNBOOK.md` step-5 line, checkpoint report label).
6. Verdict `COMPATIBLE` (exit 0) only when denominator == training mass within
   1e-9 relative AND all frozen sites agree AND the structural guards hold;
   otherwise `INCOMPATIBLE` (exit 1) naming both lineages and the ratio.

No body mass is substituted, no threshold/seed/frozen field is changed: the tool
measures and reports; correcting the denominator remains a NEW lead-authorized
registration (RUNBOOK frozen-field law).

## Pre-verified source anchors (measured before implementation, in PREREGISTRATION.md)

acceptance.py `3df32b59…` @8294053b (identical at a62b286e); run_manifest.json `3188e72f…` @8294053b;
RUNBOOK.md `73a41120…` @8294053b; walker_model.py `89840918…` @a62b286e;
report_first_skill_checkpoint.py `d41c9280…` @a62b286e; derived_numbers.json `8b6d75fb…` @33e7a444;
gait_scene.py `5c8792ae…` @33e7a444; acceptance.py ABSENT at 43b599a7 (rev-parse exit 128).
Arithmetic recomputed: 8.184 + 2x(0.557+0.269+0.080+0.021) = 10.038 kg;
10.038 x 9.80665 = 98.4391527 N; 13824.5 / 10.038 = 1377.216577007372.

## Verification (actual commands and observed results)

1. `python -B -m unittest test_implementation -v` (from this directory):
   **Ran 12 tests in 3.505s — OK** (exit 0). Coverage:
   - real pinned sources: actual binding resolves to 13824.5 kg vs 10.038 kg, verdict
     INCOMPATIBLE with ratio exactly 1377.216577007372 (rel_tol 1e-12); explicit units in
     output; all five frozen definition sites agree on the current literal; weight
     consistency 98.4391527 N vs recorded 98.439 N (|err| 0.0001527 N).
   - refusal controls (each exit 3, named, no output file): missing repo
     (SOURCE_REPO_MISSING), unresolvable pin (PIN_UNRESOLVABLE), acceptance.py @43b599a7
     (PATH_NOT_IN_PIN), wrong expected blob (BLOB_ANCHOR_MISMATCH), unparseable
     denominator (UNPARSEABLE_DENOMINATOR).
   - fixture registrations (synthetic, labeled "fixture", throwaway temp git repos):
     corrected denominator 10.038 -> COMPATIBLE (exit 0) including with positive blob
     anchors; mismatched k-fill book mass 6.15 vs 10.038 -> INCOMPATIBLE with ratio
     6.15/10.038; validator provably read-only (fixture HEAD + clean status unchanged).
2. Standalone demonstration run with all three blob anchors:
   `python -B implementation.py --source-repo E:/ChimeraWork/monkey-play-20260924
   --acceptance-commit 8294053b --trainer-commit a62b286e --scene-numbers-commit 33e7a444
   --out ../../../../../../evidence/validator_run --expect-acceptance-blob 3df32b59… --expect-manifest-blob 3188e72f… --expect-scene-numbers-blob 8b6d75fb…`
   Observed: **8/9 checks green — INCOMPATIBLE** (exit 1, 0.42 s), the single red check
   being `denominator_equals_training_mass` with the named lineages and ratio — the exact
   defect the winning diagnostic proved. Result artifact:
   `E:/ChimeraWork/monkey-coordination/kanban-attempts/D-W04-MASS-20260924-FOLLOWUP/1842fc38d3734ad096308bce09a7dfd6/evidence/validator_run/validation_result.json`.

## Falsifier self-check

- F1 (false COMPATIBLE on current tree): NOT FIRED — verdict is INCOMPATIBLE as preregistered.
- F2 (silent unresolved lineage): NOT FIRED — all five refusal controls exit 3 named, no output file.
- F3 (fixture labeled native acceptance): NOT FIRED — fixtures are labeled "fixture"; the
  validator's own notes state the verdict is a source-lineage statement, not native acceptance.
- F4 (out-of-scope physics/threshold edits): NOT FIRED — the commit adds only this
  contribution directory; no production source, threshold, seed or frozen registration
  field is touched (git diff vs base c525b82c confined to
  `tools/monkey_campaign/contributions/D-W04-MASS-20260924-FOLLOWUP/`).

## Candidate identity

- base: `c525b82c7c3ce0128565424764293a3c85811ab3` (branch-1 checkout head at assignment)
- candidate commit: recorded in the attempt-workspace receipt and publication request
  (a committed file cannot contain its own commit sha); attempt
  `1842fc38d3734ad096308bce09a7dfd6` on branch-1 of the isolated checkout.
- proposed.patch: `E:/ChimeraWork/monkey-coordination/kanban-attempts/D-W04-MASS-20260924-FOLLOWUP/1842fc38d3734ad096308bce09a7dfd6/proposed.patch`
  (diff of the candidate commit vs base; confined to this contribution directory).

## Remaining gates (reported, not closed by this card)

1. W04's denominator/body binding remains UNRESOLVED-AS-WRONG on the current tree
   (13824.5 vs 10.038 kg). The correction itself needs the lead-authorized NEW
   registration (acceptance.py:18, run_manifest.json:54, RUNBOOK step 5,
   test_first_skill_prestage.py:70, report label) — Astra registration ruling
   Q-34439597b1774332972da4d8b4ec6b2a is still open.
2. This validator is a diagnostic check, NOT native acceptance: no engine run, no GPU,
   no training process was started; W04's runtime/visual gates remain unexercised.
3. When the registration correction lands, the W04 owner should run this validator with
   the new pins (expect COMPATIBLE); a compiled scene bundle can be supplied via
   `--scene-json` for the scene-derived binding the diagnostic recommended.

---

# RECOVERY VERIFICATION — attempt 6fe4ddd9955d47f2a20f044d2f483cb5 (2026-09-25)

The candidate above was recovered from attempt `1842fc38d3734ad096308bce09a7dfd6`
(arrival `arrival-74c8fd34cbd5413d90aa516badcac808`), which ended without a
publication request. Adoption is byte-identical (git blob ids re-verified after
extraction from `proposed.patch`: implementation.py `9d16c9b3…`,
test_implementation.py `7f327485…`, PREREGISTRATION.md `027069c6…`,
report.md pre-addendum `aedb2df1…`). The recovery preregistration addendum in
`PREREGISTRATION.md` was written BEFORE this attempt ran anything.

## Re-verification actually performed by THIS attempt (all in this workspace)

1. `python -B -m unittest test_implementation -v` → **Ran 12 tests in 2.793s — OK**
   (exit 0) — replication prediction 1 exact.
2. `python -B implementation.py --source-repo E:/ChimeraWork/monkey-play-20260924
   --acceptance-commit 8294053b --trainer-commit a62b286e --scene-numbers-commit 33e7a444
   --out evidence/validator_run --expect-acceptance-blob 3df32b59b09411721913229c8df4eb3efa04379e
   --expect-manifest-blob 3188e72f949149a335ea6aa1863db90b51e402f6
   --expect-scene-numbers-blob 8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a`
   → **exit 1, "8/9 checks green — INCOMPATIBLE"**, denominator 13824.5 kg,
   training 10.038 kg, ratio **exactly 1377.216577007372**, weight 98.4391527 N —
   replication prediction 2 exact. Artifact: `evidence/validator_run/validation_result.json`
   in this attempt workspace.
3. Refusal controls and fixture COMPATIBLE control re-executed inside the suite
   (all named, exit 3 where required; corrected fixture exit 0) — prediction 3 exact.

## Independent cross-check against the parent card

The re-run itself resolves every lineage fact from pinned git objects in
`E:/ChimeraWork/monkey-play-20260924` — acceptance literal (blob `3df32b59` @8294053b),
manifest/RUNBOOK/label sites, walker structural binding @a62b286e, training mass
(blob `8b6d75fb` @33e7a444) — matching the winning D-W04-MASS-20260924 report
(PR #118, head `24db3062`, criteria `ee0cc5fb…`) line by line. No predecessor
fact is taken from prose: each was re-measured through the validator during this
re-verification.

## Recovery falsifier scorecard

- Any deviation from the replication predictions: **NOT FIRED** — all three held exactly.
- Candidate divergence during adoption: **NOT FIRED** — blob ids identical to the patch.
- New physics/thresholds/pins added by recovery: **NOT FIRED** — this attempt adds
  only re-verification evidence, the recovery addendum, and this section.

Remaining gates are unchanged from the parent report section above (the
lead-authorized NEW registration to correct the denominator; W04 runtime/visual
gates unexercised).
