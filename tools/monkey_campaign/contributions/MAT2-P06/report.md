# MAT2-P06 qualification receipt — release acceptance limits contract

Task: MAT2-P06 "Choose release acceptance limits" (planning id P06, kind=decision,
profile `records`). Attempt `6ecad9d537c346c4a31e9ce7b48a1fc7`, agent
`arrival-e43f2a7138c44240b07bc79f0e15176a`, criteria
`adfd6c0c8aa993c1ed0c5379a5fe790b8949ea4786ccc7865863b23c8b4d9ce8`,
attempt checkout branch-4 (base head `9ba1be77228e181f55ed2e4d2eb3e73e2f09685f`),
contribution path `tools/monkey_campaign/contributions/MAT2-P06/`.

## What this contribution is

One decision artifact, `release_limits.json` (schema
`mat2-p06.release_limits.contract.v1`), generated at run time by
`implementation.py` from sha256-asserted pinned bytes recovered read-only into
`reference/`, plus `test_implementation.py` (13 tests) and `PREREGISTRATION.md`
(frozen before implementation). It freezes:

- 15 carried DERIVED limits crosswalked from the lead-accepted ONT-P06
  correction (unchanged first done_when clause), re-measured here and
  program-zero-diffed against the accepted proposal (0 diffs);
- 8 new material-first DERIVED entries (numerical/convergence/energy bars,
  applicability boundary, contact-model and friction STATUS freezes);
- camera-visible player outcomes frozen from the pinned catalog text;
- the separate walking-through-woods / full-climbing reporting structure;
- 7 OPERATOR_DECISION_REQUESTED items (4 carried unchanged + 3 new) — every
  numeric no record supplies is an open request, none decided silently;
- 5 explicitly inventoried unresolved acceptance numerics.

## Reconcile (phase 1) — clause-to-evidence map

| done_when clause | evidence | verdict |
|---|---|---|
| "Supported hardware, controls, terrain/trunk envelope, session duration, latency, frame-time and stability limits are frozen before acceptance trials" | byte-identical clause text in ONT-P06 (archived, DONE). Accepted proposal: PR #156 head `2148f8d3c722cd41ec05297775538fd949a226e0`, criteria `7bea081e...`, independent PASS review `43b415fe0db04e72b9f5e047754839c4`, lead verdict ACCEPTED. Crosswalked: 15 values re-derived bit-identically from the same pinned play-repo revisions; 4 decision requests carried unchanged. | RECONCILED (old evidence satisfies unchanged clause after input/identity re-verification; old DONE not promoted silently — every value re-measured here) |
| "Freeze numerical/convergence/energy/contact/performance limits and camera-visible player outcomes before experiments" | NEW: coupled-arm native validation receipt `tools/science_funnel/validation/coupled_native_20260917/receipt.json` @ source-repo `32105f18d7340ba14d4764cc1e0d3abb4496f80f` (energy residual bound 1e-5 J, fourth-order refinement requirement, applicability boundary, measured metrics); catalog `tools/monkey_campaign/monkey_completion_map.json` @ `59f81d4dcb1cf45192bde124c1e35510fb439f1b` (walking/material profiles, MAT-WOODS/V07/S05 acceptance, camera fields, first_visible_sequence; live on-disk catalog byte-identical to pin — verified at generation); `gait_controller.hpp` @ play `8cec4a6b...` line 94 + negative heightfield search (contact-model status); `admit_gait_walker_20260919.py` @ `8707551c...` line 60 (friction placeholder status). Contact/friction/performance NUMERIC ceilings absent from all records → 3 new decision requests. | FROZEN where records supply values; OPERATOR_DECISION_REQUESTED where they do not |
| "Report first walking-through-woods acceptance separately from later full climbing completion" | report structure derived from pinned checkpoint graph (MAT-WOODS requires MAT-REUSE; V07 requires V04+V06) and `first_visible_sequence` (W10/F06 before K08/S05): report_A (V03/V04/MAT-WOODS; W10/F06/F08/U07) FIRST, report_B (V07; K04–K08 + S05) separately after | FROZEN (structural) |

Dependency verdicts: MAT2-P01 DONE — winner PR #192, head
`e61838b9fb058b19631717fc5d15be8c31681954`, merge `97993cbefaf00380803d8e67652ac51d50c37d06`,
merged 2026-09-27T08:47:35Z (board record). MAT2-P06 was claimable and claimed.
Archived ONT-P06 lineage: HISTORICAL_SCOPE_READ_ONLY, DONE (above).

## Decide (phase 2) — recorded ruling search

- The recorded lead/operator ruling for this exact decision IS the accepted
  ONT-P06 proposal for the unchanged clause (PR #156 ACCEPTED) — reused, not
  re-decided.
- The suggestion mailbox (`suggestion_box.py list`, read 2026-09-27) contains
  NO operator answer to the 4 carried decision requests (session-duration-cap,
  supported-hardware-floor, network-latency-sla-ms, frame-time-budget-ms); they
  carry forward unchanged as OPERATOR_DECISION_REQUESTED. The D-W04 denominator
  question Q-34439597b1774332972da4d8b4ec6b2a remains NEEDS_EVIDENCE and
  supersession question Q-136fedaa492e4375a5b6f7589345e881 remains OPEN.
- 3 new decision requests added (contact-geometric-tolerance,
  surface-friction-envelope, material-pass-performance-budget), each with
  options + recommendation and source=None. No policy, geometry, threshold or
  physical parameter was chosen by default.

## Verify (phase 4) — commands, identities, observed results

All CPU-only, `python -B`, no network, no GPU. Repositories touched only by
read-only `git show` / `git cat-file -e` (recovery + identity re-checks).

```
python -B implementation.py --out release_limits.json
  -> carried_count=15, material_first_derived_count=8,
     decision_requested_count=7, crosswalk zero-diff (15 values, 4 requests)
python -B implementation.py --out <tmp>/rl2.json   (second generation)
cmp release_limits.json <tmp>/rl2.json             -> byte-identical
python -B test_implementation.py
  -> Ran 13 tests OK
     (law shape/numeric accounting, counts consistency, crosswalk zero-diff,
      camera outcomes vs pinned catalog, separate-reports structure,
      identity pinings incl. live-catalog==pin, deterministic regeneration,
      negatives: pin drift, crosswalk-target tamper, crosswalk value diff,
      missing source, missing git identity, tick-pin disagreement)
```

Observed key values (all re-measured from pinned bytes; full provenance with
{path, repo, commit, blob_sha256, method, locator} in `release_limits.json`):
carried 15 identical to the accepted proposal (terrain envelope 20.0 m, spawn
[0,0,0], clearance 1.5 m, body envelope 0.25 m, seed 4598321, trunk site
[11.976783, 0.0, 2.471766], blocking 0.287 m, controls Return/Escape/R/Q,
tick 300 Hz + substeps 4 (gait==earth cross-check), episode cap 300 / window
270 ticks, worst moving ledger 30.970714 J, settle sink 0.01 m (recorded bar,
expression cross-check 0.0099998780), settle vy 0.05 m/s, poll 100 ms).
Material-first: coupled energy-residual bound 1e-5 J with measured worst
ten-second residual 4.2412640066658014e-10 J; refinement requirement "fourth"
order with measured ratio 15.962558823963903 (~2^4); worst native/reference
scalar error 1.2732925824820995e-11; friction placeholder 0.6 (bare literal,
no citation on line 60; consumed at line 179); native contact = single plane
scalar (line 94; heightfield occurrences 0 in pinned bytes).

Negative falsifier results (each refuses loudly, tested): PIN DRIFT (tampered
reference byte), PIN DRIFT (tampered crosswalk target), CROSSWALK DIFF (tampered
target value with matching hash), pinned_source_missing, git_identity_missing
(nulled commit), tick_pins_disagree (300 vs 500).

Artifact identities (sha256):
- `release_limits.json` a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8
- `implementation.py`, `test_implementation.py`, `PREREGISTRATION.md`,
  `report.md`: see publication request manifest (hashes computed at handoff).
- reference/: 13 pinned sources + 1 crosswalk target, all hash-asserted at
  import (any drift refuses).

## Profile applicability (records, offline)

`numerical_evidence_required: true` — satisfied by the pinned-record
derivations and zero-diff checks above; `nonvisual_reason` recorded: this is a
source/contract/decision task whose truth requires records and numerical
oracles, not a 3D image; no camera manifest applies
(`camera_required_fields: []`). No runtime or visual acceptance is claimed.

## Inventory of absent / unresolved components (explicit)

1. Operator answers to all 7 decision requests (freeze remains partial until
   answered; the four carried requests have been open since ONT-P06).
2. cot-denominator-lineage (D-W04 13824.5 kg vs 10.038 kg) — absolute CoT
   limits blocked; mailbox Q-34439597b... NEEDS_EVIDENCE, Q-136fedaa... OPEN.
3. Numeric contact tolerances (render/collision agreement, penetration,
   tunnelling) — absent from records; pinned walking engine is single-plane
   only (no heightfield/trunk contact service at the pinned revision).
4. Surface-friction envelope — only the uncited placeholder 0.6 exists.
5. Frame-time/VRAM budgets for the coupled GPU material passes — no
   reserved-window profile exists yet (M08/R03 will produce the first).
6. W03 anchors (302 ticks, 30.970714 J) are baseline evidence only until rerun
   against the selected material representation (catalog W03 note).
7. MAT2 F01/F03 own the authoritative clearing/trunk authoring; the carried
   terrain/trunk envelope values freeze the pinned declarations as the
   standing envelope until those cards supersede them via reviewed merges.

## Remaining gates

- Lead review + exact-head publication to `review/MAT2-P06` (base
  `astra/gait-capture`); operator answers to the decision requests; the
  downstream integration checkpoints (MAT-WOODS, V07, S05) remain separate
  milestones and are not claimed here.
- Failures encountered during this attempt: none beyond two test-harness
  iterations (numeric-leaf allowlist prefix semantics; Windows newline
  translation in a negative-test fixture), both fixed before final run.

## Writes stopped

After the publication request is recorded, this attempt ceases writes. The
candidate is preserved under the attempt checkout at
`tools/monkey_campaign/contributions/MAT2-P06/` and committed on local
branch-4 (no push; publication is lead-serialized).
