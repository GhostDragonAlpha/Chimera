# MAT2-B05 preregistration — frozen BEFORE implementation or measurement

Task **MAT2-B05** (planning id **B05**) — "Provide real mechanical port requirements".
Attempt `8747399a78324f919445ebbb7486f15c`, arrival `arrival-32ef6502ec5b434a8f5637d3995d4006`.
Isolated attempt checkout of `E:\PythonChimera`; slot branch `branch-1`, prepared base head
`c525b82c7c3ce0128565424764293a3c85811ab3`, sparse path
`tools/monkey_campaign/contributions/MAT2-B05/`. No pushes, no PRs; publication is lead-serialized.

## Identity (frozen)

- criteria_sha256: `6b8fda77de9184ced004bcb6b14b83c0e46139981609a4a9f72975a738ebc8da`
- done_when (verbatim): "Actual port patch/stiffness/couple/weight/frame inputs qualify or remain
  blocked. Material-first addition: Use material-law/interface definitions with declared stiffness,
  pressure limits and attachment area at chosen detail; distinguish engineering assumptions from
  measured anatomy."
- calculation contract **C17 "Finite attachment mechanics"** (verbatim fields): required inputs
  "Patch area/shape, areal stiffness, couple resistance, weights, frame"; calculation "Derive
  attachment stiffness and rotational resistance using the approved finite-area formulation";
  output "Actual anatomical port qualification"; verification "Analytic/independent checks and
  real-parameter bounds; synthetic lambda_min does not transfer".
- verification profile (registry `agent_slots.sqlite3`, read read-only; SHORT task_id **"B05"**):
  id `grasp`, kind `motion`; procedure "Replay approach, attach, load, hold, transfer and release
  with attachment and force telemetry"; diagnostic layers "attachment patches and endpoint IDs",
  "tendon paths", "joint/frame axes", "contact normals and forces", "support state"; views
  "whole-body/trunk relationship", "wrist/digit attachment close-up", "orthogonal view of each
  loaded interface"; clean_view_required true; falsifier "Unresolved owner, nonphysical attachment,
  unsupported transfer, concealment behind the trunk or force/pose inconsistency fails";
  numerical_evidence_required true. The profile OBJECT is re-read read-only from the registry at
  capture time and embedded verbatim in the capture context; it is never hand-copied into
  validation values.
- observation driving scope (card): "Eight ports missing parameters; source tendon points are
  insufficient".

## Clause map (frozen plan; execution recorded in the receipt)

The eight ports are the ENDPOINT sites of the foreign-forearm tendons on `radius`/`radius_l`
(pinned evidence `attachment_candidates.json` rev 5): radius — `BIClong-P11`, `BICshort-P8`,
`BRD-P3`, `PT-P5`; radius_l — `BIClong_l-P11`, `BICshort_l-P8`, `BRD_l-P3`, `PT_l-P5`. The
non-endpoint sites are waypoints and never ports (`port_vs_waypoint_rule`).

Per-input clause disposition (each input QUALIFIES against pinned evidence or remains BLOCKED with
the named missing evidence; nothing is invented):

| C17 input | disposition (frozen intent) |
|---|---|
| frame | BLOCKED as a bound port frame: an accepted ulna-edge correspondence (U-STR roll sign + radius-record supersession acceptance) and an authorized packet-to-forest binding do not exist. RECORDED as qualified references: B04 authored root frames (`root_ulna`, `root_ulna_l`, pinned chains) at exact revision; the fitted radius `local_to_world` as a provisional fitted reference (never merged, B04 `no_fusion_statement`). |
| weights | SPLIT. (a) Real counted arm bone masses QUALIFIED from B03 (`bone_radius` = 0.00910051480229847 kg, researched density provenance, byte-pinned). (b) Carried-load segment weights (physiological hand/forearm masses) BLOCKED: `.osim` segment masses are excluded transported claims (17.039978509953905 kg, never counted) and the hand shell carries ZERO volume-owned mass (B03) with hand assembly unresolved (A04/A05). (c) Patch quadrature weights `w_i` (sum 1) are part of the authored requirement at chosen detail, labeled engineering assumption. |
| patch area/shape | BLOCKED as measured anatomy: source records a POINT per site (no footprint measurement); no accepted correspondence exists that could map a footprint onto the real target bone. An AUTHORED disc-patch requirement at chosen detail is declared alongside, labeled engineering assumption (material-first addition). |
| areal stiffness `kappa_areal_n_m3` | BLOCKED as measured anatomy (no measured value exists in any pinned source). Material-first: stiffness is declared through pinned M04 law definitions and M05 interface constants, `source_status: synthetic_authored`, distinguished from measured anatomy. |
| couple resistance `k_couple_min_n_m_per_rad` | BLOCKED as measured anatomy; carried as an AUTHORED admission requirement (the approved finite-area gate takes `k_couple_min` as an authored requirement unless independently sourced). The synthetic `lambda_min = 32 N*m/rad` demo result is refused as qualification evidence (C17: synthetic lambda_min does not transfer). |
| pressure limits | Declared through pinned M03 `PressureSource` limits (authored limits, named refusals) as the interface pressure-limit definition; labeled engineering assumption. |

Material-first additions consumed at pinned revisions (upstream authority reused verbatim,
unmodified): M05 interface definition (ports are MATERIAL POINTS — rest anchor + mean body
translation; the A1 correction lesson is adopted as the declared anchor convention), M04 passive
law profiles, M03 pressure source limits, B03 counted masses, B04 authored frame forest.

## Falsifiers (frozen; each bites on a TAMPERED COPY, never on the real artifact)

- **F1 input-pin tamper**: flip one byte in a copied input → named refusal `input_pin_mismatch:<id>`;
  the real run must show all pins byte-exact.
- **F2 waypoint promotion**: declare an intermediate waypoint (e.g. `BIClong-P9`) an endpoint port →
  named refusal `waypoint_not_a_port`; the real run reports exactly 8 `candidate_port` + 24
  `waypoint_not_a_port`.
- **F3 qualification promotion**: flip any port's `mechanical_qualification` to true while any
  required input is not qualified (or fabricate a measured value without provenance) → named
  refusal `qualify_requires_all_inputs_qualified` / `unknown_provenance_value`.
- **F4 k-provenance break**: author `k` not equal `kappa_areal * A_patch` (within 1e-3 relative) →
  named refusal `k_provenance_inconsistent`.
- **F5 synthetic lambda_min transfer**: present a synthetic demo `lambda_min` as anatomical
  qualification evidence → named refusal `synthetic_lambda_min_does_not_transfer`.
- **F6 deformed-centroid anchor**: select a deformed-face-centroid anchor convention for a port →
  named refusal `deformed_centroid_anchor_refused` (M05 A1 lesson: ports are material points —
  rest anchor + mean body translation).

## Frozen predictions (P1–P10; exact observed values go in the receipt)

- **P1** The pinned candidate document resolves exactly 8 endpoint ports on `radius`/`radius_l`
  with the IDs above and exactly 24 waypoint refusals; the emitted requirements document's port
  list matches the pinned `mechanical_requirements.cannot_produce.json` list exactly (IDs, bodies,
  missing-parameter names).
- **P2** Every copied input matches its recorded sha256 (byte-exact); source positions are carried
  verbatim (bitwise) from the pinned candidate document with their units strings.
- **P3** Status ledger: frame rows BLOCKED with the two named missing evidence items; weight rows
  carry the qualified B03 counted masses (bitwise `bone_radius` = 0.00910051480229847 kg) and the
  blocked carried-load weights; patch/stiffness/couple rows BLOCKED as measured with authored
  requirements declared at chosen detail, every authored number labeled `synthetic_authored`.
- **P4** All 8 ports emit `mechanical_qualification: false` with every required input row either
  `qualified` (pinned provenance) or `blocked` (named missing evidence).
- **P5** C17 machinery on the declared disc patch: rotational block M = sum_i w_i [a_i]x^T K̄ [a_i]x
  (isotropic K̄ = kappa_areal * A_patch * I); measured weakest eigenvalue matches an independent
  closed-form evaluation within 1e-12 relative; the elongated-rectangle closed form
  {k*b^2, k*a^2, k*(a^2+b^2)} is reproduced within 1e-9 relative; uniform scaling gives lambda
  proportional to s^2 (within 1e-12 relative).
- **P6** Admission gate bites and admits correctly: the documented 40 mm x 2 mm sliver
  counterexample family (anchors x=[-0.02,0], [0.02,0], [0,1e-6] m with k = 80 N/m) measures
  lambda_min ≈ 8e-9 N*m/rad (within a factor 2 of the documented 8e-9), is REJECTED at authored
  requirement 1.0 and ADMITTED at 1e-9.
- **P7** Anchor convention: the document declares and the module enforces material-point port
  anchors (rest anchor + mean body translation); the F6 refusal fires on the tampered convention.
- **P8** Determinism: two runs produce byte-identical canonical documents (no wall-clock, no RNG).
- **P9** No invented values: every numeric in a measured-anatomy slot traces to a pinned input;
  a fabricated footprint value in a measured slot is refused (`unknown_provenance_value`).
- **P10** Pressure-limit row: the declared interface pressure limit is carried from the pinned M03
  state (value + provenance recorded) with the M03 named refusal path intact (delta-p limit
  exceeded refuses).

## Capture predictions (frozen BEFORE any capture code exists)

- Profile object for validation is READ READ-ONLY from `agent_slots.sqlite3`
  (`kanban.cards.MAT2-B05.spec.ontology_qualification.task.verification_profile`), embedded in the
  capture context with the extraction recorded; manifest `task_id` = "B05" (SHORT form).
- Sequence: 8 ticks replaying approach, attach, load, hold, transfer, release of a DECLARED port
  patch against a declared support, driven ONLY by the emitted requirements values (attachment and
  force telemetry recorded per tick; support state declared; no hidden anchors).
- Layout per frame: top row diagnostic viewports [whole-body/trunk relationship | wrist/digit
  attachment close-up | orthogonal view of loaded interface] carrying the five declared diagnostic
  layers; middle row clean viewports (same cameras, no overlays); bottom row telemetry traces
  (patch force magnitude, couple, support state, energy) + footer with tick mapping and state hash.
- Bindings: `subject_sha256` = sha256 of the emitted `mechanical_port_requirements.json`;
  `capture_sha256` = sha256 over the ordered frame PNG bytes (declared rule); every camera field in
  the registry `camera_required_fields` list is declared per viewport (fixed bookmarks; the SUBJECT
  moves, not the camera). `visual_capture.validate_manifest` must return `structurally_valid=True`
  before handoff. Honest limits: CPU structured-records renderer with declared occlusion mode; a
  requirements replay at chosen detail, not a native-runtime run (runtime-facing clauses stay
  recorded at their applicability boundary, never passed by this fixture).

## Checks planned

- `python -B tools/monkey_campaign/contributions/MAT2-B05/mechanical_port_requirements.py derive`
  → emits the document + derivation receipt.
- `python -B tools/monkey_campaign/contributions/MAT2-B05/mechanical_port_requirements.py verify`
  → re-checks pins, ledger, C17 machinery, determinism.
- `python -B tools/monkey_campaign/contributions/MAT2-B05/test_mechanical_port_requirements.py`
  → probes P1–P10 and falsifier bites F1–F6 as assertions.
- Capture build + manifest validation (registry profile object) in the attempt workspace; artifacts
  bound to the exact candidate revision.

Signed-frozen at freeze time by the implementer; any post-freeze change must be recorded as a
numbered correction (A1, A2, ...) with the triggering observation, never silently.

## Correction A1 (pre-implementation, pre-receipt)

Triggering observation: the exact documented admission counterexample geometry was located in the
pinned reference battery (host reference `tools/finite_area_attachment/test_dynamics_and_corrections.py`,
`TestAdmissionGate.LEAD_ANCHORS` — untracked host artifact, recorded by path+content below; the
formulation document and its battery are the C17 authority, not re-derived here).

- **P6 re-issued with exact numbers**: anchors
  `[[0.02, 1e-5, 0], [-0.02, 1e-5, 0], [-0.02, -1e-5, 0], [0.02, -1e-5, 0]]` m (uniform weights
  1/4), scalar k = 80 N/m; closed form `A = sum_i w_i a~_i a~_i^T = diag(4e-4, 1e-10, 0)`,
  `M = k((tr A) I - A)`; eigenvalues `{8e-9, 3.2e-2, 3.200008e-2}` N*m/rad (measured vs closed form
  within 1e-9 relative); REJECTED at authored requirement 1.0 N*m/rad; ADMITTED at 1e-9 with
  consistent provenance `kappa_areal = 1e8 N/m^3`, `A_patch = 8e-7 m^2` (k = 80 = 1e8 * 8e-7).
- **Disc-patch closed form added (P5 completion)**: three rim anchors uniformly on a circle of
  radius r, weights 1/3 each, isotropic K: `A = diag(r^2/2, r^2/2, 0)` in the patch plane basis,
  eigenvalues `{k r^2/2, k r^2/2, k r^2}` — weakest in-plane at half the normal stiffness, matching
  the reference `min_patch_radius` note; measured-vs-closed-form within 1e-12 relative.
