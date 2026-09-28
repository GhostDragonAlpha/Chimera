# MAT2-M01 — Reusable material state and distinct relation types

Task: MAT2-M01 / planning id M01. Attempt `9f1c28b48a6d4a03a10feb0d651debd1`,
arrival `arrival-4333d2ecb8df403393c79377c1f9813e`, criteria sha256
`6ad0547d180d402881dbbf09e6f62581c5b0ebafa308cbddc0b6d5f69abfd859`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.

## Reconciliation and reuse (step 1 — do not repeat existing work)

- Pinned base revision `c525b82c7c3ce0128565424764293a3c85811ab3` already contains
  the teddy prototype's real membrane regions
  (`ChimeraEngine/native/teddy_membranes.json`, 30 named regions) and its material
  catalog (`teddy_materials.json`, 6 entries). The fixture reuses those exact 30
  region IDs instead of inventing new anatomy; P4 re-verifies the pinned blob
  identity through `git show` at test time.
- Validation style and the matter owner/reference role pattern follow
  `tools/membrane_ontology/model.py` (`matter_claims` roles, strict canonical JSON,
  named refusal codes). `ChimeraEngine/THE_ACTUATED_MEMBRANE.md` and
  `ChimeraEngine/core/membranes.py` informed the state/port framing.
- No prior MAT2- card implements a versioned material-state schema; the two
  dependency receipts (MAT2-P02/P03 merges) qualified the frozen contract and the
  records gate this card builds on. No existing source module was modified.

## Frozen-first discipline (step 2)

`PREREGISTRATION.md` in this directory froze statement, predictions P1-P4,
falsifiers F1-F3 and probes before `material_state.py` existed. No prediction,
falsifier or probe was edited after the first test run; only the test file's own
bugs were fixed (listed under Failures).

## What is delivered (step 3)

- `material_state.py` — `chimera.material_state.v1`: versioned schema validating
  regions/shells with rest/current geometry, matter with exactly one owner
  (references never re-own), material direction with monotonic history,
  pressure/deformation law as declared parameters with provenance, and two DISTINCT
  mechanical relation types: contact (state: separated/touching/loaded) and bond
  (explicit endpoints + transfer kind). Containment (`parent`) is a separate,
  non-mechanical relation; no bond record is ever implied by nesting. A bond with
  fewer than two explicit endpoints is refused (`bond_requires_explicit_endpoints`).
  Canonical round-trip, stable-ID grammar, declared renames, revision-compatibility
  (`region_identity_drift`) and an independent mass oracle (`total_mass_once`) ship
  with it. `display()` emits the object's actual regions and graph relations with
  stable IDs, plus a mass summary that counts each matter id once.
- `build_teddy_fixture.py` + `teddy_fixture.json` — the known-object fixture:
  30 regions whose IDs are the pinned teddy prototype's actual membrane IDs
  (provenance records both source blob SHA-256s). Masses (1.25/0.75 kg), the one
  direction, and the placeholder law are explicitly authored at chosen fidelity
  with provenance strings saying so — no measured anatomy constant is claimed.
  Two contacts and one explicit bond connect declared ports.
- `render_material_display.py` + `material_display.json` — the display artifact.
- `test_material_state.py` — the frozen probes.

## Verification (step 4 — actual runs)

Commands (from the attempt checkout, branch-1, base `c525b82c`):

```
python -B tools/monkey_campaign/contributions/MAT2-M01/build_teddy_fixture.py
python -B tools/monkey_campaign/contributions/MAT2-M01/test_material_state.py
python -B tools/monkey_campaign/contributions/MAT2-M01/render_material_display.py
```

Observed results:

- `test_material_state.py`: `Ran 7 tests in 0.040s` → **OK**; embedded named checks:
  **PROBE SUMMARY: 35 named checks, 0 failed**.
  - P1: schema validates, canonical round-trip byte-identical, all 34 identities
    (30 regions + 2 matter + 1 bond + 1 contact classes) match the stable-ID grammar.
  - P2: owners == matter == 2; 58 reference claims; independent oracle
    `total_mass_once` == display total == 2.0 kg exactly; adding a second owner is
    refused (`duplicate_matter_owner`); a reference claim leaves the total at 2.0.
  - P3: display lists containment (1 edge), contacts (2), bonds (1) as separate
    relation kinds with the explicit note; bond endpoint on a nonexistent port is
    refused (`missing_endpoint_port`); single-endpoint bond refused.
  - P4: fixture region set == pinned `teddy_membranes.json` membrane set at base
    revision; recorded blob hash matches the freshly shown blob.
  - F1-F3 bites: double-owner refused; unowned matter refused; bond-removal drops
    bond_count 1→0 with regions and mass unchanged (containment survives — it is
    not mechanical); identity drift refused (`region_identity_drift:muzzle`);
    the same removal is lawful with a declared rename; digests stable across
    re-serialization.
- `render_material_display.py`: object teddy-prototype revision 1 — 30 regions /
  30 shells; matter owned once ×2, references 58; containment 1, contacts 2,
  bonds 1; total mass counted once = 2.0 kg; `canonical_sha256`
  `1c015e2d4cc18cc49fb9ab78d67b5a74f7cae883c5b7b3c8c1d77015a32d9bf1`.

## Failures encountered (preserved, not erased)

1. First validation run refused the fixture (`invalid_region_fields`): the schema
   initially did not allow the `ports` field on regions that relations reference.
   Fixed in the schema; recorded as part of freezing the exact field set.
2. Test bugs (not schema bugs): a leftover scratch assertion in P3
   (`__length_hint__` AttributeError), an F3 probe naming a region (`tail_stub`)
   that does not exist in the fixture, a rename probe colliding with the fixture's
   own `provenance` field, and one check still referencing `tail_stub` after the
   rename to `muzzle`. All fixed and re-run to green.

## Honest boundary (step 5 / runtime & visual)

The `material` verification profile is kind=motion with camera-required fields.
**No runtime claim is made**: base revision `c525b82c` has no runnable material
solver (the pinned runtime's honest gap is documented in
`ChimeraEngine/THE_ACTUATED_MEMBRANE.md` §3), so the visual/camera clause is
recorded **PENDING_RUNTIME** in `material_display.json.display_honesty`, deferred
to the runtime-facing material cards (M03/M04, MAT-PRESSURE) — inventorying absent
components explicitly rather than requiring them here. Numerical/records evidence
for this card's done_when (versioned schema, distinct relations, stable-ID display,
single ownership) is complete above. No GPU, training, network or engine process
was started; writes were confined to this attempt checkout.

## Artifacts (sha256 recorded at submission time in qualification_receipt.json)

- material_state.py
- test_material_state.py
- build_teddy_fixture.py
- teddy_fixture.json
- render_material_display.py
- material_display.json
- PREREGISTRATION.md
- report.md (this file)
