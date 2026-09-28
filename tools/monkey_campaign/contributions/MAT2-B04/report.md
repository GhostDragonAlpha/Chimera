# MAT2-B04 — report (Sergeant-implementer)

Date: 2026-09-28. Arrival `arrival-e62bcc21929a4d9a82be41e65baa68c9`, attempt
`98adbfd891dc4001b1c670a2e477ddd5`, workspace
`E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B04\98adbfd891dc4001b1c670a2e477ddd5`,
slot branch `branch-1` (base head `c525b82c7c3ce0128565424764293a3c85811ab3`,
sparse checkout of `tools/monkey_campaign/contributions/MAT2-B04/`). A different
instance reviews this work. No pushes; publication is lead-serialized.

## What was authored

`frame_forest.json` (`chimera.assembly_frame_forest.v1`, document sha256
`c19705a1123b97b4cf730c44589b8fc2567bcfd9b13ef77814e147515edf685b`) declares the
assembly frame forest the fitted packet references but never declares:

- `assembly_world` (null parent, identity) plus FOUR authored root frames
  `root_pelvis`, `root_thorax`, `root_ulna`, `root_ulna_l` — the exact
  `disconnected_component_roots` of Buffy 02
  (`agent_logs/local_buffy_qwen/assembly_handoff_02.md`).
- Every root transform is composed ONLY from pinned active body declarations in
  `chimanoid.xml` (raw line, field, parent, and sha256 pinned per hop):

  | Root | Chain (lines) | world transform (R = I) |
  | --- | --- | --- |
  | pelvis | L55 | t = (0, 0.73, 6.12323e-17) |
  | thorax | L55, L411 (thorax_dummy), L420 | t = (-0.08, 1.19, 6.12323e-17) |
  | ulna | L55, L411, L420, L534 (humerus), L593 | t = (-0.0915, 0.83455, 0.1577) |
  | ulna_l | L55, L411, L420, L675 (humerus_l), L733 | t = (-0.0915, 0.8345, -0.1577) |

  All active quats are identity (w x y z = 1 0 0 0), so composition is exact
  translation addition; the module recomputes every transform from its embedded
  chain and refuses any hand-tuned digit.
- Containment (`containment_edges`) and mechanical bonds (`bonds`) are separate
  relation lists with disjoint IDs; bond statuses are carried verbatim from
  `actual_monkey_fit.json` (kinematically_preserved / unresolved_body); no
  declared bond crosses components; the four components and nine unresolved
  bodies remain explicit; counted mass stays 0.0; the admission ledger statuses
  are carried through unchanged.
- The fitted packet's coordinates are NOT fused with the authored chain anywhere
  (declared `no_fusion_statement`; fitted frames bind by stable name only). The
  macaque arm osim (`4148aee2...`) and the graph `ref.macaque_arm.body.ulna`
  `world_from_local` are recorded as an independent reference, never merged.
- Decision record in-document: the commissioned lead dispatch (all four roots as
  a forest) supersedes Buffy 02's single-root question; the ontology boundary
  "source XML nesting and fitted packet tree are different representations; no
  automatic replacement" is honored.

## Checks (passes AND failures)

All predictions P1-P8 of the frozen preregistration
(`64d1d779204882f2732b15e1ad4965b2d6d2d319dcd0d5d96c208c2f239d514a`) CONFIRMED;
falsifiers F1-F4 did not fire. Full command/exit records are in
`qualification_receipt.json`. Highlights:

- `assembly_frame_forest.py --self-check` → PASS; C01 round-trip max error
  2.220446049250313e-16 over 1000 probes per root; det = 1.0.
- `semantic_frame.py` (astra-0035) → exit 0 PASS for BOTH ulna packets
  (packet_sha256 `9bfc6c98...`, `72afc1be...`). Pelvis/thorax deliberately have
  no packet (named boundary: the validator's fixed palm kinematic witness is
  appendage semantics; forcing it onto axial bodies would author invented
  semantics).
- `unittest test_assembly_frame_forest` → 25/25 OK, including live resolution of
  the three source pins and nine mutation-refusal tests (tuned digit, swapped
  basis, left-handed frame, dropped root, bond-status promotion, identity
  overlap, mass counting, disconnect-claim flip, cross-component bond).
- `capture_build.py` → `visual_capture.validate_manifest`
  `structurally_valid: true`, 6 views, sheet sha256
  `79688f145879bb53badceb11f583dc02bf8ee79bb5f6f80f0f8e500181e3bf95`,
  byte-identical across runs; context/manifest bind the real sheet and document
  hashes.

**Preserved failure:** the first capture render failed implementer pixel
inspection — the close-up drew full world chains outside a 0.45 m span (clipped
subject at viewport edges) and whole-view labels overlapped ambiguously. That
render was discarded; the renderer was repaired (viewport-surface clipping,
content-fitted close-up, legend stubs, per-root label offsets) and the final
sheet was re-inspected pixel-by-pixel at full resolution: labels readable, no
clipping, clean rows text-free, cameras match the numbers used to project.

## Honest limitations

- Frames are placement only: no geometry, mass, or inertia is validated or
  fabricated; thorax/ulna/ulna_l stay admission-unresolved; pelvis stays
  root-reference-only.
- No authored mapping exists between `anatomy_packet_fitted` and
  `assembly_world_source_chain` coordinates — authoring one would be a guessed
  alignment; binding is by name only.
- The visual leg is a 2D orthographic structured-records sheet of the authored
  document (declared as such); it is not a native-engine 3D render. No GPU or
  mailbox resource was needed or used.
- `chimanoid.xml` is pinned by sha256 + git commit `0ad24b02` (branch
  `forearm-package-20260924`); the byte-identical working copy used for
  line-number verification is `E:\PythonChimera\.tmp\chimanoid.xml`.
- The semantic packet's kinematic witness uses the source-declared elbow hinge
  (axis 0 0 1, range [0, 2.26893]) at q = 0.1 rad with distal coordinates held
  at rest; it witnesses semantic consistency of the authored frame, not a
  dynamics run.

## Submit

Lead-serialized handoff: candidate commit on `branch-1` in this attempt
checkout, submitted to the task inbox by the Lieutenant (no `--submit-pr`
registry call from this worker).
