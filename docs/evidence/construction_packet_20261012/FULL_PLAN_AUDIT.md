# FULL_PLAN_AUDIT — GAME_PLAN_ACTION_RPG.md, construction-packet implementation

Date: 2026-10-12. Purpose: completion audit of the standing objective
*"Implement `docs/GAME_PLAN_ACTION_RPG.md`"* — every explicit requirement,
numbered item, named deliverable and gate row mapped to concrete evidence.

## 0. Scope decision (the plan's own words)

The plan is a whole-game design document and explicitly forbids implementing
it wholesale: *"Do not turn this design document into an automatic controller
queue or begin implementing all rows at once."* (§13). It then names the
implementation target:

> **Immediate next engineering assignment:** reconcile the current geometry and
> attachment reference code into one narrowly scoped construction packet: two
> asymmetric material parts, one loose-contact case and one finite-area
> connection, with the same accepted geometry driving loads, native drawing and
> selection. Choose explicit material/DOF ownership and source identities
> before coding. Use a supported test fixture while whole-body locomotion is
> qualified; preserve the existing body force/support work and reuse its
> formulations rather than creating a separate game physics system.

plus the **construction-qualification gate table** (B0–B7, refining M0–M5) and
the **acceptance gallery** (items 1–17). The gates are the plan's own
definition of done for this assignment; everything else in the document
(creatures, CA rules, quests, genre library, full game loop) is explicitly
downstream: *"Free-form shapes, new materials and transport enter as their
corresponding gates pass."* This audit therefore certifies the construction
packet B0–B8 and states what remains outside it (§5).

## 1. Gate table → evidence (all green)

| Gate | Exit evidence claimed | Artifact | Battery (tests) |
|---|---|---|---|
| B0 — identify the real path | baseline recoverable; demo/standalone/target distinguished | `B0_baseline_and_ownership_map.md` (pinned HEAD `f5afc751`, exe SHA-256, every position writer + consumer) | — (map) |
| B1 — compile irregular parts | refusals, positive volumes, mass/COM/inertia, interface orientation, no overlapping ownership, compiler checks reused | `B1_construction_packet_compile.md`, `B1_resource_inventory.json` | `test_construction_packet.py` (23) |
| B2 — contact and attachment physical | off-center reactions/torque; slide/tip/separate/support-removal; numerical envelope measured | `B2_design_and_dof_ownership.md`, `B2_step1_statics_evidence.md`, `B2_step2_3_dynamics_evidence.md` | `test_b2_statics.py` (5) + `test_b2_dynamics.py` (8) |
| B3 — distinct layers | shear/slip distinct; no double mass; render/pick/contact agree; delamination exposes material | `B3_layers_evidence.md` | `test_b3_layers.py` (6) |
| B4 — interactive assembly | rejected edits preserve state; no stale selections; declared release consequence; connection explainable/improvable | `B4_assembly_evidence.md`, `b4_assembly_frame.png` | `test_b4_assembly.py` (6) |
| B5 — reuse + broadened shape | one part/connector in multiple contexts; torus/concave/triple-junction pass; no genre-specific replacement physics | `B5_reuse_evidence.md`, `b5_bridge_frame.png` | `test_b5_bridge.py` (4) + `test_b5_shapes.py` (6) |
| B6 — working processes | inventories conserved; energy closes incl. storage/heat/flux; severing removes only its contribution | `B6_processes_evidence.md` | `test_b6_processes.py` (7) |
| B7 — bound cost, preserve state | no routine full-state round trip; declared 4090 envelope; stable RAM/VRAM/disk plateau | `B7_bounds_evidence.md`, `B7_declared_envelope.json` | `test_b7_bounds.py` (8) |
| B8 — acceptance gallery + §11.3 swept contact | see §2 and §3 | `B8_gallery_evidence.md` | `test_b8_gallery.py` (4) |

**Full regression at this commit: 77 passed** (23+5+8+6+6+4+6+7+8+4),
`python -m pytest tools/construction_packet/ -q`, 128.18 s.

## 2. Acceptance gallery items 1–17 → tests

| # | Item | Covering test(s) |
|---|---|---|
| 1 | Stack two unequal wedges; lift leaves no tensile attachment | B2 `loose_contact_newton3_and_separation`, `tip_site_deactivation`, `slide_against_friction`, `offcenter_load_lever_rule` |
| 2 | Shear three layers (loose/bonded/debonded) | B3 `shear_slip_distinct`, `delamination_exposes_material`, `variants_share_visible_shape` |
| 3 | Partition a lopsided chamber obliquely | B5 `chamber_oblique_partition` (+ B6 chamber law) |
| 4 | Cut a concave or holed section; hole stays a hole | B5 `ring_frame_genus_one`, `ring_refusals_never_fill_silently`, `concave_l_partition` |
| 5 | Three-way junction, no duplicated wall/ambiguous ownership | B5 `triple_junction` |
| 6 | Loose object inside a container | **B8 `gallery_06_loose_object_in_container`** |
| 7 | Refine a thickness-bearing wall — no added material/strength | **B8 `gallery_07_13_retessellation_adds_no_strength`** |
| 8 | Sever an off-center loaded connector | B4 `connect_and_release_no_stale_selections`, `release_declared_consequence`; B5 `connector_failure_redistributes` |
| 9 | Open one of two chambers once transport exists | B6 `valve_equalizes_and_conserves`, `valve_close_sever_patch_contributions` |
| 10 | Reject an edit midway — no partial state reaches the world | B4 `place_and_transactions`; B2 `control_refusals`; B1 refusal suite |
| 11 | Repeat build→load→cut→repair→save→reload; bounded plateau | B4 `save_reload_exact`; B7 `repeated_construction_plateau`, `recovery_preserves_state` |
| 12 | Change display cadence / stop rendering | B7 `independent_physical_clock`, `display_lod_compatible` |
| 13 | Permute IDs and retessellate | B7 `triangle_order_invariance`; **B8 `gallery_07_13`** |
| 14 | Second object from the same recipe library | B5 `part_and_connector_reuse`, `bridge_statics_and_connector_law` |
| 15 | Select a moving part, then delay the edit | **B8 `gallery_15_delayed_edit_revalidates`** |
| 16 | Move quickly toward the thinnest admitted wall | **B8 `gallery_16_fast_thin_wall_no_tunneling`** |
| 17 | Cycle a chamber's volume; energy closes | B6 `chamber_pressure_law_and_energy`, `process_transaction_law` |

## 3. §11.3 swept-contact requirement — how it is met

"A fast part must not tunnel through a wall between discrete checks. Measure
this at the smallest admitted thickness and largest admitted relative motion.
Numerical contact margins are declared approximations, not invisible thick
walls." → B8: declared 15 mm backstop stop (below the 20 mm smallest admitted
thickness, visibly sunk-to, energy-booked, engagement-counted), measured at
the 20 mm plate dropped from 1 m (gallery 16) and at the container wall stop
(gallery 6); the far-face phantom fix (half-space containment) and the
coplanar noise floor are the two correctness repairs the measurement forced.
Full numbers and the two policy failures that shaped the design (spring
cannon 33 m/s; pinned statics 17.9 mm) are in `B8_gallery_evidence.md`.

## 4. Assignment clauses → evidence

| Clause | Evidence |
|---|---|
| two asymmetric material parts | B1 `wedge_a`/`wedge_b` vs closed form + Monte-Carlo inertia |
| one loose-contact case | B2 `loose_contact_newton3_and_separation` |
| one finite-area connection | B2 `weld_finite_area_connector`; B4/B5 weld law + failure |
| same accepted geometry drives loads, native drawing, selection | B3 `render_pick_contact_agree` (pixel↔ray↔contact agree, incl. after vacating a pixel) |
| explicit material/DOF ownership + source identities before coding | `B2_design_and_dof_ownership.md` written before B2 code; B0 ownership map |
| supported test fixture while locomotion qualified | B2 statics fixture on the resident runtime; loco bank untouched |
| preserve/reuse existing body force/support work | rung/penalty formulations reused from the membrane elastic foundation (B0 reuse map); no second physics system — all gates run on the one resident `chimera_engine.exe` runtime |

## 5. Not covered by this packet (honest boundary)

- Everything the plan places **downstream of the gates**: creature
  locomotion qualification, CA material rules (§11.4), genre/quest content,
  workshop/rescue gameplay, the separate game repository and named release.
  The plan itself sequences these after gate passage; none is claimed here.
- The B7 envelope is the *declared* 4090 envelope measured on this host;
  running beside the resident LLM is a separate operating profile the plan
  names but this packet does not certify.
- `docs/evidence/recipe_comparison_20261013/receipt.json` `native_sha256` is
  stale by design after the B8 engine change (connector-suspended cradle;
  physical numbers expected to reproduce on re-run).
- Design input recorded for the next gate (not implemented): the
  **material-declared compliance envelope** — five measured failure modes in
  `B8_gallery_evidence.md` §"Design input".

## 6. Publication record

Branch `WK-ENGINE-PATHS-20260929-PR`, published to
`origin/WK-ENGINE-PATHS-20260929-PR-GAME` (verified by `git ls-remote` after
each push; explicit paths only, `Agent: TIEL` trailer, no force-push).
Chain: `f5afc751` (B0 pin) → `f5fb52c5` (B1) → `20ad07ad`…`2e50935f` (B2) →
`16781e9c`/`94e90f4c` (B3) → `8665f6c3`/`cd6f5955` (B4) → `d56eecb5` (B5) →
`01ff200c` (B6) → `a2155794` (B7) → **B8 commit (branch tip, this audit's
batch)**. Other agents' uncommitted work in the shared checkout was never
staged, reset or rebased.
