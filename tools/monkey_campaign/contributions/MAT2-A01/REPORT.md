# MAT2-A01 REPORT — reconciliation of the merged ulna volar-side orientation evidence

Attempt `f59c82c7dba94fb5abb210fe818ef537`, arrival
`arrival-f0a6fc05faa548169c5afdd9fe332de4`, card MAT2-A01 (planning id A01),
criteria sha256 `3ffafb225eb06eb7dc958676d48c17bfcfd7f9d266c68b6e3a32d8b97920ff56`.
Candidate base: `8ec90f13` (merged line `origin/astra/gait-capture` tip, = MAT2-P02's
merge). PREREGISTRATION frozen at `38c2ada2` (committed alone, BEFORE the probe
script or any receipt existed). **No new measurement was made; this attempt is a
reconciliation of already-merged, lead-accepted evidence, per
`MATERIAL_PLAN_ADOPTION.md` ("Old evidence may satisfy unchanged clauses after
checking exact inputs, dependencies and validity; submit that reconciliation as the
new card's contribution instead of reimplementing known-good code").**

## done_when

> Independent anatomical evidence determines roll sign or records ambiguity

**Outcome: satisfied by the merged ONT-A01 record via the records-ambiguity arm
(`AMBIGUITY_RECORDED`, fired F2/F4), with the roll-sign values reproducing the
pinned O1 record exactly. Scoped verification 6/6 probes PASS
(`evidence/reconciliation_receipt.json`, `outcome: RECONCILED`).**

## Reconcile-first: clause identity (why reuse instead of reimplement)

- MAT2-A01 and archived ONT-A01 share `definition_raw_sha256`
  `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`, and the whole
  projected `ontology_qualification.task` object (done_when, observation,
  verification_profile with all 16 camera_required_fields, views, layers, falsifier,
  C01/C16, catalog_refs) digests identically
  (`5f121837b1c6a9a6b2405ba9320191810ca590b47118e4fbf1880b11f678dd83`): a zero-line
  unified diff (registry read-only, scope archive `01ea5cdd…`). Only the envelope
  changed: card id, scope sha (`01ea5cdd…` → `cb5475f8…`), depends_on
  (`ONT-P02` → `MAT2-P02`).

## Scoped verification (the frozen probes PR-1..PR-6, all PASS)

```
cd <attempt checkout>/tools/monkey_campaign/contributions/MAT2-A01
PYTHONDONTWRITEBYTECODE=1 python -B verify_reconciliation.py   [exit 0]
  PASS PR-1: files=25 identical blob sha256 across 6f90c288 -> 4aecbc9e -> 8ec90f13
  PASS PR-2: suite exit=0; unittest: Ran 26 tests, OK=True; FAIL/ERROR lines=0
             (cpu-only python -B; per-line-ok diagnostic=25)
  PASS PR-3: AMBIGUITY_RECORDED, F2/F4 fired, P1 x=-28.320999816060066 mm,
             P2 t=+6 D=+3.2891597453041737 mm, P3 0.15353092426937565 deg
             unanimous NO-FLIP — all exact vs the pinned record
  PASS PR-4: manifest task_id 'A01', profile anatomy, schema v1, 6 rows =
             V1/V2/V3 x diagnostic/clean, all 16 contract camera fields located
             on every row, PNG bytes bound (1639c68e…), canonical
             validate_manifest: structurally_valid=True view_count=6
  PASS PR-5: MAT2-P02 DONE via PR #196 merge 8ec90f13 == candidate base;
             freeze-commit parent == base
  PASS PR-6: failing-first — 1-byte tamper of the receipt FAILS PR-3 while the
             pristine replica passes
```

All probes read only: git objects of this attempt checkout, the registry
(`agent_slots.sqlite3`, opened read-only), and a TEMP replica extracted under the
attempt workspace's `probe_tmp/` (outside the candidate tree). CPU-only, offline.

## FALSIFIERS FIRED FIRST — honest accounting (two, both probe-implementation defects; predictions untouched)

The FIRST probe run returned `FALSIFIER_FIRED (4/6)`:

1. `PR-2 FAIL: suite exit=0 ok=25 fail/error=0 (expected 26 ok)`. Cause: my counting
   heuristic (regex `"\.\.\. ok"`) undercounts when unittest wraps a multi-line
   docstring or a ResourceWarning lands before the verdict word; unittest's own
   summary printed `Ran 26 tests` / `OK`, exit 0, zero `FAIL:`/`ERROR:` result
   lines. Fix: PR-2 now asserts the authoritative unittest summary; the per-line
   count is kept as a disclosed diagnostic. The frozen expectation (26/26, zero
   fail) was NOT changed — it held.
2. `PR-4 FAIL: missing camera fields={V1:clean, V2:clean, V3:clean:
   [visibility_layers]}`. Cause: my locator idiom `(vis.get("layers") or [None])[0]`
   read the clean rows' honestly-EMPTY declared `"layers": []` as absent. Clean rows
   carry empty layers/label_ids by definition (clean semantics; the canonical
   validator accepts this by design). Fix: an empty list is a present, honestly
   empty declaration; only an absent (null) field is missing. The frozen expectation
   (all 16 fields locatable on every row) was NOT changed — it held.

Both corrections are recorded verbatim in `probe_corrections` inside
`evidence/reconciliation_receipt.json`. Nothing was tuned after seeing results; the
falsifiers fired, were root-caused, and the implementation was repaired to measure
what the frozen predictions actually asked.

## Applicability notes and limits

- The replica suite re-execution READ one pinned external input from the read-only
  play checkout: `E:/PythonChimera/Saved/meshes/monkey_birth.bin` (target pack,
  661 076 bytes, mtime 2026-08-31) via the archived `reference/mesh_target_o1.py`.
  Read-only; no writes, no network. Recorded as a real applicability condition of
  the archived suite (it requires that pinned path to exist).
- No new visual capture was produced: the merged, review-accepted capture IS the
  visual evidence; PR-4 binds it to committed bytes (PNG sha `1639c68e…` equals
  context and manifest `capture_sha256`; canonical structural validation passes).
  No runtime/native/GPU claim anywhere.
- The merged record's own open items stay exactly where they were: target palm sign
  UNRESOLVED pending the human A/B labeling verdict (A04 scope); CT
  MorphoSource 000875604 cannot yet re-decide radius-vs-ulna or volar side; 14
  phalanges not covered; ONT-A01's F2/F4 firing stands (frozen zone-shape
  over-strictness, both readings preserved).
- Naming discrepancy recorded: the dispatch context referenced
  `contributions/MAT2-A03/` for the A03 staged-supersession record; no such
  directory exists in any merged tree — the merged planning-id-A03 record is
  `contributions/ONT-A03/` (PR #187, @`4aecbc9e`). Reconciled by content, not name.
- Zero writes outside this attempt workspace; the play checkout `E:/PythonChimera`
  was only read (git + one pinned mesh file read by the replica suite).

## Files

- `PREREGISTRATION.md` (frozen first, commit `38c2ada2`)
- `verify_reconciliation.py` (the frozen probe; corrections disclosed in receipt)
- `reconcile_clause_map.json` (clause-identity proof + clause-to-evidence map +
  dependency verdicts + preserved unresolved inventory)
- `evidence/reconciliation_receipt.json` (probe results, outcome RECONCILED 6/6,
  corrections, applicability notes)
- `qualification_receipt.json` (ontology_queue.qualification shape; head_sha null
  with binding note — the independent reviewer pins it to the reviewed head)
- `REPORT.md` (this file)
