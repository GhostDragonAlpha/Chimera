# PREREGISTRATION — D-W04-MASS-20260924-FOLLOWUP

Written BEFORE any implementation edit. Attempt `1842fc38d3734ad096308bce09a7dfd6`,
arrival `arrival-74c8fd34cbd5413d90aa516badcac808`, criteria
`d319ca0311e03505235364cec2dc895ef25fa527ad7a678f033c3df510026ee1`.

## Rule-0 statement (disagreeable)

The first-skill acceptance CoT denominator (`M_BODY_KG`, `tools/science_funnel/first_skill/acceptance.py:18`)
and the trainer env's simulated rigid-assembly mass (`derived_numbers.json body_model.mass_kg`,
consumed via `walker_model.py` `body_mass[i] = float(b["mass_kg"])`) are two independently
frozen numbers from different lineages. A source-bound validator that resolves both from the
pinned git objects MUST find them INCOMPATIBLE on the current pinned tree, and must return
COMPATIBLE only when both resolve (with explicit units and recorded blob provenance) to the
same kg value. Refusal — never a verdict — is the only legal outcome when any lineage link
is unresolvable.

## Prediction (not yet measured by this attempt at validator level)

Resolving the pinned chain yields exactly: denominator `13824.5 kg` (blob `3df32b59…`
identical at `8294053b` and `a62b286e`), training body `10.038 kg` (blob `8b6d75fb…` at
`33e7a444`), ratio `13824.5 / 10.038 = 1377.216577007372`, weight consistency
`10.038 x 9.80665 = 98.4391527 N` vs recorded `98.439 N` (rounded, |err| < 0.001 N).
Consequently: validator on the current pins exits 1 (INCOMPATIBLE) with that exact ratio;
a fixture registration whose denominator is corrected to the training mass exits 0
(COMPATIBLE); every unresolved-lineage control exits 3 with a named refusal.

## Falsifiers (named before the run)

- F1: validator reports COMPATIBLE on the current pinned tree (it must catch the documented mismatch).
- F2: any unresolved-lineage path (missing repo, unresolvable pin, path absent at pin, blob
  anchor mismatch, unparseable literal) exits 0 or 1 instead of a named exit-3 refusal.
- F3: any output labels a synthetic fixture as native acceptance, or claims a native/GPU run.
- F4: the patch touches any production source, threshold, seed or frozen registration field
  outside `tools/monkey_campaign/contributions/D-W04-MASS-20260924-FOLLOWUP/`.

## Method constraints

CPU-only; stdlib-only; git used read-only against the source repo
`E:/ChimeraWork/monkey-play-20260924` (pins: acceptance `8294053b`, trainer `a62b286e`,
scene numbers `33e7a444`); all writes inside this attempt workspace; every test invocation
under 120 s. No body mass is substituted, no training threshold changed, no frozen field
amended (the RUNBOOK law requires a NEW lead-authorized registration for that — this card
delivers the CHECK, not the swap; the W04 registration ruling Q-34439597b1774332972da4d8b4ec6b2a
remains open and is reported as a still-open gate).

## Pre-verified source anchors (measured by this attempt before implementation)

| object | pin | blob |
|---|---|---|
| first_skill/acceptance.py | 8294053b | 3df32b59b09411721913229c8df4eb3efa04379e (identical at a62b286e) |
| validation/.../run_manifest.json | 8294053b | 3188e72f949149a335ea6aa1863db90b51e402f6 |
| validation/.../RUNBOOK.md | 8294053b | 73a41120fce27a6bf85073712ccc7a68382ff46b |
| typeb_gpu/walker_model.py | a62b286e | 89840918ce8b395c11035aca09e74cc9961b20b4 |
| report_first_skill_checkpoint.py | a62b286e | d41c92802937da4c36f9183f3ae1d1bdaa053579 |
| validation/gait_controller_20260918/derived_numbers.json | 33e7a444 | 8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a |
| gait_scene.py | 33e7a444 | 5c8792aef60f9eb2eb2e10549546ff12a2efe21b |
| acceptance.py absent at 43b599a7 (refusal-test pin) | 43b599a7 | — (rev-parse exit 128) |

These anchors become the validator's `--expect-*-blob` integrity anchors: a file at the pin
whose blob differs is BLOB_ANCHOR_MISMATCH (refusal), so the validator can never silently
measure a different revision than the one the winning diagnostic cited.

---

# RECOVERY ADDENDUM — attempt 6fe4ddd9955d47f2a20f044d2f483cb5 (2026-09-25)

Recovered candidate: attempt `1842fc38d3734ad096308bce09a7dfd6` (arrival
`arrival-74c8fd34cbd5413d90aa516badcac808`) authored the four files above and its
standalone run evidence, but ended without a publication request. This attempt
(6fe4ddd9, arrival `c95e1722350849bca846b237c1f60997`, same base `c525b82c`) adopts
the candidate byte-identically (git blob ids verified:
implementation.py `9d16c9b3…`, test_implementation.py `7f327485…`,
PREREGISTRATION.md `027069c6…`, report.md `aedb2df1…`) and RE-VERIFIES it
independently. The addendum is written BEFORE any re-run of the suite or the
validator (Rule 0 for the replication measurement).

## Replication prediction (not yet measured by THIS attempt)

1. `python -B -m unittest test_implementation -v` from this workspace:
   12 tests, all OK, exit 0, under 120 s.
2. Standalone validator with all three blob anchors against
   `E:/ChimeraWork/monkey-play-20260924` (pins 8294053b / a62b286e / 33e7a444;
   anchors 3df32b59… / 3188e72f… / 8b6d75fb…): exit 1,
   "8/9 checks green — INCOMPATIBLE", denominator 13824.5 kg, training 10.038 kg,
   ratio exactly 1377.216577007372, weight 98.4391527 N.
3. The five refusal controls each exit 3 named with no output file; the fixture
   COMPATIBLE control (denominator corrected to 10.038 kg) exits 0.

## Replication falsifier

Any deviation from 1-3 that is not a named, reproducible environmental refusal
(e.g. play repo missing) fails the recovery: the candidate must reproduce exactly
or the divergence is reported, not smoothed over. This attempt adds no new
physics, thresholds, pins or claims — only the re-verification and republication.
