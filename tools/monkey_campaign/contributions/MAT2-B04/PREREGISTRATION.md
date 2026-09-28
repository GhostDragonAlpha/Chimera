# PREREGISTRATION — MAT2-B04 "Author the real assembly frame forest explicitly"

Frozen BEFORE implementation, measurement, or capture. Arrival
`arrival-e62bcc21929a4d9a82be41e65baa68c9`, attempt
`98adbfd891dc4001b1c670a2e477ddd5`, slot branch `branch-1`, base head
`c525b82c7c3ce0128565424764293a3c85811ab3`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
criteria `c74278905e286045ad068e6080d377ab33b4e0bda5e251bdcfdecdac75bc4722`.

## Statement (frozen)

Author the assembly frame forest for the real anatomy assembly as a versioned,
machine-checked document: the four referenced-but-never-declared component roots
`pelvis`, `thorax`, `ulna`, `ulna_l` (Buffy 02,
`agent_logs/local_buffy_qwen/assembly_handoff_02.md` §Root-frame status) are
declared explicitly with transforms composed ONLY from pinned source
declarations in `chimanoid.xml` (pinned sha256
`675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1`, identical to
`actual_monkey_fit.json` meta.source_identity.raw_sha256 and to the
forearm-package baseline snapshot at commit `0ad24b02`,
path `forearm_package/baseline_snapshot/source_xml/chimanoid.xml`, branch
`forearm-package-20260924`). No transform is tuned, fitted, or inferred from
appearance; containment (frame hierarchy) is a separate relation list from
mechanical bonds; the fitted packet's four disconnected components remain
explicit and no containment edge creates a bond. The macaque arm intake
(`monkeyArm_current.osim`, sha256
`4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895`) and the
creature graph `ref.macaque_arm.*` spatial frames are recorded as an INDEPENDENT
reference forest — never numerically merged with the chimanoid assembly (the
ontology bones-membrane gap forbids automatic replacement between the source XML
nesting and the fitted packet's disconnected ownership tree).

Commissioned decision being implemented (lead dispatch of 2026-09-28): author
ALL FOUR roots as a forest (not a single assembly root). This supersedes Buffy
02's open question "which single root is THE assembly root" by declaring all
four roots with equal standing under one declared `assembly_world` reference
frame; the prepared definition's per-value requirements (parent linkage,
`coordinate_unit`, `handedness`, `scale_to_m`, `origin_m`, `basis_rows`) are
satisfied per root frame. Frames are placement only: no mass is counted, no
geometry is fabricated, and the anatomy admission statuses (pelvis "root
reference frame only"; thorax/ulna/ulna_l "unresolved" for geometry/mass) are
carried through unchanged.

## Frozen source pins (verified live before implementation)

| Artifact | sha256 | Role |
| --- | --- | --- |
| `chimanoid.xml` (`.tmp/chimanoid.xml`; baseline snapshot commit `0ad24b02`, branch `forearm-package-20260924`) | `675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1` | PRIMARY: active body declarations composing the four root transforms |
| `tools/science_funnel/data/macaque_arm/monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` | REFERENCE ONLY: independent arm model (ground/sternum/clavicle/scapula/humerus/ulna chain); never merged |
| `tools/creature_graph/data/creature_graph.json` `ref.macaque_arm.body.*` | recorded by entry (`provenance.source_revision 4fb7dddeec06a0df9525c18f37234a824cb1b5b1`) | REFERENCE ONLY: graph spatial `world_from_local` for the arm reference |
| `.tmp/anatomy_compiler/runs/actual_monkey_fit.json` | `a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937` | fitted packet: 9 segments, 4 components, referenced roots, joint statuses |
| `.tmp/anatomy_compiler/runs/admission_actual_monkey.json` | `833ca65b282eab83180bdbe65bbd8f934924fdd1416c8058d510e5481d86b4ad` | admission statuses carried through unchanged |

Pinned declaration chain (raw line numbers in `chimanoid.xml`; each hop's
`quat` is the identity quaternion `w x y z = 1 0 0 0`, so every composed
rotation is the identity and composition is exact translation addition):

- L55 `<body name="pelvis" pos="       0 0.73     6.12323e-17" quat="1 0 0.0 0.0">` (world child)
- L411 `<body name="thorax_dummy" pos="-0.1007 0.0815 0.0" quat="1.0 0.0 0.0 0.0">`
- L420 `<body name="thorax" pos="   0.0207     0.3785        0" quat="1.0 0.0 0.0 0.0">`
- L534 `<body name="humerus" pos=" -0.0176   -0.007     0.17" quat="1.0 0.0 0.0 0.0">`
- L593 `<body name="ulna" pos="  0.0061  -0.34845  -0.0123" quat="1.0 0.0 0.0 0.0">`
- L675 `<body name="humerus_l" pos=" -0.0176   -0.007    -0.17" quat="1.0 0.0 0.0 0.0">`
- L733 `<body name="ulna_l" pos="  0.0061  -0.3485   0.0123" quat="1.0 0.0 0.0 0.0">`

## Predictions (frozen; each must be confirmed or the outcome recorded)

- **P1 (determinism).** `python assembly_frame_forest.py --emit` writes
  `frame_forest.json` byte-identically on two consecutive runs (sha256 equal).
- **P2 (authored roots/transforms).** The document declares exactly these four
  root frames (R = identity, unit `m`, right-handed, `scale_to_m` 1.0), each
  with its full hop chain and line pins:
  - `world->pelvis` t = `[0.0, 0.73, 6.12323e-17]`
  - `world->thorax` t = `[-0.08, 1.19, 6.12323e-17]` (via thorax_dummy L411)
  - `world->ulna` t = `[-0.0915, 0.83455, 0.1577]` (via thorax L420, humerus L534)
  - `world->ulna_l` t = `[-0.0915, 0.8345, -0.1577]` (via humerus_l L675)
- **P3 (roots reconcile the packet).** Referenced parents minus declared
  segments in `actual_monkey_fit.json` equal exactly
  `{pelvis, thorax, ulna, ulna_l}`; the document's component map has exactly
  these four components with memberships
  pelvis:{femur_r,femur_l,thorax_dummy,tibia_r,tibia_l},
  thorax:{humerus,humerus_l}, ulna:{radius}, ulna_l:{radius_l}.
- **P4 (C01 checks).** For every frame: re-composition from the embedded
  declaration chain reproduces the authored transform exactly (<= 1e-15 per
  component); round-trip `compose(inv(T),T)` = identity within 1e-12 over 1000
  pseudorandom probe points; det(R) = 1 within 1e-12; every root basis
  orthonormal within 1e-12.
- **P5 (semantic frames).** `tools/monkey_campaign/semantic_frame.py` exits 0
  with status PASS on BOTH authored packets `semantic_frame_ulna_r.json` and
  `semantic_frame_ulna_l.json`. Pelvis/thorax get NO semantic packet: the
  module's fixed required pairs and palm kinematic witness are appendage
  semantics; forcing them onto pelvis/thorax would author invented semantics.
  Recorded as a named boundary, not a silent omission.
- **P6 (separation).** The document's `bonds` list contains only
  source-declared packet joints (statuses `kinematically_preserved` /
  `unresolved_body` preserved verbatim from
  `actual_monkey_fit.json`); `bonds` is disjoint from `containment_edges`;
  removing ALL containment edges changes no bond and vice versa (mutation
  check). The four components stay disconnected in the bond graph.
- **P7 (tests).** `python -m unittest test_assembly_frame_forest -v` exits 0.
- **P8 (visual metadata).** `visual_capture.validate_manifest` returns
  `structurally_valid: true` for the frozen anatomy visible_static profile
  subset (views: whole-forest overview, thorax->ulna attachment close-up,
  orthogonal side + oblique; clean views required; task-owned layers:
  frame axes, stable 3D labels, selected bones/joints).

## Falsifiers (frozen)

- **F1 (no guessed alignment).** Any authored root transform whose value cannot
  be recomputed exactly from its pinned declaration chain fails the card. A
  single hand-tuned digit fails.
- **F2 (containment is not a bond).** If containment edges imply bonds (bond
  count/identity changes under containment-only mutation), or any disconnected
  component disappears from the explicit component inventory, the card fails.
- **F3 (no invented semantics/geometry).** If the semantic packets refuse/fail
  for a reason other than a recorded, named limitation, or if any mass/geometry
  status is promoted, the card fails.
- **F4 (visual toggles preserve state).** Diagnostic vs clean views of the same
  view id must share the state binding sha256; any toggle that changes the
  physical state hash fails (card falsifier: "View toggles must preserve the
  physical state hash"; also "Wrong owner/frame, hidden outside placement,
  clipped/occluded subject or label ambiguity fails").

## Frozen probes

Numerical: P1-P7 commands run from this directory with
`/c/Python314/python -B`; exit codes and hashes captured into
`qualification_receipt.json`.

Visual (task-owned subset of the anatomy visible_static profile; the remaining
profile layers — outer envelope, muscle/tendon paths, attachment sites — are
out of B04 scope and inventoried as explicitly absent, never fabricated):
3 views x (diagnostic + clean), single hash-rooted PNG capture validated with
`visual_capture.validate_manifest`, all 16 declared camera fields per view.
