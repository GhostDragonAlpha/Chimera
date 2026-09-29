# LOCAL-BUFFY-QWEN — assembly_handoff_01

**Assignment.** An isolated assembly-manifest adapter joining anatomy candidates, material mass
properties and mechanical attachment requirements, answering exactly one question: *"Does this
assembly have the explicitly authored information needed for a dynamics trial, and exactly what is
missing?"*

**Status: complete.** Adapter + 4 synthetic fixtures (all passing) + real-packet readiness report.
The answer for the real packet is **no**, with every missing dependency named.

This session continued from two predecessors that ran out of context; their handoff claims were
re-verified against the files, and two of them did not hold (§ Failures and corrections).

---

## Changed files

All inside owned paths (`tools/assembly_handoff/`, `agent_logs/local_buffy_qwen/`). No upstream file
was edited.

| Path | State | What it is |
|---|---|---|
| [`tools/assembly_handoff/assembly_handoff.py`](../tools/assembly_handoff/assembly_handoff.py) | edited (1511 lines) | the adapter; CLI `--bundle <bundle.json> [--out manifest.json]` |
| [`tools/assembly_handoff/run_fixtures.py`](../tools/assembly_handoff/run_fixtures.py) | edited (308 lines) | fixtures 1–4 + negative controls a–g, with assertions |
| [`tools/assembly_handoff/real_packet_readiness.py`](../tools/assembly_handoff/real_packet_readiness.py) | edited (276 lines) | example 5 — the real anatomy packet; exits 3 if it ever reports ready |
| [`tools/assembly_handoff/fixtures/parts/PROVENANCE.md`](../tools/assembly_handoff/fixtures/parts/PROVENANCE.md) | **new** | which parts are authored synthetic, their claim-ref prefixes, and where each number comes from |
| [`tools/assembly_handoff/DERIVATION.md`](../tools/assembly_handoff/DERIVATION.md) | **new** | Rule 0 STATEMENT / PREDICTION / FALSIFIER, plus what the falsifiers actually caught |
| `tools/assembly_handoff/out/*.json` | generated | 10 manifests/refusal records |

The four fixture bundles and their parts were already present from predecessors and are unchanged
except `material_volume_synthetic.json`.

---

## Commands and results

```
python tools/assembly_handoff/run_fixtures.py                 → exit 0, all fixtures + controls pass
python tools/assembly_handoff/real_packet_readiness.py        → exit 0, ready=false (expected)
python tools/assembly_handoff/assembly_handoff.py --bundle \
    tools/assembly_handoff/fixtures/duplicate_mass_ownership.json   → exit 2, refusal
python tools/material_volume_checks.py                        → exit 0, Ran 17 tests OK
python -m pytest tools/finite_area_attachment -q              → exit 0, 48 passed
```

Fixture suite output:

```
[fixture 1] complete synthetic assembly must pass
  ready=True, counted mass 1.000000 kg, 2/2 attachments qualified, lambda_min=32.000 N*m/rad, 1 note code(s)
[fixture 2] duplicate mass ownership must be refused
  REFUSED as required: duplicate_mass_ownership at components[body-upper].mass_claims
[fixture 3] unresolved anatomy mass must block readiness
  ready=False, blocking=['component_mass_not_validated'] (x2 components)
[fixture 4] waypoint + missing mechanical parameters stays incomplete
  ready=False, 3 authored fields left missing, waypoint kept as waypoint_not_a_port
[controls] refusal paths, mutated from fixture 1
  REFUSED as required: mass_status_promotion at ownership[ownership_complete].mass_claims[2].assert_mass_status
  REFUSED as required: waypoint_promoted_to_attachment at requirements[requirements_complete].attachments[1].endpoints
  unbound matter blocked readiness as required
  absent material-volume document blocked readiness as required
  REFUSED as required: unsupported_surface_mass_claim at ownership[ownership_surface].mass_claims[3].counts_toward_component_mass
  REFUSED as required: duplicate_mass_ownership at mass_ownership_ledger.claims[material_volume:...region-upper]
  REFUSED as required: duplicate_role_input at inputs[role=ownership_bindings]     ← added this session
```

The four required fixtures map to the requirement one-for-one: complete passes; duplicate mass
ownership is **refused** (no manifest emitted); unresolved anatomy mass **blocks** readiness; a
geometric waypoint without mechanical parameters stays **incomplete**.

---

## The synthetic manifest

`tools/assembly_handoff/out/complete_assembly_manifest.json`
digest **`e6a7456790736985c5a51b2063ac1c2bc5589f01eca5aff18b6284f02a76b317`**

```json
{
 "schema_version": "chimera.assembly_manifest.v1",
 "assembly_id": "synthetic-two-segment-assembly",
 "units": {"canonical": {"angle_unit":"rad","length_unit":"m","mass_unit":"kg","time_unit":"s"},
           "conflicts": [], "declared_in": [ …4 per-field declarations, all names_si_m_kg_s… ]},
 "readiness": {"dynamics_trial_ready": true, "blocking_codes": [],
   "checks": {"all_required_inputs_present": true, "units_consistent": true,
              "every_component_has_validated_tissue_mass": true,
              "every_authored_frame_bound": true, "no_unbound_frame_is_referenced": true,
              "no_matter_unowned": true, "every_attachment_qualified": true,
              "every_anatomical_port_covered": true},
   "counts": {"inputs_present":5,"inputs_absent":0,"components":4,"matter_claims":4,
              "geometric_candidates":4,"anatomical_ports":2,"mechanical_attachments":2,
              "mechanically_qualified":2,"unresolved_records":3}}
}
```

Mass ownership in that manifest: 4 components — `body-upper` and `body-lower` validated from the
reconstructed tetrahedral regions (1/3 kg + 2/3 kg = **exactly 1.000000 kg** counted); two membrane
patches authored massless; both transported anatomy records present with their assumption strings
but `counts_toward_component_mass: false`, so the same matter is never counted twice. Geometric and
mechanical statuses are kept in separate blocks with an explicit note that neither is derived from
the other. The 3 unresolved records are all severity `note` (`frame_observed_not_bound`).

---

## Real-packet readiness report

`tools/assembly_handoff/out/real_packet_readiness.json`, manifest digest
`afd4cb9fffd18e8d4eb38dd68b225b5562df8dfbbf8f677c32037651972c6a86`.

**Answer: `dynamics_trial_ready = false`.** Nothing was substituted to make it pass.

Evidence admitted as `real`, hashed from bytes (paths repo-relative):

| Packet | Role | sha256 | Schema detected |
|---|---|---|---|
| `.tmp/anatomy_compiler/runs/actual_monkey_fit.json` | anatomy_packet | `a4475550…c3880937` (1 346 469 B) | `anatomy_compiler/v3` |
| `.tmp/anatomy_compiler/runs/attachment_candidates.json` | attachment_candidates | `854f7097…0e1032ae` (62 615 B) | `attachment_candidates.revision_5` |
| `.tmp/anatomy_compiler/runs/admission_actual_monkey.json` | anatomy_admission_ledger | `833ca65b…1d86b4ad` (5 223 B) | recognised, **not integrated** into readiness |

### Exactly what is missing

Blocking records, by code:

* **`required_input_absent` × 3** — three documents a dynamics trial needs exist nowhere in the
  repo. Named at the path each would have to appear at, with what it must supply:
  * `tools/assembly_handoff/inputs/material_volume_document.json` — a reconstructed
    material-volume partition whose regions carry a declared `density_source`; the only thing that
    can turn geometry into validated tissue mass and inertia.
  * `tools/assembly_handoff/inputs/ownership_bindings.json` — components, kinds, local frames, and
    which single matter representation counts toward each mass. The membrane/body double-count
    boundary cannot be inferred; it has to be authored.
  * `tools/assembly_handoff/inputs/mechanical_requirements.json` — the assembly frame tree plus, per
    attachment, anchors, weights, patch area, areal stiffness and the minimum couple stiffness.
* **`unbound_matter_claim` × 9** — every anatomy physiology body (`pelvis`, `femur_r/l`,
  `tibia_r/l`, `humerus/humerus_l`, `radius/radius_l`) carries matter with no owner binding, because
  the ownership document is absent. **17.039978509953905 kg** of transported mass sits uncounted.
* **`attachment_port_unqualified` × 8** — the eight anatomical ports (`radius` and `radius_l`:
  BIClong-P11, BICshort-P8, BRD-P3, PT-P5 and their left-side counterparts) have no mechanically
  qualified attachment; all 32 candidates carry `mechanical_qualification: false`.
* **`root_frame_ambiguous` × 1** — *no authored frame declares a null parent, so there is no
  assembly root to bind anything to.* This one was not predicted by the handoff; it is a genuine
  fourth gap rather than a bug, and it is the most consequential: until someone authors a root
  frame, every quantity in both packets is unplaced.

Note-level (recorded, deliberately non-blocking): `frame_observed_not_bound` × 3 — one anatomy rest
frame and two candidate body frames. They are kept as observations of upstream convention; binding
them would mean inventing a transform nobody authored.

Mass status: 9 claims known, **0 bound to a component, 0 counting toward mass, 0 validated tissue
mass**; `counted_mass_kg = 0.0`, `uncounted_mass_kg = 17.039978…`. Status histogram:
`root_reference_frame_only: 1`, `transported_source_effective: 8`. The admission ledger's own
totals agree (`physically_admitted: 0`, `density_validated: false`) — treated as a claim, and
independently confirmed from the anatomy packet's `mass_kind` / `status` fields.

Policy declaration in the report, all measured rather than asserted: no transported mass promoted,
no waypoint promoted, 0 matter counted without an owner, no densities inferred, no meshes repaired,
no silent defaults, no dynamics executed.

---

## Failures and corrections

Kept here rather than quietly fixed. Items 1–11 came from this session's predecessors (recorded in
their handoff, re-verified by running); items marked **[this session]** were found and fixed now.

**Predecessor defects corrected before this session** (each was a real bug found by execution):
`_require_list` rejecting tuples returned by `compile_document()`; `_summed()` being handed whole
mass dicts instead of floats; `build()` blocking on upstream-observed frames, contradicting the
"observed frames are notes" rule; manifest emitting raw frame dict instead of a sorted list; a
KeyError on a non-existent candidate key in fixture 4; dead placeholder loop raising `StopIteration`;
`compile_document()` refusing an unknown top-level provenance field.

**Rules completed before this session:** `stiffness_kbar` could fall through to `AttachmentSpec`'s
internal default of 1 N/m — a silent default smuggled in via a dependency; duplicate-ownership was
only checked per component, not per claim; `unsupported_surface_mass_claim` was unreachable.

**Corrections to predecessor claims found this session:**

1. **Digest drift.** The handoff reported fixture-1 digest `2010719e9df497aa…`. The code on disk
   produced `eb2c710b…`. Not non-determinism (byte-stable across repeated runs) — the recorded digest
   was stale relative to later edits. Reported digests must be re-measured, not carried forward.
2. **`root_frame_ambiguous` missing from the predicted real-packet gaps.** The handoff predicted 3
   absent inputs + 9 unbound claims + 8 unqualified ports; the run adds a fourth blocking code. Its
   "Expected" list understated the real packet's gaps.

**Defects found and fixed this session** (by adversarial probing beyond the fixture suite, not by
reading the handoff):

3. **[this session] Silent winner between documents claiming one role.** `build()` resolved
   multiple present inputs of the same role by keeping `by_role[role][0]` — no refusal, no record.
   Two ownership documents meant one set of mass bindings silently vanished, changing the ledger.
   Now raises `duplicate_role_input`. Locked in as control (g). This was reachable and invisible:
   fixture 1 still passed with it, which is why probing rather than the suite found it.
4. **[this session] Validation without a declared density source.** `_material_claims()` set
   `mass_status = reconstructed_tissue_volume` unconditionally, so a component could read
   `validated_tissue_mass: true` while the same manifest carried a record saying that mass "is
   reported but never validated" — the manifest contradicted itself on the single most important
   rule. Added status `reconstructed_volume_density_unsourced`; only a sourced reconstruction
   validates, and an unsourced one now also trips `component_mass_not_validated`. Honest caveat:
   upstream `material_volume.compile_document()` already refuses empty *and* whitespace-only sources,
   so this guard is defence in depth rather than the active path — it is stated as such. Fixture 1
   now asserts the invariant directly (every validated component traces to a compiled region with a
   declared source).
5. **[this session] Manifest digests covered absolute host paths.** Every input row stored
   `E:\PythonChimera\…`, so the digest — and therefore any "stable hash" claim built on it — was a
   property of the machine, not the assembly: two agents in two checkouts would report different
   digests for byte-identical inputs. Added `display_path()`: repo-root-relative POSIX paths inside
   the repo, normalised absolute outside; applied to input rows and upstream-dependency evidence.
   **Verified by relocating the whole tree** (adapter + upstream deps + real packets) to a different
   filesystem root: all 10 outputs byte-identical, `real_packet_readiness` digest unchanged at
   `afd4cb9f…`. Fixture digests changed as expected (`eb2c710b… → e6a74567…`).

**Adversarial probe result:** 7/7 rules hold (unsourced density, NaN injection, duplicate component
id, unknown claim ref, omitted weights not defaulted, one matter two owners, duplicate role). The
probe script lives in the session scratchpad; its two findings were promoted into permanent fixture
assertions rather than left as a throwaway.

---

## What the adapter will not do

Never turns transported source-effective anatomy mass into validated tissue mass; never promotes a
tendon waypoint to a membrane patch (a waypoint authored as an endpoint *role* is recorded as
`waypoint_authored_as_port` at note level and its geometric status stays `waypoint_not_a_port`);
leaves missing patch area, stiffness, material or frame information missing; infers no densities,
repairs no meshes, supplies no silent defaults (including via dependencies), alters no physics.
Synthetic inputs are admitted as synthetic with provenance preserved. Other agents' reports were
treated as claims throughout — the two corrections above came from reading files.
