# MAT2-B05 report — real mechanical port requirements (Sergeant-implementer)

Date 2026-09-28. Arrival `arrival-32ef6502ec5b434a8f5637d3995d4006`, attempt
`8747399a78324f919445ebbb7486f15c`, workspace
`E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B05\8747399a78324f919445ebbb7486f15c`,
slot branch `branch-1` (prepared base `c525b82c7c3ce0128565424764293a3c85811ab3`, sparse checkout
of `tools/monkey_campaign/contributions/MAT2-B05/`). Remote
`git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git` — REPORTED ONLY; no pushes, no PRs
(publication is lead-serialized). A different instance reviews this work.

Preregistration was committed BEFORE any implementation (039ded76), with correction A1 committed
before implementation (07937aa2: the exact documented admission counterexample replaced the
frozen guess) and correction A2 recorded pre-receipt in the same file (motion-profile video
artifact binding + 360-tick sequence; triggering observations recorded). Final preregistration
sha256 `f8b3faee9453966544dec764fad287bd303b7d7b956becfdefb57b820c2aa9b2` (embedded in the
emitted document).

## done_when execution (criteria sha256
6b8fda77de9184ced004bcb6b14b83c0e46139981609a4a9f72975a738ebc8da, verbatim in the receipt)

"Actual port patch/stiffness/couple/weight/frame inputs qualify or remain blocked." — The eight
ports (radius: BIClong-P11, BICshort-P8, BRD-P3, PT-P5; radius_l: BIClong_l-P11, BICshort_l-P8,
BRD_l-P3, PT_l-P5; pinned candidates rev 5, sha256 854f70976deb10264f052a8dafc3247c9bf6bf03761748e343329ce30e1032ae)
are emitted in `mechanical_port_requirements.json` (canonical sha256
`ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d`) with per-input status rows:
ALL EIGHT PORTS REMAIN BLOCKED (`ports_mechanically_qualified: 0`,
`ports_remaining_blocked: 8`), every blocked row naming its missing evidence, every qualified row
carrying a byte-pinned provenance. No value was invented: measured-anatomy slots stay empty, and
declared engineering requirements are labeled `source_status: synthetic_authored`.

Material-first addition — material-law/interface definitions at chosen detail, distinguished from
measured anatomy:

| input | disposition |
|---|---|
| frame | BLOCKED as a bound port frame (missing: accepted ulna-edge correspondence — U-STR roll sign + radius supersession; authorized packet-to-forest binding). Qualified references recorded from B04's authored frame forest (`root_ulna` origin [-0.09150000000000001, 0.8345500000000001, 0.15770000000000006] m, pinned chains) and the provisional fitted radius record (never merged; B04 `no_fusion_statement`). |
| weights | SPLIT. Qualified: B03 counted arm bone masses (`bone_radius` 0.00910051480229847 kg bitwise; researched density provenance). Blocked: carried-load physiological segment weights (17.039978509953905 kg transported claims never counted; hand shell zero-volume mass; hand assembly unresolved). Quadrature weights w_i = [1/3,1/3,1/3] authored at chosen detail. |
| patch area | BLOCKED as measured (source records exactly one POINT per site; no footprint measurement; correspondence unaccepted). Authored disc requirement at chosen detail: radius 2.5e-3 m, A = 1.9634954084936207e-05 m^2, normal [1,0,0] source-local, 3 rim anchors. |
| areal stiffness | BLOCKED as measured (no measured value in any pinned source; M04 assigns arm regions rigid, synthetic_authored). Authored requirement carried from pinned M05 `K_CONTACT_PA_PER_M` = 1.0e5 Pa/m = 1.0e5 N/m^3 (parsed from pinned bytes, never hand-copied). |
| couple resistance | BLOCKED as measured. Authored admission requirement carried from pinned M05 `K_TWIST_N_M_PER_RAD` = 0.8 N*m/rad. The C17 clause "synthetic lambda_min does not transfer" is enforced by a named refusal (`synthetic_lambda_min_does_not_transfer`). |
| pressure limits | Declared from pinned M03 pressure source (max delta-p 5000.0 Pa, max dV/dt 1e-3 m^3/s, named refusal `pressure_source_delta_p_limit_exceeded` demonstrated). |

C17 (finite attachment mechanics): the module re-implements the approved closed-form block
M = sum_i w_i [a~_i]_x^T Kbar [a~_i]_x with Kbar = kappa_areal*A_patch*I and the admission rule
lambda_min(M) >= k_couple_min (authored requirement). Per port it derives
k = 1.9634954084936207 N/m, lambda_min measured 6.135923e-06 N*m/rad vs closed form k*r^2/2
(relative error 2.761e-16), algebraic matrix identity M == (k r^2/2)(I + n n^T) worst relative
Frobenius error 1.039e-15, and records the REAL-PARAMETER OUTCOME: the declared patch at chosen
detail does NOT meet the declared couple requirement (6.14e-06 << 0.8; sizing to meet it would
need r = 4.766e-02 m) — recorded as `admitted: false`, honestly reinforcing "remain blocked".
The documented 40x20 um sliver counterexample (anchors [[0.02,1e-5,0],[-0.02,1e-5,0],
[-0.02,-1e-5,0],[0.02,-1e-5,0]] m, k=80 N/m) measures lambda_min 8e-9 N*m/rad, is REJECTED at
authored requirement 1.0 and ADMITTED at 1e-9 with consistent provenance (kappa 1e8 N/m^3,
A 8e-7 m^2).

## Verification (exact candidate revision; commands and exit codes in receipts)

1. `python -B mechanical_port_requirements.py derive` -> emits document + derivation_receipt
   (8 pins byte-exact; counts 8/8/24).
2. `python -B mechanical_port_requirements.py verify` -> 14/14 checks PASS (P8 determinism
   byte-identical double derivation; P2 pins; P1 inventory 8+24; P4 all blocked; P3 B03 mass
   bitwise + status ledger; P5 closed form 2.761e-16 + matrix identity 1.039e-15 + eigen-solver
   diagnostic 5.522e-16; P6 admission outcome; P3 ledger; P7 material-point anchors; P10 M03
   limit refusal; P9 ledger shape; P4b document validator). Receipt:
   `work/runs/verification_receipt.json`.
3. `python -B test_mechanical_port_requirements.py` -> 13/13 OK (P1-P10 probes + falsifier
   assertions + waypoint refusal API).
4. `python -B mechanical_port_requirements.py falsifiers` -> all falsifier arms BITE on tampered
   COPIES (copies under `work/falsifiers/`, discarded after logging; log
   `work/runs/falsifier_log.json`): F1 `input_pin_mismatch`; F2 `endpoint_role_inconsistent` +
   `waypoint_not_a_port` (pin guard deliberately re-pinned so the SEMANTIC guard is what bites);
   F3a `qualify_requires_all_inputs_qualified`; F3b `unknown_provenance_value`; F4
   `k_provenance_inconsistent`; F5 `synthetic_lambda_min_does_not_transfer`; F6
   `deformed_centroid_anchor_refused`. Real artifact untouched: committed sha == re-derived
   canonical sha (ef69ee74...).

## Motion-profile capture (grasp; task_id "B05" SHORT form)

- Profile object READ READ-ONLY from `E:\ChimeraWork\monkey-coordination\agent_slots.sqlite3`
  (`kanban.cards.MAT2-B05.spec.ontology_qualification.task.verification_profile`; id `grasp`,
  kind `motion`); registry criteria sha matches the card criteria.
- `build_capture.py` replays the profile procedure from the document's declared values only
  (approach 0-47, attach 48, handover 49-59, hook opens 60, hold A 61-150, handover back
  151-161, transfer carriage 162-261 with the strap UNBOUND, bind B 262, hold B 274-295,
  release 296 with all bond/patch forces bitwise zero and the stored elastic energy dissipated
  as a declared ledger term, unsupported free flight 297-359). Support state is `supported` at
  every tick 0-295 and `unsupported` 297-359 (telemetry in `replay_trace.json`, sha256
  `ec7b690956135d9d0e46f2e8fa78dff907927709e5f0c80d2b58f7690b0b56cd`). Worst energy-ledger
  residual 7.829e-02 J (handover blend actuation bounded by the declared reservoir; constant
  during free flight).
- 360 lossless PNG sheets 2560x840 (top row diagnostic viewports [whole-body/trunk
  relationship | wrist/digit attachment close-up | orthographic face-on of each loaded
  interface] carrying the five declared diagnostic layers; middle row clean pairs with
  identical cameras; bottom row telemetry traces + honest footer). Encoded single artifact
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B05\8747399a78324f919445ebbb7486f15c\capture\capture\capture_mat2_b05_ports_20260928.mkv`
  sha256 `d7f677aad1cb85c9513d64325812a70b3822086c5e8e72574c1a6d6dc5729e60` (2560x840 h264,
  1 tick = 1 video second, slow motion x300 declared in every footer).
- Bindings: `subject_sha256` = sha256(mechanical_port_requirements.json) = ef69ee74...;
  `state_binding` = trace sha ec7b6909...; `capture_sha256` = the mkv sha (single on-disk
  artifact; per-frame hashes in `sheet_layout.frame_files`).
- `visual_capture.validate_manifest` returned `structurally_valid: true` (6 views, profile
  grasp, capture_kind video) BEFORE handoff; receipt `capture_validation_receipt.json`.
- Implementer pixel inspection (not inferred from filenames): tick 10 approach (gap 44.7 mm
  label, support `hook+carriage`), tick 100 hold A (patch disc + 3 rim anchors at the pinned
  source-local position, Fpatch 0.0194 N arrow, strap T=0.180 N, support paths
  `['patch A','strap->A']`), tick 200 transfer (strap unbound, carriage carries, support
  `['hook+carriage']`), tick 262 bind B (T=0.180 N, support adds `patch B`/`strap->B`), tick 320
  post-release (`unsupported paths=[]`, load fallen, magenta release line at 296). Decoded video
  frame 262 vs source frame: mean abs pixel diff 2.179 (lossy yuv420 only). Clean rows carry no
  labels or overlays.

## Honest limits

- The eight anatomical ports remain mechanically UNQUALIFIED — that IS the card's outcome
  ("qualify or remain blocked"); each input is either qualified against pinned evidence or
  blocked with named missing evidence.
- The C17 requirement check runs on DECLARED inputs at chosen detail (engineering assumptions
  labeled synthetic_authored); it demonstrates the approved gate mechanics and the real-parameter
  outcome of the declared values, not anatomy.
- The replay is a CPU structured-records demonstration (translucent carrier box declared as a
  visual carrier, occlusion_mode `mixed`; patch element modeled as an axial ligament of declared
  rest length carrying the document's derived stiffness). It is NOT a native-engine runtime run;
  runtime-facing qualification belongs to downstream checkpoints (V11 / B06 / B07) and is not
  claimed. Post-release free flight shows no floor contact (declared out of scope).
- `agent_logs/local_buffy_qwen/assembly_handoff_02.md` and the finite-area reference
  (`tools/finite_area_attachment/`) are untracked host artifacts; their bytes are sha256-pinned
  in the document and copied where needed (`data/`), so the candidate is self-contained.
- Structural camera validation only; independent visual acceptance belongs to the reviewer.

## Durable lessons (for the Lieutenant to record)

1. Port identity needs TWO records: the display `endpoint_roles` field AND the authoritative
   ordered tendon-path membership. F2 bit because a tampered display field disagreed with the
   path roles — trust the path, cross-check the display.
2. Windows `Path.write_text` silently translates `\n` to `\r\n`, breaking canonical-byte
   determinism claims. Write canonical JSON with `newline="\n"` explicitly.
3. A trigonometric cubic 3x3 eigensolver loses accuracy on clustered spectra (two equal
   eigenvalues); the independent check for declared geometry should be the exact algebraic
   matrix identity, with the generic solver demoted to a declared diagnostic.
4. Energy ledgers must accumulate dissipation ONLY from active force elements — scaling a
   constraint off (handover blends) without stopping its damper term creates phantom dissipation
   that grows monotonically and reads as an energy violation.
5. Motion profiles require a video artifact locator in the committed validator; freeze capture
   predictions with the binding rule "single encoded artifact" from the start.
