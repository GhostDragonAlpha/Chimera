# F03 Report — the rigid climbable trunk asset

Author: M-F03. Date: 2026-09-24. Checkout `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924`, HEAD `1d34b0f5` (base = game tip `33e7a444`).
Item F03, verbatim: "Trunk geometry, surface IDs, material provenance and collision
representation are explicit. Deformable branches and bark damage deferred."
Calculation contract C15.

## What was done

1. **Discovery** (`discovery_note.md`): mapped the compiled-bundle pattern (canonical
   JSON + self-pinned sha256, strict `require`/`Refusal` intake, `chimera.*.v1`
   schemas); established that the frozen engine has NO rigid-prop or mesh-collision
   machinery at all (gait lane = contact-point spheres vs ONE plane,
   `gait_controller.hpp:94,716,1727,2005`; earth lane = body vs inclined plane,
   `earth_environment.hpp:51,56,102`; mesh routes are render-only,
   `graph_earth.hpp:26-30,82`); found the lineage's only friction number (the walking
   contract's `contact_friction = 0.6`,
   `admit_gait_walker_20260919.py:60` — an uncited design constant) and searched the
   on-disk data packages for bark evidence (none); took the provenance FORM from
   `Chimera/docs/matter/matter_library.json` (other lineage, form only).
2. **Prereg frozen before implementation** (`PREREGISTRATION.md`): statement,
   prediction, frozen values, four falsifiers, stop rule. The height and radius are
   DERIVED from P02P03-pinned Oku-2021 walker numbers, the ring count and tolerance
   are derived from each other, and the friction provenance is fixed as
   UNEVIDENCED-PLACEHOLDER with G04 named as the acquisition prerequisite.
3. **Implementation** (pure Python, stdlib-only):
   - `tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py` — frozen constants,
     analytic surface predicates, deterministic mesh builder, representation-error
     measurement, canonical compile, strict `loads`, and a full validator that
     re-derives every claim from stored numbers (closed key vocabulary included).
   - `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` — the compiled
     `chimera.trunk_asset.v1` declaration (16,634 canonical bytes).
4. **Tests** (`tests/test_trunk.py`): 49 cases — determinism (in-process x2, fresh
   subprocess x2, committed-file identity, digest identity), strict loader refusals,
   site contract against F01's LIVE declaration, derivation identities, footprint
   bound, representation error (measured vs formula vs tolerance vs recomputation),
   surface/material identity (explicit, unique, resolvable, honest provenance),
   rigid-only closed vocabulary, reachable approach. **All 49 green**, standalone and
   via `python -m unittest` from the repo root; F01's 30-suite re-run stays green
   (79/79 joint).
5. **Receipts** (`receipts/`): `test_run.txt` (49/49 verbose),
   `validate_receipt.json`, `determinism_receipt.txt` (byte identity).
6. **Handoffs** (`HANDOFFS.md`): F04 (contact verification) and G01 (grip
   feasibility), each with the exact fields to consume and the named debts.

## Measured numbers

| Quantity | Value | Frozen bound / rule |
|---|---|---|
| Declaration bytes | 16,634, canonical, sorted keys | byte-identical per compile (3 subprocess + in-process + committed) |
| `declaration_sha256` (body without pin) | `b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3` | self-pinned, validator-checked |
| sha256 of the committed file (with pin) | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` | — |
| Site | (11.976783, 0.0, 2.471766) m, axis +Y, terrain 0.0 m, slope 0.0 | equals F01's live `trunk_sites[0]`; F01 body digest `aa2607df…` pinned and re-checked |
| Trunk height H | 1.158 m = (0.419+0.482)+(0.125+0.132) | derived, no multiplier; top exceeds the 0.901 m standing bound by one forelimb |
| Trunk radius R | 0.037 m = 0.074/2 | derived; opposed-grip span rule; contact ratio R/r_sole = 9.25 |
| Footprint | R = 0.037 m, every vertex within 0.5 m | F01's bound (falsifier a) |
| Render mesh | 130 vertices (9-float), 384 uint32 indices, 128 triangles, 32 ring segments, outward winding verified per triangle | house `graph_earth.hpp` layout |
| Representation error (measured) | 1.78307e-4 m; sagitta formula 1.78165e-4 m (diff 1.4e-7) | ≤ 2e-4 m = 5% of the 0.004 m sole sphere (falsifier b) |
| Ring-segment derivation | delta(30)=2.027e-4 > TOL ≥ delta(31)=1.898e-4 → N_min=31; N=32 smallest power of two | N=24 refused by the compiler |
| Worst vertex on-surface error | 3.67e-7 m | ≤ 2e-6 m rounding envelope |
| Surface IDs | `trunk_01.lateral` (climbable), `trunk_01.base_cap`, `trunk_01.top_cap` — each with analytic definition, normal law, material ref | unique, resolvable (falsifier c) |
| Material | `mat.bark.trunk_01`; friction 0.6 `UNEVIDENCED-PLACEHOLDER`, acquisition G04; colour `design` | honest provenance; relabelling refused |
| Spawn clearance (real radius) | 12.192185 m | ≥ 1.5 m required |
| Energies | full ascent 113.992539 J; above-reach 25.298862 J | m=10.038 kg, g=9.80665, from stored fields |

## Falsifier verdicts

- **(a) Geometry exceeding the 0.5 m footprint: NOT OBSERVED.** R = 0.037 m; every
  mesh vertex within the bound (per-vertex check, worst far below); solid inside the
  extent. Tampered giant radius refused (`f03_radius_frozen`).
- **(b) Collision representation diverging from render beyond tolerance: NOT
  OBSERVED.** Measured discretization 1.78307e-4 m ≤ 2e-4 m; measured = sagitta
  formula within 1.4e-7; recomputes from the stored vertex table; every declared
  vertex on the analytic surface within the rounding envelope. Widened tolerance,
  shrunk segments, displaced vertex, false measured value, inward winding — each
  refused with a named code.
- **(c) Missing/implicit surface or material identity: NOT OBSERVED.** Three explicit
  surface IDs with analytic definitions, normal laws and resolvable material refs;
  the friction record names its own provenance UNEVIDENCED-PLACEHOLDER with the G04
  acquisition debt and the search receipt. Renamed refs, deleted/duplicated surfaces,
  relabelled provenance ("researched"), dropped acquisition field, changed value —
  each refused.
- **(d) Any deformable/damage claim: NOT OBSERVED.** `rigid: true`, `deformable:
  false`, `damage_model: "none"`, `branches: "deferred"` — and the closed key
  vocabulary refuses any added damage/deformability/plasticity field at top level,
  in geometry, in collision, or in the material record.

## Deviations and honest boundaries

- The engine HTTP contract was NOT exercised (CPU-only; frozen C++; no servers).
  F02 owns the terrain-side exercise; F04 owns contact verification. The declaration
  provides the render mesh in the house 9-float layout so `load_mesh` consumes it
  unchanged.
- The friction value 0.6 is NOT evidence — it is the walking lane's own uncited
  design constant, carried as a labelled placeholder; acquisition is G04's
  prerequisite. No invented number is presented as evidence anywhere in the record.
- The radius rule rests on the Oku foot as the span proxy because map A05 (hand
  digits) is open; G01 consumes the consequence, and changing the radius is a prereg
  amendment, not an edit.

## Integrity paste (git status --porcelain -uall at completion)

```
?? tools/material_volume_diagnostic.md
?? tools/material_volume_diagnostic.py
?? tools/monkey_campaign/agents/F02_terrain/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F02_terrain/brief.md
?? tools/monkey_campaign/agents/F02_terrain/discovery_note.md
?? tools/monkey_campaign/agents/F03_trunk/HANDOFFS.md
?? tools/monkey_campaign/agents/F03_trunk/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F03_trunk/brief.md
?? tools/monkey_campaign/agents/F03_trunk/discovery_note.md
?? tools/monkey_campaign/agents/F03_trunk/receipts/determinism_receipt.txt
?? tools/monkey_campaign/agents/F03_trunk/receipts/test_run.txt
?? tools/monkey_campaign/agents/F03_trunk/receipts/validate_receipt.json
?? tools/monkey_campaign/agents/F03_trunk/tests/test_trunk.py
?? tools/monkey_campaign/agents/U02_camera/INTEGRATION_U07_W10.md
?? tools/monkey_campaign/agents/U02_camera/PREREGISTRATION.md
?? tools/monkey_campaign/agents/U02_camera/brief.md
?? tools/monkey_campaign/agents/U02_camera/discovery_note.md
?? tools/monkey_campaign/agents/U02_camera/receipts/latency_run.json
?? tools/monkey_campaign/agents/U02_camera/receipts/test_run.txt
?? tools/monkey_campaign/agents/U03_focus/PREREGISTRATION.md
?? tools/monkey_campaign/agents/U03_focus/brief.md
?? tools/monkey_campaign/agents/X02_flow/brief.md
?? tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json
?? tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py
?? tools/monkey_campaign/data/monkey_clearing/terrain_query.py
?? tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json
?? tools/monkey_campaign/data/monkey_trunk/trunk_recipe.py
?? tools/monkey_campaign/product/focus_policy.py
?? tools/monkey_campaign/product/focus_policy_tests.py
?? tools/monkey_campaign/product/follow_camera.py
?? tools/monkey_campaign/product/follow_camera_tests.py
?? tools/rigid_body_mass_consumption_validator.DEPENDENCIES.md
?? tools/rigid_body_mass_consumption_validator.md
?? tools/rigid_body_mass_consumption_validator.py
?? tools/tests/material_volume/conftest.py
?? tools/tests/material_volume/test_material_volume_diagnostic.py
?? tools/tests/material_volume/test_validator.py
?? tools/tests/material_volume/test_w6_con16_aggregate.py
?? tools/tests/material_volume/test_w6_exit_classes.py
?? tools/tests/material_volume/test_w6_fullreport_mvb31.py
?? tools/tests/material_volume/test_w6_hash_scope_mvo1.py
?? tools/tests/material_volume/test_w6_reconciled_records.py
```

F03-owned paths (exactly the declared set): `agents/F03_trunk/**` (9 files) plus the
two declared data paths `data/monkey_trunk/trunk_recipe.py` and
`data/monkey_trunk/trunk_declaration.json`. Every other entry belongs to sibling
agents working in parallel (F02's terrain files under `data/monkey_clearing/`, the
U02/U03/X02 lanes, the product/ and material-volume lanes) — created by them,
untouched by M-F03. Scratch compiles were deleted from `.tmp/`; nothing outside the
owned set was written; no existing file was modified; no engine C++ edits; no GPU; no
servers launched.

Not committed (coordinator commits agent files, per campaign pattern).
